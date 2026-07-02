"""标签管理。

Git 支持轻量标签和附注标签。轻量标签只是 refs/tags 下的引用文件；附注
标签需要先创建 tag 对象，再让 refs/tags 指向该 tag 对象。
"""

from __future__ import annotations

import time

from .commit import default_identity, timezone_offset
from .errors import PygitError
from .objects import read_object, validate_oid, write_object
from .refs import ref_path, update_ref
from .repository import Repository
from .revision import resolve_commit


class TagError(PygitError):
    """标签名、目标对象或重复标签不合法时抛出。"""


def create_lightweight_tag(repo: Repository, name: str, target: str) -> str:
    """创建轻量标签，返回目标 commit SHA-1。"""

    validate_tag_name(name)
    oid = resolve_commit(repo, target)
    ensure_tag_absent(repo, name)
    update_ref(repo, f"refs/tags/{name}", oid)
    return oid


def create_annotated_tag(repo: Repository, name: str, target: str, message: str) -> str:
    """创建附注标签对象，并让 refs/tags 指向该 tag 对象。"""

    validate_tag_name(name)
    target_oid = resolve_commit(repo, target)
    ensure_tag_absent(repo, name)
    content = encode_tag_object(repo, target_oid, name, message)
    tag_oid = write_object(repo, "tag", content)
    update_ref(repo, f"refs/tags/{name}", tag_oid)
    return tag_oid


def list_tags(repo: Repository) -> list[str]:
    """列出本地标签名。"""

    tags_dir = repo.refs_dir / "tags"
    if not tags_dir.exists():
        return []
    return sorted(path.relative_to(tags_dir).as_posix() for path in tags_dir.rglob("*") if path.is_file())


def encode_tag_object(repo: Repository, target_oid: str, name: str, message: str) -> bytes:
    """编码附注 tag 对象内容。"""

    validate_oid(target_oid, allow_short=False)
    target = read_object(repo, target_oid)
    now = int(time.time())
    identity = default_identity()
    tz = timezone_offset()
    normalized_message = message.rstrip("\n") + "\n"
    text = (
        f"object {target_oid}\n"
        f"type {target.object_type}\n"
        f"tag {name}\n"
        f"tagger {identity} {now} {tz}\n"
        f"\n"
        f"{normalized_message}"
    )
    return text.encode("utf-8")


def ensure_tag_absent(repo: Repository, name: str) -> None:
    """确保标签不存在，避免静默覆盖历史标记。"""

    if ref_path(repo, f"refs/tags/{name}").exists():
        raise TagError(f"tag already exists: {name}")


def validate_tag_name(name: str) -> None:
    """校验标签名，防止路径逃逸和明显非法名称。"""

    if not name or name.startswith("/") or name.endswith("/") or "\\" in name:
        raise TagError(f"invalid tag name: {name}")
    if name in {".", ".."} or ".." in name.split("/"):
        raise TagError(f"invalid tag name: {name}")
    if name.startswith("refs/"):
        raise TagError("tag name must be short name, not refs path")

