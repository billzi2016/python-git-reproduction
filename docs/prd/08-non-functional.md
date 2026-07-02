# 08. 非功能性需求

## 标准库限制

实现必须只使用 Python 标准库。允许使用的典型模块包括 `hashlib`、`zlib`、`struct`、`os`、`pathlib`、`configparser`、`socket`、`time`、`stat`、`tempfile`。

## 设计原则

项目实现必须遵循 SOLID 和 DRY 原则。

SOLID 在本项目中的要求：

- 单一职责：对象库、Index、refs、工作区、merge、packfile、remote、CLI 必须分模块实现，不能把二进制解析、文件系统写入、命令行解析和业务编排混在一个巨型函数中。
- 开闭原则：新增命令或新增对象存储来源时，应优先扩展清晰接口，而不是改坏已有对象库、index 或 refs 行为。
- 里氏替换与接口隔离：底层模块暴露的函数必须语义明确，例如 `read_object`、`write_index`、`update_ref`，不能要求调用方理解内部文件布局才能正确使用。
- 依赖倒置：命令层可以依赖对象库、index、refs、working tree 等底层能力；底层模块不能反向依赖 CLI 参数或用户交互。

DRY 在本项目中的要求：

- SHA-1 计算、对象 header 编解码、zlib 压缩解压、Index checksum、引用锁、路径边界校验、原子写入、对象完整性校验等关键逻辑必须集中实现并复用。
- `reset --hard`、`checkout`、`rm`、`stash` 等危险命令必须复用统一的路径安全和工作区写入逻辑，不能各自复制一份容易漏保护的删除代码。
- 重复逻辑只有在能证明 Git 语义确实不同的情况下才允许分叉，并且必须用中文注释说明差异。

## 大文件处理

超过 50MB 的文件必须使用 64KB 块进行流式读取。`hash-object`、`add` 和 pack 写入流程不能无条件把大文件完整读入内存。

项目不实现 Git LFS。大文件不能通过 LFS pointer 替代普通 blob，也不能引入 `.gitattributes` LFS filter、LFS 本地对象库或 LFS 远端 batch API。所有大文件能力都必须沿普通 Git 对象库和 packfile 路线优化。

## 锁文件

写入 index 或 refs 前必须创建 `.lock` 文件。写入完成后使用 `os.replace` 原子替换目标文件。

## 数据校验

读取对象时必须校验：

- zlib 解压成功。
- header 合法。
- header 声明 size 与实际 content 长度一致。
- 重新计算 SHA-1 与对象名一致。

## 异常处理

任何写入失败都不能留下半写入状态。对象写入、index 写入、ref 写入、pack 写入必须使用临时文件或锁文件保护。

## 测试目录与 unittest 要求

项目必须在根目录维护 `tests/` 文件夹，并使用 Python 标准库 `unittest` 编写自动化测试，避免引入第三方测试框架依赖。

测试文件命名必须遵循 `test_*.py`。每个核心模块都应有对应测试文件，例如 `test_objects.py`、`test_index.py`、`test_refs.py`、`test_plumbing.py`、`test_porcelain.py`、`test_merge.py`、`test_pack.py`。

测试必须覆盖成功路径、失败路径、异常回滚和危险操作保护。涉及真实文件删除、工作区重写、引用改写、pack 解包等场景时，必须使用临时目录，禁止直接在用户真实项目目录执行破坏性测试。

每个阶段完成后必须能通过以下命令运行测试：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 注释要求

Python 代码必须使用中文解释所有关键点。

每个 Python 文件开头必须写意图注释，说明该文件在 Git 复现系统中的职责、边界、输入输出和不能破坏的兼容性要求。

每个公开函数、命令处理函数、复杂内部函数都必须写中文函数注释，说明参数、返回值、副作用、异常场景和对 `.pygit` 仓库状态的影响。

长条件判断、长难句逻辑、跨模块调用、二进制格式、危险文件操作和 Git 兼容性关键点必须写中文关键注释，不能只写一行模糊说明。

尤其是二进制协议、位运算、路径排序、时间戳、冲突 stage、pack offset、delta 展开、锁文件原子替换，必须写出“为什么这样做”和“如果不这样做会破坏什么兼容性”。

## Git 提交要求

项目提交信息必须使用中文，并且要详细、清晰、聚焦，符合高质量 Git 项目的提交要求。

commit 标题必须说明本次变更的核心目的，不能只写 `update`、`fix`、`change` 这类模糊词。

commit 正文必须说明：

- 为什么需要这次变更。
- 具体改变了哪些行为或约束。
- 对 Git 兼容性、数据安全、危险操作、测试覆盖是否有影响。
- 已运行哪些测试，测试结果是什么。

提交必须主题集中。不能把无关格式化、文档、功能和重构混在同一个 commit 中，除非它们是完成同一行为变更所必需的一部分。
