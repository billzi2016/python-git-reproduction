"""路径安全与仓库路径工具。

本模块负责把用户输入路径转换为可审计的真实路径，并保证后续危险操作
只能作用在仓库工作区内部。即使当前 MVP 还没有实现删除和 checkout，
路径边界也必须从第一阶段建立，避免后续命令各自复制不完整的判断。
"""

from __future__ import annotations

from pathlib import Path

from .errors import PathSafetyError


def resolve_existing_or_parent(path: Path) -> Path:
    """解析路径或其最近存在父目录的真实路径。

    参数:
        path: 用户输入或内部拼接得到的路径。

    返回:
        如果路径存在，返回该路径的真实路径；如果路径尚不存在，则解析
        最近存在父目录后再拼回未存在的尾部路径。

    说明:
        Python 的 Path.resolve(strict=False) 能处理不存在路径，但这里仍然
        单独封装，是为了后续在符号链接和路径边界策略变化时集中调整。
    """

    return path.resolve(strict=False)


def ensure_within_directory(base: Path, target: Path) -> Path:
    """确保目标路径位于指定目录内部。

    参数:
        base: 允许访问的根目录，通常是工作区根目录。
        target: 需要检查的目标路径。

    返回:
        规范化后的目标真实路径。

    异常:
        PathSafetyError: 当目标路径逃逸 base 时抛出。
    """

    real_base = base.resolve(strict=False)
    real_target = resolve_existing_or_parent(target)
    try:
        real_target.relative_to(real_base)
    except ValueError as exc:
        raise PathSafetyError(f"path escapes repository worktree: {target}") from exc
    return real_target


def normalize_repo_relative(worktree: Path, target: Path) -> str:
    """把工作区内路径转换为 Git 使用的正斜杠相对路径。

    Git 的 index 和 tree 路径使用正斜杠，不使用平台相关分隔符。
    这里集中转换，避免 Windows、macOS、Linux 上的路径表现不一致。
    """

    safe_target = ensure_within_directory(worktree, target)
    return safe_target.relative_to(worktree.resolve(strict=False)).as_posix()

