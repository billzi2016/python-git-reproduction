"""修订名解析。

Git 的很多命令都接受“分支名或对象 ID”作为目标，例如 reset、tag、merge。
本模块集中把用户输入解析为 commit SHA-1，避免每个命令重复实现一套略有
差异的分支查找、短 SHA-1 解析和对象类型校验。
"""

from __future__ import annotations

from .errors import PygitError
from .objects import GitObject, read_object
from .refs import read_ref
from .repository import Repository


class RevisionError(PygitError):
    """修订名不存在或不是 commit 时抛出。"""


def resolve_commit(repo: Repository, target: str) -> str:
    """把分支名、完整 SHA-1 或唯一短 SHA-1 解析为 commit SHA-1。"""

    branch_oid = read_ref(repo, f"refs/heads/{target}")
    if branch_oid is not None:
        return peel_to_commit(repo, branch_oid)

    tag_oid = read_ref(repo, f"refs/tags/{target}")
    if tag_oid is not None:
        return peel_to_commit(repo, tag_oid)

    obj = read_object(repo, target)
    return object_to_commit(repo, obj)


def peel_to_commit(repo: Repository, oid: str) -> str:
    """把可能的 tag 对象递归剥离到 commit。"""

    obj = read_object(repo, oid)
    return object_to_commit(repo, obj)


def object_to_commit(repo: Repository, obj: GitObject) -> str:
    """确认对象最终指向 commit。

    附注标签对象会保存 `object <sha1>` 和 `type <type>`。这里递归剥离 tag，
    让 `reset v1.0.0` 这类命令既支持轻量标签，也支持附注标签。
    """

    if obj.object_type != "commit":
        if obj.object_type == "tag":
            target = parse_tag_target(obj.content)
            return peel_to_commit(repo, target)
        raise RevisionError("revision does not point to a commit")
    return obj.oid


def parse_tag_target(content: bytes) -> str:
    """从 tag 对象内容中解析目标对象 SHA-1。"""

    for line in content.decode("utf-8").splitlines():
        key, _, value = line.partition(" ")
        if key == "object":
            return value
    raise RevisionError("tag object is missing target object")
