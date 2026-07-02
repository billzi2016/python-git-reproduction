# python-git-reproduction 文档入口

本项目目标是使用纯 Python 3 复现 Git 的核心底层逻辑、上层命令工作流、对象存储格式、索引格式、引用系统、合并机制、打包文件以及远端同步能力。项目生成的版本控制目录命名为 `.pygit`。

## 文档阅读顺序

1. `prd/00-overview.md`：项目目标、范围和兼容性原则。
2. `prd/01-repository-layout.md`：`.pygit` 仓库目录结构。
3. `prd/02-object-database.md`：Git 四类核心对象与对象库。
4. `prd/03-index.md`：Git Index V2 二进制暂存区。
5. `prd/04-plumbing-commands.md`：底层管道命令。
6. `prd/05-porcelain-commands.md`：上层用户命令。
7. `prd/06-merge.md`：分支合并与冲突处理。
8. `prd/07-packfile-remote.md`：Packfile、fetch、push、clone。
9. `prd/08-non-functional.md`：性能、锁、校验、异常处理。
10. `prd/09-roadmap.md`：分阶段实现路线。
11. `PROJECT_TREE.md`：推荐代码目录结构与模块职责。

## 全局实现原则

- 必须以“复现 Git 全部核心能力”为最终目标，而不是实现一个简化版玩具系统。
- 必须尽量兼容官方 Git 的对象格式、索引格式、引用格式和 packfile 格式。
- 必须严格使用 Python 标准库，不引入第三方依赖。
- 必须优先保证数据正确性、二进制格式兼容性和异常情况下的仓库一致性。
- Python 源码必须使用全面中文注释：文件开头写意图注释，函数写功能注释，复杂逻辑、长难句、二进制布局、边界条件和关键算法必须写清楚中文解释。

