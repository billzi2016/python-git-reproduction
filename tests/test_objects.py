"""loose object 编解码测试。

对象库是 Git 的内容寻址基础。这里重点测试对象 header、SHA-1、zlib 写入、
短 ID 解析和损坏对象拒绝，确保 MVP 生成的数据具备 Git 兼容基础。
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
import zlib
from pathlib import Path

from pygit.errors import ObjectError
from pygit.objects import encode_object, hash_file_object, object_id, read_object, resolve_oid, write_file_object, write_object
from pygit.repository import init_repository


class ObjectTests(unittest.TestCase):
    """验证 Git loose object 的核心行为。"""

    def test_encode_and_hash_blob_matches_git_format(self) -> None:
        """blob 的 SHA-1 必须基于 `blob size\\0content` 计算。"""

        content = b"hello\n"
        raw = b"blob 6\x00hello\n"

        self.assertEqual(encode_object("blob", content), raw)
        self.assertEqual(object_id("blob", content), hashlib.sha1(raw).hexdigest())

    def test_write_and_read_blob(self) -> None:
        """写入 loose object 后应能读回同一类型和内容。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            oid = write_object(repo, "blob", b"hello\n")
            obj = read_object(repo, oid)

            self.assertEqual(obj.oid, oid)
            self.assertEqual(obj.object_type, "blob")
            self.assertEqual(obj.content, b"hello\n")
            self.assertTrue((repo.objects_dir / oid[:2] / oid[2:]).is_file())

    def test_resolve_short_oid(self) -> None:
        """唯一短 SHA-1 应解析为完整对象 ID。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            oid = write_object(repo, "blob", b"hello\n")

            self.assertEqual(resolve_oid(repo, oid[:8]), oid)

    def test_corrupted_object_is_rejected(self) -> None:
        """对象内容被篡改后必须拒绝读取，不能静默返回错误内容。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            oid = write_object(repo, "blob", b"hello\n")
            path = repo.objects_dir / oid[:2] / oid[2:]
            path.write_bytes(zlib.compress(b"blob 5\x00HELLO", level=zlib.Z_BEST_COMPRESSION))

            with self.assertRaises(ObjectError):
                read_object(repo, oid)

    def test_streaming_file_hash_and_write(self) -> None:
        """文件对象应能通过分块路径计算和写入。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            path = root / "large.bin"
            path.write_bytes((b"0123456789abcdef" * 8192) + b"\n")

            oid = write_file_object(repo, path)

            self.assertEqual(hash_file_object(path), oid)
            self.assertEqual(read_object(repo, oid).content, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
