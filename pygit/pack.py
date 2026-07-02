"""Packfile 与 idx v2 读写。

本模块实现 Git pack v2 的基础能力：生成非 delta pack、生成 idx v2、读取
idx fan-out 表、通过 idx 随机定位 pack 中的对象，并解析普通对象与 ref-delta
对象。Packfile 是远端 fetch/push 的基础，因此这里不使用模拟对象，所有测试
都应写真实 pack/idx 文件并从磁盘读取验证。
"""

from __future__ import annotations

import binascii
import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

from .errors import ObjectError, PygitError
from .objects import GitObject, decode_raw_object, encode_object, read_object, validate_oid
from .repository import Repository

PACK_SIGNATURE = b"PACK"
PACK_VERSION = 2
IDX_SIGNATURE = b"\xfftOc"
IDX_VERSION = 2
TYPE_TO_CODE = {"commit": 1, "tree": 2, "blob": 3, "tag": 4}
CODE_TO_TYPE = {1: "commit", 2: "tree", 3: "blob", 4: "tag", 6: "ofs_delta", 7: "ref_delta"}


class PackError(PygitError):
    """pack 或 idx 文件格式、校验、delta 解析失败时抛出。"""


@dataclass(frozen=True)
class PackIndexEntry:
    """idx 中的一条对象索引记录。"""

    oid: str
    crc32: int
    offset: int


@dataclass(frozen=True)
class PackedObject:
    """pack 中解压后的对象记录。"""

    object_type: str
    content: bytes
    oid: str
    offset: int
    crc32: int
    packed_end: int


def write_pack(repo: Repository, oids: list[str]) -> tuple[Path, Path]:
    """把对象列表写成 pack v2 和 idx v2 文件。

    当前生成器写普通非 delta 对象，保证格式清晰可验证；读取器已经支持
    ref-delta，为后续远端接收标准 Git pack 做准备。
    """

    unique_oids = sorted(dict.fromkeys(oids))
    chunks = [struct.pack(">4sII", PACK_SIGNATURE, PACK_VERSION, len(unique_oids))]
    object_records: list[tuple[str, int, int]] = []
    offset = len(chunks[0])
    for oid in unique_oids:
        obj = read_object(repo, oid)
        encoded = encode_pack_object(obj.object_type, obj.content)
        crc = binascii.crc32(encoded) & 0xFFFFFFFF
        chunks.append(encoded)
        object_records.append((obj.oid, crc, offset))
        offset += len(encoded)

    pack_without_checksum = b"".join(chunks)
    pack_checksum = hashlib.sha1(pack_without_checksum).digest()
    pack_data = pack_without_checksum + pack_checksum
    pack_name = f"pack-{pack_checksum.hex()}"
    pack_path = repo.objects_dir / "pack" / f"{pack_name}.pack"
    idx_path = repo.objects_dir / "pack" / f"{pack_name}.idx"
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_bytes(pack_data)
    idx_path.write_bytes(encode_idx(object_records, pack_checksum))
    return pack_path, idx_path


def encode_pack_object(object_type: str, content: bytes) -> bytes:
    """编码单个 pack 对象条目。"""

    if object_type not in TYPE_TO_CODE:
        raise PackError(f"unsupported pack object type: {object_type}")
    header = encode_pack_object_header(TYPE_TO_CODE[object_type], len(content))
    compressed = zlib.compress(content, level=zlib.Z_BEST_COMPRESSION)
    return header + compressed


def encode_pack_object_header(type_code: int, size: int) -> bytes:
    """编码 pack 对象变长 header。"""

    first_size_bits = size & 0x0F
    size >>= 4
    first = (type_code << 4) | first_size_bits
    out = []
    if size:
        first |= 0x80
    out.append(first)
    while size:
        byte = size & 0x7F
        size >>= 7
        if size:
            byte |= 0x80
        out.append(byte)
    return bytes(out)


