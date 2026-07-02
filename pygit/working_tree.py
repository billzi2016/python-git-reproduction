"""工作区扫描与树对象生成。

本模块负责把用户输入路径转换为可添加文件列表，并把 index 中的扁平路径
组装成 Git tree 对象。它依赖 objects 和 index 的底层能力，但不直接处理
CLI 参数，保持工作流逻辑可测试。
"""

from __future__ import annotations

from pathlib import Path

from .errors import PathSafetyError
from .index import IndexEntry, entry_from_stat, read_index, replace_entries, write_index
from .objects import read_object, write_object
from .paths import ensure_within_directory, normalize_repo_relative
from .repository import PYGIT_DIR_NAME, Repository


def iter_addable_files(repo: Repository, targets: list[Path]) -> list[Path]:
    """根据用户输入路径返回可加入 index 的普通文件列表。

    MVP 阶段先忽略 `.pygit` 目录，并递归展开目录。后续 `.pygit/info/exclude`
    和 `.gitignore` 风格规则会在 ignore 模块中集中实现。
    """

    files: list[Path] = []
    for target in targets:
        safe_target = ensure_within_directory(repo.worktree, repo.worktree / target)
        if not safe_target.exists():
            raise PathSafetyError(f"path does not exist: {target}")
        if safe_target.is_file():
            if PYGIT_DIR_NAME not in safe_target.relative_to(repo.worktree).parts:
                files.append(safe_target)
            continue
        if safe_target.is_dir():
            for child in sorted(safe_target.rglob("*")):
                if PYGIT_DIR_NAME in child.relative_to(repo.worktree).parts:
                    continue
                if child.is_file():
                    files.append(child)
            continue
        raise PathSafetyError(f"unsupported path type: {target}")
    return sorted(set(files))


def add_paths(repo: Repository, targets: list[Path]) -> list[IndexEntry]:
    """把路径写入对象库并更新 index。

    返回:
        本次新增或更新的 IndexEntry 列表，便于 CLI 或测试确认行为。
    """

    new_entries: list[IndexEntry] = []
    for file_path in iter_addable_files(repo, targets):
        relative_path = normalize_repo_relative(repo.worktree, file_path)
        content = file_path.read_bytes()
        oid = write_object(repo, "blob", content)
        new_entries.append(entry_from_stat(relative_path, oid, file_path.stat()))

    entries = replace_entries(read_index(repo), new_entries)
    write_index(repo, entries)
    return new_entries


def build_tree_from_index(repo: Repository) -> str:
    """从当前 index 生成根 tree 对象，并返回根 tree SHA-1。"""

    entries = read_index(repo)
    root = TreeNode()
    for entry in entries:
        if entry.stage != 0:
            raise PathSafetyError("cannot write tree with unresolved conflict entries")
        root.add(entry.path.split("/"), entry)
    return write_tree_node(repo, root)


class TreeNode:
    """内存中的树节点，用于把扁平 index 路径组装成层级 tree。"""

    def __init__(self) -> None:
        """创建空树节点。"""

        self.files: dict[str, IndexEntry] = {}
        self.children: dict[str, TreeNode] = {}

    def add(self, parts: list[str], entry: IndexEntry) -> None:
        """按路径片段插入 index 条目。"""

        if len(parts) == 1:
            self.files[parts[0]] = entry
            return
        head, *tail = parts
        self.children.setdefault(head, TreeNode()).add(tail, entry)


def write_tree_node(repo: Repository, node: TreeNode) -> str:
    """递归写入 tree 节点并返回该节点 SHA-1。"""

    tree_entries: list[tuple[str, str, str]] = []
    for name, child in node.children.items():
        child_oid = write_tree_node(repo, child)
        tree_entries.append(("40000", name, child_oid))
    for name, entry in node.files.items():
        # tree 中普通文件 mode 使用八进制字符串，不带 Python 的 `0o` 前缀。
        tree_entries.append((format(entry.mode, "o"), name, entry.oid))

    content = encode_tree_entries(tree_entries)
    return write_object(repo, "tree", content)


def encode_tree_entries(entries: list[tuple[str, str, str]]) -> bytes:
    """编码 tree 对象内容。

    Git tree 条目格式是 `[mode] [name]\x00[20-byte sha1]`。SHA-1 在 tree 中
    使用原始 20 字节，而不是 40 位十六进制文本，这是常见兼容性陷阱。
    """

    chunks: list[bytes] = []
    for mode, name, oid in sorted(entries, key=lambda item: item[1]):
        chunks.append(f"{mode} {name}".encode("utf-8") + b"\x00" + bytes.fromhex(oid))
    return b"".join(chunks)


def format_tree_pretty(repo: Repository, content: bytes) -> bytes:
    """把 tree 原始内容格式化为类似 `git cat-file -p` 的文本。"""

    offset = 0
    lines: list[str] = []
    while offset < len(content):
        nul = content.find(b"\x00", offset)
        if nul == -1:
            raise PathSafetyError("tree entry is missing NUL separator")
        header = content[offset:nul].decode("utf-8")
        mode, name = header.split(" ", 1)
        oid_raw = content[nul + 1 : nul + 21]
        if len(oid_raw) != 20:
            raise PathSafetyError("tree entry sha1 is truncated")
        oid = oid_raw.hex()
        object_type = read_object(repo, oid).object_type
        lines.append(f"{mode} {object_type} {oid}\t{name}")
        offset = nul + 21
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")

