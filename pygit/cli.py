"""命令行入口。

本模块只负责解析 CLI 参数、调用底层模块并把错误转换为稳定的退出码。
具体 Git 语义不直接写在这里，避免命令行表现和对象库实现耦合。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import PygitError
from .objects import object_id, read_object, write_object
from .repository import find_repository, init_repository


def build_parser() -> argparse.ArgumentParser:
    """创建 `.pygit` 命令解析器。"""

    parser = argparse.ArgumentParser(prog="pygit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="初始化 .pygit 仓库")

    hash_object = subparsers.add_parser("hash-object", help="计算或写入 Git 对象")
    hash_object.add_argument("-t", "--type", default="blob", help="对象类型，默认 blob")
    hash_object.add_argument("-w", "--write", action="store_true", help="写入对象库")
    hash_object.add_argument("path", help="要读取的文件路径")

    cat_file = subparsers.add_parser("cat-file", help="读取 Git 对象")
    mode = cat_file.add_mutually_exclusive_group(required=True)
    mode.add_argument("-t", "--type", action="store_true", help="输出对象类型")
    mode.add_argument("-s", "--size", action="store_true", help="输出对象内容大小")
    mode.add_argument("-p", "--pretty", action="store_true", help="输出对象内容")
    cat_file.add_argument("object", help="完整或唯一短对象 ID")

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    """执行 init 命令。"""

    repo = init_repository(Path.cwd())
    print(f"Initialized empty pygit repository in {repo.gitdir}")
    return 0


def cmd_hash_object(args: argparse.Namespace) -> int:
    """执行 hash-object 命令。"""

    content = Path(args.path).read_bytes()
    if args.write:
        repo = find_repository(Path.cwd())
        oid = write_object(repo, args.type, content)
    else:
        oid = object_id(args.type, content)
    print(oid)
    return 0


def cmd_cat_file(args: argparse.Namespace) -> int:
    """执行 cat-file 命令。"""

    repo = find_repository(Path.cwd())
    obj = read_object(repo, args.object)
    if args.type:
        print(obj.object_type)
    elif args.size:
        print(len(obj.content))
    else:
        # `cat-file -p` 对 blob 应输出原始字节，避免文本编码破坏二进制内容。
        sys.stdout.buffer.write(obj.content)
        if obj.content and not obj.content.endswith(b"\n"):
            sys.stdout.buffer.write(b"\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """命令行主函数，返回进程退出码。"""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            return cmd_init(args)
        if args.command == "hash-object":
            return cmd_hash_object(args)
        if args.command == "cat-file":
            return cmd_cat_file(args)
    except PygitError as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