def encode_idx(records: list[tuple[str, int, int]], pack_checksum: bytes) -> bytes:
    """编码 idx v2 文件。"""

    sorted_records = sorted(records, key=lambda item: item[0])
    fanout = []
    count = 0
    for prefix in range(256):
        while count < len(sorted_records) and int(sorted_records[count][0][:2], 16) <= prefix:
            count += 1
        fanout.append(count)

    chunks = [IDX_SIGNATURE, struct.pack(">I", IDX_VERSION)]
    chunks.extend(struct.pack(">I", value) for value in fanout)
    chunks.extend(bytes.fromhex(oid) for oid, _crc, _offset in sorted_records)
    chunks.extend(struct.pack(">I", crc) for _oid, crc, _offset in sorted_records)
    chunks.extend(struct.pack(">I", offset) for _oid, _crc, offset in sorted_records)
    chunks.append(pack_checksum)
    body = b"".join(chunks)
    return body + hashlib.sha1(body).digest()


def read_idx(idx_path: Path) -> list[PackIndexEntry]:
    """读取 idx v2 并返回对象索引记录。"""

    data = idx_path.read_bytes()
    if len(data) < 8 + 1024 + 40:
        raise PackError("idx file is too small")
    body = data[:-20]
    if hashlib.sha1(body).digest() != data[-20:]:
        raise PackError("idx checksum mismatch")
    if body[:4] != IDX_SIGNATURE:
        raise PackError("idx signature is invalid")
    version = struct.unpack(">I", body[4:8])[0]
    if version != IDX_VERSION:
        raise PackError(f"unsupported idx version: {version}")

    fanout_offset = 8
    fanout = [struct.unpack(">I", body[fanout_offset + i * 4 : fanout_offset + (i + 1) * 4])[0] for i in range(256)]
    count = fanout[-1]
    names_offset = fanout_offset + 1024
    crc_offset = names_offset + count * 20
    offsets_offset = crc_offset + count * 4
    if offsets_offset + count * 4 + 20 != len(body):
        raise PackError("idx layout size is invalid")

    entries = []
    for index in range(count):
        oid = body[names_offset + index * 20 : names_offset + (index + 1) * 20].hex()
        crc = struct.unpack(">I", body[crc_offset + index * 4 : crc_offset + (index + 1) * 4])[0]
        offset = struct.unpack(">I", body[offsets_offset + index * 4 : offsets_offset + (index + 1) * 4])[0]
        entries.append(PackIndexEntry(oid=oid, crc32=crc, offset=offset))
    return entries


def find_pack_object(repo: Repository, oid_prefix: str) -> tuple[Path, PackIndexEntry] | None:
    """在所有 idx 文件中查找完整或唯一短对象 ID。"""

    validate_oid(oid_prefix, allow_short=True)
    matches: list[tuple[Path, PackIndexEntry]] = []
    for idx_path in sorted((repo.objects_dir / "pack").glob("*.idx")):
        for entry in read_idx(idx_path):
            if entry.oid.startswith(oid_prefix):
                matches.append((idx_path.with_suffix(".pack"), entry))
    if not matches:
        return None
    if len(matches) > 1:
        raise ObjectError(f"ambiguous object id: {oid_prefix}")
    return matches[0]


def read_packed_object(repo: Repository, pack_path: Path, entry: PackIndexEntry) -> GitObject:
    """通过 idx 记录从 pack 中随机读取对象。"""

    pack_data = pack_path.read_bytes()
    verify_pack_header(pack_data)
    packed = read_pack_entry(repo, pack_data, entry.offset)
    if packed.oid != entry.oid:
        raise PackError("packed object oid does not match idx")
    return GitObject(object_type=packed.object_type, content=packed.content, oid=packed.oid)


def verify_pack_header(pack_data: bytes) -> int:
    """校验 pack header 和尾部 checksum，返回对象数量。"""

    if len(pack_data) < 32:
        raise PackError("pack file is too small")
    if hashlib.sha1(pack_data[:-20]).digest() != pack_data[-20:]:
        raise PackError("pack checksum mismatch")
    signature, version, count = struct.unpack(">4sII", pack_data[:12])
    if signature != PACK_SIGNATURE:
        raise PackError("pack signature is invalid")
    if version != PACK_VERSION:
        raise PackError(f"unsupported pack version: {version}")
    return count


