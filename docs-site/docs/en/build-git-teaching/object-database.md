# Object Database

The object database is the foundation of the entire repository. If object encoding and validation are unreliable, every higher-level command becomes unreliable with it.

## What The Object Layer Must Do

At minimum, a Git-like object database must:

- encode objects using the expected header format,
- compute object IDs,
- write objects to object paths,
- compress loose objects,
- read and validate loose objects,
- reject corrupted data,
- support packed-object lookup where applicable.

That is not optional infrastructure. It is the trust boundary for repository storage.

## Why Loose Objects Come First

Loose objects are an ideal first implementation target because they are:

- conceptually simple,
- easy to inspect,
- easy to compare with official Git behavior,
- sufficient for the first local workflow stages.

Once loose objects work correctly, trees, commits, and tags can be built on top of them.

## Why Pack Fallback Matters

A serious repository implementation cannot remain loose-object-only forever. Once pack and idx files exist, object reads need to support:

- checking loose objects first,
- falling back to packed objects,
- using idx data for lookup,
- resolving deltas where required.

That is part of the transition from a local storage exercise to a distributed repository system.
