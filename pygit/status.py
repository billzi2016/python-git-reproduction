"""工作区状态比较。

status 需要比较 HEAD tree、index 和工作区三方状态。本模块只负责计算状态
结果，不直接打印 CLI 文本，便于后续 porcelain、测试和潜在机器可读输出复用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .commit import parse_commit
from .index import read_index
from .objects import object_id
from .refs import current_commit
from .repository import Repository
from .working_tree import iter_worktree_files, read_tree_recursive


@dataclass(frozen=True)
class StatusResult:
    """三方状态比较结果。"""

    staged_added: list[str] = field(default_factory=list)
    staged_modified: list[str] = field(default_factory=list)
    staged_deleted: list[str] = field(default_factory=list)
    unstaged_modified: list[str] = field(default_factory=list)
    unstaged_deleted: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        """判断工作区、index 和 HEAD 是否完全一致。"""

        return not any(
            [
                self.staged_added,
                self.staged_modified,
                self.staged_deleted,
                self.unstaged_modified,
                self.unstaged_deleted,
                self.untracked,
            ]
        )


def collect_status(repo: Repository) -> StatusResult:
    """计算当前仓库状态。

    比较规则:
        1. HEAD tree vs index：得到已暂存新增、修改、删除。
        2. index vs 工作区：得到未暂存修改、删除。
        3. 工作区 vs index：得到未追踪文件。
    """

    head_entries = head_tree_entries(repo)
    index_entries = {entry.path: entry for entry in read_index(repo) if entry.stage == 0}
    worktree_files = {path: file_path for path, file_path in iter_worktree_files(repo)}

    staged_added: list[str] = []
    staged_modified: list[str] = []
    staged_deleted: list[str] = []
    for path in sorted(set(head_entries) | set(index_entries)):
        head_oid = head_entries.get(path)
        index_entry = index_entries.get(path)
        if head_oid is None and index_entry is not None:
            staged_added.append(path)
        elif head_oid is not None and index_entry is None:
            staged_deleted.append(path)
        elif index_entry is not None and head_oid != index_entry.oid:
            staged_modified.append(path)

    unstaged_modified: list[str] = []
    unstaged_deleted: list[str] = []
    for path, entry in sorted(index_entries.items()):
        file_path = worktree_files.get(path)
        if file_path is None:
            unstaged_deleted.append(path)
            continue
        content = file_path.read_bytes()
        if object_id("blob", content) != entry.oid:
            unstaged_modified.append(path)

    untracked = sorted(path for path in worktree_files if path not in index_entries)
    return StatusResult(
        staged_added=staged_added,
        staged_modified=staged_modified,
        staged_deleted=staged_deleted,
        unstaged_modified=unstaged_modified,
        unstaged_deleted=unstaged_deleted,
        untracked=untracked,
    )


def head_tree_entries(repo: Repository) -> dict[str, str]:
    """返回 HEAD commit 的 tree 扁平路径表。

    空仓库没有 HEAD commit，此时 HEAD tree 视为空。
    """

    commit_oid = current_commit(repo)
    if commit_oid is None:
        return {}
    commit = parse_commit(repo, commit_oid)
    return {path: oid for path, _mode, oid in read_tree_recursive(repo, commit.tree)}


def format_status(result: StatusResult) -> str:
    """把状态结果格式化为面向用户的文本。"""

    if result.is_clean():
        return "nothing to commit, working tree clean\n"

    lines: list[str] = []
    if result.staged_added or result.staged_modified or result.staged_deleted:
        lines.append("Changes to be committed:")
        lines.extend(f"  new file:   {path}" for path in result.staged_added)
        lines.extend(f"  modified:   {path}" for path in result.staged_modified)
        lines.extend(f"  deleted:    {path}" for path in result.staged_deleted)
        lines.append("")

    if result.unstaged_modified or result.unstaged_deleted:
        lines.append("Changes not staged for commit:")
        lines.extend(f"  modified:   {path}" for path in result.unstaged_modified)
        lines.extend(f"  deleted:    {path}" for path in result.unstaged_deleted)
        lines.append("")

    if result.untracked:
        lines.append("Untracked files:")
        lines.extend(f"  {path}" for path in result.untracked)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

