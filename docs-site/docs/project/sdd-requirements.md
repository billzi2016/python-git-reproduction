# SDD Requirements

This page explains the engineering rules behind `python-git-reproduction`. In this repository, SDD means that specification, design, development, testing, and safety constraints advance together rather than being treated as separate phases that barely talk to each other.

That matters because this project does not implement harmless demo commands only. It implements repository metadata writes, object storage, branch updates, merge state transitions, pack handling, and destructive working-tree operations such as `reset --hard`, `checkout`, `switch`, and `rm`. In a real repository, weak safety rules would turn small mistakes into data loss.

## Core SDD Principle

Every feature should be understandable from four angles at the same time:

- what the feature is supposed to do,
- how it is designed internally,
- how it is implemented,
- how it is tested and bounded for safety.

If one of those four angles is missing, the feature is incomplete even if it appears to work during a quick manual demo.

## Specification Before Coding

Before implementing a feature, the repository expects the specification to answer several basic questions:

- what are the inputs,
- what are the outputs,
- which `.pygit` files are read,
- which `.pygit` files are written,
- whether the working tree is modified,
- how failures are handled,
- what rollback or atomicity behavior is expected.

This is especially important for Git-like commands because many of them have side effects that extend beyond one file.

## Design Before Sprawl

The repository also expects core modules to have a clear design before code grows:

- data structures should be explicit,
- binary layouts should be explicit,
- path-boundary handling should be explicit,
- lock-file strategy should be explicit,
- exception behavior should be explicit,
- compatibility goals with official Git formats should be explicit.

Without those decisions, code tends to grow by accident rather than by design.

## SOLID And DRY In Practical Terms

The project requires SOLID and DRY, but the point is practical, not ceremonial.

In this repository, SOLID means:

- objects, index, refs, lock handling, working-tree logic, merge behavior, pack handling, and remote behavior should remain separate responsibilities,
- low-level modules should not depend backward on CLI orchestration,
- function interfaces should reflect real Git concepts instead of vague bags of state.

In this repository, DRY means:

- SHA-1 handling should be shared,
- object-header encoding should be shared,
- zlib compression and decompression helpers should be shared,
- path-safety checks should be shared,
- lock-file logic should be shared,
- checksum validation should be shared,
- object integrity verification should be shared.

This is not about elegance for its own sake. Repeated safety logic tends to drift, and drift is dangerous in repository code.

## Testing Requirements

The repository requires substantial automated testing. The point of the tests is not just to increase a coverage number. The point is to demonstrate that repository state remains correct across success paths, failure paths, and rollback-sensitive paths.

The required testing scope includes:

- object tests for blob, tree, commit, and tag encoding and validation,
- index tests for header, entries, padding, flags, stage bits, sorting, and checksum,
- ref tests for `HEAD`, branches, tags, symbolic refs, detached `HEAD`, old-value checks, and lock updates,
- plumbing command tests,
- porcelain command tests,
- merge tests,
- packfile tests,
- remote tests,
- exceptional-path tests for corruption, missing files, permission errors, and interrupted writes.

For any command that changes disk state, the engineering standard is stricter: there should be tests for the success path, the failure path, and the repository state after the failure.

## No-Mock Policy For Core Behavior

One of the strongest rules in the project is that tests should not replace core Git behavior with mocks.

Why is that rule so strong? Because this project is about real repository state:

- real object bytes,
- real compressed files,
- real index files,
- real refs,
- real working-tree files,
- real merge conflicts,
- real pack transfer behavior.

If those parts are mocked away, the tests stop proving the thing the project actually claims to implement.

That does not mean every helper in every unit test must avoid abstraction. It means the core repository behavior should be exercised against real temporary directories and real repository state rather than synthetic stand-ins.

## Dangerous Command Requirements

This project treats dangerous commands as first-class engineering concerns. Dangerous operations include:

- deleting working-tree files,
- `reset --hard`,
- `checkout` and `switch` when they rewrite tracked paths,
- `rm`,
- stash flows that both apply and remove state,
- ref rewrites,
- pack unpacking,
- remote operations that update target repositories.

All dangerous operations must confirm that they operate inside the repository boundary. Path handling must defend against:

- `..` path traversal,
- absolute-path escapes,
- symlink escapes,
- platform-specific separator issues.

The implementation should not rely on naive string-prefix checks. It should rely on normalized and trustworthy path resolution.

## Machine Protection Requirements

The repository assumes it may run on a real personal machine rather than in an isolated throwaway container. That assumption changes the default risk posture.

As a result:

- the code must never implement broad recursive deletion outside tracked repository state,
- it must never clean parent directories of the repository,
- it must not delete untracked files by default in commands that do not explicitly require that behavior,
- dangerous tests must run in temporary directories rather than against the real project checkout.

These are not secondary conveniences. They are direct defenses against accidental data loss.

## Data Consistency Requirements

Metadata writes must be done carefully:

- index, refs, config, and pack-related writes should use lock files or temporary files,
- final writes should use atomic replacement,
- object writes should be validated before the final move,
- interrupted writes must not silently leave corrupted authoritative files behind.

If a write fails, the repository should fail loudly rather than drift into half-written metadata.

## Compatibility Expectations

The project tries to stay as close as possible to official Git's object, index, ref, and pack formats. Where full compatibility is not yet achieved, that limitation should be documented clearly rather than hidden.

This is another reason SDD matters: compatibility claims should be traceable to implementation and tests, not left as vague marketing language.

## Code Comment Requirements

The project also requires comprehensive Chinese comments in Python source files:

- each file should begin with an intent comment,
- functions should describe their role, parameters, return values, side effects, and exceptions,
- complex logic, binary layouts, edge cases, and compatibility-critical rules should be explained in Chinese.

This requirement exists because a Git reproduction project contains a large amount of logic that is easy to misunderstand if left implicit.

## Commit Quality Requirements

The repository's commit policy is also part of the SDD workflow.

- Commits should remain focused on one coherent problem.
- Commit messages should be written in Chinese.
- The message should explain why the change is being made, not only which files changed.
- Changes involving safety boundaries, binary formats, or data consistency should have especially clear commit messages.

Good commits are part of maintainability. In a repository like this, a vague commit is not just annoying. It makes future debugging and auditing harder.
