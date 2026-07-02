# Tasks

This page explains the task breakdown used by `python-git-reproduction`. It is based on the internal `docs/TASKS.md` file, but it is written for readers who want to understand not only what was done, but why the work was broken down in this order.

## Why A Task Breakdown Matters

Building a Git-like system becomes confusing very quickly if you treat it as one large coding task. Git is not one feature. It is a network of related behaviors:

- a content-addressed object store,
- a binary staging file,
- named references,
- a commit graph,
- working-tree rewrite rules,
- merge logic,
- pack transport,
- safety boundaries,
- and tests that prove the whole thing behaves consistently.

Because of that, the project uses a staged task list. The goal of the list is not project management theater. The goal is to make sure prerequisites appear before dependent features, and to make sure safety and tests grow alongside functionality.

## High-Level Task Flow

The implementation work was organized in this order:

1. Define documentation and engineering constraints.
2. Create the base project skeleton.
3. Implement repository initialization.
4. Implement the object database.
5. Implement plumbing commands.
6. Implement Index V2 staging behavior.
7. Build the local commit workflow.
8. Implement refs and branch operations.
9. Implement working-tree status and file removal behavior.
10. Implement checkout and switch behavior.
11. Implement the remaining porcelain commands such as tag, reset, and stash.
12. Implement merge behavior.
13. Implement packfile and remote capabilities.
14. Build a real test suite around all of the above.

That order is important. For example, you cannot implement `commit` correctly before you can write trees and commits, and you cannot implement safe `checkout` before you can validate working-tree rewrite boundaries.

## Documentation And Engineering Constraints

The first group of tasks established the rules of the project itself. That included:

- splitting the giant PRD into maintainable files under `docs/prd/`,
- writing a project tree document,
- writing SDD engineering requirements,
- requiring Python standard library `unittest`,
- requiring no mock-based replacement of core Git behavior,
- requiring strong safety handling for dangerous commands,
- requiring SOLID and DRY principles,
- requiring comprehensive Chinese code comments,
- explicitly declaring that Git LFS is out of scope.

This may look like planning work rather than implementation work, but in a systems project it is part of implementation quality. It determines whether later code remains coherent.

## Project Skeleton

The next task group built the basic repository shape:

- `pyproject.toml`,
- the `pygit/` package,
- the `tests/` directory,
- `.gitignore`,
- shared modules such as `errors.py`, `paths.py`, `lockfile.py`, and `cli.py`.

This stage matters because Git-like behavior touches many areas at once. If you do not create shared error handling, path validation, and atomic write logic early, that logic tends to get duplicated across commands later.

## Repository Initialization

After the skeleton came repository initialization:

- create `.pygit`,
- create `HEAD`,
- create `config`,
- create `objects/info` and `objects/pack`,
- create `refs/heads`, `refs/tags`, and `refs/remotes`,
- support upward repository discovery,
- reject repeated initialization.

This stage provides the minimum repository context required for all later commands.

## Object Database

The object-database tasks built the storage engine:

- Git object header encoding,
- blob SHA-1 calculation,
- loose object path layout,
- zlib best-compression writes,
- loose object reads,
- header parsing,
- size validation,
- SHA-1 re-validation,
- unique short SHA-1 resolution,
- corrupted object rejection,
- streaming support for large files,
- packfile object reads.

This is the real foundation of the system. Once objects exist, the rest of Git becomes a matter of naming, ordering, grouping, and comparing those objects.

## Plumbing Commands

The plumbing stage exposed the low-level repository engine as commands:

- `hash-object`,
- `cat-file`,
- `write-tree`,
- `read-tree`,
- `commit-tree`,
- `update-ref`.

These commands are valuable because they make the storage model inspectable. They also allow higher-level commands to be built from smaller verified primitives.

## Index V2 Staging

The index tasks implemented the binary staging area:

- Index V2 header,
- entry encoding,
- 8-byte padding,
- trailing SHA-1 checksum,
- checksum validation on read,
- path sorting,
- updating existing paths instead of duplicating them,
- stage 1/2/3 conflict entries,
- extension support.

