# Index V2

Index V2 is often the first place where a Git reproduction project meets a genuinely strict binary format.

## Why Index V2 Is Harder Than It Looks

The challenge is not simply storing file paths and object IDs. A realistic Index V2 implementation must deal with:

- a fixed header,
- variable-length entries,
- metadata fields,
- path ordering,
- stage bits,
- 8-byte padding,
- a trailing checksum,
- extension handling.

That means small mistakes can make the index unreadable or subtly wrong.

## Why A Simplified Text File Is Not Enough

A toy implementation might be tempted to replace the index with a simple text mapping of path to SHA-1. That is easier to implement, but it loses too much real Git behavior:

- merge conflict stages,
- realistic staging metadata,
- checksum validation,
- compatibility teaching value,
- accurate status and tree-generation semantics.

If the goal is to reproduce Git rather than merely imitate its command names, Index V2 deserves proper treatment.

## Why The Index Is Central

The index sits between the working tree and committed history. Commands such as `add`, `status`, `write-tree`, `read-tree`, and merge conflict handling all depend on it.

That makes Index V2 one of the repository's central state structures rather than just an implementation detail.
