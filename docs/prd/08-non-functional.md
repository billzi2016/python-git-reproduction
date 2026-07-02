# 08. 非功能性需求

## 标准库限制

实现必须只使用 Python 标准库。允许使用的典型模块包括 `hashlib`、`zlib`、`struct`、`os`、`pathlib`、`configparser`、`socket`、`time`、`stat`、`tempfile`。

## 大文件处理

超过 50MB 的文件必须使用 64KB 块进行流式读取。`hash-object`、`add` 和 pack 写入流程不能无条件把大文件完整读入内存。

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

Python 代码必须使用中文解释所有关键点。尤其是二进制协议、位运算、路径排序、时间戳、冲突 stage、pack offset、delta 展开、锁文件原子替换，必须写出“为什么这样做”和“如果不这样做会破坏什么兼容性”。
