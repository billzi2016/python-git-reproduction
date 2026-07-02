# 项目目录结构规划

本文档定义 `python-git-reproduction` 的推荐代码结构。目录设计目标是把 Git 的对象库、索引、引用、命令、合并、远端通信等能力拆成可独立验证的模块。

## 推荐结构

```text
python-git-reproduction/
├── docs/
│   ├── README.md
│   ├── PROJECT_TREE.md
│   └── prd/
│       ├── 00-overview.md
│       ├── 01-repository-layout.md
│       ├── 02-object-database.md
│       ├── 03-index.md
│       ├── 04-plumbing-commands.md
│       ├── 05-porcelain-commands.md
│       ├── 06-merge.md
│       ├── 07-packfile-remote.md
│       ├── 08-non-functional.md
│       └── 09-roadmap.md
├── pygit/
│   ├── __init__.py
│   ├── cli.py
│   ├── errors.py
│   ├── paths.py
│   ├── lockfile.py
│   ├── repository.py
│   ├── objects.py
│   ├── index.py
│   ├── refs.py
│   ├── ignore.py
│   ├── diff.py
│   ├── merge.py
│   ├── pack.py
│   ├── remote.py
│   ├── working_tree.py
│   └── commands/
│       ├── __init__.py
│       ├── plumbing.py
│       └── porcelain.py
├── tests/
│   ├── test_objects.py
│   ├── test_index.py
│   ├── test_refs.py
│   ├── test_plumbing.py
│   ├── test_porcelain.py
│   ├── test_merge.py
│   └── test_pack.py
└── pyproject.toml
```

## 模块职责

`pygit/cli.py` 负责命令行入口解析，将用户输入分发到管道命令或瓷器命令。

`pygit/repository.py` 负责仓库发现、初始化、`.pygit` 路径解析和仓库级上下文对象。

`pygit/objects.py` 负责 blob、tree、commit、tag 的编码、解码、SHA-1 计算、zlib 压缩、松散对象读写和对象校验。

`pygit/index.py` 负责 Git Index V2 的二进制读写、条目排序、路径对齐、stage 位解析、尾部 checksum 校验。

`pygit/refs.py` 负责 HEAD、分支、标签、远端追踪引用的读取、解析、更新和锁文件写入。

`pygit/lockfile.py` 负责 `.lock` 文件创建、原子替换、异常清理，所有会改写仓库元数据的模块必须复用它。

`pygit/working_tree.py` 负责工作区扫描、文件写回、删除旧追踪文件、路径安全检查。

`pygit/diff.py` 负责树之间、索引和工作区之间的差异计算，后续为 status、merge、stash 提供基础能力。

`pygit/merge.py` 负责 LCA 搜索、快进判断、三方合并、冲突标记和 index stage 维护。

`pygit/pack.py` 负责 packfile 和 idx 文件解析、生成、对象随机寻址、delta 对象处理。

`pygit/remote.py` 负责 fetch、push、clone 使用的远端协议模拟、对象发现、增量传输和引用更新。

`pygit/commands/plumbing.py` 负责 `hash-object`、`cat-file`、`write-tree`、`read-tree`、`commit-tree`、`update-ref`。

`pygit/commands/porcelain.py` 负责 `init`、`add`、`rm`、`status`、`commit`、`log`、`branch`、`checkout`、`switch`、`tag`、`reset`、`stash`、`merge`、`fetch`、`push`、`clone`。

## Python 注释规范

每个 Python 文件开头必须包含中文意图注释，说明该文件在 Git 复现系统中的职责、输入输出边界和不能破坏的兼容性约束。

每个公开函数、复杂内部函数和命令处理函数都必须写中文函数注释，说明参数含义、返回值、异常场景和对仓库状态的影响。

涉及二进制格式、SHA-1 计算、zlib 压缩、index padding、pack offset、delta 展开、引用锁、三方合并冲突的代码必须写关键点中文注释。

凡是逻辑句子较长、判断条件较多、容易误解 Git 语义的地方，必须拆成多行注释说明，不允许只写一句模糊说明。

