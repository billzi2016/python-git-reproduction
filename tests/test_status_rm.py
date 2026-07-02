"""status 与 rm 命令测试。

status 是 HEAD、index、工作区三方比较；rm 涉及物理删除，是危险操作。
这些测试使用临时目录，确保不会触碰用户真实文件。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.index import read_index
from pygit.repository import init_repository
from pygit.status import collect_status
from pygit.working_tree import add_paths, remove_paths


class StatusAndRmTests(unittest.TestCase):
    """验证 status 计算和 rm 安全删除。"""

    def test_status_detects_staged_and_untracked_files(self) -> None:
        """空 HEAD 下 add 的文件应显示 staged added，未 add 文件显示 untracked。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "tracked.txt").write_bytes(b"tracked\n")
            (root / "untracked.txt").write_bytes(b"untracked\n")

            add_paths(repo, [Path("tracked.txt")])
            status = collect_status(repo)

            self.assertEqual(status.staged_added, ["tracked.txt"])
            self.assertEqual(status.untracked, ["untracked.txt"])

    def test_status_detects_unstaged_modification_after_commit(self) -> None:
        """提交后修改工作区文件应显示 unstaged modified。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "hello.txt"
            path.write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "initial\n")

            path.write_bytes(b"changed\n")
            status = collect_status(repo)

            self.assertEqual(status.unstaged_modified, ["hello.txt"])

    def test_rm_cached_keeps_worktree_file(self) -> None:
        """rm --cached 只更新 index，不删除工作区文件。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            file_path = root / "hello.txt"
            file_path.write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])

            remove_paths(repo, [Path("hello.txt")], cached=True)

            self.assertTrue(file_path.exists())
            self.assertEqual(read_index(repo), [])

    def test_rm_deletes_only_tracked_file(self) -> None:
        """rm 默认删除已追踪工作区文件，并从 index 移除。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            file_path = root / "hello.txt"
            file_path.write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])

            remove_paths(repo, [Path("hello.txt")], cached=False)

            self.assertFalse(file_path.exists())
            self.assertEqual(read_index(repo), [])

    def test_exclude_ignored_files_from_status_and_add(self) -> None:
        """info/exclude 中的文件不应被 add 或 status 追踪。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            repo.gitdir.joinpath("info", "exclude").write_text("*.log\n", encoding="utf-8")
            (root / "debug.log").write_bytes(b"ignore\n")

            add_paths(repo, [Path(".")])
            status = collect_status(repo)

            self.assertEqual(read_index(repo), [])
            self.assertEqual(status.untracked, [])


if __name__ == "__main__":
    unittest.main()
