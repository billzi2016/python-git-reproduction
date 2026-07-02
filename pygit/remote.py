"""本地路径远端同步。

本模块实现 clone、fetch、push 的本地物理路径版本。它使用真实 `.pygit`
目录、真实对象数据库和真实引用文件完成同步，不使用模拟对象。网络 socket
协议可以在此基础上扩展，但本地路径远端已经覆盖分布式同步最核心的对象
复制、远端追踪引用和非快进拒绝语义。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .errors import PygitError
from .merge import ancestors_by_distance
from .refs import current_branch_name, current_commit, list_branches, read_ref, update_ref
from .repository import Repository, find_repository, init_repository
from .reset import reset


class RemoteError(PygitError):
    """远端路径、引用或非快进状态不合法时抛出。"""


def clone(remote_path: Path, target_path: Path) -> Repository:
    """从本地路径远端克隆到目标目录。"""

    remote = find_repository(remote_path)
    repo = init_repository(target_path)
    write_origin_config(repo, remote.worktree)
    fetch(repo, remote.worktree)

    main = read_ref(repo, "refs/remotes/origin/main")
    if main is not None:
        update_ref(repo, "refs/heads/main", main)
        reset(repo, "main", "--hard")
    return repo


def fetch(repo: Repository, remote_path: Path | None = None) -> dict[str, str]:
    """从 origin 或指定本地远端路径抓取对象和分支引用。"""

    remote = find_repository(remote_path or read_origin_config(repo))
    copy_object_database(remote, repo)
    fetched: dict[str, str] = {}
    for branch in list_branches(remote):
        oid = read_ref(remote, f"refs/heads/{branch}")
        if oid is None:
            continue
        update_ref(repo, f"refs/remotes/origin/{branch}", oid)
        fetched[branch] = oid
    return fetched


def push(repo: Repository, remote_path: Path | None = None, branch: str | None = None) -> str:
    """把当前或指定本地分支推送到 origin。"""

    branch_name = branch or current_branch_name(repo)
    if branch_name is None:
        raise RemoteError("cannot push detached HEAD")
    local_oid = read_ref(repo, f"refs/heads/{branch_name}")
    if local_oid is None:
        raise RemoteError(f"local branch not found: {branch_name}")

    remote = find_repository(remote_path or read_origin_config(repo))
    remote_oid = read_ref(remote, f"refs/heads/{branch_name}")
    if remote_oid is not None and remote_oid not in ancestors_by_distance(repo, local_oid):
        raise RemoteError("non-fast-forward push rejected")

    copy_object_database(repo, remote)
    update_ref(remote, f"refs/heads/{branch_name}", local_oid)
    update_ref(repo, f"refs/remotes/origin/{branch_name}", local_oid)
    return local_oid


def copy_object_database(source: Repository, target: Repository) -> None:
    """复制 loose objects 和 packfiles。

    对象以内容寻址，复制已存在对象是幂等操作。这里跳过临时文件和锁文件，
    避免把写入中间状态传播到另一个仓库。
    """

    for path in source.objects_dir.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix in {".lock", ".tmp"} or path.name.endswith(".lock"):
            continue
        relative = path.relative_to(source.objects_dir)
        target_path = target.objects_dir / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.exists():
            shutil.copy2(path, target_path)


def write_origin_config(repo: Repository, remote_worktree: Path) -> None:
    """写入最小 origin 配置。"""

    repo.gitdir.joinpath("config").write_text(
        "[core]\n"
        "\trepositoryformatversion = 0\n"
        "[remote \"origin\"]\n"
        f"\turl = {remote_worktree}\n",
        encoding="utf-8",
    )


def read_origin_config(repo: Repository) -> Path:
    """从 config 读取 origin URL。

    当前实现只解析本项目写入的最小 INI 风格配置，避免在 remote 模块引入
    更复杂的配置系统。后续 config 模块可以替换这里的解析。
    """

    config = repo.gitdir.joinpath("config")
    if not config.exists():
        raise RemoteError("config does not exist")
    in_origin = False
    for line in config.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == '[remote "origin"]':
            in_origin = True
            continue
        if stripped.startswith("[") and stripped != '[remote "origin"]':
            in_origin = False
        if in_origin and stripped.startswith("url = "):
            return Path(stripped[len("url = ") :])
    raise RemoteError("origin remote is not configured")

