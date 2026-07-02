# python-git-reproduction

`python-git-reproduction` 是一个使用纯 Python 3 复现 Git 的工程。项目目标不是做一个简化版版本控制玩具，而是尽可能完整地实现 Git 的核心底层逻辑、上层工作流、对象存储格式、索引格式、引用系统、合并机制、打包文件和远端同步能力。

项目运行后会在工作区生成 `.pygit` 目录。`.pygit` 的设计目标是尽量兼容官方 Git 的对象格式、索引格式、引用格式和 packfile 格式。

## 项目目标

最终目标是用 Python 标准库复现 Git 的完整核心功能，包括：

- 仓库初始化。
- loose object 对象库。
- blob、tree、commit、tag 四类对象。
- Git Index V2 暂存区。
- HEAD、branch、tag、remote ref 引用系统。
- `hash-object`、`cat-file`、`write-tree`、`read-tree`、`commit-tree`、`update-ref` 等管道命令。
- `init`、`add`、`rm`、`status`、`commit`、`log`、`branch`、`checkout`、`switch`、`tag`、`reset`、`stash` 等瓷器命令。
- 分支合并、最近公共祖先、快进合并、三方合并、冲突标记和 index stage。
- packfile、idx、delta、fetch、push、clone 等分布式同步能力。

## 当前实现状态

当前处于 MVP 第一阶段，已经实现：

- `pygit init`
- `pygit add`
- `pygit hash-object`
- `pygit hash-object -w`
- `pygit cat-file -t`
- `pygit cat-file -s`
- `pygit cat-file -p`
- `pygit write-tree`
- `pygit read-tree`
- `pygit commit-tree`
- `pygit update-ref`
- `pygit commit -m`
- `pygit log`
- `pygit log --oneline`
- `pygit status`
- `pygit rm`
- `pygit rm --cached`
- `pygit branch`
- `pygit branch <name>`
- `pygit branch -d <name>`
- `pygit checkout <branch-or-commit>`
- `pygit switch <branch>`
- `pygit tag`
- `pygit tag <name>`
- `pygit tag -a <name> -m <message>`
- `pygit reset --soft <target>`
- `pygit reset --mixed <target>`
- `pygit reset --hard <target>`
- `pygit stash push`
- `pygit stash apply`
- `pygit stash pop`
- `pygit merge <target>`
- `.pygit` 基础目录初始化。
- loose object 编码、SHA-1 计算、zlib 压缩写入。
- loose object 解压、header 解析、size 校验、SHA-1 反校验。
- 唯一短 SHA-1 解析。
- Git Index V2 基础读写、排序、padding 和 checksum。
- 从 index 递归生成 tree 对象。
- 从 tree 重建 index。
- 基于当前分支 HEAD 创建 commit 并沿第一父链查看历史。
- HEAD、index、工作区三方状态比较。
- 已追踪文件从 index 移除和安全工作区删除。
- 本地分支创建、列出和删除。
- 干净工作区下切换分支或游离 HEAD，并重写工作区与 index。
- 轻量标签和附注标签。
- soft、mixed、hard reset。
- reset 目标支持分支名、commit SHA-1、轻量标签和附注标签。
- 基础 stash push/apply/pop。
- merge 支持 LCA、快进、非快进自动合并、冲突标记和 index stage 1/2/3。
- pack v2 与 idx v2 基础读写、idx 随机寻址、ref-delta 解析和非 delta pack 生成。
- 基于 Python 标准库 `unittest` 的测试目录。

尚未实现：

- 远端同步。
- packfile、fetch、push、clone。

## 快速使用

当前可以直接通过 Python 模块方式运行：

```bash
python3 -m pygit.cli init
```

写入一个 blob 对象：

```bash
echo "hello" > hello.txt
python3 -m pygit.cli hash-object -w hello.txt
```

查看对象类型：

```bash
python3 -m pygit.cli cat-file -t <object-id>
```

查看对象大小：

```bash
python3 -m pygit.cli cat-file -s <object-id>
```

查看对象内容：

```bash
python3 -m pygit.cli cat-file -p <object-id>
```

如果项目以 editable 方式安装，`pyproject.toml` 提供了 `pygit` 命令入口：

```bash
pygit init
```

## 测试

项目测试统一放在根目录 `tests/` 下，并使用 Python 标准库 `unittest`。

运行全部测试：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

当前测试覆盖：