def read_pack_entry(repo: Repository, pack_data: bytes, offset: int) -> PackedObject:
    """读取 pack 中指定偏移处的对象条目。"""

    type_code, declared_size, cursor = decode_pack_object_header(pack_data, offset)
    object_type = CODE_TO_TYPE.get(type_code)
    if object_type is None:
        raise PackError(f"unsupported pack type code: {type_code}")

    base_oid = None
    if object_type == "ref_delta":
        base_oid = pack_data[cursor : cursor + 20].hex()
        cursor += 20
    elif object_type == "ofs_delta":
        raise PackError("ofs_delta is not implemented")

    content, end = decompress_from(pack_data, cursor)
    if len(content) != declared_size:
        raise PackError("packed object size does not match header")

    if object_type == "ref_delta":
        if base_oid is None:
            raise PackError("ref_delta is missing base oid")
        base = read_object(repo, base_oid)
        content = apply_delta(base.content, content)
        object_type = base.object_type

    oid = hashlib.sha1(encode_object(object_type, content)).hexdigest()
    crc = binascii.crc32(pack_data[offset:end]) & 0xFFFFFFFF
    return PackedObject(object_type=object_type, content=content, oid=oid, offset=offset, crc32=crc, packed_end=end)


def decode_pack_object_header(data: bytes, offset: int) -> tuple[int, int, int]:
    """解码 pack 对象变长 header，返回 type、size 和内容起始偏移。"""

    first = data[offset]
    type_code = (first >> 4) & 0b111
    size = first & 0x0F
    shift = 4
    cursor = offset + 1
    byte = first
    while byte & 0x80:
        byte = data[cursor]
        cursor += 1
        size |= (byte & 0x7F) << shift
        shift += 7
    return type_code, size, cursor


def decompress_from(data: bytes, offset: int) -> tuple[bytes, int]:
    """从指定偏移开始 zlib 解压，并返回消耗后的结束偏移。"""

    decompressor = zlib.decompressobj()
    content = decompressor.decompress(data[offset:])
    if not decompressor.eof:
        raise PackError("packed zlib stream is truncated")
    consumed = len(data[offset:]) - len(decompressor.unused_data)
    return content, offset + consumed


def apply_delta(base: bytes, delta: bytes) -> bytes:
    """应用 Git delta 指令，返回重建后的对象内容。"""

    cursor, base_size = read_delta_size(delta, 0)
    cursor, result_size = read_delta_size(delta, cursor)
    if base_size != len(base):
        raise PackError("delta base size mismatch")
    out = bytearray()
    while cursor < len(delta):
        opcode = delta[cursor]
        cursor += 1
        if opcode & 0x80:
            copy_offset = 0
            copy_size = 0
            if opcode & 0x01:
                copy_offset |= delta[cursor]
                cursor += 1
            if opcode & 0x02:
                copy_offset |= delta[cursor] << 8
                cursor += 1
            if opcode & 0x04:
                copy_offset |= delta[cursor] << 16
                cursor += 1
            if opcode & 0x08:
                copy_offset |= delta[cursor] << 24
                cursor += 1
            if opcode & 0x10:
                copy_size |= delta[cursor]
                cursor += 1
            if opcode & 0x20:
                copy_size |= delta[cursor] << 8
                cursor += 1
            if opcode & 0x40:
                copy_size |= delta[cursor] << 16
                cursor += 1
            if copy_size == 0:
                copy_size = 0x10000
            out.extend(base[copy_offset : copy_offset + copy_size])
        elif opcode:
            out.extend(delta[cursor : cursor + opcode])
            cursor += opcode
        else:
            raise PackError("delta opcode 0 is invalid")
    if len(out) != result_size:
        raise PackError("delta result size mismatch")
    return bytes(out)


def read_delta_size(data: bytes, offset: int) -> tuple[int, int]:
    """读取 Git delta 的变长 size 字段。"""

    size = 0
    shift = 0
    cursor = offset
    while True:
        byte = data[cursor]
        cursor += 1
        size |= (byte & 0x7F) << shift
        if not byte & 0x80:
            break
        shift += 7
    return cursor, size

