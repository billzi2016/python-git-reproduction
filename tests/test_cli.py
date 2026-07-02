"""CLI 基础命令测试。

命令行测试只覆盖 MVP 暴露给用户的行为：init、hash-object 和 cat-file。
更复杂的 Git 工作流会在 index、commit、refs 模块实现后继续补充。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    """通过 `python -m pygit.cli` 验证命令行行为。"""

    def run_cli(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        """在指定目录运行 pygit CLI，并捕获 stdout/stderr。"""

        env = os.environ.copy()
        project_root = Path(__file__).resolve().parents[1]
        env["PYTHONPATH"] = str(project_root)
        return subprocess.run(
            [sys.executable, "-m", "pygit.cli", *args],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_init_hash_object_and_cat_file(self) -> None:
        """CLI 应能完成 init、写 blob、查看类型/大小/内容。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / "sample.txt"
            sample.write_bytes(b"hello\n")

            init_result = self.run_cli(root, "init")
            self.assertEqual(init_result.returncode, 0, init_result.stderr.decode())

            hash_result = self.run_cli(root, "hash-object", "-w", "sample.txt")
            self.assertEqual(hash_result.returncode, 0, hash_result.stderr.decode())
            oid = hash_result.stdout.decode().strip()
            self.assertEqual(len(oid), 40)

            type_result = self.run_cli(root, "cat-file", "-t", oid)
            self.assertEqual(type_result.stdout, b"blob\n")

            size_result = self.run_cli(root, "cat-file", "-s", oid)
            self.assertEqual(size_result.stdout, b"6\n")

            pretty_result = self.run_cli(root, "cat-file", "-p", oid)
            self.assertEqual(pretty_result.stdout, b"hello\n")

    def test_add_and_write_tree(self) -> None:
        """CLI 应能 add 文件并通过 write-tree 生成 tree 对象。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hello.txt").write_bytes(b"hello\n")

            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            add_result = self.run_cli(root, "add", "hello.txt")
            self.assertEqual(add_result.returncode, 0, add_result.stderr.decode())

            tree_result = self.run_cli(root, "write-tree")
            self.assertEqual(tree_result.returncode, 0, tree_result.stderr.decode())
            tree_oid = tree_result.stdout.decode().strip()
            self.assertEqual(len(tree_oid), 40)

            pretty_result = self.run_cli(root, "cat-file", "-p", tree_oid)
            self.assertEqual(pretty_result.returncode, 0, pretty_result.stderr.decode())
            self.assertIn(b"hello.txt", pretty_result.stdout)

    def test_commit_and_log_oneline(self) -> None:
        """CLI 应能从 add 到 commit 再到 log 形成最小提交闭环。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hello.txt").write_bytes(b"hello\n")

            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            self.assertEqual(self.run_cli(root, "add", "hello.txt").returncode, 0)

            commit_result = self.run_cli(root, "commit", "-m", "initial commit")
            self.assertEqual(commit_result.returncode, 0, commit_result.stderr.decode())
            self.assertIn(b"initial commit", commit_result.stdout)

            log_result = self.run_cli(root, "log", "--oneline")
            self.assertEqual(log_result.returncode, 0, log_result.stderr.decode())
            self.assertIn(b"initial commit", log_result.stdout)


if __name__ == "__main__":
    unittest.main()
