# SDD Teaching

This track explains how `python-git-reproduction` uses specification-driven development for a systems project that can read, write, rewrite, and sometimes delete real repository state.

For many beginners, SDD sounds abstract until they see it attached to a concrete technical problem. This project is a good example because Git reproduction is not a safe place for casual engineering. A small misunderstanding in object layout, ref updates, path validation, or working-tree rewrite logic can corrupt repository data or damage user files.

That is exactly why this project treats SDD as an operational discipline rather than as a documentation slogan.

## What SDD Means In This Project

Here, SDD means that five things move together:

- specification,
- design,
- implementation,
- tests,
- safety boundaries.

The repository does not consider a feature complete if only the code exists. A feature is only mature when its expected behavior, internal structure, verification strategy, and destructive-risk boundaries are all clear.

## Why SDD Fits This Repository

If you are reproducing Git, you are not building a simple CRUD web app. You are building a stateful system with:

- binary file formats,
- graph history,
- mutable refs,
- multi-step working-tree rewrites,
- merge conflicts,
- object transfer,
- and commands that can destroy local state if mishandled.

That makes "code first, explain later" a weak strategy. By the time you discover a safety gap, the project may already have duplicated the wrong assumption across many modules.

## The Three Main SDD Questions

As you read the pages in this section, keep these questions in mind:

1. How does a large requirement become a set of manageable tasks?
2. How do testing and safety rules shape implementation decisions?
3. Why is it dangerous to simulate core repository behavior with mocks in a project like this?

Those three questions define the teaching goal of this section.

## What You Will Learn In This Track

The pages in this track cover:

- what SDD means in the context of a Git reproduction project,
- how a large PRD is split into smaller maintainable documents,
- how implementation tasks are derived from those documents,
- why dangerous commands require explicit safety boundaries,
- why real tests matter more than mock-heavy tests for repository semantics,
- how project rules such as SOLID, DRY, atomic writes, and comment discipline support maintainability.

## Recommended Reading Order

If you are new to SDD, read this section in this order:

1. `What Is SDD`
2. `PRD to Tasks`
3. `Testing Strategy`
4. `Dangerous Commands`
5. `No Mock Policy`

That order moves from idea, to planning, to verification, to safety, and finally to testing philosophy.

## Relationship To The Rest Of The Site

This track connects the other documentation areas:

- `Git Teaching` explains the domain being reproduced.
- `Build Git Teaching` explains how the repository implements that domain.
- `SDD Teaching` explains how the engineering process keeps that implementation trustworthy.

If you want to study both the system and the method used to build it, this section is the bridge between them.