- 仓库初始化目录结构。
- 仓库向上发现。
- 重复初始化拒绝。
- blob 对象 header 编码。
- Git 对象 SHA-1 计算。
- loose object 写入和读取。
- 短 SHA-1 解析。
- 损坏对象拒绝。
- Git Index V2 编解码、排序和 checksum。
- `add` 写入 blob 并更新 index。
- `write-tree` 生成递归 tree。
- `commit-tree` 创建 commit 对象。
- `commit` 更新 HEAD 当前分支。
- `log --oneline` 查看提交历史。
- `status` 三方状态比较。
- `rm` 和 `rm --cached`。
- `branch` 创建、列出和删除。
- `checkout` 分支或 commit。
- `switch` 本地分支。
- `tag` 轻量标签和附注标签。
- `reset` soft、mixed、hard。
- `stash` push、apply、pop。
- `merge` LCA、快进、三方合并和冲突隔离。
- CLI `init/hash-object/cat-file/add/write-tree/commit/log` 基础链路。

后续每个核心模块都必须补充对应测试：

- `tests/test_index.py`
- `tests/test_refs.py`
- `tests/test_plumbing.py`
- `tests/test_porcelain.py`
- `tests/test_merge.py`
- `tests/test_pack.py`
- `tests/test_remote.py`

## 项目文档

核心文档入口：

- `docs/README.md`：文档阅读顺序。
- `docs/SDD_REQUIREMENTS.md`：SDD 工程要求、测试要求、危险指令安全要求、SOLID/DRY 和提交质量要求。
- `docs/TASKS.md`：开发任务清单，已完成任务使用 `[x]` 标记。
- `docs/PROJECT_TREE.md`：推荐代码目录结构与模块职责。
- `docs/prd/`：拆分后的产品需求文档。

## 项目结构

```text
python-git-reproduction/
├── docs/
│   ├── README.md
│   ├── PROJECT_TREE.md
│   ├── SDD_REQUIREMENTS.md
│   └── prd/
├── pygit/
│   ├── __init__.py
│   ├── checkout.py
│   ├── cli.py
│   ├── commit.py
│   ├── errors.py
│   ├── index.py
│   ├── lockfile.py
│   ├── merge.py
│   ├── objects.py
│   ├── paths.py
│   ├── refs.py
│   ├── reset.py
│   ├── repository.py
│   ├── revision.py
│   ├── status.py
│   ├── stash.py
│   ├── tag.py
│   └── working_tree.py
├── tests/
│   ├── test_cli.py
│   ├── test_branch.py
│   ├── test_checkout.py
│   ├── test_index.py
│   ├── test_merge.py
│   ├── test_objects.py
│   ├── test_refs_commit.py
│   ├── test_repository.py
│   ├── test_reset.py
│   ├── test_stash.py
│   ├── test_status_rm.py
│   ├── test_tag.py
│   └── test_working_tree.py
├── pyproject.toml
└── README.md
```

详细规划见：

- `docs/README.md`
- `docs/PROJECT_TREE.md`
- `docs/SDD_REQUIREMENTS.md`
- `docs/prd/`

## 设计原则

### 纯标准库

实现必须严格使用 Python 标准库。项目可以使用 `hashlib`、`zlib`、`struct`、`os`、`pathlib`、`configparser`、`socket`、`time`、`stat`、`tempfile`、`unittest` 等标准库模块，但不能引入第三方依赖。

### Git 格式兼容

项目优先复现 Git 的真实数据格式，而不是只模拟命令输出。对象 ID 必须基于 Git 标准格式计算：

```text
[object_type] [content_length]\x00[content_bytes]
```

loose object 必须使用 SHA-1 内容寻址和 zlib 压缩，路径格式为：

```text
.pygit/objects/[sha1前2位]/[sha1后38位]
```

后续 index、tree、commit、tag、packfile 和 refs 都必须以官方 Git 兼容格式为目标。

### SDD

本项目遵循 SDD 工作方式：规格、设计、开发、测试同步推进。

每个功能实现前必须明确：

- 输入是什么。
- 输出是什么。
- 会读哪些 `.pygit` 文件。
- 会写哪些 `.pygit` 文件。
- 是否会改写工作区。
- 失败时如何回滚。
- 如何测试成功路径和失败路径。

### SOLID

模块必须保持职责清晰：

- `repository.py` 只负责仓库发现和初始化。
- `objects.py` 只负责对象编码、写入、读取和校验。
- `lockfile.py` 只负责锁文件和原子写入。
- `paths.py` 只负责路径规范化和边界检查。
- `cli.py` 只负责命令行解析和错误展示。

