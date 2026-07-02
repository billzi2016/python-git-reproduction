"""Git Index V2 测试。

这些测试验证 index 的二进制 header、checksum、条目排序和读取写回能力。
Index 是后续 commit、status、checkout、merge 的共同基础，必须尽早用
unittest 锁定格式。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import hashlib
import struct

from pygit.index import INDEX_SIGNATURE, INDEX_VERSION, IndexEntry, encode_index, read_index, write_index
from pygit.repository import init_repository


class IndexTests(unittest.TestCase):
    """验证 Index V2 编解码。"""

    def make_entry(self, path: str, oid: str) -> IndexEntry:
        """创建稳定的测试条目。"""

        return IndexEntry(
            ctime_s=1,
            ctime_ns=2,
            mtime_s=3,
            mtime_ns=4,
            dev=5,
            ino=6,
            mode=0o100644,
            uid=7,
            gid=8,
            file_size=9,
            oid=oid,
            flags=len(path),
            path=path,
        )

    def test_write_and_read_index_entries_sorted(self) -> None:
        """写入 index 后读取应保持按路径排序。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            first_oid = "1" * 40
            second_oid = "2" * 40

            write_index(repo, [self.make_entry("b.txt", second_oid), self.make_entry("a.txt", first_oid)])
            entries = read_index(repo)

            self.assertEqual([entry.path for entry in entries], ["a.txt", "b.txt"])
            self.assertEqual(entries[0].oid, first_oid)
            self.assertEqual(entries[1].oid, second_oid)

    def test_missing_index_is_empty(self) -> None:
        """空仓库没有 index 文件时应返回空列表。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))

            self.assertEqual(read_index(repo), [])

    def test_read_index_skips_extension_area(self) -> None:
        """读取 index 时应跳过扩展区，兼容官方 Git 写入的扩展。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            entry = self.make_entry("a.txt", "1" * 40)
            body = encode_index([entry])[:-20] + b"TREE" + struct.pack(">I", 4) + b"data"
            repo.index_path.write_bytes(body + hashlib.sha1(body).digest())

            entries = read_index(repo)

            self.assertEqual([item.path for item in entries], ["a.txt"])


if __name__ == "__main__":
    unittest.main()