For beginners, this is a crucial transition point. Up to this stage, Git can still look like "files plus hashes." Once the index appears, the difference between the working tree, the staging area, and committed history becomes much clearer.

## Local Commit Workflow

The next tasks turned the storage engine into a usable history workflow:

- `add` writes blobs and updates the index,
- `write-tree` generates recursive trees,
- `commit-tree` creates commit objects,
- `commit -m` creates commits from the index and updates the current branch,
- `log` and `log --oneline` traverse history,
- multi-parent commit display works,
- author and committer information can come from config.

This is where the repository begins to feel like Git rather than like a binary storage exercise.

## Refs And Branches

After commits came naming and navigation:

- reading `HEAD`,
- symbolic `HEAD`,
- detached `HEAD`,
- atomic ref updates,
- lightweight and annotated tags,
- revision resolution through branches and tags,
- branch creation, listing, deletion, renaming,
- upstream tracking support.

Branches are easy to misunderstand if you think of them as containers. These tasks make it clear that a branch is only a movable ref pointing to a commit.

## Working Tree And Deletion Safety

The working-tree tasks focused on visibility and safe mutation:

- compare `HEAD` tree to index,
- compare index to working tree,
- show staged and unstaged changes,
- show untracked files,
- support `rm --cached`,
- support tracked-file removal from disk plus index updates,
- perform path-boundary checks before deletion,
- avoid recursive directory deletion,
- support ignore rules,
- improve status output format.

This is where a Git-like project starts interacting with user files in a truly risky way. That is why safety requirements are not optional background details.

## Checkout, Switch, Tag, Reset, Stash, And Merge

The later command groups completed the state-transition workflow:

- branch checkout and detached checkout,
- `switch` and `switch -c`,
- pre-check refusal on dirty working trees,
- target object validation before rewrite,
- rewrite only tracked files from the old index,
- refresh the index after checkout,
- update `HEAD` at the right point,
- lightweight and annotated tags,
- soft, mixed, and hard reset,
- preservation of untracked files during hard reset,
- stash push, apply, and pop,
- stash stack support,
- three-way stash application,
- DAG traversal,
- lowest common ancestor search,
- fast-forward merge,
- three-way merge,
- merge commits with two parents,
- conflict markers,
- index stages 1/2/3,
- refusal to commit while conflicts remain unresolved.

This is the point where Git's behavior becomes less about file storage and more about state coordination under change.

## Packfile, Remote, And Server Tasks

The remote stage expanded the repository from local history to synchronized history:

- pack v2 reading,
- idx v2 reading,
- random object access in packfiles,
- delta parsing,
- pack generation,
- `clone`, `fetch`, and `push`,
- non-fast-forward push rejection,
- a dedicated `.pygit` server,
- `pygit://host:port` remotes,
- local-path and server-based clone/fetch/push,
- explicit rejection of official Git wire protocol scope,
- explicit rejection of Git LFS scope.

This stage matters because it proves the project is not limited to a single local repository. It can move real object history between repositories.

## Test Tasks

The final task group built a substantial `unittest` suite around repository behavior:

- repository tests,
- object tests,
- CLI tests,
- index tests,
- working-tree tests,
- refs and commit tests,
- status and removal tests,
- branch tests,
- checkout tests,
- reset tests,
- tag tests,
- merge tests,
- pack tests,
- remote tests,
- server tests.

The repository's stated policy is that core Git behavior must not be substituted with mocks. The tests are expected to use real temporary directories, real repositories, real object files, real index files, and real working-tree state.

## Current Status

The internal task list is fully checked off. At the project level, that means the repository is no longer in the "design only" stage. It already has a completed first full implementation boundary for local use and for a self-hosted `.pygit` server.

For readers, the main lesson is this: the task list is not busywork. It is the map that keeps a Git reproduction project from collapsing into unstructured command hacking.
