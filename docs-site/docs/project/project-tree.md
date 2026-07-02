# Project Tree

This page explains how `python-git-reproduction` is structured and why the repository layout matters. The goal is not to memorize file names. The goal is to understand how a Git-like system is divided into modules that can be reasoned about, tested, and changed without breaking unrelated behavior.

## Why Structure Matters In A Git Project

Git is one of those systems that becomes messy very quickly if its concerns are mixed together. Object encoding, index parsing, ref updates, working-tree deletion, merge logic, and remote transport all touch disk state, but they should not all live inside the same command function.

If you collapse everything into a few giant scripts, three problems appear immediately:

- safety-critical logic gets duplicated,
- binary-format code becomes hard to audit,
- tests become difficult to isolate and interpret.

That is why this project uses a module-oriented structure.

## Recommended Repository Layout

The internal project-tree document describes the repository roughly as follows:

```text
python-git-reproduction/
├── docs/
│   ├── README.md
│   ├── PROJECT_TREE.md
│   └── prd/
├── pygit/
│   ├── __init__.py
│   ├── cli.py
│   ├── errors.py
│   ├── paths.py
│   ├── lockfile.py
│   ├── repository.py
│   ├── objects.py
│   ├── index.py
│   ├── refs.py
│   ├── ignore.py
│   ├── diff.py
│   ├── merge.py
│   ├── pack.py
│   ├── remote.py
│   ├── working_tree.py
│   └── commands/
│       ├── __init__.py
│       ├── plumbing.py
│       └── porcelain.py
├── tests/
└── pyproject.toml
```

The exact repository may evolve, but the responsibility boundaries are the important part.

## Module Responsibilities

### `pygit/cli.py`

This module is the command-line entry point. Its job is to parse user input and route execution to the right command handler. It should not become the place where binary object parsing, merge algorithms, or path safety logic are implemented directly.

### `pygit/repository.py`

This module manages repository discovery, repository initialization, `.pygit` path resolution, and repository-level context. It answers questions like:

- where is the repository root,
- where is the `.pygit` directory,
- how should paths be resolved safely,
- what does the current repository state look like at a structural level.

### `pygit/objects.py`

This is the storage core for blob, tree, commit, and tag objects. It is responsible for:

- object header encoding and decoding,
- SHA-1 computation,
- zlib compression and decompression,
- loose object reading and writing,
- object integrity checks,
- and part of the interface between stored bytes and higher-level repository meaning.

### `pygit/index.py`

This module owns the Git Index V2 binary staging file. That means:

- header parsing,
- entry parsing,
- flags and stage handling,
- path sorting,
- 8-byte alignment,
- trailing checksum validation,
- extension-area handling.

This module is one of the most important compatibility modules in the repository because the index is not just a list of paths. It is a binary state machine sitting between the working tree and committed history.

### `pygit/refs.py`

This module manages `HEAD`, branches, tags, and remote-tracking refs. It handles:

- symbolic refs,
- detached `HEAD`,
- ref reads and writes,
- old-value validation,
- lock-based atomic updates.

Branch behavior becomes much easier to understand once you see that it is just ref movement implemented carefully.

### `pygit/lockfile.py`

This module centralizes `.lock` file creation, atomic replace behavior, and cleanup. It is intentionally shared because any metadata write path that re-implements lock handling independently is likely to drift into inconsistent behavior.

### `pygit/working_tree.py`

This module deals with the actual files visible to the user:

- scanning the working tree,
- writing file content back to disk,
- removing old tracked files,
- checking path safety before destructive actions.

This is where repository semantics and filesystem risk meet, so the module boundary needs to stay very clear.

### `pygit/diff.py`

This module provides difference calculation between trees, the index, and the working tree. Higher-level commands such as `status`, `merge`, and `stash` depend on accurate differences, but they should not each re-implement path-by-path comparison logic from scratch.

### `pygit/merge.py`

This module is responsible for merge behavior:

- lowest common ancestor search,
- fast-forward detection,
- three-way merge logic,
- conflict marker generation,
- index stage maintenance for conflicts.

Merging is both graph logic and content logic, which is why it deserves a dedicated module.

### `pygit/pack.py`

This module owns pack and idx behavior:

- packfile parsing,
- idx parsing,
- random access into packed objects,
- offset handling,
- delta expansion,
- pack generation.

This is another compatibility-critical module because binary layout errors here can silently break remote synchronization.

### `pygit/remote.py`

This module implements remote synchronization behavior such as discovery, transfer, and ref updates for local-path remotes and the dedicated `.pygit` server.

### `pygit/commands/plumbing.py`

This command layer exposes low-level operations such as:

- `hash-object`,
- `cat-file`,
- `write-tree`,
- `read-tree`,
- `commit-tree`,
- `update-ref`.

These commands are close to the repository engine and should mainly orchestrate verified lower-level module behavior.

### `pygit/commands/porcelain.py`

This command layer exposes user-oriented workflows such as:

- `init`,
- `add`,
- `rm`,
- `status`,
- `commit`,
- `log`,
- `branch`,
- `checkout`,
- `switch`,
- `tag`,
- `reset`,
- `stash`,
- `merge`,
- `fetch`,
- `push`,
- `clone`.

Porcelain commands are allowed to coordinate more moving parts, but they should still reuse lower-level modules instead of duplicating core logic.

## Why These Boundaries Support SOLID And DRY

The project explicitly requires SOLID and DRY principles. In practical terms, that means:

- object encoding logic should not be copied into commands,
- lock handling should not be rewritten in every ref update path,
- path-safety checks should not be re-invented separately in `rm`, `checkout`, and `reset`,
- merge-stage handling should not be scattered across unrelated modules,
- CLI parsing should not be mixed with binary parsing.

The point is not abstract design purity. The point is to keep dangerous and compatibility-sensitive logic in places where it can be audited and tested.

## Code Comment Requirements

The internal project rules also require comprehensive Chinese comments in Python source files. That means:

- each file should begin with an intent comment,
- public and complex internal functions should explain behavior, arguments, return values, exceptions, and side effects,
- binary layouts, long conditional logic, edge cases, and key algorithms should be explained in Chinese where they would otherwise be easy to misunderstand.

That comment policy is part of the project structure story because maintainability is not only about directories. It is also about how much future readers can trust the code to explain itself honestly.
