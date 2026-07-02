"""本地路径与 pygit 专用服务器远端同步。

本模块实现 clone、fetch、push。远端可以是本地物理路径，也可以是
`pygit://host:port` 专用服务器。两种远端都使用真实 `.pygit` 对象和引用，
不实现 GitHub 或官方 Git wire protocol。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .errors import PygitError
from .merge import ancestors_by_distance
from .refs import current_branch_name, current_commit, list_branches, read_ref, update_ref
from .repository import Repository, find_repository, init_repository
from .reset import reset
from .server import objects_payload, parse_pygit_url, request, write_objects_payload


class RemoteError(PygitError):
    """远端路径、引用或非快进状态不合法时抛出。"""


def clone(remote_path: Path | str, target_path: Path) -> Repository:
    """从本地路径或 pygit 专用服务器克隆到目标目录。"""

    repo = init_repository(target_path)
    write_origin_config(repo, str(remote_path))
    fetch(repo, str(remote_path))

    main = read_ref(repo, "refs/remotes/origin/main")
    if main is not None:
        update_ref(repo, "refs/heads/main", main)
        reset(repo, "main", "--hard")
    return repo


def fetch(repo: Repository, remote_path: Path | str | None = None) -> dict[str, str]:
    """从 origin 或指定本地远端路径抓取对象和分支引用。"""

    remote_value = str(remote_path or read_origin_config(repo))
    url = parse_pygit_url(remote_value)
    if url is not None:
        response = request(url, {"action": "fetch"})
        write_objects_payload(repo, response["objects"])
        fetched = response["refs"]
        for branch, oid in fetched.items():
            update_ref(repo, f"refs/remotes/origin/{branch}", oid)
        return fetched

    remote = find_repository(Path(remote_value))
    copy_object_database(remote, repo)
    fetched: dict[str, str] = {}
    for branch in list_branches(remote):
        oid = read_ref(remote, f"refs/heads/{branch}")
        if oid is None:
            continue
        update_ref(repo, f"refs/remotes/origin/{branch}", oid)
        fetched[branch] = oid
    return fetched


def push(repo: Repository, remote_path: Path | str | None = None, branch: str | None = None) -> str:
    """把当前或指定本地分支推送到 origin。"""

    branch_name = branch or current_branch_name(repo)
    if branch_name is None:
        raise RemoteError("cannot push detached HEAD")
    local_oid = read_ref(repo, f"refs/heads/{branch_name}")
    if local_oid is None:
        raise RemoteError(f"local branch not found: {branch_name}")

    remote_value = str(remote_path or read_origin_config(repo))
    url = parse_pygit_url(remote_value)
    if url is not None:
        refs = request(url, {"action": "refs"})["refs"]
        remote_oid = refs.get(branch_name)
        if remote_oid is not None and remote_oid not in ancestors_by_distance(repo, local_oid):
            raise RemoteError("non-fast-forward push rejected")
        response = request(
            url,
            {
                "action": "push",
                "branch": branch_name,
                "old": remote_oid,
                "new": local_oid,
                "objects": objects_payload(repo),
            },
        )
        update_ref(repo, f"refs/remotes/origin/{branch_name}", response["new"])
        return response["new"]

    remote = find_repository(Path(remote_value))
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


def write_origin_config(repo: Repository, remote_worktree: str) -> None:
    """写入最小 origin 配置。"""

    repo.gitdir.joinpath("config").write_text(
        "[core]\n"
        "\trepositoryformatversion = 0\n"
        "[remote \"origin\"]\n"
        f"\turl = {remote_worktree}\n",
        encoding="utf-8",
    )


def read_origin_config(repo: Repository) -> str:
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
            return stripped[len("url = ") :]
    raise RemoteError("origin remote is not configured")
