# Commits and DAG

Git history is better understood as a directed acyclic graph, or DAG, than as a simple list of commits.

## What A Commit Stores

A commit typically stores:

- the root tree object ID,
- one or more parent commit IDs,
- author and committer metadata,
- timestamps,
- a message.

Importantly, the branch name is not stored inside the commit. Branches are refs that point to commits.

## Why History Is A Graph

If every commit had only one parent and no merges ever happened, history would look like a chain.

But Git allows:

- branching from earlier history,
- parallel development,
- merge commits with multiple parents.

As soon as multi-parent commits appear, history stops being a simple line and becomes a graph.

## What DAG Means

DAG stands for Directed Acyclic Graph.

- **Directed** means commit relationships have a direction: newer commits point to parents.
- **Acyclic** means the graph does not loop back into itself.

Those properties make it possible to reason about:

- ancestry,
- lowest common ancestors,
- fast-forward possibilities,
- merge bases,
- history traversal.

## Why Branches Are Lightweight

Once you see history as a commit graph, branch behavior becomes easier to explain.

A branch is just a movable ref pointing at a commit. Creating a branch does not duplicate the repository snapshot; it creates another name in the graph.

That is one reason Git branching is so lightweight compared with many centralized version-control systems.

## Why DAG Knowledge Matters

Commands such as `log`, `merge`, `branch`, `checkout`, and `reset` all make more sense when you think in terms of commit graph movement rather than in terms of a flat sequence of saved folders.
