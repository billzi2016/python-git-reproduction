# PRD to Tasks

One of the most important SDD moves in this repository is turning a large PRD into an explicit implementation task list. Without that step, the project goal stays ambitious but execution becomes blurry.

## Why PRD Alone Is Not Enough

The PRD describes scope, behavior, binary formats, command expectations, safety requirements, and compatibility goals. That is necessary, but it does not yet answer the day-to-day engineering question:

What should be built first, and what depends on what?

For example:

- object storage must exist before commit creation,
- Index V2 must exist before realistic staging behavior,
- ref handling must exist before branch switching,
- path-safety rules must be defined before dangerous commands are trusted.

## How This Project Breaks Work Down

The repository turns the PRD into staged work roughly like this:

1. document engineering constraints,
2. create the project skeleton,
3. initialize repositories,
4. implement the object database,
5. expose plumbing commands,
6. implement Index V2,
7. build the local commit loop,
8. implement refs and branches,
9. implement status and working-tree mutation rules,
10. implement checkout, switch, reset, stash, and merge,
11. implement pack, clone, fetch, push, and the dedicated server,
12. validate the system with real tests.

This structure is not project-management ceremony. It is dependency management for a stateful system.

## Why The Mapping Matters

When tasks are derived clearly from the PRD:

- scope becomes auditable,
- omissions become visible,
- documentation and implementation stay connected,
- safety requirements stop being treated as optional polish.

That is one of the main SDD lessons this project tries to teach.
