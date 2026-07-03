# No Mock Policy

Core Git behavior must be tested with real temporary directories, real `.pygit` repositories, real object databases, real indexes, and real working tree files.

## Why This Rule Exists

This project is about real repository semantics. The most important question is not whether a function was called, but whether the repository state on disk behaves correctly.

If the tests replace core repository behavior with mocks, they stop proving the main claim of the project.

## What Should Stay Real

For core Git behavior, the tests should prefer:

- real temporary repositories,
- real object writes and reads,
- real index files,
- real refs,
- real working-tree files,
- real merge and remote state transitions.

That does not mean every helper must be handwritten or that no abstraction is allowed. It means the repository's core state machine should not be simulated away.

## What This Protects Against

A no-mock policy for core behavior helps expose bugs such as:

- incorrect object encoding,
- invalid checksums,
- unsafe path handling,
- broken conflict stages,
- incorrect packed-object lookup,
- non-atomic repository writes.

Those are exactly the kinds of bugs a Git reproduction project must not quietly miss.
