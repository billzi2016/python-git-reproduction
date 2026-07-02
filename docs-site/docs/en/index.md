# python-git-reproduction

`python-git-reproduction` is a pure Python 3 project that reproduces Git as a real version-control system rather than as a small teaching toy. The repository created by this project is named `.pygit`, and the project aims to reproduce Git's object model, index format, references, commit graph, merge behavior, packfile handling, and remote synchronization workflow with the Python standard library only.

This documentation site is written for readers who want more than a command list. It is meant to help three kinds of readers at the same time:

- readers who want to understand how Git works internally,
- readers who want to build a Git-like system in Python,
- readers who want to learn a specification-driven engineering workflow from a nontrivial systems project.

The repository still keeps its internal engineering source documents under the root `docs/` directory. This `docs-site/` directory is the public-facing documentation site built with MkDocs Material, and it is organized for learning rather than for internal tracking.

## What This Project Is

This project is an attempt to rebuild Git's core behavior in pure Python without third-party runtime dependencies. That means the implementation is expected to deal with real object bytes, real SHA-1 object IDs, real zlib-compressed loose objects, a real binary Index V2 file, real branch references, real merge conflicts, real pack and idx files, and real repository state transitions.

That design choice matters because many "build your own Git" exercises stop early. They often implement only `init`, `add`, and `commit`, or they skip binary compatibility constraints, skip index details, skip merge conflict stages, or avoid remote synchronization entirely. This repository takes the harder path: it treats Git's low-level storage and workflow rules as the main subject rather than as background details.

## Who This Documentation Is For

You should be able to use this site if you fall into any of these groups:

- You use Git every day but have never studied why `add`, `commit`, `checkout`, `merge`, and `push` work.
- You want to understand Git as a content-addressed filesystem plus a commit graph.
- You want to build a Git-like system in Python and need a concrete project structure instead of isolated code snippets.
- You want to study SDD, meaning a workflow where specification, design, development, testing, and safety constraints move forward together.

This site is intentionally written with beginners in mind. It does not assume that you already know packfile layout, index padding rules, three-way merge semantics, or the difference between a symbolic `HEAD` and a detached `HEAD`.

## How To Read This Site

The site is organized into three learning tracks plus two project-reference tracks.

### Git Teaching

This track explains Git itself. It starts from the object model and staging area, then moves to commits, DAG history, merges, conflicts, and packfiles. If your main goal is to understand Git as a tool, start there.

### Build Git Teaching

This track explains how this repository turns Git concepts into Python modules, data structures, validation rules, and safety checks. If your goal is to implement Git-like behavior yourself, start there after reading the basic Git Teaching pages.

### SDD Teaching

This track explains how a complex systems project can be driven by requirements, design constraints, tests, and explicit safety boundaries. If your goal is to learn a disciplined engineering workflow, this is the track to follow.

### Project

This section explains the actual repository, task breakdown, project structure, and SDD requirements used in this codebase.

### PRD

This section contains the split product requirement documents in web-friendly form. These pages are more formal and more specification-oriented than the teaching pages.

## Current Scope

At the current stage, the project already supports the main local repository workflow, object storage, branching, checkout, merge, reset, stash, packfile basics, local-path remotes, and a dedicated `pygit://host:port` server.

Implemented areas include:

- local `.pygit` repository initialization,
- loose object storage,
- blob, tree, commit, and tag objects,
- Git Index V2 reading and writing,
- references for `HEAD`, branches, tags, and remote-tracking refs,
- plumbing commands such as `hash-object`, `cat-file`, `write-tree`, `read-tree`, `commit-tree`, and `update-ref`,
- porcelain commands such as `add`, `status`, `commit`, `log`, `branch`, `checkout`, `switch`, `tag`, `reset`, `stash`, and `merge`,
- pack v2 and idx v2 basics,
- local-path `clone`, `fetch`, and `push`,
- a dedicated `.pygit` TCP server for `pygit://host:port` remotes.

## Explicit Non-Goals

This project is ambitious about Git's core model, but it is not trying to become a drop-in replacement for every Git ecosystem feature.

Not implemented:

- GitHub-specific integration,
- SSH Git transport,
- HTTP Git transport,
- the official Git wire protocol,
- Git LFS.

Those exclusions are important because they define the teaching boundary. The project focuses on Git's storage, state transitions, merge logic, and repository semantics first. It does not claim to reproduce every production deployment surface of official Git hosting.

## Why The Boundary Matters

For a newcomer, it is easy to confuse "complete core Git reproduction" with "complete Git ecosystem reproduction." They are not the same thing.

This repository aims to reproduce the complete core repository behavior needed for local usage and for a self-hosted `.pygit` server. That includes objects, index, refs, commits, merge states, pack transport, remote synchronization logic, and safety checks around destructive operations. It does not include every network protocol or hosting feature that has grown around Git over time.

That boundary is deliberate. It keeps the project technically serious while still keeping the implementation teachable.

## Where To Start

If you are new to the project, use this order:

1. Read [Getting Started](getting-started.md) to understand what runs today and how to try it safely.
2. Read the `Git Teaching` overview pages if you want Git concepts first.
3. Read the `Build Git Teaching` overview pages if you want implementation structure next.
4. Read the `SDD Teaching` pages if you want to understand how the project was organized and verified.
5. Use the `Project` and `PRD` sections as reference material when you want the formal engineering view.
