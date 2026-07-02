"""Git Index V2 暂存区读写。

Index 是 Git 工作区和提交对象之间的二进制状态机。本模块只负责 Index V2
文件的编码、解码、校验和条目更新，不直接扫描工作区，也不创建对象。
这样 `add`、`write-tree`、`status` 和 `merge` 都能复用同一份暂存区逻辑。
"""

from __future__ import annotations

import hashlib
import stat
import struct
from dataclasses import dataclass

from .errors import PygitError
from .lockfile import write_file_atomically
from .repository import Repository

INDEX_SIGNATURE = b"DIRC"
INDEX_VERSION = 2
ENTRY_FIXED_SIZE = 62
MAX_PATH_LENGTH_IN_FLAGS = 0xFFF


class IndexError(PygitError):
    """Index 文件格式、校验和或条目内容不合法时抛出。"""


@dataclass(frozen=True)
class IndexEntry:
    """Index V2 中的一条暂存记录。

    字段基本对应 Git Index V2 二进制布局。`path` 使用 Git 内部正斜杠相对
    路径；`oid` 使用 40 位十六进制字符串，写入时会转换为 20 字节原始 SHA-1。
    """

    ctime_s: int
    ctime_ns: int
    mtime_s: int
    mtime_ns: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    file_size: int
    oid: str
    flags: int
    path: str

    @property
    def stage(self) -> int:
        """返回合并冲突 stage 位。普通条目为 0。"""

        return (self.flags >> 12) & 0b11


def mode_from_stat(st_mode: int) -> int:
    """把操作系统 stat mode 转换为 Git index mode。

    MVP 阶段只处理普通文件和可执行文件。目录不会直接进入 index，而是在
    `write-tree` 时由路径层级推导为 tree 对象。
    """

    if stat.S_ISREG(st_mode):
        if st_mode & stat.S_IXUSR:
            return 0o100755
        return 0o100644
    raise IndexError("only regular files can be added to the index")


def entry_from_stat(path: str, oid: str, stat_result: stat_result_like) -> IndexEntry:
    """根据文件 stat 和 blob SHA-1 创建 IndexEntry。"""

    path_length = min(len(path.encode("utf-8")), MAX_PATH_LENGTH_IN_FLAGS)
    return IndexEntry(
        ctime_s=int(stat_result.st_ctime),
        ctime_ns=int(getattr(stat_result, "st_ctime_ns", 0) % 1_000_000_000),
        mtime_s=int(stat_result.st_mtime),
        mtime_ns=int(getattr(stat_result, "st_mtime_ns", 0) % 1_000_000_000),
        dev=int(stat_result.st_dev),
        ino=int(stat_result.st_ino),
        mode=mode_from_stat(stat_result.st_mode),
        uid=int(stat_result.st_uid),
        gid=int(stat_result.st_gid),
        file_size=int(stat_result.st_size) & 0xFFFFFFFF,
        oid=oid,
        flags=path_length,
        path=path,
    )


