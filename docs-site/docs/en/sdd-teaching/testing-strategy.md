# Testing Strategy

This project's testing strategy is designed to prove repository behavior, not just function behavior.

## Why The Strategy Is Different

Many projects can get useful value from heavily mocked tests because their most important behavior lives in pure logic or API wiring. A Git reproduction project is different. It claims to implement:

- real object bytes,
- real compressed loose objects,
- a real binary index,
- real refs,
- real working-tree rewrites,
- real merge conflicts,
- real packfile behavior,
- real repository-to-repository synchronization.

That means the tests must exercise real repository state wherever core behavior is involved.

## What The Tests Need To Cover

The repository's engineering requirements expect meaningful coverage across:

- object database behavior,
- Index V2 behavior,
- refs and `HEAD`,
- plumbing commands,
- porcelain commands,
- merge behavior,
- pack and idx behavior,
- remote synchronization,
- failure and rollback-sensitive paths.

For destructive or stateful commands, success-path tests alone are not enough. The system also needs tests for:

- failure paths,
- partial-progress risk,
- repository consistency after failure.

## Why Temporary Real Repositories Matter

Using real temporary directories, real `.pygit` repositories, real index files, and real working-tree files exposes classes of bugs that mocks easily hide:

- padding mistakes,
- checksum mistakes,
- path-boundary mistakes,
- wrong ref updates,
- merge-stage handling gaps,
- pack offset and delta issues.

This is why the repository treats real filesystem tests as a core part of its SDD discipline rather than as expensive extras.
