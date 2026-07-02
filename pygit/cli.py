"""命令行入口。

本模块只负责解析 CLI 参数、调用底层模块并把错误转换为稳定的退出码。
具体 Git 语义不直接写在这里，避免命令行表现和对象库实现耦合。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checkout import checkout_target, switch_branch
from .commit import commit_index, create_commit, parse_commit, walk_first_parent
from .errors import PygitError
from .objects import object_id, read_object, write_object
from .refs import create_branch, current_branch_name, current_commit, delete_branch, list_branches, update_ref
from .reset import reset
from .repository import find_repository, init_repository
from .status import collect_status, format_status
from .tag import create_annotated_tag, create_lightweight_tag, list_tags
from .working_tree import add_paths, build_tree_from_index, format_tree_pretty, remove_paths


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

    add = subparsers.add_parser("add", help="把文件加入暂存区")
    add.add_argument("paths", nargs="+", help="要加入暂存区的文件或目录")

    rm = subparsers.add_parser("rm", help="从暂存区和工作区删除文件")
    rm.add_argument("--cached", action="store_true", help="只从暂存区删除，保留工作区文件")
    rm.add_argument("paths", nargs="+", help="要删除的已追踪文件")

    subparsers.add_parser("status", help="显示工作区状态")

    subparsers.add_parser("write-tree", help="把当前 index 写成 tree 对象")

    commit_tree = subparsers.add_parser("commit-tree", help="根据 tree 创建 commit 对象")
    commit_tree.add_argument("tree", help="根 tree 对象 ID")
    commit_tree.add_argument("-p", "--parent", action="append", default=[], help="父 commit 对象 ID")

    update_ref_parser = subparsers.add_parser("update-ref", help="安全更新引用")
    update_ref_parser.add_argument("ref", help="引用全路径，例如 refs/heads/main")
    update_ref_parser.add_argument("new", help="新的 40 位对象 ID")
    update_ref_parser.add_argument("old", nargs="?", help="可选预期旧值")

    commit = subparsers.add_parser("commit", help="提交当前 index")
    commit.add_argument("-m", "--message", required=True, help="提交说明")

    log = subparsers.add_parser("log", help="显示提交历史")
    log.add_argument("-n", "--max-count", type=int, default=None, help="最多显示多少条")
    log.add_argument("--oneline", action="store_true", help="单行模式")

    branch = subparsers.add_parser("branch", help="列出、创建或删除本地分支")
    branch.add_argument("-d", "--delete", action="store_true", help="删除分支")
    branch.add_argument("name", nargs="?", help="分支名")

    checkout = subparsers.add_parser("checkout", help="切换到分支或 commit")
    checkout.add_argument("target", help="分支名或 commit SHA-1")

    switch = subparsers.add_parser("switch", help="切换到本地分支")
    switch.add_argument("branch", help="分支名")

    tag = subparsers.add_parser("tag", help="列出或创建标签")
    tag.add_argument("-a", "--annotate", action="store_true", help="创建附注标签")
    tag.add_argument("-m", "--message", help="附注标签说明")
    tag.add_argument("name", nargs="?", help="标签名")
    tag.add_argument("target", nargs="?", help="目标 commit，默认 HEAD")

    reset_parser = subparsers.add_parser("reset", help="重置当前 HEAD")
    reset_mode = reset_parser.add_mutually_exclusive_group()
    reset_mode.add_argument("--soft", action="store_true", help="只移动 HEAD")
    reset_mode.add_argument("--mixed", action="store_true", help="移动 HEAD 并刷新 index")
    reset_mode.add_argument("--hard", action="store_true", help="移动 HEAD、刷新 index 并重写工作区")
    reset_parser.add_argument("target", help="目标 commit 或分支名")

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
    elif obj.object_type == "tree":
        sys.stdout.buffer.write(format_tree_pretty(repo, obj.content))
    else:
        # `cat-file -p` 对 blob 应输出原始字节，避免文本编码破坏二进制内容。
        sys.stdout.buffer.write(obj.content)
        if obj.content and not obj.content.endswith(b"\n"):
            sys.stdout.buffer.write(b"\n")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """执行 add 命令。"""

    repo = find_repository(Path.cwd())
    add_paths(repo, [Path(path) for path in args.paths])
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    """执行 rm 命令。"""

    repo = find_repository(Path.cwd())
    remove_paths(repo, [Path(path) for path in args.paths], cached=args.cached)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """执行 status 命令。"""

    repo = find_repository(Path.cwd())
    sys.stdout.write(format_status(collect_status(repo)))
    return 0


def cmd_write_tree(args: argparse.Namespace) -> int:
    """执行 write-tree 命令。"""

    repo = find_repository(Path.cwd())
    print(build_tree_from_index(repo))
    return 0


def cmd_commit_tree(args: argparse.Namespace) -> int:
    """执行 commit-tree 命令。"""

    repo = find_repository(Path.cwd())
    message = sys.stdin.read()
    print(create_commit(repo, args.tree, args.parent, message))
    return 0


def cmd_update_ref(args: argparse.Namespace) -> int:
    """执行 update-ref 命令。"""

    repo = find_repository(Path.cwd())
    update_ref(repo, args.ref, args.new, args.old)
    return 0


def cmd_commit(args: argparse.Namespace) -> int:
    """执行 commit 命令。"""

    repo = find_repository(Path.cwd())
    oid = commit_index(repo, args.message)
    info = parse_commit(repo, oid)
    first_line = info.message.splitlines()[0] if info.message.splitlines() else ""
    print(f"[{oid[:7]}] {first_line}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """执行 log 命令。"""

    repo = find_repository(Path.cwd())
    start = current_commit(repo)
    for info in walk_first_parent(repo, start, args.max_count):
        if args.oneline:
            first_line = info.message.splitlines()[0] if info.message.splitlines() else ""
            print(f"{info.oid[:7]} {first_line}")
        else:
            print(f"commit {info.oid}")
            print(f"Author: {info.author}")
            print()
            for line in info.message.rstrip("\n").splitlines():
                print(f"    {line}")
            print()
    return 0


def cmd_branch(args: argparse.Namespace) -> int:
    """执行 branch 命令。"""

    repo = find_repository(Path.cwd())
    if args.delete:
        if args.name is None:
            raise PygitError("branch -d requires a branch name")
        delete_branch(repo, args.name)
        return 0
    if args.name is not None:
        create_branch(repo, args.name)
        return 0

    current = current_branch_name(repo)
    for branch in list_branches(repo):
        marker = "*" if branch == current else " "
        print(f"{marker} {branch}")
    return 0


def cmd_checkout(args: argparse.Namespace) -> int:
    """执行 checkout 命令。"""

    repo = find_repository(Path.cwd())
    checkout_target(repo, args.target)
    return 0


def cmd_switch(args: argparse.Namespace) -> int:
    """执行 switch 命令。"""

    repo = find_repository(Path.cwd())
    switch_branch(repo, args.branch)
    return 0


def cmd_tag(args: argparse.Namespace) -> int:
    """执行 tag 命令。"""

    repo = find_repository(Path.cwd())
    if args.name is None:
        for name in list_tags(repo):
            print(name)
        return 0

    target = args.target or current_commit(repo)
    if target is None:
        raise PygitError("cannot tag without commits")
    if args.annotate:
        if args.message is None:
            raise PygitError("annotated tag requires -m")
        create_annotated_tag(repo, args.name, target, args.message)
    else:
        create_lightweight_tag(repo, args.name, target)
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    """执行 reset 命令。"""

    repo = find_repository(Path.cwd())
    mode = "--mixed"
    if args.soft:
        mode = "--soft"
    elif args.hard:
        mode = "--hard"
    reset(repo, args.target, mode)
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
        if args.command == "add":
            return cmd_add(args)
        if args.command == "rm":
            return cmd_rm(args)
        if args.command == "status":
            return cmd_status(args)
        if args.command == "write-tree":
            return cmd_write_tree(args)
        if args.command == "commit-tree":
            return cmd_commit_tree(args)
        if args.command == "update-ref":
            return cmd_update_ref(args)
        if args.command == "commit":
            return cmd_commit(args)
        if args.command == "log":
            return cmd_log(args)
        if args.command == "branch":
            return cmd_branch(args)
        if args.command == "checkout":
            return cmd_checkout(args)
        if args.command == "switch":
            return cmd_switch(args)
        if args.command == "tag":
            return cmd_tag(args)
        if args.command == "reset":
            return cmd_reset(args)
    except PygitError as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
