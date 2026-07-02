"""仓库初始化测试。

这些测试验证 `.pygit` 目录结构是否按 PRD 创建。初始化是所有命令的基础，
如果目录结构不稳定，后续对象库、引用和 index 都无法可靠工作。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.errors import RepositoryError
from pygit.repository import find_repository, init_repository


class RepositoryTests(unittest.TestCase):
    """验证仓库创建和发现行为。"""

    def test_init_creates_required_layout(self) -> None:
        """init 应创建 HEAD、config、objects 和 refs 基础目录。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))

            self.assertEqual((repo.gitdir / "HEAD").read_text(encoding="utf-8"), "ref: refs/heads/main\n")
            self.assertTrue((repo.gitdir / "config").is_file())
            self.assertTrue((repo.gitdir / "objects" / "info").is_dir())
            self.assertTrue((repo.gitdir / "objects" / "pack").is_dir())
            self.assertTrue((repo.gitdir / "refs" / "heads").is_dir())
            self.assertTrue((repo.gitdir / "refs" / "tags").is_dir())
            self.assertTrue((repo.gitdir / "refs" / "remotes").is_dir())

    def test_find_repository_walks_upwards(self) -> None:
        """仓库发现应能从子目录向上找到 `.pygit`。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            nested = root / "a" / "b"
            nested.mkdir(parents=True)

            found = find_repository(nested)

            self.assertEqual(found, repo)

    def test_init_rejects_existing_repository(self) -> None:
        """重复 init 必须拒绝，避免覆盖已有仓库元数据。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repository(root)

            with self.assertRaises(RepositoryError):
                init_repository(root)


if __name__ == "__main__":
    unittest.main()

