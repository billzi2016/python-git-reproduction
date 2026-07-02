"""Git loose object 编解码与校验。

本模块实现 MVP 阶段最关键的数据链路：把原始内容编码为 Git 标准对象、
计算 SHA-1、按 loose object 布局写入 `.pygit/objects`，并在读取时进行
zlib 解压、header 解析、长度校验和 SHA-1 反校验。
"""

from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path

from .errors import ObjectError
from .repository import Repository

VALID_OBJECT_TYPES = {"blob", "tree", "commit", "tag"}


@dataclass(frozen=True)
class GitObject:
    """解码后的 Git 对象。"""

    object_type: str
    content: bytes
    oid: str


def encode_object(object_type: str, content: bytes) -> bytes:
    """把对象类型和内容编码为 Git 标准未压缩字节流。

    Git 的 SHA-1 不是只对文件内容计算，而是对
    `[type] [size]\x00[content]` 整体计算。这个 header 是对象兼容性的
    核心，任何遗漏都会导致官方 Git 无法识别生成的对象 ID。
    """

    if object_type not in VALID_OBJECT_TYPES:
        raise ObjectError(f"unsupported object type: {object_type}")
    header = f"{object_type} {len(content)}".encode("ascii") + b"\x00"
    return header + content


def object_id(object_type: str, content: bytes) -> str:
    """计算对象的 40 位 SHA-1 十六进制 ID。"""

    return hashlib.sha1(encode_object(object_type, content)).hexdigest()


def object_path(repo: Repository, oid: str) -> Path:
    """根据对象 ID 返回 loose object 存储路径。"""

    validate_oid(oid, allow_short=False)
    return repo.objects_dir / oid[:2] / oid[2:]


def validate_oid(oid: str, *, allow_short: bool) -> None:
    """校验对象 ID 是否是合法十六进制字符串。"""

    min_length = 4 if allow_short else 40
    if len(oid) < min_length or len(oid) > 40:
        raise ObjectError(f"invalid object id length: {oid}")
    try:
        int(oid, 16)
    except ValueError as exc:
        raise ObjectError(f"invalid object id: {oid}") from exc


def write_object(repo: Repository, object_type: str, content: bytes) -> str:
    """把对象写入 loose object 数据库并返回 SHA-1。

    写入时使用 zlib 最高压缩等级。对象文件名由内容决定，因此同一内容
    重复写入是幂等操作；已存在的对象无需重写。
    """

    raw = encode_object(object_type, content)
    oid = hashlib.sha1(raw).hexdigest()
    path = object_path(repo, oid)
    if path.exists():
        return oid

    path.parent.mkdir(parents=True, exist_ok=True)
    compressed = zlib.compress(raw, level=zlib.Z_BEST_COMPRESSION)
    tmp_path = path.with_name(f"{path.name}.tmp")
    try:
        tmp_path.write_bytes(compressed)
        tmp_path.replace(path)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
    return oid


def decode_raw_object(raw: bytes, expected_oid: str | None = None) -> GitObject:
    """解析未压缩对象字节并执行长度和 SHA-1 校验。"""

    nul_index = raw.find(b"\x00")
    if nul_index == -1:
        raise ObjectError("object header is missing NUL separator")

    header = raw[:nul_index]
    content = raw[nul_index + 1 :]
    try:
        object_type_raw, size_raw = header.split(b" ", 1)
        object_type = object_type_raw.decode("ascii")
        declared_size = int(size_raw.decode("ascii"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ObjectError("object header is invalid") from exc

    if object_type not in VALID_OBJECT_TYPES:
        raise ObjectError(f"unsupported object type: {object_type}")
    if declared_size != len(content):
        raise ObjectError("object size does not match header")

    actual_oid = hashlib.sha1(raw).hexdigest()
    if expected_oid is not None and actual_oid != expected_oid:
        raise ObjectError("Fatal: Object Corrupted")
    return GitObject(object_type=object_type, content=content, oid=actual_oid)


def read_object(repo: Repository, oid: str) -> GitObject:
    """读取 loose object，解压并验证完整性。"""

    full_oid = resolve_oid(repo, oid)
    path = object_path(repo, full_oid)
    if not path.is_file():
        raise ObjectError(f"object not found: {oid}")
    try:
        raw = zlib.decompress(path.read_bytes())
    except zlib.error as exc:
        raise ObjectError("object zlib data is invalid") from exc
    return decode_raw_object(raw, expected_oid=full_oid)


def resolve_oid(repo: Repository, oid_prefix: str) -> str:
    """把完整或短对象 ID 解析为唯一 40 位 SHA-1。

    短 SHA-1 至少 4 位。解析时只扫描 loose object 目录；packfile 支持会在
    后续阶段加入同一个接口，保证命令层不需要关心对象存储位置。
    """

    validate_oid(oid_prefix, allow_short=True)
    if len(oid_prefix) == 40:
        return oid_prefix

    directory = repo.objects_dir / oid_prefix[:2]
    if not directory.is_dir():
        raise ObjectError(f"object not found: {oid_prefix}")

    matches = []
    rest = oid_prefix[2:]
    for candidate in directory.iterdir():
        if candidate.name.startswith(rest):
            matches.append(oid_prefix[:2] + candidate.name)

    if not matches:
        raise ObjectError(f"object not found: {oid_prefix}")
    if len(matches) > 1:
        raise ObjectError(f"ambiguous object id: {oid_prefix}")
    return matches[0]

