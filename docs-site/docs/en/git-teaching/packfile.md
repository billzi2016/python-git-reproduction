# Packfile

Loose objects are easy to understand, but they are not the most efficient long-term storage and transfer format for a large repository.

That is where packfiles enter the picture.

## Why Packfiles Exist

Packfiles improve:

- storage compactness,
- filesystem efficiency,
- transfer efficiency,
- reuse through delta-style compression.

Instead of leaving every object as a separate loose file, Git can bundle many objects into a `.pack` file and describe them with an accompanying `.idx` file.

## What A `.pack` File Does

A pack file stores many objects in a compact binary stream. It usually contains:

- a header,
- an object count,
- encoded object entries,
- optionally delta-based object entries,
- final integrity-related data.

This makes large repositories and remote transfer workflows far more efficient than pure loose-object storage.

## What A `.idx` File Does

The `.idx` file exists so the system can locate objects inside the pack without scanning the whole pack sequentially every time.

Conceptually, it provides:

- sorted object IDs,
- fan-out table data,
- offsets into the pack,
- faster object lookup.

You can think of `.pack` as the storage container and `.idx` as the search structure.

## Why Delta Objects Matter

Many repository objects are highly similar to earlier objects. Delta encoding allows the pack to represent a target object in terms of how it differs from a base object.

That reduces both storage and transfer cost.

## Why Packfiles Matter For Remote Workflows

Once you move from a single repository to `clone`, `fetch`, and `push`, packfiles become central. Remote synchronization is fundamentally about transferring missing objects efficiently and then updating refs safely.
