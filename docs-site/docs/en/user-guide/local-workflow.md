# Local Workflow

This page describes the core local `.pygit` workflow that the project already supports.

## Repository Initialization

Create a repository:

```bash
python3 -m pygit.cli init
```

This creates the `.pygit` directory and the basic repository layout needed for all later commands.

## Stage And Commit

Create a file, stage it, and commit it:

```bash
echo "hello" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "initial commit"
```

This flow writes a blob, updates the index, generates a tree, creates a commit, and updates the current branch.

## Inspect State

Check the current repository state:

```bash
python3 -m pygit.cli status
python3 -m pygit.cli log --oneline
```

`status` compares `HEAD`, the index, and the working tree. `log` traverses history from the current `HEAD`.

## Branch And Switch

Create and switch to a branch:

```bash
python3 -m pygit.cli branch dev
python3 -m pygit.cli switch dev
```

Or create and switch in one step:

```bash
python3 -m pygit.cli switch -c dev
```

## Merge

After making a commit on another branch, merge it back:

```bash
python3 -m pygit.cli switch main
python3 -m pygit.cli merge dev
```

The project supports fast-forward merges, three-way merges, conflict markers, and conflict stages in the index.

## Safety Expectations

Commands that rewrite the working tree, such as `checkout`, `switch`, and `reset --hard`, are expected to apply repository-boundary protections. Even so, destructive flows should still be practiced first in test repositories rather than in irreplaceable working directories.
