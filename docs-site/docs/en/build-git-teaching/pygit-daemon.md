# Pygit Daemon

This project implements a dedicated `.pygit` TCP server for the custom `pygit://host:port` remote scheme.

## Why A Dedicated Server Exists

The project aims to cover real distributed repository behavior for local use and self-hosted experiments, but it does not claim full compatibility with the official Git transport ecosystem.

That leads to a deliberate middle ground:

- support local-path remotes,
- support a dedicated project-specific server,
- avoid over-claiming official GitHub, SSH, HTTP, or wire-protocol compatibility.

## What The Server Teaches

Even though the protocol is project-specific, it still teaches several important distributed concepts:

- remote discovery,
- object transfer,
- ref update behavior,
- non-fast-forward protection,
- the role of pack-style transport in repository synchronization.

## Why This Boundary Is Honest

Saying "this is a dedicated pygit server" is technically cleaner than pretending the project already reproduces the entire official Git transport stack. The server extends the project into real remote workflows without turning the documentation into an inaccurate compatibility claim.
