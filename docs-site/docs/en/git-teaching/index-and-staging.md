# Index and Staging

Many beginners misunderstand `git add` because they think it "commits a file." It does not. It stages a repository state change.

## Why The Index Exists

Without a staging area, Git would only compare the current working tree directly against the last commit. That would remove an important capability:

the ability to choose exactly which current changes belong in the next commit.

The index gives Git a third state layer:

- `HEAD`: the last committed snapshot,
- `index`: the next candidate snapshot,
- working tree: the files you are editing right now.

That separation allows Git to express:

- modified but unstaged,
- staged but uncommitted,
- committed,
- conflicted.

## The Index Is A Real Binary Structure

The index is not just a conceptual to-do list. In this project, it is treated as a real Index V2 binary file.

It stores data such as:

- timestamps,
- device and inode metadata,
- mode,
- uid and gid,
- file size,
- the staged blob object ID,
- flags and stage bits,
- path names,
- a trailing checksum.

That is why the index is better understood as a binary staging-state machine than as a simple list.

## What `add` Really Does

When you run `add`, Git-like behavior typically involves:

1. reading the file from the working tree,
2. encoding it as a blob,
3. computing the blob object ID,
4. writing the blob into the object database,
5. updating or inserting the path entry in the index.

The commit has not happened yet. The candidate next snapshot has merely been updated.

## Why `status` Needs Three Comparisons

Once the index exists, status becomes a three-way comparison problem:

1. `HEAD` vs `index`
2. `index` vs working tree
3. working tree paths not represented in the index

That is why Git can distinguish staged changes, unstaged changes, and untracked files so precisely.

## Why Conflicts Also Touch The Index

During merge conflicts, the index can carry multiple stages for the same path:

- Stage 1: base
- Stage 2: ours
- Stage 3: theirs

This means conflicts are not only visible in working-tree marker text. They also exist in repository metadata.

Understanding the index is one of the most important steps in moving from "Git commands I memorized" to "Git state transitions I actually understand."
