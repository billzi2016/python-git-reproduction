"""reset 工作流。

reset 会移动当前 HEAD 目标，并按模式选择是否刷新 index 和工作区。由于
`--hard` 具有破坏性，本模块复用 checkout 的目标对象预读和工作区写入逻辑，
并且只删除当前 index 中明确追踪的文件，不删除未追踪文件。
"""

from __future__ import annotations

from dataclasses import replace

from .checkout import materialize_tree_plan, remove_tracked_files, write_tree_to_worktree
from .commit import parse_commit
from .errors import PygitError
from .index import IndexEntry, write_index
from .objects import read_object
from .refs import update_head_target
from .repository import Repository
from .revision import resolve_commit
from .working_tree import read_tree_recursive


class ResetError(PygitError):
    """reset 目标或模式不合法时抛出。"""


def reset(repo: Repository, target: str, mode: str = "--mixed") -> str:
    """执行 reset 并返回目标 commit SHA-1。"""

    if mode not in {"--soft", "--mixed", "--hard"}:
        raise ResetError(f"unsupported reset mode: {mode}")

    commit_oid = resolve_commit(repo, target)
    commit = parse_commit(repo, commit_oid)

    # 先解析目标 tree，确认对象完整，再移动 HEAD 或改写 index/工作区。
    if mode == "--soft":
        update_head_target(repo, commit_oid)
        return commit_oid

    if mode == "--mixed":
        entries = index_entries_from_tree(repo, commit.tree)
        update_head_target(repo, commit_oid)
        write_index(repo, entries)
        return commit_oid

    target_files = materialize_tree_plan(repo, commit.tree)
    update_head_target(repo, commit_oid)
    remove_tracked_files(repo)
    write_index(repo, write_tree_to_worktree(repo, target_files))
    return commit_oid


def index_entries_from_tree(repo: Repository, tree_oid: str) -> list[IndexEntry]:
    """把 tree 展开为 index 条目，不改写工作区。

    mixed reset 和 read-tree 都需要这种能力。由于没有工作区 stat 信息，这里
    使用 0 填充时间戳和 inode 等文件系统字段，并用 blob 内容长度填 file_size。
    """

    entries: list[IndexEntry] = []
    for path, mode, oid in read_tree_recursive(repo, tree_oid):
        blob = read_object(repo, oid)
        if blob.object_type != "blob":
            raise ResetError(f"tree entry is not a blob: {path}")
        flags = min(len(path.encode("utf-8")), 0xFFF)
        entries.append(
            IndexEntry(
                ctime_s=0,
                ctime_ns=0,
                mtime_s=0,
                mtime_ns=0,
                dev=0,
                ino=0,
                mode=int(mode, 8),
                uid=0,
                gid=0,
                file_size=len(blob.content) & 0xFFFFFFFF,
                oid=oid,
                flags=flags,
                path=path,
            )
        )
    return entries

