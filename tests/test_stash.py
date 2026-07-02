"""stash 工作流测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.refs import current_commit
from pygit.repository import init_repository
from pygit.stash import read_stash_stack, stash_apply, stash_pop, stash_push
from pygit.working_tree import add_paths


class StashTests(unittest.TestCase):
    """验证 stash push/apply/pop 基础行为。"""

    def test_stash_push_saves_and_resets_worktree(self) -> None:
        """stash push 应保存修改并恢复到 HEAD。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "hello.txt"
            path.write_bytes(b"one\n")
            add_paths(repo, [Path("hello.txt")])
            head = commit_index(repo, "one\n")
            path.write_bytes(b"two\n")

            stash_oid = stash_push(repo, "change hello")

            self.assertEqual(current_commit(repo), head)
            self.assertEqual(path.read_bytes(), b"one\n")
            self.assertEqual(read_stash_stack(repo), [stash_oid])

    def test_stash_apply_restores_snapshot(self) -> None:
        """stash apply 应恢复栈顶快照但保留栈记录。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "hello.txt"
            path.write_bytes(b"one\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "one\n")
            path.write_bytes(b"two\n")
            stash_oid = stash_push(repo, "change hello")

            stash_apply(repo)

            self.assertEqual(path.read_bytes(), b"two\n")
            self.assertEqual(read_stash_stack(repo), [stash_oid])

    def test_stash_pop_restores_and_removes_entry(self) -> None:
        """stash pop 应恢复栈顶快照并移除记录。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "hello.txt"
            path.write_bytes(b"one\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "one\n")
            path.write_bytes(b"two\n")
            stash_push(repo, "change hello")

            stash_pop(repo)

            self.assertEqual(path.read_bytes(), b"two\n")
            self.assertEqual(read_stash_stack(repo), [])

    def test_stash_apply_uses_three_way_and_conflicts(self) -> None:
        """当前 HEAD 和 stash 同改一路径时应产生冲突标记。"""

        from pygit.merge import MergeConflict

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "hello.txt"
            path.write_bytes(b"base\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "base\n")
            path.write_bytes(b"stash\n")
            stash_push(repo, "stash change")
            path.write_bytes(b"head\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "head change\n")

            with self.assertRaises(MergeConflict):
                stash_apply(repo)

            self.assertIn("<<<<<<< HEAD", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
