# Merge Engine

The merge engine is one of the hardest parts of a Git reproduction project because it combines graph logic, file-difference logic, working-tree behavior, and conflict-state handling.

## Why It Is Not Just A Text Merge

Before file content can even be compared, the merge engine needs to determine:

- the current commit,
- the target commit,
- their lowest common ancestor.

That is a commit-graph problem, not a line-by-line text problem.

## Fast-Forward Versus Three-Way Merge

A correct merge engine must first decide whether the merge is a fast-forward case. If so, it can often move the current ref without creating a merge commit.

If not, it must perform a three-way merge using:

- base,
- ours,
- theirs.

That requires both historical reasoning and content reasoning.

## Conflict Handling Is A Full Repository State

When conflicts occur, the merge engine needs to do more than inject conflict markers into a file. It should also keep conflict state in repository metadata, such as index stages for base, ours, and theirs.

That is why merge handling deserves a dedicated module and a dedicated test strategy.
