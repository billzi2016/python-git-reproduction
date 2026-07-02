# python-git-reproduction 文档入口

本项目目标是使用纯 Python 3 复现 Git 的核心底层逻辑、上层命令工作流、对象存储格式、索引格式、引用系统、合并机制、打包文件以及远端同步能力。项目生成的版本控制目录命名为 `.pygit`。

## 推荐阅读顺序

1. `README.md`：本文档，作为 `docs/` 下所有文档的总入口。
2. `SDD_REQUIREMENTS.md`：SDD 工程要求、测试要求、危险指令安全要求、SOLID/DRY 和提交质量要求。
3. `TASKS.md`：开发任务清单与完成状态，已完成任务使用 `[x]` 标记。
4. `PROJECT_TREE.md`：推荐代码目录结构与模块职责。
5. `prd/00-overview.md`：项目目标、范围和兼容性原则。
6. `prd/01-repository-layout.md`：`.pygit` 仓库目录结构。
7. `prd/02-object-database.md`：Git 四类核心对象与对象库。
8. `prd/03-index.md`：Git Index V2 二进制暂存区。
9. `prd/04-plumbing-commands.md`：底层管道命令。
10. `prd/05-porcelain-commands.md`：上层用户命令。
11. `prd/06-merge.md`：分支合并与冲突处理。
12. `prd/07-packfile-remote.md`：Packfile、fetch、push、clone。
13. `prd/08-non-functional.md`：性能、锁、校验、异常处理和 unittest 要求。
14. `prd/09-roadmap.md`：分阶段实现路线。

## 全部文档索引

```text
docs/
├── README.md
├── PROJECT_TREE.md
├── SDD_REQUIREMENTS.md
├── TASKS.md
└── prd/
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

## 文件说明

`PROJECT_TREE.md` 说明推荐源码目录、模块职责、测试目录和 Python 中文注释规范。

`SDD_REQUIREMENTS.md` 说明规格、设计、开发、测试同步推进的工程要求，并强调危险命令必须保护用户电脑。

`TASKS.md` 跟踪当前实现进度。当前任务清单已经全部完成，没有未勾选任务项。

`prd/` 目录保存拆分后的产品需求文档。每个文件只负责一个主题，避免单个巨型 PRD 难以维护。

## 当前实现边界

当前项目已经实现本地 `.pygit` 使用、本地路径远端同步和自建 `.pygit` 专用 TCP 服务器。

已完成能力包括：

- 本地提交闭环：`init`、`add`、`commit`、`log`、`status`。
- 管道命令：`hash-object`、`cat-file`、`write-tree`、`read-tree`、`commit-tree`、`update-ref`。
- 本地工作流：`rm`、`branch`、`checkout`、`switch`、`tag`、`reset`、`stash`、`merge`。
- 对象数据库：loose object、tree、commit、tag、pack v2、idx v2、ref-delta 读取。
- 远端同步：本地路径 `clone/fetch/push`，以及 `pygit://host:port` 专用服务器 `clone/fetch/push`。
- 安全边界：非快进 push 拒绝、危险工作区操作路径检查、未追踪文件保护。
- 测试：62 个 `unittest` 用例，全部使用真实临时目录、真实 `.pygit`、真实对象库、真实 index 和真实工作区文件。

明确不实现：

- GitHub、SSH Git、HTTP Git 和官方 Git wire protocol。
- Git LFS。
- 官方 `git daemon`。本项目实现的是 `.pygit` 专用服务端，即 pygit daemon。

## 验证状态

当前收工验证命令：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

当前结果：

```text
Ran 62 tests

OK
```

项目要求测试不得使用模拟对象替代核心 Git 行为。当前全仓库没有 `mock`、`Mock`、`unittest.mock`、`MagicMock` 或 `patch(` 用法。

## 全局实现原则

- 必须以“复现 Git 全部核心能力”为最终目标，而不是实现一个简化版玩具系统。
- 必须尽量兼容官方 Git 的对象格式、索引格式、引用格式和 packfile 格式。
- 必须严格使用 Python 标准库，不引入第三方依赖。
- 必须优先保证数据正确性、二进制格式兼容性和异常情况下的仓库一致性。
- 项目设计必须遵循 SOLID 和 DRY 原则：模块职责清晰，重复逻辑集中复用，危险操作和兼容性关键逻辑不能散落复制。
- 抽象必须服务于 Git 语义和可测试性，不能为了形式上的设计模式牺牲二进制格式的清晰度。
- Python 源码必须使用全面中文注释：文件开头写意图注释，函数写功能注释，复杂逻辑、长难句、二进制布局、边界条件和关键算法必须写清楚中文解释。
