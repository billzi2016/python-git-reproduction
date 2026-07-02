"""checkout/switch 工作区切换测试。

checkout 会删除和重写工作区文件，因此所有测试都必须在临时目录中运行。
当前实现采用保守策略：工作区必须干净才能切换。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.checkout import CheckoutError, checkout_target, switch_branch
from pygit.commit import commit_index
from pygit.index import read_index
from pygit.refs import create_branch, current_branch_name, current_commit
from pygit.repository import init_repository
from pygit.working_tree import add_paths


class CheckoutTests(unittest.TestCase):
    """验证 checkout 的安全切换行为。"""

    def test_checkout_branch_rewrites_worktree_and_head(self) -> None:
        """切换分支应重写工作区、刷新 index，并更新 HEAD 符号引用。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            file_path = root / "hello.txt"
            file_path.write_bytes(b"main\n")
            add_paths(repo, [Path("hello.txt")])
            main_commit = commit_index(repo, "main\n")
            create_branch(repo, "dev")

            file_path.write_bytes(b"main second\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "main second\n")

            checkout_target(repo, "dev")

            self.assertEqual(current_branch_name(repo), "dev")
            self.assertEqual(current_commit(repo), main_commit)
            self.assertEqual(file_path.read_bytes(), b"main\n")
            self.assertEqual(read_index(repo)[0].path, "hello.txt")

    def test_checkout_detached_commit(self) -> None:
        """checkout commit SHA-1 应进入游离 HEAD。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            file_path = root / "hello.txt"
            file_path.write_bytes(b"one\n")
            add_paths(repo, [Path("hello.txt")])
            first = commit_index(repo, "one\n")

            file_path.write_bytes(b"two\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "two\n")

            checkout_target(repo, first)

            self.assertIsNone(current_branch_name(repo))
            self.assertEqual(current_commit(repo), first)
            self.assertEqual(file_path.read_bytes(), b"one\n")

    def test_checkout_rejects_dirty_worktree(self) -> None:
        """工作区有未提交修改时应拒绝 checkout。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            file_path = root / "hello.txt"
            file_path.write_bytes(b"main\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "main\n")
            create_branch(repo, "dev")
            file_path.write_bytes(b"dirty\n")

            with self.assertRaises(CheckoutError):
                checkout_target(repo, "dev")

    def test_switch_rejects_detached_commit_target(self) -> None:
        """switch 只接受分支名，不接受裸 commit。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"main\n")
            add_paths(repo, [Path("hello.txt")])
            commit_oid = commit_index(repo, "main\n")

            with self.assertRaises(CheckoutError):
                switch_branch(repo, commit_oid)


if __name__ == "__main__":
    unittest.main()
