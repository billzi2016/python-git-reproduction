"""commit 对象创建与历史解析。

本模块负责 Git commit 对象的内容拼接、写入和解析。它依赖对象库和引用
模块，但不处理命令行参数，便于 `commit-tree`、`commit`、`log` 复用。
"""

from __future__ import annotations

import configparser
import os
import time
from dataclasses import dataclass

from .errors import ObjectError
from .objects import read_object, validate_oid, write_object
from .refs import current_commit, update_head_target
from .repository import Repository
from .working_tree import build_tree_from_index


@dataclass(frozen=True)
class CommitInfo:
    """解析后的 commit 基本信息。"""

    oid: str
    tree: str
    parents: list[str]
    author: str
    committer: str
    message: str


def default_identity(repo: Repository | None = None) -> str:
    """返回默认作者身份。

    真实 Git 会读取 config 和环境变量。MVP 先使用环境变量兜底，保证测试和
    本地运行都能生成稳定合法的 commit header。
    """

    config_name, config_email = read_config_identity(repo) if repo is not None else (None, None)
    name = os.environ.get("PYGIT_AUTHOR_NAME") or os.environ.get("GIT_AUTHOR_NAME") or config_name or "Pygit User"
    email = os.environ.get("PYGIT_AUTHOR_EMAIL") or os.environ.get("GIT_AUTHOR_EMAIL") or config_email or "pygit@example.com"
    return f"{name} <{email}>"


def read_config_identity(repo: Repository | None) -> tuple[str | None, str | None]:
    """从 `.pygit/config` 读取 user.name 和 user.email。"""

    if repo is None:
        return None, None
    parser = configparser.ConfigParser()
    parser.read(repo.gitdir / "config", encoding="utf-8")
    if not parser.has_section("user"):
        return None, None
    return parser.get("user", "name", fallback=None), parser.get("user", "email", fallback=None)


def timezone_offset() -> str:
    """返回 Git commit header 使用的 `+HHMM` 或 `-HHMM` 时区。"""

    if time.localtime().tm_isdst and time.daylight:
        offset_seconds = -time.altzone
    else:
        offset_seconds = -time.timezone
    sign = "+" if offset_seconds >= 0 else "-"
    offset_seconds = abs(offset_seconds)
    hours = offset_seconds // 3600
    minutes = (offset_seconds % 3600) // 60
    return f"{sign}{hours:02d}{minutes:02d}"


def create_commit(
    repo: Repository,
    tree_oid: str,
    parents: list[str],
    message: str,
    *,
    timestamp: int | None = None,
) -> str:
    """创建 commit 对象并返回 commit SHA-1。"""

    validate_oid(tree_oid, allow_short=False)
    for parent in parents:
        validate_oid(parent, allow_short=False)
    tree = read_object(repo, tree_oid)
    if tree.object_type != "tree":
        raise ObjectError("commit-tree requires a tree object")

    now = int(time.time() if timestamp is None else timestamp)
    tz = timezone_offset()
    identity = default_identity(repo)
    normalized_message = message.rstrip("\n") + "\n"

    lines = [f"tree {tree_oid}"]
    lines.extend(f"parent {parent}" for parent in parents)
    lines.append(f"author {identity} {now} {tz}")
    lines.append(f"committer {identity} {now} {tz}")
    content = ("\n".join(lines) + "\n\n" + normalized_message).encode("utf-8")
    return write_object(repo, "commit", content)


def commit_index(repo: Repository, message: str) -> str:
    """把当前 index 写成 tree，并创建普通提交后更新 HEAD。"""

    tree_oid = build_tree_from_index(repo)
    parent = current_commit(repo)
    parents = [parent] if parent is not None else []
    commit_oid = create_commit(repo, tree_oid, parents, message)
    update_head_target(repo, commit_oid)
    return commit_oid


def parse_commit(repo: Repository, oid: str) -> CommitInfo:
    """读取并解析 commit 对象。"""

    obj = read_object(repo, oid)
    if obj.object_type != "commit":
        raise ObjectError("object is not a commit")

    text = obj.content.decode("utf-8")
    header_text, _, message = text.partition("\n\n")
    tree = ""
    parents: list[str] = []
    author = ""
    committer = ""
    for line in header_text.splitlines():
        key, _, value = line.partition(" ")
        if key == "tree":
            tree = value
        elif key == "parent":
            parents.append(value)
        elif key == "author":
            author = value
        elif key == "committer":
            committer = value
    if not tree:
        raise ObjectError("commit is missing tree")
    return CommitInfo(oid=oid, tree=tree, parents=parents, author=author, committer=committer, message=message)


def walk_first_parent(repo: Repository, start_oid: str | None, limit: int | None = None) -> list[CommitInfo]:
    """沿第一父提交链遍历历史。"""

    commits: list[CommitInfo] = []
    current = start_oid
    while current is not None:
        info = parse_commit(repo, current)
        commits.append(info)
        if limit is not None and len(commits) >= limit:
            break
        current = info.parents[0] if info.parents else None
    return commits
