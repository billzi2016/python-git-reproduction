# Pygit Server

The project implements a dedicated `.pygit` server.

It is not official `git daemon`, and it does not implement GitHub, SSH Git, HTTP Git, `git-upload-pack`, `git-receive-pack`, or the official Git wire protocol.

## Start The Server

Run the server against a repository path:

```bash
python3 -m pygit.cli serve --host 127.0.0.1 --port 9419 /path/to/repo
```

This starts the dedicated `.pygit` TCP server for that repository.

## Clone From The Server

Use the custom remote URL scheme:

```bash
python3 -m pygit.cli clone pygit://127.0.0.1:9419 /path/to/clone
```

The remote protocol is project-specific and intentionally smaller than the full official Git protocol family.

## Fetch And Push

Once cloned, normal project remote workflows are available:

```bash
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

## Non-Fast-Forward Protection

The project rejects non-fast-forward push where appropriate. That keeps the dedicated server aligned with the same core repository safety expectations enforced in local workflows.
