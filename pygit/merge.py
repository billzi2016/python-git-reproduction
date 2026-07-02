"""分支合并引擎。

本模块实现 merge 的基础图算法和三方文件选择。它不直接解析 CLI 参数，
只接收已经打开的 Repository 和用户目标修订名。当前版本支持最近公共祖先、
快进合并、路径级三方合并、冲突文件标记和 index stage 1/2/3 写入。
"""

from __future__ import annotations

from .checkout import materialize_tree_plan, remove_tracked_files, write_tree_to_worktree
from .commit import create_commit, parse_commit
from .errors import PygitError
from .index import IndexEntry, write_index
from .objects import read_object, write_object
from .refs import current_commit, update_head_target
from .repository import Repository
from .revision import resolve_commit
from .status import collect_status
from .working_tree import build_tree_from_entries, read_tree_recursive


class MergeError(PygitError):
    """merge 目标、仓库状态或三方合并过程不合法时抛出。"""


class MergeConflict(MergeError):
    """发生内容冲突时抛出。冲突文件和 index stage 已经写入工作区。"""


DELETE = object()
CONFLICT = object()


def merge(repo: Repository, target: str, message: str | None = None) -> str:
    """把目标分支或 commit 合并到当前 HEAD。

    返回:
        如果快进，返回目标 commit；如果非快进自动合并成功，返回新建的 merge
        commit。发生冲突时，会先写入冲突标记和 stage 条目，再抛出 MergeConflict。
    """

    if not collect_status(repo).is_clean():
        raise MergeError("working tree is not clean")

    ours = current_commit(repo)
    if ours is None:
        raise MergeError("cannot merge without commits")
    theirs = resolve_commit(repo, target)
    if ours == theirs:
        return ours

    base = lowest_common_ancestor(repo, ours, theirs)
    if base is None:
        raise MergeError("no common ancestor found")

    if base == ours:
        fast_forward(repo, theirs)
        return theirs

    result = merge_trees(repo, base, ours, theirs, target)
    remove_tracked_files(repo)
    clean_entries = write_tree_to_worktree(repo, result.clean_files)
    write_index(repo, clean_entries + result.conflict_entries)
    write_conflict_files(repo, result.conflict_files)
    if result.conflict_files:
        raise MergeConflict("merge conflicts detected")
    tree_oid = build_tree_from_entries(repo, clean_entries)
    merge_message = message or f"Merge {target} into HEAD\n"
    merge_oid = create_commit(repo, tree_oid, [ours, theirs], merge_message)
    update_head_target(repo, merge_oid)
    return merge_oid


def fast_forward(repo: Repository, target_commit: str) -> None:
    """执行快进合并。

    快进必须同时移动当前 HEAD 目标、重写工作区并刷新 index。这里先读取目标
    tree 的所有 blob，确认对象完整后再删除旧追踪文件，避免半写入状态。
    """

    target = parse_commit(repo, target_commit)
    files = materialize_tree_plan(repo, target.tree)
    update_head_target(repo, target_commit)
    remove_tracked_files(repo)
    write_index(repo, write_tree_to_worktree(repo, files))


def ancestors_by_distance(repo: Repository, start: str) -> dict[str, int]:
    """广度优先遍历 commit DAG，返回祖先到起点的最短距离。"""

    distances: dict[str, int] = {}
    queue: list[tuple[str, int]] = [(start, 0)]
    while queue:
        oid, distance = queue.pop(0)
        if oid in distances:
            continue
        distances[oid] = distance
        commit = parse_commit(repo, oid)
        for parent in commit.parents:
            queue.append((parent, distance + 1))
    return distances


def lowest_common_ancestor(repo: Repository, ours: str, theirs: str) -> str | None:
    """查找两个 commit 的最近公共祖先。"""

    ours_ancestors = ancestors_by_distance(repo, ours)
    theirs_ancestors = ancestors_by_distance(repo, theirs)
    common = set(ours_ancestors) & set(theirs_ancestors)
    if not common:
        return None
    # 以两边距离之和作为“最近”标准；距离相同则按 ours 侧距离稳定排序。
    return min(common, key=lambda oid: (ours_ancestors[oid] + theirs_ancestors[oid], ours_ancestors[oid], oid))


