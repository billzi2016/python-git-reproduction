# python-git-reproduction

`python-git-reproduction` 是一个使用纯 Python 3 复现 Git 的项目。它不是一个只演示 `init`、`add`、`commit` 的简化玩具，而是尽量把 Git 真正重要的核心能力做出来：对象数据库、Index V2、引用系统、提交图、分支切换、合并冲突、packfile、远端同步，以及一个自建的 `.pygit` 专用服务端。

这个文档站默认优先展示英文内容。你现在看到的是中文入口页，目的是让中文读者也能顺着同样的知识结构阅读，但英文仍然是默认首页和默认主导航。

## 这个文档站是给谁看的

这套文档同时服务三类读者：

- 想理解 Git 原理的人；
- 想自己用 Python 复现 Git 的人；
- 想学习如何用 SDD 方法做一个复杂系统项目的人。

如果你平时只是会用 Git，但不清楚 `add` 到底做了什么、`commit` 为什么只是指向一个 tree、`branch` 为什么本质上只是一个 ref、`merge` 为什么会产生冲突，那么这套文档就是给你准备的。

## 这不是一个“壳子项目”

这个项目的重点不是“套一个 Git 命令名字然后内部偷懒”，而是尽可能让 `.pygit` 真的具备 Git 的核心语义：

- 对象是内容寻址的；
- tree 记录目录快照；
- commit 形成 DAG 历史；
- index 是二进制暂存区，不是内存里的列表；
- refs 是移动指针，不是魔法对象；
- merge 既是图问题，也是文件内容问题；
- 远端同步依赖 pack、idx、对象发现和引用更新。

## 站点阅读方式

这个站点分成几条主线：

### Git Teaching

讲 Git 本身。适合先理解 Git 是什么、Git 为什么这样设计、对象模型和暂存区是怎么工作的读者。

### Build Git Teaching

讲“怎么用 Python 把 Git 做出来”。适合已经理解 Git 基本概念，接下来想知道模块怎么拆、对象库怎么写、merge 怎么做、pack 怎么读的人。

### SDD Teaching

讲这个项目背后的工程方法。不是只看功能，而是看一个复杂项目如何从 PRD 走到任务、代码、测试和安全边界。

### Project

讲当前这个仓库本身，包括任务拆分、项目结构、工程约束和维护规则。

### PRD

讲正式需求文档，适合想看规格、范围和兼容性要求的读者。

## 当前项目边界

当前已经实现的重点能力包括：

- 本地 `.pygit` 仓库初始化和提交闭环；
- loose object、tree、commit、tag；
- Git Index V2；
- `HEAD`、branch、tag、remote refs；
- `hash-object`、`cat-file`、`write-tree`、`read-tree`、`commit-tree`、`update-ref`；
- `add`、`status`、`commit`、`log`、`branch`、`checkout`、`switch`、`tag`、`reset`、`stash`、`merge`；
- pack v2、idx v2 基础能力；
- 本地路径远端 `clone/fetch/push`；
- 自建 `pygit://host:port` 专用服务端。

明确不实现：

- GitHub 集成；
- SSH Git；
- HTTP Git；
- 官方 Git wire protocol；
- Git LFS。

这不是退缩，而是边界管理。项目的目标是把 Git 的核心仓库行为做好，而不是在网络协议和托管平台生态上无限外扩。

## 建议阅读顺序

如果你是第一次进入这个项目，建议按这个顺序读：

1. 先看[快速开始](getting-started.md)，确认项目怎么运行、现在能做什么；
2. 再回英文主导航里的 `Git Teaching`，先把 Git 概念吃透；
3. 再看 `Build Git Teaching`，理解 Python 实现层；
4. 再看[项目总览](project/index.md)和 [SDD 教学总览](sdd-teaching/index.md)，理解工程组织方式；
5. 最后把 [PRD 总览](prd/index.md) 当成正式规格参考。

## 这套中文页和英文页的关系

英文是默认入口，中文不是另起一套完全不同的结构。当前策略是：

- 站点打开时先看到英文；
- 中文通过顶层“中文”导航分组进入；
- 中文页尽量和英文页保持同样的信息架构；
- 重要边界、实现状态和工程规则在两边都要说清楚，避免两套文档语义漂移。
