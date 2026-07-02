# Getting Started

This page is the safest place to begin if you want to try `python-git-reproduction` without first reading every design document. It explains what the project currently does, what it does not do, how to run it, and how to validate that your local environment is behaving correctly.

## What You Are Running

This repository provides a Git-like implementation written in pure Python 3. The repository metadata directory it creates is named `.pygit`.

The project is not a wrapper around the official `git` binary. It computes object IDs itself, writes loose objects itself, reads and writes its own Index V2 file, manages its own refs, performs its own merge logic, and can transfer repository state through either local-path remotes or a dedicated `.pygit` TCP server.

## What Works Today

The current implementation already supports a serious local workflow:

- initialize a repository,
- add files into the staging area,
- create commits,
- inspect history,
- create and delete branches,
- switch branches,
- create tags,
- run soft, mixed, and hard reset,
- stash work in progress,
- merge branches,
- clone, fetch, and push against local-path remotes,
- clone, fetch, and push through a dedicated `pygit://host:port` server.

It also supports core storage and validation behaviors such as:

- loose object compression and validation,
- tree generation from the index,
- index reconstruction from tree objects,
- pack v2 and idx v2 basics,
- ref-delta reading,
- conflict stages in the index for merge conflicts,
- refusal of non-fast-forward push,
- safety checks around dangerous working-tree operations.

## What Does Not Work

Before you start, it is important to understand the boundary clearly.

This project does not currently implement:

- GitHub integration,
- SSH Git,
- HTTP Git,
- the official Git wire protocol,
- Git LFS.

So if your expectation is "I can point this at GitHub and use it as a full official Git client," that is outside the current scope. If your expectation is "I can study and use a locally functional Git-like system with real object storage, real index behavior, and a self-hosted `.pygit` server," that is the intended use case.

## Environment Assumptions

The project is designed to run with Python 3 and the Python standard library only. That means you do not need a large dependency stack just to run the implementation.

The repository also follows a conservative safety model because some commands are destructive by nature. Commands such as `reset --hard`, `checkout`, `switch`, `rm`, and some stash or merge flows can rewrite or remove tracked files in the working tree. The implementation is therefore expected to protect paths outside the repository and avoid unsafe deletion behavior.

## Run From Source

The simplest way to start is to run the CLI module directly from the repository root:

```bash
python3 -m pygit.cli init
```

This creates a `.pygit` directory in the current working directory.

## Minimal Local Workflow

Create a repository:

```bash
python3 -m pygit.cli init
```

Create a file, stage it, and commit it:

```bash
echo "hello" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "initial commit"
```

Inspect the result:

```bash
python3 -m pygit.cli log --oneline
python3 -m pygit.cli status
```

This sequence is the smallest useful closed loop in the project. If it works, you have confirmed that repository initialization, object writing, index updates, commit creation, ref updates, history traversal, and status comparison are all working together.

## Low-Level Object Commands

If you want to inspect the storage model directly, you can use the plumbing commands.

Write a blob object:

```bash
echo "hello" > hello.txt
python3 -m pygit.cli hash-object -w hello.txt
```

Inspect an object's type:

```bash
python3 -m pygit.cli cat-file -t <object-id>
```

Inspect an object's size:

```bash
python3 -m pygit.cli cat-file -s <object-id>
```

Print an object's content:

```bash
python3 -m pygit.cli cat-file -p <object-id>
```

These commands are important because they let you see that `.pygit` is built around content-addressed objects rather than around file names or branch labels.

## Branching And Merge Example

You can also try a simple branch-and-merge flow:

```bash
python3 -m pygit.cli branch dev
python3 -m pygit.cli switch dev
echo "change" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "update hello"
python3 -m pygit.cli switch main
python3 -m pygit.cli merge dev
```

This exercises branch creation, branch switching, a second commit, `HEAD` movement, merge-base logic, and working-tree rewrite behavior.

## Tags, Reset, And Stash

The project also supports a useful set of day-to-day repository state tools:

```bash
python3 -m pygit.cli tag v1.0.0
python3 -m pygit.cli tag -a v1.0.1 -m "release v1.0.1"
python3 -m pygit.cli reset --hard v1.0.0
python3 -m pygit.cli stash push -m "temporary work"
python3 -m pygit.cli stash pop
```

These commands are where safety really matters. `reset --hard` is intentionally dangerous in any Git-like system, so the implementation must be careful about path boundaries and deletion behavior.

## Local-Path Remote Workflow

You do not need a network server just to test remote behavior. The project supports local-path remotes:

```bash
python3 -m pygit.cli clone /path/to/source-repo /path/to/clone
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

This is a good first remote workflow because it lets you inspect both repositories directly on disk.

## Dedicated `.pygit` Server

The project also implements its own dedicated TCP server. It is not the official Git daemon and does not speak the official Git wire protocol.

Start the server:

```bash
python3 -m pygit.cli serve --host 127.0.0.1 --port 9419 /path/to/repo
```

Then clone from it:

```bash
python3 -m pygit.cli clone pygit://127.0.0.1:9419 /path/to/clone
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

If you are new to repository internals, this server is useful because it keeps the transport model small enough to study.

## How To Verify Your Setup

The repository uses Python standard library `unittest` and keeps real integration-style tests under `tests/`.

Run the full suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

The current documented validation state is:

```text
Ran 62 tests

OK
```

That matters because this project does not rely on mocks for its core Git behavior. The tests are meant to exercise real temporary repositories, real `.pygit` directories, real objects, real index files, and real working-tree files.

## Recommended Next Steps

After you complete the quick start, continue in one of these directions:

- Read `Git Teaching` if you first want to understand Git's ideas.
- Read `Build Git Teaching` if you want implementation structure and module-level reasoning.
- Read `Project` if you want the engineering boundary, task breakdown, and SDD constraints.
- Read `PRD` if you want the formal requirement documents behind the codebase.