class MergeTreeResult:
    """三方合并后的工作区写入计划。"""

    def __init__(self) -> None:
        """创建空合并结果。"""

        self.clean_files: list[tuple[str, str, str, bytes]] = []
        self.conflict_files: list[tuple[str, bytes]] = []
        self.conflict_entries: list[IndexEntry] = []


def merge_trees(repo: Repository, base: str, ours: str, theirs: str, target_name: str) -> MergeTreeResult:
    """对 base、ours、theirs 三个 commit 的 tree 做路径级三方合并。"""

    base_map = tree_map(repo, parse_commit(repo, base).tree)
    ours_map = tree_map(repo, parse_commit(repo, ours).tree)
    theirs_map = tree_map(repo, parse_commit(repo, theirs).tree)
    result = MergeTreeResult()

    for path in sorted(set(base_map) | set(ours_map) | set(theirs_map)):
        base_entry = base_map.get(path)
        ours_entry = ours_map.get(path)
        theirs_entry = theirs_map.get(path)
        decision = choose_entry(base_entry, ours_entry, theirs_entry)
        if decision is DELETE:
            continue
        if decision is not CONFLICT:
            chosen = decision
            mode, oid = chosen
            result.clean_files.append((path, mode, oid, read_object(repo, oid).content))
            continue

        conflict_content = conflict_blob(repo, ours_entry, theirs_entry, target_name)
        result.conflict_files.append((path, conflict_content))
        result.conflict_entries.extend(conflict_index_entries(repo, path, base_entry, ours_entry, theirs_entry))
    return result


def tree_map(repo: Repository, tree_oid: str) -> dict[str, tuple[str, str]]:
    """把 tree 展开为 `path -> (mode, oid)` 映射。"""

    return {path: (mode, oid) for path, mode, oid in read_tree_recursive(repo, tree_oid)}


def choose_entry(
    base: tuple[str, str] | None,
    ours: tuple[str, str] | None,
    theirs: tuple[str, str] | None,
) -> tuple[str, str] | None:
    """根据三方条目选择无冲突结果。

    返回 DELETE 表示结果应删除该路径，返回 CONFLICT 表示双方都相对 base
    做了不同修改，需要进入冲突处理。
    """

    if ours == theirs:
        return DELETE if ours is None else ours
    if base == ours:
        return DELETE if theirs is None else theirs
    if base == theirs:
        return DELETE if ours is None else ours
    if base is None and ours is None:
        return DELETE if theirs is None else theirs
    if base is None and theirs is None:
        return DELETE if ours is None else ours
    return CONFLICT


def conflict_blob(
    repo: Repository,
    ours: tuple[str, str] | None,
    theirs: tuple[str, str] | None,
    target_name: str,
) -> bytes:
    """生成工作区冲突文件内容。"""

    ours_content = read_object(repo, ours[1]).content if ours is not None else b""
    theirs_content = read_object(repo, theirs[1]).content if theirs is not None else b""
    return b"".join(
        [
            b"<<<<<<< HEAD\n",
            ours_content if ours_content.endswith(b"\n") or not ours_content else ours_content + b"\n",
            b"=======\n",
            theirs_content if theirs_content.endswith(b"\n") or not theirs_content else theirs_content + b"\n",
            f">>>>>>> {target_name}\n".encode("utf-8"),
        ]
    )


def conflict_index_entries(
    repo: Repository,
    path: str,
    base: tuple[str, str] | None,
    ours: tuple[str, str] | None,
    theirs: tuple[str, str] | None,
) -> list[IndexEntry]:
    """为冲突路径创建 stage 1/2/3 index 条目。"""

    entries: list[IndexEntry] = []
    for stage, item in [(1, base), (2, ours), (3, theirs)]:
        if item is None:
            continue
        mode, oid = item
        blob = read_object(repo, oid)
        flags = min(len(path.encode("utf-8")), 0xFFF) | (stage << 12)
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


def write_conflict_files(repo: Repository, files: list[tuple[str, bytes]]) -> None:
    """把冲突文件写入工作区，并为冲突内容写 loose blob 便于用户后续 add。"""

    for path, content in files:
        file_path = repo.worktree / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        write_object(repo, "blob", content)
