# Refs

If the object database answers "what is stored," refs answer "what names point to which objects right now."

## What Refs Do

Refs provide names for repository state:

- branches,
- tags,
- remote-tracking refs,
- `HEAD`.

Without refs, commits would still exist, but most everyday repository workflows would become much harder to navigate.

## Why `HEAD` Is Special

`HEAD` is the current checkout target.

In common branch-attached workflows, it is a symbolic ref such as:

```text
ref: refs/heads/main
```

In detached workflows, it can point directly to a commit ID.

That is why `HEAD` is both part of the ref system and more special than ordinary branch refs.

## Why Ref Updates Need Care

Ref writes are high-value metadata writes. If they are not protected properly, the repository can end up with:

- lost branch movement,
- incorrect old-value assumptions,
- half-written metadata,
- inconsistent branch state.

That is why this project centralizes lock-file and atomic-write behavior for ref updates rather than leaving each command to invent its own approach.
