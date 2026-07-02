"""branch 命令底层逻辑测试。

分支是 refs/heads 下的引用文件。这里先测试创建、列出和删除，checkout 会在
后续阶段基于这些引用能力继续实现。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.errors import PygitError
from pygit.refs import create_branch, delete_branch, list_branches, read_ref, rename_branch, set_upstream
from pygit.repository import init_repository
from pygit.working_tree import add_paths


class BranchTests(unittest.TestCase):
    """验证本地分支引用管理。"""

    def test_create_branch_requires_commit(self) -> None:
        """空仓库没有 HEAD commit 时不能创建分支。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))

            with self.assertRaises(PygitError):
                create_branch(repo, "dev")

    def test_create_list_and_delete_branch(self) -> None:
        """分支应基于当前 commit 创建，并能列出和删除。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])
            commit_oid = commit_index(repo, "initial\n")

            create_branch(repo, "dev")

            self.assertIn("dev", list_branches(repo))
            self.assertEqual(read_ref(repo, "refs/heads/dev"), commit_oid)

            delete_branch(repo, "dev")
            self.assertNotIn("dev", list_branches(repo))

    def test_rename_branch_and_set_upstream(self) -> None:
        """应支持分支重命名和上游配置写入。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])
            commit_index(repo, "initial\n")
            create_branch(repo, "dev")

            rename_branch(repo, "dev", "feature")
            set_upstream(repo, "feature", "refs/remotes/origin/feature")

            self.assertIn("feature", list_branches(repo))
            self.assertIn('[branch "feature"]', repo.gitdir.joinpath("config").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
