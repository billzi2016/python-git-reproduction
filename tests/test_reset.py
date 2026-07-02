"""reset 工作流测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.index import read_index
from pygit.refs import current_commit
from pygit.repository import init_repository
from pygit.reset import reset
from pygit.working_tree import add_paths


class ResetTests(unittest.TestCase):
    """验证 soft、mixed 和 hard reset。"""

    def make_two_commits(self, root: Path):
        """创建包含两个提交的测试仓库。"""

        repo = init_repository(root)
        file_path = root / "hello.txt"
        file_path.write_bytes(b"one\n")
        add_paths(repo, [Path("hello.txt")])
        first = commit_index(repo, "one\n")
        file_path.write_bytes(b"two\n")
        add_paths(repo, [Path("hello.txt")])
        second = commit_index(repo, "two\n")
        return repo, file_path, first, second

    def test_reset_soft_moves_head_only(self) -> None:
        """soft reset 只移动 HEAD，不改 index 和工作区。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo, file_path, first, _second = self.make_two_commits(Path(tmp))

            reset(repo, first, "--soft")

            self.assertEqual(current_commit(repo), first)
            self.assertEqual(file_path.read_bytes(), b"two\n")
            self.assertEqual(read_index(repo)[0].path, "hello.txt")

    def test_reset_mixed_refreshes_index_only(self) -> None:
        """mixed reset 移动 HEAD 并刷新 index，但不改工作区。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo, file_path, first, _second = self.make_two_commits(Path(tmp))

            reset(repo, first, "--mixed")

            self.assertEqual(current_commit(repo), first)
            self.assertEqual(file_path.read_bytes(), b"two\n")
            self.assertEqual(read_index(repo)[0].file_size, len(b"one\n"))

    def test_reset_hard_rewrites_worktree(self) -> None:
        """hard reset 移动 HEAD、刷新 index 并重写已追踪文件。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo, file_path, first, _second = self.make_two_commits(Path(tmp))
            untracked = Path(tmp) / "note.txt"
            untracked.write_bytes(b"keep me\n")

            reset(repo, first, "--hard")

            self.assertEqual(current_commit(repo), first)
            self.assertEqual(file_path.read_bytes(), b"one\n")
            self.assertTrue(untracked.exists())


if __name__ == "__main__":
    unittest.main()