def read_index(repo: Repository) -> list[IndexEntry]:
    """读取 `.pygit/index` 并返回按路径排序的条目列表。

    空仓库可以没有 index 文件，此时返回空列表。若文件存在，则必须校验
    尾部 SHA-1，避免后续 `write-tree` 使用损坏的暂存区生成错误 tree。
    """

    if not repo.index_path.exists():
        return []

    data = repo.index_path.read_bytes()
    if len(data) < 32:
        raise IndexError("index file is too small")

    body = data[:-20]
    checksum = data[-20:]
    if hashlib.sha1(body).digest() != checksum:
        raise IndexError("index checksum mismatch")

    signature, version, count = struct.unpack(">4sII", body[:12])
    if signature != INDEX_SIGNATURE:
        raise IndexError("index signature is invalid")
    if version != INDEX_VERSION:
        raise IndexError(f"unsupported index version: {version}")

    entries: list[IndexEntry] = []
    offset = 12
    for _ in range(count):
        entry_start = offset
        fixed = body[offset : offset + ENTRY_FIXED_SIZE]
        if len(fixed) != ENTRY_FIXED_SIZE:
            raise IndexError("index entry is truncated")
        (
            ctime_s,
            ctime_ns,
            mtime_s,
            mtime_ns,
            dev,
            ino,
            mode,
            uid,
            gid,
            file_size,
            oid_raw,
            flags,
        ) = struct.unpack(">10I20sH", fixed)
        offset += ENTRY_FIXED_SIZE

        nul_index = body.find(b"\x00", offset)
        if nul_index == -1:
            raise IndexError("index path is missing NUL terminator")
        try:
            path = body[offset:nul_index].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IndexError("index path is not valid utf-8") from exc
        offset = nul_index + 1

        # 每条 entry 从 entry_start 开始按 8 字节边界对齐。padding 属于 entry，
        # 不是整个文件，因此必须用 entry_start 计算，否则多条目时会错位。
        while (offset - entry_start) % 8 != 0:
            if offset >= len(body):
                raise IndexError("index entry padding is truncated")
            if body[offset] != 0:
                raise IndexError("index entry padding is invalid")
            offset += 1

        entries.append(
            IndexEntry(
                ctime_s=ctime_s,
                ctime_ns=ctime_ns,
                mtime_s=mtime_s,
                mtime_ns=mtime_ns,
                dev=dev,
                ino=ino,
                mode=mode,
                uid=uid,
                gid=gid,
                file_size=file_size,
                oid=oid_raw.hex(),
                flags=flags,
                path=path,
            )
        )

    while offset < len(body):
        if offset + 8 > len(body):
            raise IndexError("index extension header is truncated")
        signature = body[offset : offset + 4]
        extension_size = struct.unpack(">I", body[offset + 4 : offset + 8])[0]
        offset += 8
        if offset + extension_size > len(body):
            raise IndexError(f"index extension {signature!r} is truncated")
        # 当前实现不会写扩展区，但读取时必须能跳过扩展区，否则官方 Git
        # 写入 TREE、REUC 等扩展后，本项目会误判 index 损坏。
        offset += extension_size
    return sorted(entries, key=lambda entry: entry.path)


def encode_index(entries: list[IndexEntry]) -> bytes:
    """把条目列表编码为完整 Index V2 字节流。"""

    sorted_entries = sorted(entries, key=lambda entry: entry.path)
    chunks = [struct.pack(">4sII", INDEX_SIGNATURE, INDEX_VERSION, len(sorted_entries))]
    for entry in sorted_entries:
        chunks.append(encode_entry(entry))
    body = b"".join(chunks)
    return body + hashlib.sha1(body).digest()


def encode_entry(entry: IndexEntry) -> bytes:
    """编码单条 IndexEntry，并补齐到 8 字节边界。"""

    path_bytes = entry.path.encode("utf-8")
    flags = (entry.flags & ~MAX_PATH_LENGTH_IN_FLAGS) | min(len(path_bytes), MAX_PATH_LENGTH_IN_FLAGS)
    fixed = struct.pack(
        ">10I20sH",
        entry.ctime_s,
        entry.ctime_ns,
        entry.mtime_s,
        entry.mtime_ns,
        entry.dev,
        entry.ino,
        entry.mode,
        entry.uid,
        entry.gid,
        entry.file_size,
        bytes.fromhex(entry.oid),
        flags,
    )
    raw = fixed + path_bytes + b"\x00"
    padding = (8 - (len(raw) % 8)) % 8
    return raw + (b"\x00" * padding)


def write_index(repo: Repository, entries: list[IndexEntry]) -> None:
    """把 IndexEntry 列表原子写入 `.pygit/index`。"""

    write_file_atomically(repo.index_path, encode_index(entries))


def replace_entries(existing: list[IndexEntry], new_entries: list[IndexEntry]) -> list[IndexEntry]:
    """按路径替换 index 条目。

    `git add` 对同一路径应更新原条目而不是追加重复记录。这里集中处理
    路径去重，后续 stage 1/2/3 的冲突条目扩展也可以在这里演进。
    """

    by_path = {entry.path: entry for entry in existing}
    for entry in new_entries:
        by_path[entry.path] = entry
    return sorted(by_path.values(), key=lambda entry: entry.path)


class stat_result_like:
    """供类型检查和注释阅读使用的 stat 结果协议占位类。"""

    st_ctime: float
    st_ctime_ns: int
    st_mtime: float
    st_mtime_ns: int
    st_dev: int
    st_ino: int
    st_mode: int
    st_uid: int
    st_gid: int
    st_size: int
