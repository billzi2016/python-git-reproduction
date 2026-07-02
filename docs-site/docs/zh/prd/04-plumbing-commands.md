# 04. 管道命令

管道命令直接操作对象库、索引和引用，不承载复杂用户工作流。

## hash-object

读取目标文件，按指定对象类型拼接对象头，计算 SHA-1。指定 `-w` 时写入对象库。

要求：

- 默认类型为 blob。
- 大文件必须流式读取，不能一次性全部载入内存。
- 写入 loose object 必须使用 zlib 最高压缩等级。

## cat-file

读取对象并输出类型、大小或内容。

要求：

- 支持完整 SHA-1。
- 支持唯一短 SHA-1。
- 必须校验对象完整性。
- `-p` 应按对象类型做可读输出。

## write-tree

读取 index，把暂存区条目转换为 tree 对象，并递归写入对象库，最后输出根 tree SHA-1。

## read-tree

读取 tree 对象，递归展开为 index 条目，并覆盖写入 `.pygit/index`。

## commit-tree

根据根 tree、父提交参数和标准输入 message 创建 commit 对象，写入对象库并输出 commit SHA-1。

## update-ref

使用锁文件安全更新引用。提供旧值时必须先比较旧值，不一致则拒绝更新。

