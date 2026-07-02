# 02. 对象数据库

`.pygit/objects` 是内容寻址对象库。所有对象写入前都必须拼接 Git 标准对象头：

```text
[object_type] [content_length]\x00[content_bytes]
```

完整字节流的 SHA-1 十六进制值就是对象 ID。写入 loose object 时，必须使用 zlib 压缩后存储到：

```text
.pygit/objects/[sha1前2位]/[sha1后38位]
```

## Blob

Blob 只保存文件原始内容，不保存路径、文件名或权限。

```text
blob [size]\x00[raw_bytes]
```

## Tree

Tree 保存目录快照。每个条目包含 mode、name 和 20 字节原始 SHA-1。

```text
tree [size]\x00[mode] [name]\x00[20_bytes_sha1]...
```

常见 mode：

- `100644`：普通文件。
- `100755`：可执行文件。
- `40000`：目录 tree。

## Commit

Commit 保存 DAG 节点信息，包括根 tree、父提交、作者、提交者、时间戳和提交说明。

```text
tree [tree_sha1]
parent [parent_sha1]
author [name] <[email]> [timestamp] [timezone]
committer [name] <[email]> [timestamp] [timezone]

[message]
```

## Tag

附注标签必须写成 tag 对象。轻量标签只需要在 `refs/tags/` 中写目标 SHA-1。

```text
object [sha1]
type [object_type]
tag [tag_name]
tagger [name] <[email]> [timestamp] [timezone]

[message]
```

## 校验要求

读取对象时必须解压、解析 header、检查声明 size 和真实内容长度一致，并重新计算 SHA-1。只要校验失败，必须抛出致命错误，禁止继续使用该对象。

