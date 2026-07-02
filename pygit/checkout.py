"""checkout 与 switch 工作区切换。

checkout 是危险命令：它会删除旧版本追踪文件、写入目标 commit 的 blob，
并刷新 index 和 HEAD。本模块采用保守策略：只有当前 status 完全干净时才
允许切换；切换前先完整校验目标 commit/tree/blob，避免删除旧文件后发现
目标对象损坏。
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from .commit import parse_commit
from .errors import PygitError, PathSafetyError
from .index import IndexEntry, entry_from_stat, read_index, write_index
from .objects import read_object
from .paths import ensure_within_directory
from .refs import read_ref, set_detached_head, set_head_ref
from .repository import Repository
from .status import collect_status
from .working_tree import read_tree_recursive


class CheckoutError(PygitError):
    """checkout/switch 前置校验或工作区重写失败时抛出。"""


def checkout_target(repo: Repository, target: str) -> str:
    """切换到分支名或 commit SHA-1。

    返回:
        目标 commit SHA-1。
    """

    status = collect_status(repo)
    if not status.is_clean():
        raise CheckoutError("working tree is not clean")

    branch_ref = f"refs/heads/{target}"
    branch_oid = read_ref(repo, branch_ref)
    if branch_oid is not None:
        checkout_commit(repo, branch_oid, branch_ref=branch_ref)
        return branch_oid

    # read_object 支持唯一短 SHA-1；读取后再要求对象类型为 commit。
    obj = read_object(repo, target)
    if obj.object_type != "commit":
        raise CheckoutError("checkout target is not a commit")
    checkout_commit(repo, obj.oid, branch_ref=None)
    return obj.oid


def switch_branch(repo: Repository, branch: str) -> str:
    """切换到本地分支。

    `switch` 与 `checkout` 的差异在于它不接受裸 commit。这样可以避免用户
    误以为自己仍在分支上，实际却进入游离 HEAD。
    """

    branch_ref = f"refs/heads/{branch}"
    branch_oid = read_ref(repo, branch_ref)
    if branch_oid is None:
        raise CheckoutError(f"branch not found: {branch}")
    status = collect_status(repo)
    if not status.is_clean():
        raise CheckoutError("working tree is not clean")
    checkout_commit(repo, branch_oid, branch_ref=branch_ref)
    return branch_oid


def checkout_commit(repo: Repository, commit_oid: str, *, branch_ref: str | None) -> None:
    """把工作区、index 和 HEAD 切换到指定 commit。

    顺序很重要：
        1. 解析 commit 和 tree，读取所有 blob，确认目标对象完整。
        2. 删除当前 index 中的旧追踪文件。
        3. 写入目标 tree 的文件并重建 index。
        4. 最后更新 HEAD。

    这样即使目标对象损坏，也不会提前破坏用户工作区。
    """

    commit = parse_commit(repo, commit_oid)
    target_files = materialize_tree_plan(repo, commit.tree)

    remove_tracked_files(repo)
    new_entries = write_tree_to_worktree(repo, target_files)
    write_index(repo, new_entries)

    if branch_ref is None:
        set_detached_head(repo, commit_oid)
    else:
        set_head_ref(repo, branch_ref)


def materialize_tree_plan(repo: Repository, tree_oid: str) -> list[tuple[str, str, str, bytes]]:
    """读取目标 tree 中所有 blob，形成可写入计划。

    返回:
        `(path, mode, oid, content)` 列表。
    """

    plan: list[tuple[str, str, str, bytes]] = []
    for path, mode, oid in read_tree_recursive(repo, tree_oid):
        blob = read_object(repo, oid)
        if blob.object_type != "blob":
            raise CheckoutError(f"tree entry is not a blob: {path}")
        plan.append((path, mode, oid, blob.content))
    return plan


def remove_tracked_files(repo: Repository) -> None:
    """删除当前 index 记录的旧追踪文件。

    这里只删除 index 中明确登记的普通文件路径，不递归清理目录，也不触碰
    未追踪文件。路径仍然经过工作区边界校验，避免损坏用户电脑其它位置。
    """

    for entry in read_index(repo):
        file_path = ensure_within_directory(repo.worktree, repo.worktree / entry.path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()


def write_tree_to_worktree(repo: Repository, files: list[tuple[str, str, str, bytes]]) -> list[IndexEntry]:
    """把目标 tree 文件写入工作区，并返回新的 index 条目。"""

    entries: list[IndexEntry] = []
    for path, mode, oid, content in files:
        file_path = ensure_within_directory(repo.worktree, repo.worktree / path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        if mode == "100755":
            current_mode = file_path.stat().st_mode
            os.chmod(file_path, current_mode | 0o111)
        entry = entry_from_stat(path, oid, file_path.stat())
        # tree 中的 mode 是目标提交的一部分。文件系统可能因为 umask 或平台差异
        # 返回不同可执行位，因此这里用 tree mode 修正 index mode，保持提交语义。
        entries.append(replace(entry, mode=int(mode, 8)))
    return entries
