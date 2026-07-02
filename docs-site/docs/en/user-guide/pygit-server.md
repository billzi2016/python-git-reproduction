# Pygit Server

The project implements a dedicated `.pygit` server.

It is not official `git daemon`, and it does not implement GitHub, SSH Git, HTTP Git, `git-upload-pack`, `git-receive-pack`, or the official Git wire protocol.

Planned content:

- Start server with `pygit serve`.
- Clone from `pygit://host:port`.
- Fetch and push.
- Non-fast-forward rejection.

