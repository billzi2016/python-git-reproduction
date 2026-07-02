"""HEAD 与引用文件管理。

Git 的分支、标签和远端追踪分支本质上都是引用文件。引用写入属于仓库
关键元数据修改，必须通过锁文件原子替换。本模块集中处理 HEAD 解析、
当前分支定位、引用读取和 update-ref 语义，避免命令层直接改写文件。
"""

from __future__ import annotations

from pathlib import Path

from .errors import PygitError
from .lockfile import write_file_atomically
from .objects import validate_oid
from .repository import Repository

ZERO_OID = "0" * 40


class RefError(PygitError):
    """引用不存在、格式错误或旧值校验失败时抛出。"""


def ref_path(repo: Repository, ref_name: str) -> Path:
    """把引用名转换为 `.pygit` 内部路径。

    MVP 阶段只允许 refs 命名空间，避免调用方传入任意路径改写仓库外文件。
    HEAD 单独由 `repo.head_path` 管理，不通过这个函数写入。
    """

    if not ref_name.startswith("refs/"):
        raise RefError(f"ref must start with refs/: {ref_name}")
    if ".." in Path(ref_name).parts:
        raise RefError(f"invalid ref path: {ref_name}")
    return repo.gitdir / ref_name


def read_ref(repo: Repository, ref_name: str) -> str | None:
    """读取引用文件中的 SHA-1。

    返回:
        引用不存在时返回 None；存在时返回 40 位 SHA-1。
    """

    path = ref_path(repo, ref_name)
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        return None
    validate_oid(value, allow_short=False)
    return value


def update_ref(repo: Repository, ref_name: str, new_oid: str, expected_old: str | None = None) -> None:
    """原子更新引用文件。

    参数:
        repo: 当前仓库。
        ref_name: 形如 `refs/heads/main` 的完整引用名。
        new_oid: 新的 40 位对象 ID。
        expected_old: 可选旧值；提供时必须与当前文件内容一致。
    """

    validate_oid(new_oid, allow_short=False)
    current = read_ref(repo, ref_name)
    if expected_old is not None:
        validate_oid(expected_old, allow_short=False)
        if (current or ZERO_OID) != expected_old:
            raise RefError("ref current value does not match expected old value")
    write_file_atomically(ref_path(repo, ref_name), f"{new_oid}\n".encode("ascii"))


def read_head(repo: Repository) -> tuple[str | None, str | None]:
    """读取 HEAD。

    返回:
        `(ref_name, oid)`。符号引用状态下 ref_name 为当前分支引用，oid 为该
        引用当前值或 None；游离 HEAD 状态下 ref_name 为 None，oid 为 HEAD
        中直接保存的 commit SHA-1。
    """

    if not repo.head_path.exists():
        raise RefError("HEAD does not exist")
    value = repo.head_path.read_text(encoding="utf-8").strip()
    if value.startswith("ref: "):
        ref_name = value[5:]
        return ref_name, read_ref(repo, ref_name)
    validate_oid(value, allow_short=False)
    return None, value


def current_commit(repo: Repository) -> str | None:
    """返回 HEAD 当前指向的 commit SHA-1，空仓库返回 None。"""

    _, oid = read_head(repo)
    return oid


def update_head_target(repo: Repository, new_oid: str) -> None:
    """更新 HEAD 当前目标。

    如果 HEAD 是符号引用，则更新对应分支；如果是游离 HEAD，则直接改写
    HEAD 文件。当前 MVP 初始化后默认是符号引用。
    """

    ref_name, _ = read_head(repo)
    if ref_name is None:
        write_file_atomically(repo.head_path, f"{new_oid}\n".encode("ascii"))
    else:
        update_ref(repo, ref_name, new_oid)


def current_branch_name(repo: Repository) -> str | None:
    """返回当前分支短名称，游离 HEAD 返回 None。"""

    ref_name, _ = read_head(repo)
    if ref_name is None:
        return None
    prefix = "refs/heads/"
    if not ref_name.startswith(prefix):
        return None
    return ref_name[len(prefix) :]


def list_branches(repo: Repository) -> list[str]:
    """列出本地分支短名称。"""

    heads = repo.refs_dir / "heads"
    if not heads.exists():
        return []
    branches: list[str] = []
    for path in sorted(heads.rglob("*")):
        if path.is_file():
            branches.append(path.relative_to(heads).as_posix())
    return branches


def create_branch(repo: Repository, name: str) -> None:
    """基于当前 HEAD commit 创建本地分支。"""

    validate_branch_name(name)
    oid = current_commit(repo)
    if oid is None:
        raise RefError("cannot create branch without commits")
    target = f"refs/heads/{name}"
    if ref_path(repo, target).exists():
        raise RefError(f"branch already exists: {name}")
    update_ref(repo, target, oid)


def delete_branch(repo: Repository, name: str) -> None:
    """删除本地分支引用文件。"""

    validate_branch_name(name)
    current = current_branch_name(repo)
    if current == name:
        raise RefError("cannot delete the current branch")
    path = ref_path(repo, f"refs/heads/{name}")
    if not path.exists():
        raise RefError(f"branch not found: {name}")
    path.unlink()


def validate_branch_name(name: str) -> None:
    """校验分支短名称，防止路径逃逸和明显非法引用。"""

    if not name or name.startswith("/") or name.endswith("/") or "\\" in name:
        raise RefError(f"invalid branch name: {name}")
    if ".." in Path(name).parts or name in {".", ".."}:
        raise RefError(f"invalid branch name: {name}")
    if name.startswith("refs/"):
        raise RefError("branch name must be short name, not refs path")
