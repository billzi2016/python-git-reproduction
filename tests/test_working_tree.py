"""工作区 add 与 write-tree 测试。

这里验证从真实文件到 blob、index、tree 的最小闭环。后续 commit-tree 和
commit 会直接建立在这条链路之上。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.index import read_index
from pygit.objects import read_object
from pygit.repository import init_repository
from pygit.reset import index_entries_from_tree
from pygit.working_tree import add_paths, build_tree_from_index, format_tree_pretty


class WorkingTreeTests(unittest.TestCase):
    """验证 add 和 write-tree 的核心行为。"""

    def test_add_file_updates_index_and_writes_blob(self) -> None:
        """add 应写入 blob 并在 index 中记录相对路径。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")

            add_paths(repo, [Path("hello.txt")])
            entries = read_index(repo)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].path, "hello.txt")
            self.assertEqual(read_object(repo, entries[0].oid).content, b"hello\n")

    def test_write_tree_creates_tree_for_nested_paths(self) -> None:
        """write-tree 应把嵌套路径转换为递归 tree 对象。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_bytes(b"print('hi')\n")
            (root / "README.md").write_bytes(b"# demo\n")

            add_paths(repo, [Path(".")])
            tree_oid = build_tree_from_index(repo)
            tree = read_object(repo, tree_oid)

            self.assertEqual(tree.object_type, "tree")
            pretty = format_tree_pretty(repo, tree.content).decode("utf-8")
            self.assertIn("README.md", pretty)
            self.assertIn("src", pretty)

    def test_read_tree_entries_from_tree(self) -> None:
        """read-tree 底层能力应能从 tree 重建扁平 index 条目。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_bytes(b"print('hi')\n")
            add_paths(repo, [Path(".")])
            tree_oid = build_tree_from_index(repo)

            entries = index_entries_from_tree(repo, tree_oid)

            self.assertEqual([entry.path for entry in entries], ["src/app.py"])


if __name__ == "__main__":
    unittest.main()
