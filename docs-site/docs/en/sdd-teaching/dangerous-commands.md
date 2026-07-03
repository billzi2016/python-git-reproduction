# Dangerous Commands

This repository treats dangerous commands as first-class engineering concerns.

## What Counts As Dangerous

A command is dangerous if it can:

- delete files,
- overwrite the working tree,
- rewrite refs,
- unpack large sets of objects,
- move repository state in ways that are hard to reverse.

In this project, that includes commands and workflows such as:

- `rm`,
- `checkout`,
- `switch`,
- `reset --hard`,
- `stash pop`,
- `update-ref`,
- pack unpacking,
- clone/fetch/push target-state updates.

## Why These Commands Need Extra Rules

The cost of mistakes here is high. A broken status command is annoying. A broken hard reset or unsafe path deletion can destroy user data.

That is why the project requires:

- repository-boundary checks,
- protection against `..` traversal and absolute-path escapes,
- protection against symlink escape patterns,
- tracked-file awareness before deletion,
- validation of target objects before working-tree rewrite,
- atomic metadata writes for refs, index, and similar files.

## The SDD Lesson

Dangerous commands are where requirements and engineering discipline become concrete. If safety rules are not explicit early, the same bad assumption gets duplicated across multiple commands. That is much harder to fix later.
