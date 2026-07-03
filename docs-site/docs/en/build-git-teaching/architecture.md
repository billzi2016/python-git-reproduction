# Architecture

If you want to build a Git-like system that remains understandable as it grows, architecture matters early.

## Why This Project Needs Clear Module Boundaries

This repository touches:

- binary object formats,
- a binary index,
- refs and `HEAD`,
- working-tree rewrites,
- merge behavior,
- pack and idx parsing,
- remote synchronization,
- destructive filesystem operations.

If those concerns are mixed together inside a few command handlers, the result becomes difficult to audit and difficult to test.

## The Core Architectural Split

The project separates:

- repository discovery and path context,
- object encoding and decoding,
- Index V2 handling,
- ref handling,
- lock-file and atomic-write behavior,
- working-tree mutation,
- diff computation,
- merge behavior,
- pack handling,
- remote synchronization,
- command orchestration.

This makes the system easier to reason about because low-level binary behavior is not entangled with user-facing command parsing.

## Why This Supports SOLID And DRY

The project's engineering requirements call for SOLID and DRY in practical terms:

- shared safety logic should stay centralized,
- binary-format logic should not be duplicated across commands,
- command orchestration should reuse lower-level verified modules,
- dangerous operations should not each invent their own path-protection logic.

That architecture is not an aesthetic preference. It is one of the main ways the repository stays maintainable.
