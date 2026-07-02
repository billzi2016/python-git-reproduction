"""锁文件与原子写入工具。

Git 对 index 和 refs 的写入依赖 `.lock` 文件加 `os.replace` 原子替换。
本模块提供最小的通用锁文件能力，后续 refs、index、config、pack idx 写入
都应复用这里的逻辑，避免危险写入策略在不同模块中复制粘贴。
"""

from __future__ import annotations

import os
from pathlib import Path

from .errors import LockError


class LockFile:
    """基于同级 `.lock` 文件的原子写入辅助类。"""

    def __init__(self, target: Path) -> None:
        """创建锁对象但不立即写入磁盘。

        参数:
            target: 最终要被原子替换的目标文件路径。
        """

        self.target = target
        self.lock_path = target.with_name(f"{target.name}.lock")
        self._file = None

    def acquire(self) -> None:
        """独占创建锁文件。

        使用 `x` 模式可以确保锁文件已存在时不会覆盖，从而避免两个进程
        同时写同一个引用或 index。
        """

        self.target.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._file = self.lock_path.open("xb")
        except FileExistsError as exc:
            raise LockError(f"lock already exists: {self.lock_path}") from exc

    def write(self, data: bytes) -> None:
        """向锁文件写入完整字节内容。"""

        if self._file is None:
            raise LockError("lock file is not acquired")
        self._file.write(data)

    def commit(self) -> None:
        """刷盘并把锁文件原子替换为正式文件。"""

        if self._file is None:
            raise LockError("lock file is not acquired")
        self._file.flush()
        os.fsync(self._file.fileno())
        self._file.close()
        self._file = None
        os.replace(self.lock_path, self.target)

    def rollback(self) -> None:
        """放弃锁文件，尽量恢复到写入前状态。"""

        if self._file is not None:
            self._file.close()
            self._file = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def write_file_atomically(target: Path, data: bytes) -> None:
    """使用锁文件原子写入目标文件。"""

    lock = LockFile(target)
    lock.acquire()
    try:
        lock.write(data)
        lock.commit()
    except Exception:
        lock.rollback()
        raise

