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

## 注释要求

Python 代码必须使用中文解释所有关键点。尤其是二进制协议、位运算、路径排序、时间戳、冲突 stage、pack offset、delta 展开、锁文件原子替换，必须写出“为什么这样做”和“如果不这样做会破坏什么兼容性”。