后续新增的 `index.py`、`refs.py`、`merge.py`、`pack.py`、`remote.py` 也必须保持单一职责。底层模块不能反向依赖命令层。

### DRY

重复且关键的逻辑必须集中实现并复用，例如：

- SHA-1 计算。
- 对象 header 编码和解析。
- zlib 压缩和解压。
- index checksum。
- 引用锁文件。
- 路径边界校验。
- 原子写入。
- 对象完整性校验。
- 工作区危险删除保护。

不能在多个命令里复制粘贴相似的安全逻辑。尤其是 `reset --hard`、`checkout`、`rm`、`stash` 这类危险命令，必须共用统一的路径边界和删除保护能力。

### 中文注释

Python 源码必须有充分中文注释：

- 文件开头写该文件的实现意图。
- 函数写职责、参数、返回值、副作用和异常。
- 二进制格式必须写清楚每个字段的含义。
- 长条件判断必须解释为什么这样判断。
- 危险操作必须解释安全边界。
- Git 兼容性关键点必须解释如果做错会破坏什么。

## 安全要求

这个项目会实现一些危险能力，因此默认必须以保护用户电脑为第一优先级。

危险操作包括：

- 删除工作区文件。
- `reset --hard`。
- `checkout` 或 `switch` 重写工作区。
- `rm` 删除物理文件。
- `stash pop` 应用并移除 stash。
- `update-ref` 改写分支或标签。
- pack 解包写入大量对象。
- fetch、push、clone 改写引用和目标目录。

安全要求：

- 任何危险操作前必须确认目标路径位于当前仓库工作区内部。
- 不能只做字符串前缀判断，必须使用规范化真实路径。
- 必须防御 `..`、绝对路径和符号链接逃逸。
- 默认不能删除未追踪文件。
- 工作区重写前必须先完成目标对象完整性校验。
- 测试危险操作时必须使用临时目录。

## 开发路线

### MVP：对象库和本地提交闭环

- `init`：已实现。
- `hash-object`：已实现。
- `cat-file`：已实现。
- loose object 读写和校验：已实现。
- Git Index V2 基础读写：已实现。
- `add`：已实现。
- `write-tree`：已实现。
- `read-tree`：已实现。
- `commit-tree`：已实现。
- `update-ref`：已实现。
- `commit`：已实现。
- `log`：已实现。
- `status`：已实现基础三方比较。
- `rm`：已实现基础文件删除和 `--cached`。

### V1：本地工作流

- `status`
- `rm`
- `branch`
- `checkout`
- `switch`
- `tag`
- `reset`
- ignore 规则基础支持

### V2：合并

- commit DAG 遍历。
- LCA 查找。
- fast-forward merge。
- 三方合并。
- 冲突文件标记。
- index stage 1/2/3。
- 未解决冲突禁止提交。

### V3：stash

- `stash push`
- `stash apply`
- `stash pop`
- stash commit 结构。
- stash 与工作区/index 的恢复逻辑。

### V4：Packfile

- pack v2 读取：已实现。
- idx v2 读取：已实现。
- pack 随机对象定位：已实现。
- delta 对象解析：已实现 ref-delta。
- pack 生成：已实现非 delta pack。

### V5：远端同步

- `clone`
- `fetch`
- `push`
- 远端引用协商。
- want/have 对象协商。
- 非快进拒绝。
- pack 网络传输。

## 当前限制

当前版本已经实现了从工作区文件到 blob、index、tree、commit、HEAD 更新和 log 的最小本地提交闭环，并具备基础 `status`、`rm`、`branch`、`checkout`、`switch`、`tag`、`reset`、`stash`、`merge` 与 packfile 能力。它还没有实现远端同步。

项目明确不实现 Git LFS。大文件后续只按普通 Git blob 和 packfile 路线优化，不引入 LFS pointer、LFS filter、LFS 对象目录或 LFS 远端协议。

现阶段 `.pygit` 是项目自己的仓库目录，不能直接替代 `.git`。后续会逐步提高与官方 Git 的格式兼容性，并通过测试验证生成数据是否能被官方 Git 工具识别。

## 提交要求

项目提交信息必须使用中文，并说明变更原因、行为影响和测试情况。

提交应保持主题集中。不要把无关格式化、功能变更和重构混在同一个 commit 中。

涉及危险操作、安全边界、二进制格式、数据一致性或 Git 兼容性的改动，commit 信息必须写得更详细。
