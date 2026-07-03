# python-git-reproduction

[![Docs](https://img.shields.io/badge/docs-online-blue)](https://billzi2016.github.io/python-git-reproduction/)
[![English](https://img.shields.io/badge/language-English-black)](README.md)
[![中文](https://img.shields.io/badge/language-%E4%B8%AD%E6%96%87-red)](README_CN.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

`python-git-reproduction` is a project that reproduces Git in pure Python 3. The goal of this project is not to build a simplified version-control toy, but to implement Git's core low-level logic, high-level workflow, object storage format, index format, reference system, merge engine, packfile handling, and remote synchronization capabilities as completely as possible.

When the project runs, it creates a `.pygit` directory in the workspace. The design goal of `.pygit` is to be as compatible as possible with official Git object formats, index formats, reference formats, and packfile formats.

## Documentation Site

Public documentation site:

- https://billzi2016.github.io/python-git-reproduction/

The site is English-first by default. Chinese pages are available from the top-level Chinese navigation group inside the site.

## Documentation System

This repository now maintains two documentation layers:

- `docs/`: internal engineering documents, including the split PRD, SDD requirements, tasks, and project-structure planning.
- `docs-site/`: the public documentation website source built with MkDocs.

The public documentation site uses:

- **MkDocs Material** as the theme and site framework.
- **mkdocs-static-i18n** for bilingual site generation and per-page language switching.

The bilingual documentation structure is organized as:

- `docs-site/docs/en/`: English pages.
- `docs-site/docs/zh/`: Chinese pages.

The site is intentionally **English-first**:

- English is the default language and default entry point.
- Chinese is available through the language selector.
- When the same page exists in both languages, the MkDocs i18n setup is intended to keep readers on the corresponding page while switching languages.

In practice, this means:

- readers opening the site directly will land on English content first,
- Chinese readers can switch through the site language selector,
- internal source specifications remain under `docs/`,
- reader-facing tutorials and curated explanations live under `docs-site/`.

## License

This repository is released under the MIT License. See [LICENSE](LICENSE).

## Project Goals

The final goal is to reproduce Git's complete core feature set with the Python standard library, including:

- Repository initialization.
- Loose object storage.
- The four object types: blob, tree, commit, and tag.
- Git Index V2 staging area.
- The reference system for HEAD, branches, tags, and remote refs.
- Plumbing commands such as `hash-object`, `cat-file`, `write-tree`, `read-tree`, `commit-tree`, and `update-ref`.
- Porcelain commands such as `init`, `add`, `rm`, `status`, `commit`, `log`, `branch`, `checkout`, `switch`, `tag`, `reset`, and `stash`.
- Branch merging, lowest common ancestor computation, fast-forward merges, three-way merges, conflict markers, and index stages.
- Distributed synchronization capabilities such as packfiles, idx files, delta handling, `fetch`, `push`, and `clone`.

## Current Implementation Status

The current task list has been completed. The project supports local `.pygit` usage, local-path remotes, and a self-hosted `.pygit` dedicated TCP server.

Implemented commands:

- `pygit init`
- `pygit add`
- `pygit hash-object`
- `pygit hash-object -w`
- `pygit cat-file -t`
- `pygit cat-file -s`
- `pygit cat-file -p`
- `pygit write-tree`
- `pygit read-tree`
- `pygit commit-tree`
- `pygit update-ref`
- `pygit commit -m`
- `pygit log`
- `pygit log --oneline`
- `pygit status`
- `pygit rm`
- `pygit rm --cached`
- `pygit branch`
- `pygit branch <name>`
- `pygit branch -d <name>`
- `pygit checkout <branch-or-commit>`
- `pygit switch <branch>`
- `pygit tag`
- `pygit tag <name>`
- `pygit tag -a <name> -m <message>`
- `pygit reset --soft <target>`
- `pygit reset --mixed <target>`
- `pygit reset --hard <target>`
- `pygit stash push`
- `pygit stash apply`
- `pygit stash pop`
- `pygit merge <target>`
- `pygit clone <remote> <target>`
- `pygit fetch [remote]`
- `pygit push [remote] [branch]`
- `pygit serve [--host HOST] [--port PORT] [path]`

Implemented capabilities:

- Initialization of the base `.pygit` directory structure.
- Loose object encoding, SHA-1 calculation, and zlib-compressed storage.
- Loose object decompression, header parsing, size validation, and SHA-1 re-validation.
- Unique short SHA-1 resolution.
- 64 KB chunked hashing and compressed writing for large file blobs.
- Basic Git Index V2 reading and writing, sorting, padding, and checksum handling.
- Skipping Index V2 extension areas.
- Recursive tree object generation from the index.
- Index reconstruction from tree objects.
- Commit creation from the current branch HEAD and history traversal along the first-parent chain.
- Display of multi-parent merge commits.
- Reading author and committer information from `.pygit/config`.
- Three-way state comparison between HEAD, index, and working tree.
- Removal of tracked files from the index and safe deletion from the working tree.
- Local branch creation, listing, deletion, renaming, and upstream configuration.
- Clean-working-tree checkout to a branch or detached HEAD, with working tree and index rewrite.
- `checkout -- <path>` to restore a path from HEAD.
- `switch -c <branch>` to create and switch to a branch.
- Lightweight tags and annotated tags.
- Soft, mixed, and hard reset.
- Reset targets that support branch names, commit SHA-1 values, lightweight tags, and annotated tags.
- `stash push/apply/pop`, including three-way merge style application.
- Merge support for LCA, fast-forward, non-fast-forward automatic merge, conflict markers, and index stages 1/2/3.
- Basic pack v2 and idx v2 reading and writing, idx random access, ref-delta resolution, and non-delta pack generation.
- Local-path remote `clone`, `fetch`, `push`, and non-fast-forward push rejection.
- A self-hosted `.pygit` dedicated TCP server and `pygit://host:port` remotes.
- Ignore rules through `info/exclude`.
- A test suite directory based on Python standard library `unittest`.

Explicitly not implemented:

- GitHub, SSH Git, HTTP Git, and the official Git wire protocol.
- Git LFS.

## Quick Start

At the moment, the project can be run directly as a Python module:

```bash
python3 -m pygit.cli init
```

Write a blob object:

```bash
echo "hello" > hello.txt
python3 -m pygit.cli hash-object -w hello.txt
```

Show an object's type:

```bash
python3 -m pygit.cli cat-file -t <object-id>
```

Show an object's size:

```bash
python3 -m pygit.cli cat-file -s <object-id>
```

Show an object's content:

```bash
python3 -m pygit.cli cat-file -p <object-id>
```

If the project is installed in editable mode, `pyproject.toml` provides the `pygit` command entry point:

```bash
pygit init
```

### Local Commit Loop

```bash
python3 -m pygit.cli init
echo "hello" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "initial commit"
python3 -m pygit.cli log --oneline
python3 -m pygit.cli status
```

### Branching and Switching

```bash
python3 -m pygit.cli branch dev
python3 -m pygit.cli switch dev
echo "change" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "update hello"
python3 -m pygit.cli switch main
python3 -m pygit.cli merge dev
```

### Tags, Reset, and Stash

```bash
python3 -m pygit.cli tag v1.0.0
python3 -m pygit.cli tag -a v1.0.1 -m "release v1.0.1"
python3 -m pygit.cli reset --hard v1.0.0
python3 -m pygit.cli stash push -m "temporary work"
python3 -m pygit.cli stash pop
```

### Local-Path Remotes

```bash
python3 -m pygit.cli clone /path/to/source-repo /path/to/clone
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

### Self-Hosted `.pygit` Dedicated Server

Server side:

```bash
python3 -m pygit.cli serve --host 127.0.0.1 --port 9419 /path/to/repo
```

Client side:

```bash
python3 -m pygit.cli clone pygit://127.0.0.1:9419 /path/to/clone
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

`pygit://host:port` is this project's own dedicated protocol. It is not the official Git wire protocol.

## Tests

All project tests are placed under the root `tests/` directory and use Python standard library `unittest`.

Run the full test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Current test coverage includes:

- 62 `unittest` test cases.
- Repository initialization directory layout.
- Upward repository discovery.
- Rejection of repeated initialization.
- Blob object header encoding.
- Git object SHA-1 calculation.
- Loose object writing and reading.
- Large-file streaming hash and write.
- Short SHA-1 resolution.
- Corrupted object rejection.
- Git Index V2 encoding, decoding, sorting, and checksum.
- Index V2 extension skipping.
- `add` writing a blob and updating the index.
- `write-tree` generating recursive trees.
- `read-tree` rebuilding the index from a tree.
- `commit-tree` creating commit objects.
- `commit` updating the current HEAD branch.
- `log --oneline` reading commit history.
- Config-based author and committer handling.
- `status` three-way state comparison.
- `rm` and `rm --cached`.
- Ignore rules.
- `branch` creation, listing, deletion, renaming, and upstream configuration.
- `checkout` by branch or commit.
- `checkout -- <path>`.
- `switch` for local branches.
- `switch -c`.
- `tag` lightweight and annotated tags.
- `reset` soft, mixed, and hard.
- `stash` push, apply, pop, and three-way apply conflicts.
- `merge` LCA, fast-forward, three-way merge, and conflict isolation.
- Pack v2, idx v2, random pack access, and ref-delta.
- Local-path remote clone/fetch/push and non-fast-forward rejection.
- Self-hosted `.pygit` dedicated TCP server clone/fetch/push.
- The main CLI workflow chain.

The project requires tests to avoid replacing core Git behavior with mocks. The current repository contains no use of `mock`, `Mock`, `unittest.mock`, `MagicMock`, or `patch(`.

## Project Documentation

Core documentation entry points:

- `docs/README.md`: documentation reading order.
- `docs/SDD_REQUIREMENTS.md`: SDD engineering requirements, testing requirements, dangerous-command safety requirements, SOLID/DRY, and commit quality requirements.
- `docs/TASKS.md`: development task list, with completed tasks marked as `[x]`.
- `docs/PROJECT_TREE.md`: recommended code layout and module responsibilities.
- `docs/prd/`: the split product requirements documents.

## Project Structure

The repository is organized around a layered Git reproduction architecture:

```text
python-git-reproduction/
├── docs/                 # Internal engineering documents, PRD, SDD, tasks, and planning
├── docs-site/            # Public MkDocs documentation site source
├── pygit/                # Core Python implementation
│   ├── cli.py            # CLI entry point
│   ├── repository.py     # Repository discovery and repository context
│   ├── objects.py        # Blob/tree/commit/tag encoding, storage, and validation
│   ├── index.py          # Git Index V2 binary staging area
│   ├── refs.py           # HEAD, branches, tags, and remote refs
│   ├── lockfile.py       # Atomic write and lock-file handling
│   ├── working_tree.py   # Working-tree scanning and rewrite behavior
│   ├── diff.py           # State comparison helpers
│   ├── merge.py          # LCA, fast-forward, three-way merge, and conflicts
│   ├── pack.py           # Pack and idx parsing and generation
│   ├── remote.py         # Local-path remotes and dedicated pygit server sync
│   └── commands/         # Plumbing and porcelain command orchestration
├── tests/                # Real unittest-based repository tests
├── LICENSE               # MIT license
└── pyproject.toml        # Packaging and command entry-point definition
```

High-level module responsibilities:

- `pygit/objects.py`: manages Git object headers, SHA-1 object IDs, zlib compression, loose objects, and object integrity validation.
- `pygit/index.py`: implements Git Index V2 encoding, decoding, sorting, stage bits, padding, and checksums.
- `pygit/refs.py`: manages symbolic `HEAD`, detached `HEAD`, branch refs, tags, remote refs, and atomic ref updates.
- `pygit/merge.py`: manages DAG traversal, lowest common ancestor discovery, fast-forward checks, three-way merge behavior, and conflict states.
- `pygit/pack.py`: manages pack v2, idx v2, packed object lookup, and delta-related behavior.
- `pygit/remote.py`: manages local-path remote workflows and the dedicated `.pygit` server protocol.
- `tests/`: verifies repository behavior with real temporary repositories, real object files, real index files, and real working-tree state instead of mocks.

This structure reflects the project's engineering rules: clear module responsibilities, centralized handling of dangerous logic, and reuse of binary-format and safety-critical behavior.
