"""stash 临时保存工作区状态。

基础版本把当前工作区快照写成 tree，再创建一个临时 commit 并把 commit ID
压入 `.pygit/refs/stash`。apply/pop 会把该快照恢复到工作区和 index。
后续可以在这个结构上扩展为更接近 Git 的 index commit + worktree commit
以及三方合并式应用。
"""

from __future__ import annotations

from pathlib import Path

from .checkout import materialize_tree_plan, remove_tracked_files, write_tree_to_worktree
from .commit import create_commit, parse_commit
from .errors import PygitError
from .index import IndexEntry, entry_from_stat, write_index
from .lockfile import write_file_atomically
from .objects import write_object
from .refs import current_commit
from .repository import Repository
from .reset import reset
from .status import collect_status
from .working_tree import build_tree_from_entries, iter_worktree_files
from .merge import MergeConflict, merge_trees, write_conflict_files


class StashError(PygitError):
    """stash 栈为空、工作区干净或应用失败时抛出。"""


def stash_path(repo: Repository) -> Path:
    """返回 `.pygit/refs/stash` 文件路径。"""

    return repo.gitdir / "refs" / "stash"


def stash_push(repo: Repository, message: str = "WIP") -> str:
    """保存当前工作区快照，压入 stash 栈，并恢复到 HEAD。"""

    status = collect_status(repo)
    if status.is_clean():
        raise StashError("no local changes to save")

    tree_oid = build_worktree_tree(repo)
    parent = current_commit(repo)
    parents = [parent] if parent is not None else []
    stash_oid = create_commit(repo, tree_oid, parents, f"stash: {message}\n")
    append_stash(repo, stash_oid)

    if parent is not None:
        reset(repo, parent, "--hard")
    else:
        write_index(repo, [])
    return stash_oid


def stash_apply(repo: Repository) -> str:
    """应用 stash 栈顶快照，但不移除栈记录。"""

    oid = peek_stash(repo)
    apply_stash_commit(repo, oid)
    return oid


def stash_pop(repo: Repository) -> str:
    """应用 stash 栈顶快照，并在成功后移除该记录。"""

    oid = peek_stash(repo)
    apply_stash_commit(repo, oid)
    entries = read_stash_stack(repo)
    write_stash_stack(repo, entries[:-1])
    return oid


def build_worktree_tree(repo: Repository) -> str:
    """把当前工作区所有普通文件写成 tree。"""

    entries: list[IndexEntry] = []
    for path, file_path in iter_worktree_files(repo):
        oid = write_object(repo, "blob", file_path.read_bytes())
        entries.append(entry_from_stat(path, oid, file_path.stat()))
    return build_tree_from_entries(repo, entries)


def apply_stash_commit(repo: Repository, oid: str) -> None:
    """把 stash commit 以三方合并方式恢复到工作区和 index。"""

    commit = parse_commit(repo, oid)
    if not commit.parents:
        target_files = materialize_tree_plan(repo, commit.tree)
        remove_tracked_files(repo)
        write_index(repo, write_tree_to_worktree(repo, target_files))
        return

    current = current_commit(repo)
    if current is None:
        target_files = materialize_tree_plan(repo, commit.tree)
        remove_tracked_files(repo)
        write_index(repo, write_tree_to_worktree(repo, target_files))
        return

    result = merge_trees(repo, commit.parents[0], current, oid, "stash")
    remove_tracked_files(repo)
    clean_entries = write_tree_to_worktree(repo, result.clean_files)
    write_index(repo, clean_entries + result.conflict_entries)
    write_conflict_files(repo, result.conflict_files)
    if result.conflict_files:
        raise MergeConflict("stash conflicts detected")


def read_stash_stack(repo: Repository) -> list[str]:
    """读取 stash 栈，文件不存在时返回空栈。"""

    path = stash_path(repo)
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_stash_stack(repo: Repository, entries: list[str]) -> None:
    """原子写回 stash 栈。"""

    data = "".join(f"{entry}\n" for entry in entries).encode("ascii")
    write_file_atomically(stash_path(repo), data)


def append_stash(repo: Repository, oid: str) -> None:
    """把新 stash 记录追加到栈顶。"""

    entries = read_stash_stack(repo)
    entries.append(oid)
    write_stash_stack(repo, entries)


def peek_stash(repo: Repository) -> str:
    """返回 stash 栈顶 commit。"""

    entries = read_stash_stack(repo)
    if not entries:
        raise StashError("no stash entries")
    return entries[-1]
