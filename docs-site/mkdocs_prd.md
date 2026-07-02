# MkDocs 文档站 PRD

本文档记录 `python-git-reproduction` 后续文档站建设目标，避免上下文压缩后丢失方向。

## 1. 目标

为项目新增一套面向读者的文档系统，使用 **MkDocs Material** 构建。

现有根目录 `docs/` 保留为项目内部工程文档，包括 PRD、SDD、TASKS 和项目结构规划。新的 `docs-site/` 专门用于生成可发布的网站文档。

## 2. 为什么选择 MkDocs Material

项目当前文档主要是 Markdown，内容类型包括：

- Git 原理教学。
- 如何用 Python 实现 Git 的工程教学。
- SDD 工作流教学。
- PRD、任务清单、项目设计说明展示。

这些内容更适合 MkDocs Material 的导航、搜索、侧边栏和教学型页面组织方式。Sphinx 更适合 API 自动文档，不是当前主要需求。

后续如果需要 Python API reference，可以在 MkDocs 中加入 `mkdocstrings`，不需要迁移到 Sphinx。

## 3. 目录边界

保留：

```text
docs/
```

用途：

- 内部 PRD。
- SDD 工程要求。
- TASKS 开发任务清单。
- 项目结构规划。

新增：

```text
docs-site/
```

用途：

- MkDocs Material 网站源码。
- 对外教程。
- 整理后的项目文档展示。
- 面向读者的 Git/pygit/SDD 教学。

## 4. 文档站信息架构

推荐文档站结构：

```text
docs-site/
├── mkdocs.yml
├── mkdocs_prd.md
└── docs/
    ├── index.md
    ├── getting-started.md
    ├── user-guide/
    │   ├── index.md
    │   ├── local-workflow.md
    │   ├── pygit-server.md
    │   └── commands.md
    ├── git-teaching/
    │   ├── index.md
    │   ├── git-object-model.md
    │   ├── index-and-staging.md
    │   ├── commits-and-dag.md
    │   ├── merge-conflict.md
    │   └── packfile.md
    ├── build-git-teaching/
    │   ├── index.md
    │   ├── architecture.md
    │   ├── object-database.md
    │   ├── index-v2.md
    │   ├── refs.md
    │   ├── merge-engine.md
    │   └── pygit-daemon.md
    ├── sdd-teaching/
    │   ├── index.md
    │   ├── what-is-sdd.md
    │   ├── prd-to-tasks.md
    │   ├── testing-strategy.md
    │   ├── dangerous-commands.md
    │   └── no-mock-policy.md
    ├── project/
    │   ├── index.md
    │   ├── tasks.md
    │   ├── project-tree.md
    │   └── sdd-requirements.md
    └── prd/
        ├── index.md
        ├── 00-overview.md
        ├── 01-repository-layout.md
        ├── 02-object-database.md
        ├── 03-index.md
        ├── 04-plumbing-commands.md
        ├── 05-porcelain-commands.md
        ├── 06-merge.md
        ├── 07-packfile-remote.md
        ├── 08-non-functional.md
        └── 09-roadmap.md
```

## 5. 三条主线

### 5.1 Git 教学

目标读者：想理解 Git 原理的人。

内容重点：

- Git 是内容寻址文件系统。
- blob/tree/commit/tag 四类对象。
- index 暂存区。
- commit DAG。
- 分支、merge 和冲突。
- packfile 和 idx。

### 5.2 怎么做 Git 教学

目标读者：想自己用 Python 复现 Git 的人。

内容重点：

- 项目架构如何拆分。
- 对象库怎么实现。
- Index V2 怎么实现。
- refs 和 HEAD 怎么实现。
- checkout/reset/merge/stash 怎么保证安全。
- pygit daemon 为什么不是官方 Git daemon。
- 如何通过真实测试验证仓库状态。

### 5.3 SDD 教学

目标读者：想学习规格驱动开发的人。

内容重点：

- PRD 如何拆分。
- TASKS 如何从 PRD 生成。
- 为什么危险命令要先设计安全边界。
- 为什么测试必须使用真实临时目录和真实 `.pygit`。
- 为什么不使用 mock 替代核心 Git 行为。
- commit 信息如何写清楚原因、影响和测试。

## 6. MkDocs 配置要求

`docs-site/mkdocs.yml` 应使用 MkDocs Material。

推荐插件：

- `search`

可选插件：

- `mkdocstrings`：后续如果需要 Python API reference 再加。
- `git-revision-date-localized`：后续如果需要页面更新时间再加。

暂时不要引入复杂插件，避免文档站启动成本过高。

## 7. 内容迁移策略

不要直接移动根目录 `docs/`。

迁移方式：

- `docs-site/docs/prd/`：复制并整理 `docs/prd/` 内容。
- `docs-site/docs/project/tasks.md`：整理 `docs/TASKS.md`。
- `docs-site/docs/project/project-tree.md`：整理 `docs/PROJECT_TREE.md`。
- `docs-site/docs/project/sdd-requirements.md`：整理 `docs/SDD_REQUIREMENTS.md`。

站点内容可以比内部文档更偏教学，内部文档可以继续保留更工程化的原始记录。

## 8. 后续任务

- [ ] 创建 `docs-site/mkdocs.yml`。
- [ ] 创建 `docs-site/docs/index.md`。
- [ ] 创建 `docs-site/docs/getting-started.md`。
- [ ] 创建 `git-teaching/` 教学页面。
- [ ] 创建 `build-git-teaching/` 实现教学页面。
- [ ] 创建 `sdd-teaching/` SDD 教学页面。
- [ ] 整理并复制 PRD 到 `docs-site/docs/prd/`。
- [ ] 整理项目文档到 `docs-site/docs/project/`。
- [ ] 本地运行 `mkdocs serve` 验证导航。
- [ ] 后续可接 GitHub Pages，但不是当前必须项。

