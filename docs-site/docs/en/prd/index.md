# PRD

This section presents the product requirement documents for `python-git-reproduction` in a web-friendly structure. The original requirement set was intentionally split into multiple files because a single giant PRD quickly becomes hard to review, hard to update, and hard to connect to implementation work.

## Why The PRD Was Split

The project started from a large requirement set describing a pure-Python reproduction of Git. That requirement set covered:

- repository layout,
- object formats,
- Index V2 rules,
- plumbing commands,
- porcelain commands,
- merge behavior,
- packfile and remote behavior,
- non-functional constraints,
- and staged implementation expectations.

That is too much material for one giant document if the goal is long-term maintenance. When a PRD becomes too large, several things go wrong:

- readers stop navigating it carefully,
- updates become risky because one file holds too many unrelated concerns,
- implementation tasks become harder to trace back to specific requirements,
- and teaching value drops because the document becomes a wall of text rather than a map.

Splitting the PRD solves those problems.

## How To Use This Section

This section is best read as a formal reference layer rather than as the first introduction to the project.

If you are completely new, start with:

- `Home`,
- `Getting Started`,
- `Git Teaching`,
- `Build Git Teaching`,
- and `Project`.

Then come back to the PRD when you want to answer formal questions such as:

- what exact repository layout is required,
- what exact object format is expected,
- what exact Index V2 behavior is expected,
- what commands are required,
- what non-functional constraints the implementation must respect.

## PRD File Structure

The split PRD is organized by topic:

- `00-overview`: project goals, scope, and compatibility principles,
- `01-repository-layout`: the `.pygit` directory structure,
- `02-object-database`: blob, tree, commit, and tag objects,
- `03-index`: Git Index V2 staging requirements,
- `04-plumbing-commands`: low-level command requirements,
- `05-porcelain-commands`: high-level workflow command requirements,
- `06-merge`: merge behavior and conflict handling,
- `07-packfile-remote`: pack, fetch, push, clone, and remote communication scope,
- `08-non-functional`: performance, locking, validation, and testing requirements,
- `09-roadmap`: staged implementation direction.

Each file focuses on one subject so that changes remain local and readers can study one system area at a time.

## Relationship To SDD

In this repository, the PRD is not decorative documentation. It is part of the SDD workflow.

The intended flow is:

1. define requirements in the PRD,
2. derive task breakdowns from those requirements,
3. design repository modules that can satisfy those requirements,
4. implement the code,
5. verify the behavior with tests and safety checks,
6. update the documentation when scope or boundaries change.

That relationship is important because it keeps the project grounded. The PRD describes what the system is supposed to become, while the task list and tests show how much of that target has actually been achieved.

## What The PRD Does Not Mean

A PRD is not proof that the implementation already exists. It is a contract about intent and expected behavior.

For that reason, readers should always interpret the PRD together with:

- the project status pages,
- the task list,
- the SDD requirements,
- and the verification state.

This prevents a common mistake: reading an ambitious requirement document and assuming the implementation must already support every declared feature.

## Recommended Reading Order Within PRD

If you want a disciplined reading order, use this:

1. `00-overview`
2. `01-repository-layout`
3. `02-object-database`
4. `03-index`
5. `04-plumbing-commands`
6. `05-porcelain-commands`
7. `06-merge`
8. `07-packfile-remote`
9. `08-non-functional`
10. `09-roadmap`

That order starts from system identity, then moves through storage, workflow, merging, remote behavior, and operational constraints.
