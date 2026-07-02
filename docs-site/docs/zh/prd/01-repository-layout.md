# 01. `.pygit` 仓库目录结构

初始化后，工作区根目录必须创建 `.pygit` 隐式目录。该目录是版本库的全部元数据根目录。

```text
.pygit/
├── HEAD
├── config
├── index
├── objects/
│   ├── info/
│   └── pack/
└── refs/
    ├── heads/
    ├── tags/
    └── remotes/
```

## 文件职责

`HEAD` 存储当前活动分支的符号引用，例如 `ref: refs/heads/main\n`；游离 HEAD 状态下直接存储 40 位 commit SHA-1。

`config` 使用 INI 风格文本，记录远端仓库、分支追踪关系和用户配置。

`index` 是 Git Index V2 二进制文件，表示暂存区状态。

`objects/` 是对象数据库，存储 loose object 和 packfile。

`refs/heads/` 存储本地分支引用，每个文件内容是 40 位 commit SHA-1 加换行。

`refs/tags/` 存储轻量标签或附注标签对象引用。

`refs/remotes/` 存储远端追踪分支。

## init 要求

`init` 必须检测当前目录是否已经存在 `.pygit`。如果存在，应拒绝重复初始化。如果不存在，创建完整目录结构，并把 `HEAD` 初始化为：

```text
ref: refs/heads/main
```

