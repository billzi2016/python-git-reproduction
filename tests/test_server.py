"""pygit 专用 TCP 服务器测试。

这些测试启动真实 socketserver，客户端通过 `pygit://host:port` 执行 clone、
fetch 和 push。测试不使用模拟对象，验证真实网络连接、真实 `.pygit` 对象库、
真实引用更新和真实工作区 checkout。
"""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.refs import read_ref
from pygit.remote import clone, fetch, push
from pygit.repository import init_repository
from pygit.reset import reset
from pygit.server import serve
from pygit.working_tree import add_paths


class ServerTests(unittest.TestCase):
    """验证 pygit 专用服务器端到端同步。"""

    def make_remote(self, root: Path):
        """创建带初始提交的服务端仓库。"""

        repo = init_repository(root)
        (root / "file.txt").write_bytes(b"one\n")
        add_paths(repo, [Path("file.txt")])
        commit_oid = commit_index(repo, "one\n")
        return repo, commit_oid

    def run_server(self, repo_path: Path):
        """启动后台 pygit server，并返回 URL 和 server 对象。"""

        server = serve(repo_path, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return f"pygit://{host}:{port}", server

    def test_clone_from_pygit_server(self) -> None:
        """clone 应能从 pygit 专用服务器复制对象并 checkout main。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote_root = base / "remote"
            _remote, commit_oid = self.make_remote(remote_root)
            url, server = self.run_server(remote_root)
            try:
                clone_root = base / "clone"
                repo = clone(url, clone_root)

                self.assertEqual(read_ref(repo, "refs/remotes/origin/main"), commit_oid)
                self.assertEqual((clone_root / "file.txt").read_bytes(), b"one\n")
            finally:
                server.shutdown()
                server.server_close()

    def test_fetch_and_push_against_pygit_server(self) -> None:
        """fetch/push 应能通过 pygit 专用服务器同步引用和对象。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote_root = base / "remote"
            remote, _first = self.make_remote(remote_root)
            url, server = self.run_server(remote_root)
            try:
                local_root = base / "local"
                local = clone(url, local_root)

                (remote_root / "file.txt").write_bytes(b"two\n")
                add_paths(remote, [Path("file.txt")])
                second = commit_index(remote, "two\n")
                fetched = fetch(local, url)
                self.assertEqual(fetched["main"], second)

                reset(local, second, "--hard")
                (local_root / "file.txt").write_bytes(b"three\n")
                add_paths(local, [Path("file.txt")])
                third = commit_index(local, "three\n")
                pushed = push(local, url)

                self.assertEqual(pushed, third)
                self.assertEqual(read_ref(remote, "refs/heads/main"), third)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
