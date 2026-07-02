"""引用与 commit 链路测试。

这些测试验证 update-ref、commit-tree、commit 和 log 需要的核心能力。提交
对象是 Git DAG 的节点，必须确保 tree、parent、message 和 HEAD 更新正确。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index, create_commit, parse_commit, walk_first_parent
from pygit.refs import current_commit, read_ref, update_ref
from pygit.repository import init_repository
from pygit.working_tree import add_paths, build_tree_from_index


class RefAndCommitTests(unittest.TestCase):
    """验证引用更新和 commit 对象创建。"""

    def test_update_ref_writes_branch(self) -> None:
        """update_ref 应创建 refs/heads 下的分支文件。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            oid = "1" * 40

            update_ref(repo, "refs/heads/main", oid)

            self.assertEqual(read_ref(repo, "refs/heads/main"), oid)

    def test_create_commit_from_tree(self) -> None:
        """commit-tree 应基于 tree 对象创建 commit 对象。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])
            tree_oid = build_tree_from_index(repo)

            commit_oid = create_commit(repo, tree_oid, [], "initial commit\n", timestamp=1)
            info = parse_commit(repo, commit_oid)

            self.assertEqual(info.tree, tree_oid)
            self.assertEqual(info.parents, [])
            self.assertEqual(info.message, "initial commit\n")

    def test_commit_index_updates_head_and_walks_history(self) -> None:
        """commit 应创建提交、更新当前分支，并能沿第一父链遍历。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])

            first = commit_index(repo, "first\n")
            self.assertEqual(current_commit(repo), first)

            (root / "hello.txt").write_bytes(b"hello again\n")
            add_paths(repo, [Path("hello.txt")])
            second = commit_index(repo, "second\n")

            commits = walk_first_parent(repo, second)
            self.assertEqual([commit.message for commit in commits], ["second\n", "first\n"])

    def test_commit_uses_config_identity(self) -> None:
        """commit author/committer 应能从 config 读取。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            repo.gitdir.joinpath("config").write_text(
                "[core]\n\trepositoryformatversion = 0\n[user]\n\tname = Alice\n\temail = alice@example.com\n",
                encoding="utf-8",
            )
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])

            oid = commit_index(repo, "initial\n")
            info = parse_commit(repo, oid)

            self.assertIn("Alice <alice@example.com>", info.author)


if __name__ == "__main__":
    unittest.main()
