"""仓库发现与初始化。

本模块只负责 `.pygit` 仓库目录本身的生命周期：从工作区向上发现仓库、
创建初始化目录结构、暴露常用路径。对象读写、引用更新和 index 解析不在
这里实现，以保持职责单一。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import RepositoryError

PYGIT_DIR_NAME = ".pygit"


@dataclass(frozen=True)
class Repository:
    """表示一个已发现或已初始化的 `.pygit` 仓库。"""

    worktree: Path
    gitdir: Path

    @property
    def objects_dir(self) -> Path:
        """返回对象数据库目录。"""

        return self.gitdir / "objects"

    @property
    def refs_dir(self) -> Path:
        """返回引用命名空间目录。"""

        return self.gitdir / "refs"

    @property
    def head_path(self) -> Path:
        """返回 HEAD 文件路径。"""

        return self.gitdir / "HEAD"

    @property
    def index_path(self) -> Path:
        """返回 Git Index V2 暂存区文件路径。"""

        return self.gitdir / "index"


def init_repository(path: Path) -> Repository:
    """在指定工作区初始化 `.pygit` 仓库。

    参数:
        path: 工作区根目录。目录不存在时会创建。

    返回:
        初始化后的 Repository 对象。

    异常:
        RepositoryError: `.pygit` 已存在时拒绝重复初始化。
    """

    worktree = path.resolve(strict=False)
    gitdir = worktree / PYGIT_DIR_NAME
    if gitdir.exists():
        raise RepositoryError(f"repository already exists: {gitdir}")

    worktree.mkdir(parents=True, exist_ok=True)
    (gitdir / "objects" / "info").mkdir(parents=True)
    (gitdir / "objects" / "pack").mkdir(parents=True)
    (gitdir / "refs" / "heads").mkdir(parents=True)
    (gitdir / "refs" / "tags").mkdir(parents=True)
    (gitdir / "refs" / "remotes").mkdir(parents=True)

    # HEAD 必须使用 Git 符号引用格式，后续 commit 会通过它找到当前分支。
    (gitdir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (gitdir / "config").write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")
    return Repository(worktree=worktree, gitdir=gitdir)


def find_repository(start: Path) -> Repository:
    """从指定路径向上查找最近的 `.pygit` 仓库。

    参数:
        start: 当前工作目录或某个工作区内部路径。

    返回:
        找到的 Repository 对象。

    异常:
        RepositoryError: 向上搜索到文件系统根仍未找到仓库。
    """

    current = start.resolve(strict=False)
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        gitdir = directory / PYGIT_DIR_NAME
        if gitdir.is_dir():
            return Repository(worktree=directory, gitdir=gitdir)
    raise RepositoryError("not a pygit repository")
