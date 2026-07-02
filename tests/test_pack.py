"""Packfile 与 idx v2 测试。

测试使用真实临时目录、真实 pack/idx 文件和真实对象库读写，避免只验证内存
数据结构。packfile 是远端同步基础，必须验证磁盘格式、idx 随机寻址和 delta
重建都能在真实 `.pygit` 目录中工作。
"""

from __future__ import annotations

import binascii
import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from pygit.objects import object_id, object_path, read_object, write_object
from pygit.pack import encode_idx, encode_pack_object_header, read_idx, write_pack
from pygit.repository import init_repository


class PackTests(unittest.TestCase):
    """验证 pack 生成、idx 读取、随机寻址和 ref-delta 解析。"""

    def test_write_pack_and_read_object_after_removing_loose(self) -> None:
        """对象 loose 文件删除后，应能通过 idx 从 pack 随机读回。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            oid = write_object(repo, "blob", b"hello\n")
            pack_path, idx_path = write_pack(repo, [oid])
            object_path(repo, oid).unlink()

            entries = read_idx(idx_path)
            obj = read_object(repo, oid)

            self.assertTrue(pack_path.exists())
            self.assertEqual(entries[0].oid, oid)
            self.assertEqual(obj.object_type, "blob")
            self.assertEqual(obj.content, b"hello\n")

    def test_short_oid_resolves_from_pack(self) -> None:
        """唯一短 SHA-1 应能解析 pack 中对象。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            oid = write_object(repo, "blob", b"packed\n")
            write_pack(repo, [oid])
            object_path(repo, oid).unlink()

            self.assertEqual(read_object(repo, oid[:8]).content, b"packed\n")

    def test_ref_delta_pack_object(self) -> None:
        """ref-delta pack 条目应基于 loose base 对象重建目标 blob。"""

        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repository(Path(tmp))
            base_oid = write_object(repo, "blob", b"hello ")
            target_content = b"hello world"
            target_oid = object_id("blob", target_content)

            # delta 格式：base size、result size、copy 指令、insert 指令。
            # copy 指令 0x90 表示后面有 1 字节 copy_size，从 base offset 0 复制 6 字节。
            delta = bytes([6, len(target_content), 0x90, 6, 5]) + b"world"
            encoded_delta = encode_pack_object_header(7, len(delta)) + bytes.fromhex(base_oid) + zlib.compress(delta)
            pack_without_checksum = struct.pack(">4sII", b"PACK", 2, 1) + encoded_delta
            pack_checksum = hashlib.sha1(pack_without_checksum).digest()
            pack_data = pack_without_checksum + pack_checksum
            pack_path = repo.objects_dir / "pack" / f"pack-{pack_checksum.hex()}.pack"
            idx_path = pack_path.with_suffix(".idx")
            pack_path.parent.mkdir(parents=True, exist_ok=True)
            pack_path.write_bytes(pack_data)
            crc = binascii.crc32(encoded_delta) & 0xFFFFFFFF
            idx_path.write_bytes(encode_idx([(target_oid, crc, 12)], pack_checksum))

            obj = read_object(repo, target_oid)

            self.assertEqual(obj.object_type, "blob")
            self.assertEqual(obj.content, target_content)


if __name__ == "__main__":
    unittest.main()

