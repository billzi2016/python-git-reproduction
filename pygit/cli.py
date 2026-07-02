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
from .merge import merge
from .objects import hash_file_object, read_object, write_file_object
from .refs import create_branch, current_branch_name, current_commit, delete_branch, list_branches, rename_branch, set_upstream, update_ref
from .remote import clone, fetch, push
from .reset import index_entries_from_tree, reset
from .repository import find_repository, init_repository
from .status import collect_status, format_status
from .stash import stash_apply, stash_pop, stash_push
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

    read_tree = subparsers.add_parser("read-tree", help="把 tree 对象读入 index")
    read_tree.add_argument("tree", help="根 tree 对象 ID")

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
    branch.add_argument("-m", "--move", nargs=2, metavar=("OLD", "NEW"), help="重命名分支")
    branch.add_argument("--set-upstream-to", metavar="UPSTREAM", help="设置分支上游引用")
    branch.add_argument("name", nargs="?", help="分支名")

    checkout = subparsers.add_parser("checkout", help="切换到分支、commit 或恢复路径")
    checkout.add_argument("items", nargs=argparse.REMAINDER, help="分支名、commit SHA-1，或 -- 后面的路径")

    switch = subparsers.add_parser("switch", help="切换到本地分支")
    switch.add_argument("-c", "--create", action="store_true", help="基于当前 HEAD 创建并切换分支")
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

    stash = subparsers.add_parser("stash", help="临时保存或恢复工作区状态")
    stash_sub = stash.add_subparsers(dest="stash_command")
    stash_push_parser = stash_sub.add_parser("push", help="保存当前工作区状态")
    stash_push_parser.add_argument("-m", "--message", default="WIP", help="stash 说明")
    stash_sub.add_parser("apply", help="应用栈顶 stash")
    stash_sub.add_parser("pop", help="应用并移除栈顶 stash")

    merge_parser = subparsers.add_parser("merge", help="合并分支或 commit")
    merge_parser.add_argument("target", help="要合并的分支名、标签或 commit")
    merge_parser.add_argument("-m", "--message", help="自动合并提交说明")

    clone_parser = subparsers.add_parser("clone", help="从本地路径远端克隆")
    clone_parser.add_argument("remote", help="远端仓库路径")
    clone_parser.add_argument("target", help="目标目录")

    fetch_parser = subparsers.add_parser("fetch", help="从 origin 抓取")
    fetch_parser.add_argument("remote", nargs="?", help="可选远端仓库路径")

    push_parser = subparsers.add_parser("push", help="推送到 origin")
    push_parser.add_argument("remote", nargs="?", help="可选远端仓库路径")
    push_parser.add_argument("branch", nargs="?", help="可选分支名")

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    """执行 init 命令。"""

    repo = init_repository(Path.cwd())
    print(f"Initialized empty pygit repository in {repo.gitdir}")
    return 0


def cmd_hash_object(args: argparse.Namespace) -> int:
    """执行 hash-object 命令。"""

    if args.write:
        repo = find_repository(Path.cwd())
        oid = write_file_object(repo, Path(args.path), args.type)
    else:
        oid = hash_file_object(Path(args.path), args.type)
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
    branch = current_branch_name(repo)
    if branch is not None:
        print(f"On branch {branch}")
    sys.stdout.write(format_status(collect_status(repo)))
    return 0


def cmd_write_tree(args: argparse.Namespace) -> int:
    """执行 write-tree 命令。"""

    repo = find_repository(Path.cwd())
    print(build_tree_from_index(repo))
    return 0


def cmd_read_tree(args: argparse.Namespace) -> int:
    """执行 read-tree 命令。"""

    repo = find_repository(Path.cwd())
    from .index import write_index

    write_index(repo, index_entries_from_tree(repo, args.tree))
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
            if len(info.parents) > 1:
                print("Merge: " + " ".join(parent[:7] for parent in info.parents))
            print(f"Author: {info.author}")
            print()
            for line in info.message.rstrip("\n").splitlines():
                print(f"    {line}")
            print()
    return 0


def cmd_branch(args: argparse.Namespace) -> int:
    """执行 branch 命令。"""

    repo = find_repository(Path.cwd())
    if args.move is not None:
        rename_branch(repo, args.move[0], args.move[1])
        return 0
    if args.set_upstream_to is not None:
        if args.name is None:
            raise PygitError("--set-upstream-to requires a branch name")
        set_upstream(repo, args.name, args.set_upstream_to)
        return 0
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
    if args.items[0] == "--":
        from .checkout import checkout_paths

        checkout_paths(repo, args.items[1:])
    else:
        checkout_target(repo, args.items[0])
    return 0


def cmd_switch(args: argparse.Namespace) -> int:
    """执行 switch 命令。"""

    repo = find_repository(Path.cwd())
    if args.create:
        create_branch(repo, args.branch)
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


def cmd_stash(args: argparse.Namespace) -> int:
    """执行 stash 命令。"""

    repo = find_repository(Path.cwd())
    command = args.stash_command or "push"
    if command == "push":
        oid = stash_push(repo, args.message)
        print(f"Saved working directory and index state {oid[:7]}")
        return 0
    if command == "apply":
        stash_apply(repo)
        return 0
    if command == "pop":
        stash_pop(repo)
        return 0
    raise PygitError(f"unsupported stash command: {command}")


def cmd_merge(args: argparse.Namespace) -> int:
    """执行 merge 命令。"""

    repo = find_repository(Path.cwd())
    oid = merge(repo, args.target, args.message)
    print(oid)
    return 0


def cmd_clone(args: argparse.Namespace) -> int:
    """执行 clone 命令。"""

    clone(Path(args.remote), Path(args.target))
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    """执行 fetch 命令。"""

    repo = find_repository(Path.cwd())
    fetched = fetch(repo, Path(args.remote) if args.remote else None)
    for branch, oid in fetched.items():
        print(f"{oid} refs/remotes/origin/{branch}")
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    """执行 push 命令。"""

    repo = find_repository(Path.cwd())
    oid = push(repo, Path(args.remote) if args.remote else None, args.branch)
    print(oid)
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
        if args.command == "read-tree":
            return cmd_read_tree(args)
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
        if args.command == "stash":
            return cmd_stash(args)
        if args.command == "merge":
            return cmd_merge(args)
        if args.command == "clone":
            return cmd_clone(args)
        if args.command == "fetch":
            return cmd_fetch(args)
        if args.command == "push":
            return cmd_push(args)
    except PygitError as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
