"""本地路径远端同步测试。

测试使用真实临时目录创建多个 `.pygit` 仓库，通过真实对象复制、真实引用
更新和真实工作区 checkout 验证 clone、fetch、push 和非快进拒绝。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.refs import read_ref
from pygit.remote import RemoteError, clone, fetch, push
from pygit.repository import init_repository
from pygit.working_tree import add_paths


class RemoteTests(unittest.TestCase):
    """验证本地路径远端工作流。"""

    def create_repo_with_commit(self, root: Path, content: bytes = b"one\n"):
        """创建带有 main 分支提交的仓库。"""

        repo = init_repository(root)
        (root / "file.txt").write_bytes(content)
        add_paths(repo, [Path("file.txt")])
        commit_oid = commit_index(repo, "initial\n")
        return repo, commit_oid

    def test_clone_fetches_objects_and_checks_out_main(self) -> None:
        """clone 应复制对象、建立 origin 追踪引用并 checkout main。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote_root = base / "remote"
            _remote, commit_oid = self.create_repo_with_commit(remote_root)
            clone_root = base / "clone"

            repo = clone(remote_root, clone_root)

            self.assertEqual(read_ref(repo, "refs/remotes/origin/main"), commit_oid)
            self.assertEqual((clone_root / "file.txt").read_bytes(), b"one\n")

    def test_fetch_updates_remote_tracking_branch(self) -> None:
        """fetch 应复制远端新增对象并更新 refs/remotes/origin。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote_root = base / "remote"
            remote, _first = self.create_repo_with_commit(remote_root)
            local_root = base / "local"
            local = clone(remote_root, local_root)

            (remote_root / "file.txt").write_bytes(b"two\n")
            add_paths(remote, [Path("file.txt")])
            second = commit_index(remote, "second\n")

            fetched = fetch(local, remote_root)

            self.assertEqual(fetched["main"], second)
            self.assertEqual(read_ref(local, "refs/remotes/origin/main"), second)

    def test_push_updates_remote_branch(self) -> None:
        """push 应复制本地对象并更新远端分支。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote_root = base / "remote"
            _remote, _first = self.create_repo_with_commit(remote_root)
            local_root = base / "local"
            local = clone(remote_root, local_root)

            (local_root / "file.txt").write_bytes(b"two\n")
            add_paths(local, [Path("file.txt")])
            second = commit_index(local, "second\n")
            pushed = push(local, remote_root)

            self.assertEqual(pushed, second)
            self.assertEqual(read_ref(_remote, "refs/heads/main"), second)

    def test_push_rejects_non_fast_forward(self) -> None:
        """远端分支不在本地历史中时应拒绝 push。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote_root = base / "remote"
            remote, _first = self.create_repo_with_commit(remote_root)
            local_root = base / "local"
            local = clone(remote_root, local_root)

            (remote_root / "file.txt").write_bytes(b"remote\n")
            add_paths(remote, [Path("file.txt")])
            commit_index(remote, "remote\n")

            (local_root / "file.txt").write_bytes(b"local\n")
            add_paths(local, [Path("file.txt")])
            commit_index(local, "local\n")

            with self.assertRaises(RemoteError):
                push(local, remote_root)


if __name__ == "__main__":
    unittest.main()

