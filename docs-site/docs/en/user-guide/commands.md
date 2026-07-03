# Commands

This page summarizes the major implemented command surface.

## Plumbing Commands

The project implements the following low-level commands:

- `hash-object`
- `cat-file`
- `write-tree`
- `read-tree`
- `commit-tree`
- `update-ref`

These commands expose the object database, tree generation, commit creation, and ref updates more directly.

## Porcelain Commands

The project implements the following user-oriented commands:

- `init`
- `add`
- `rm`
- `status`
- `commit`
- `log`
- `branch`
- `checkout`
- `switch`
- `tag`
- `reset`
- `stash`
- `merge`
- `clone`
- `fetch`
- `push`
- `serve`

## Command Boundary

The command set is meant to provide a usable local and self-hosted workflow around `.pygit`. It is not a claim of official Git transport compatibility with GitHub, SSH Git, HTTP Git, or the official wire protocol.
