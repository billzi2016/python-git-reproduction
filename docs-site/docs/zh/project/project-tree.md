# 项目结构

这一页解释的是：这个仓库为什么要按现在这样的方式拆模块，而不是把所有逻辑揉进几个命令文件里。

## 为什么结构对 Git 项目尤其重要

Git 类系统不是普通的脚本工具。它同时涉及：

- 二进制对象格式；
- 二进制 index 文件；
- refs 与 `HEAD`；
- 工作区扫描与重写；
- 合并算法；
- pack 与 idx；
- 本地和远端同步。

如果这些职责混在一起，会立刻产生三个问题：

- 危险逻辑到处复制，容易漏保护；
- 二进制格式代码难以审计；
- 测试出问题时很难定位是对象层、状态层还是命令编排层出错。

所以项目结构不是美观问题，而是可维护性和安全性问题。

## 推荐结构

项目内部文档给出的推荐结构大致如下：

```text
python-git-reproduction/
├── docs/
├── pygit/
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
│       ├── plumbing.py
│       └── porcelain.py
├── tests/
└── pyproject.toml
```

重点不在于文件名必须一字不差，而在于职责边界要清楚。

## 主要模块职责

### `pygit/cli.py`

负责命令行入口解析，把用户输入分发到对应命令处理层。它不应该承担对象解码、merge 算法或者路径保护的底层实现。

### `pygit/repository.py`

负责仓库发现、初始化、`.pygit` 路径解析，以及仓库级上下文管理。它回答的问题是：

- 仓库根在哪里；
- `.pygit` 在哪里；
- 当前操作应当以哪个仓库为上下文；
- 某个路径是否属于这个仓库。

### `pygit/objects.py`

负责 blob、tree、commit、tag 的编码、解码、SHA-1 计算、zlib 压缩与解压、loose object 读写、对象校验。它是整个系统的存储核心。

### `pygit/index.py`

负责 Git Index V2：

- header；
- entry；
- flags；
- stage；
- padding；
- checksum；
- 扩展区。

index 不是随便存几个路径而已，它是 Git 暂存区真正的二进制表达。

### `pygit/refs.py`

负责：

- `HEAD`；
- branch；
- tag；
- remote refs；
- symbolic refs；
- detached `HEAD`；
- 原子更新；
- 旧值校验。

很多分支操作在本质上都是 ref 更新，所以这个模块非常关键。

### `pygit/lockfile.py`

负责 `.lock` 文件和原子替换。这个模块必须集中复用，因为只要某个元数据写路径绕开了统一锁逻辑，就有可能留下半写入状态。

### `pygit/working_tree.py`

负责工作区文件层面的操作：

- 扫描；
- 写回；
- 删除旧追踪文件；
- 路径边界检查。

这是仓库语义和真实文件系统风险直接接触的地方。

### `pygit/diff.py`

负责 tree、index、working tree 之间的差异计算。`status`、`merge`、`stash` 都依赖这层能力，不能每个命令各自复制一套比较逻辑。

### `pygit/merge.py`

负责：

- LCA 搜索；
- 快进判断；
- 三方合并；
- 冲突标记；
- index stage 维护。

merge 是图算法和内容合并逻辑的结合点，所以需要独立模块。

### `pygit/pack.py`

负责：

- pack 解析；
- idx 解析；
- 包内对象随机寻址；
- offset 处理；
- delta 展开；
- pack 生成。

这是另一个格式兼容性特别敏感的模块。

### `pygit/remote.py`

负责本地路径远端和 `.pygit` 专用服务器的同步逻辑，包括对象发现、传输和引用更新。

### `pygit/commands/plumbing.py`

负责低层命令，如：

- `hash-object`
- `cat-file`
- `write-tree`
- `read-tree`
- `commit-tree`
- `update-ref`

这些命令应主要编排底层模块，而不是把核心二进制逻辑重复写一遍。

### `pygit/commands/porcelain.py`

负责高层命令，如：

- `init`
- `add`
- `rm`
- `status`
- `commit`
- `log`
- `branch`
- `checkout`
- `switch`
- `tag`
- `reset`
- `stash`
- `merge`
- `fetch`
- `push`
- `clone`

这层可以做更多业务编排，但依然应该复用下层模块，而不是自己重新实现对象、index、refs 和路径保护。

## 这和 SOLID / DRY 的关系

项目明确要求遵循 SOLID 和 DRY。落到结构上，意思不是背设计原则名词，而是：

- 对象编码逻辑不能复制进多个命令；
- 锁文件逻辑不能每个模块自己写一份；
- 路径安全检查不能在 `rm`、`reset`、`checkout` 里各写一套不一致版本；
- CLI 解析不能和二进制格式解析搅在一起。

结构好不好，最终体现在危险逻辑能不能集中、兼容性关键代码能不能审计、测试能不能精准定位问题。

## 中文注释规范

这个项目还有一条明确规则：Python 代码必须带充分中文注释，包括：

- 文件开头的意图注释；
- 函数级职责说明；
- 二进制布局说明；
- 长难句逻辑的解释；
- 关键边界条件和危险路径说明。

这不是装饰要求，而是为了让复杂仓库代码在几个月后依然能被自己和别人读懂。
