"""merge 工作流测试。

这些测试全部使用真实临时目录、真实 `.pygit` 对象库、真实 index 和真实
工作区文件，不使用模拟对象替代核心 Git 行为。merge 涉及历史图、引用移动、
工作区重写和冲突 stage，必须用端到端状态验证。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.checkout import checkout_target
from pygit.commit import commit_index, parse_commit
from pygit.index import read_index
from pygit.merge import MergeConflict, ancestors_by_distance, lowest_common_ancestor, merge
from pygit.refs import create_branch, current_commit
from pygit.repository import init_repository
from pygit.working_tree import add_paths


class MergeTests(unittest.TestCase):
    """验证快进、非快进自动合并和冲突隔离。"""

    def test_ancestor_bfs_and_lca(self) -> None:
        """BFS 祖先表和 LCA 应能识别分叉历史的公共祖先。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "file.txt"
            path.write_bytes(b"base\n")
            add_paths(repo, [Path("file.txt")])
            base = commit_index(repo, "base\n")
            create_branch(repo, "side")

            path.write_bytes(b"main\n")
            add_paths(repo, [Path("file.txt")])
            main = commit_index(repo, "main\n")
            checkout_target(repo, "side")
            path.write_bytes(b"side\n")
            add_paths(repo, [Path("file.txt")])
            side = commit_index(repo, "side\n")

            self.assertIn(base, ancestors_by_distance(repo, side))
            self.assertEqual(lowest_common_ancestor(repo, main, side), base)

    def test_fast_forward_merge_moves_head_and_worktree(self) -> None:
        """当前分支落后目标分支时 merge 应执行快进。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "file.txt"
            path.write_bytes(b"base\n")
            add_paths(repo, [Path("file.txt")])
            commit_index(repo, "base\n")
            create_branch(repo, "feature")
            checkout_target(repo, "feature")
            path.write_bytes(b"feature\n")
            add_paths(repo, [Path("file.txt")])
            feature = commit_index(repo, "feature\n")
            checkout_target(repo, "main")

            result = merge(repo, "feature")

            self.assertEqual(result, feature)
            self.assertEqual(current_commit(repo), feature)
            self.assertEqual(path.read_bytes(), b"feature\n")

    def test_non_fast_forward_merge_creates_merge_commit(self) -> None:
        """双方修改不同路径时应自动合并并创建双父提交。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "base.txt").write_bytes(b"base\n")
            add_paths(repo, [Path("base.txt")])
            commit_index(repo, "base\n")
            create_branch(repo, "feature")

            (root / "main.txt").write_bytes(b"main\n")
            add_paths(repo, [Path("main.txt")])
            main = commit_index(repo, "main\n")
            checkout_target(repo, "feature")
            (root / "feature.txt").write_bytes(b"feature\n")
            add_paths(repo, [Path("feature.txt")])
            feature = commit_index(repo, "feature\n")
            checkout_target(repo, "main")

            merge_oid = merge(repo, "feature", "merge feature\n")
            info = parse_commit(repo, merge_oid)

            self.assertEqual(info.parents, [main, feature])
            self.assertTrue((root / "main.txt").exists())
            self.assertTrue((root / "feature.txt").exists())

    def test_conflict_writes_markers_and_stage_entries(self) -> None:
        """同一路径双方不同修改时应写冲突标记和 stage 1/2/3。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "file.txt"
            path.write_bytes(b"base\n")
            add_paths(repo, [Path("file.txt")])
            commit_index(repo, "base\n")
            create_branch(repo, "feature")

            path.write_bytes(b"ours\n")
            add_paths(repo, [Path("file.txt")])
            commit_index(repo, "ours\n")
            checkout_target(repo, "feature")
            path.write_bytes(b"theirs\n")
            add_paths(repo, [Path("file.txt")])
            commit_index(repo, "theirs\n")
            checkout_target(repo, "main")

            with self.assertRaises(MergeConflict):
                merge(repo, "feature")

            content = path.read_text(encoding="utf-8")
            self.assertIn("<<<<<<< HEAD", content)
            self.assertIn("=======", content)
            self.assertIn(">>>>>>> feature", content)
            self.assertEqual([entry.stage for entry in read_index(repo)], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
