"""忽略规则处理。

当前实现读取 `.pygit/info/exclude`，支持空行、注释、简单 glob 和目录前缀。
忽略判断集中在这里，避免 add、status、checkout 等模块各写一份路径过滤。
"""

from __future__ import annotations

import fnmatch

from .repository import Repository


def load_exclude_patterns(repo: Repository) -> list[str]:
    """读取 `.pygit/info/exclude` 中的忽略规则。"""

    path = repo.gitdir / "info" / "exclude"
    if not path.exists():
        return []
    patterns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns


def is_ignored(repo: Repository, path: str) -> bool:
    """判断 Git 相对路径是否被 exclude 规则忽略。"""

    for pattern in load_exclude_patterns(repo):
        normalized = pattern.rstrip("/")
        if pattern.endswith("/") and (path == normalized or path.startswith(f"{normalized}/")):
            return True
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path.split("/")[-1], pattern):
            return True
    return False
