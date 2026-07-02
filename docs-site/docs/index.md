# python-git-reproduction

`python-git-reproduction` is a pure Python reproduction of Git core storage, workflows, packfiles, and a dedicated `.pygit` server.

This documentation site is organized around three learning tracks:

- **Git Teaching**: learn Git internals.
- **Build Git Teaching**: learn how this project implements Git-like behavior in Python.
- **SDD Teaching**: learn how the project uses specification-driven development.

The internal engineering documents remain in the repository root `docs/` directory. This `docs-site/` directory is the public-facing MkDocs site.

## Current Scope

Implemented:

- Local `.pygit` workflows.
- Object database, Index V2, refs, commits, tags, reset, stash, merge.
- Packfile and idx v2 basics.
- Local-path remotes.
- A dedicated `pygit://host:port` server.

Not implemented:

- GitHub, SSH Git, HTTP Git, or official Git wire protocol.
- Git LFS.

