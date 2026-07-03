# Git Object Model

If you remember only one core idea about Git, make it this one:

Git is fundamentally a content-addressed object database.

That statement is more precise than saying Git is "just a version-control tool." The version-control behavior comes from how Git stores and names objects.

## Content-Addressed Storage

In Git, an object's identity is derived from its content rather than from a filename, a path, or a database row number.

Before an object is written, Git conceptually turns it into bytes shaped like this:

```text
[type] [size]\x00[content]
```

It then computes a SHA-1 digest over that full byte sequence. The digest becomes the object ID.

This has several consequences:

- equal content produces the same object ID,
- changed content produces a different object ID,
- identical file content can be stored once and referenced from multiple paths.

That is the root of Git's deduplication and snapshot behavior.

## The Four Core Object Types

Git's most important object types are:

- `blob`
- `tree`
- `commit`
- `tag`

### Blob

A blob stores raw file content. It does not store the filename or directory position of the file.

That means the same file content can be referenced from different paths without duplicating the blob itself.

### Tree

A tree describes one directory snapshot layer. Its entries map names and modes to object IDs.

- file entries usually point to blobs,
- directory entries point to other trees.

Taken together, trees describe the shape of a full repository snapshot.

### Commit

A commit records:

- the root tree,
- zero or more parent commits,
- author and committer metadata,
- timestamps,
- a message.

The commit does not directly store a branch name. Branches are refs that point to commits.

### Tag

Tags can exist as:

- lightweight refs,
- annotated tag objects.

Annotated tags carry additional metadata and then point to their target object.

## Why The Model Matters

Once you understand the object model, many Git workflows stop looking magical:

- `add` writes blobs and updates the index,
- `commit` turns staged state into trees and commits,
- branches are movable refs,
- merges compare commits and trees,
- remote transfer moves objects plus refs rather than copying a working tree.

That is why the object model is the right place to start when learning Git internals.
