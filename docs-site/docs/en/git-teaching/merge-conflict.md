# Merge Conflict

Merging is not just "putting two files together." It is a combination of graph reasoning and content reasoning.

## The First Merge Question Is Graph-Based

Before comparing file content, a merge algorithm needs to identify:

- `ours`,
- `theirs`,
- the lowest common ancestor, or base.

That base commit is what makes a three-way merge possible.

## Fast-Forward Is The Easy Case

If the current branch has no work beyond the merge base and only trails the target branch, the merge can often be resolved by moving the current ref forward.

That is a fast-forward merge. No merge commit is needed because the graph already has a direct path.

## Three-Way Merge

When a fast-forward is not possible, the system compares:

- base -> ours
- base -> theirs

From there, it can identify:

- changes only one side made,
- compatible changes both sides made,
- incompatible overlapping changes.

The last case becomes a conflict.

## Why Conflicts Happen

Conflicts appear when the system cannot safely decide which overlapping change should win automatically.

That is not a sign that the merge engine is broken. It is a sign that human intent cannot be recovered reliably from the available data.

## Conflict Markers And Index Stages

In working-tree files, conflicts are often shown through markers such as:

```text
<<<<<<< HEAD
ours
=======
theirs
>>>>>>> target
```

But the conflict is not only text in the file. The index can also record staged conflict state:

- Stage 1: base
- Stage 2: ours
- Stage 3: theirs

That is why merge conflict handling is both a working-tree problem and a repository-metadata problem.
