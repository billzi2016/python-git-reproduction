# 03. Git Index V2 暂存区

`.pygit/index` 必须以 Git Index V2 为目标格式。Index 是暂存区状态机，也是 `add`、`write-tree`、`status`、`checkout`、`merge` 的核心数据源。

## 二进制布局

```text
Header:
  signature: 4 bytes, "DIRC"
  version:   4 bytes, big-endian integer, value 2
  entries:   4 bytes, big-endian integer

Entry:
  ctime seconds      4 bytes
  ctime nanoseconds  4 bytes
  mtime seconds      4 bytes
  mtime nanoseconds  4 bytes
  dev                4 bytes
  ino                4 bytes
  mode               4 bytes
  uid                4 bytes
  gid                4 bytes
  file_size          4 bytes
  sha1               20 bytes
  flags              2 bytes
  path               N bytes + NUL + padding to 8-byte boundary

Checksum:
  SHA-1 of all previous bytes, 20 bytes
```

## 排序要求

所有条目必须按路径字节序升序排列。写入 index 前必须重新排序并重算 checksum。

## Stage 要求

flags 中的 stage 位用于合并冲突：

- Stage 0：普通已暂存条目。
- Stage 1：冲突 base 版本。
- Stage 2：冲突 ours 版本。
- Stage 3：冲突 theirs 版本。

存在 Stage 1/2/3 条目时，`commit` 必须被拒绝，直到用户解决冲突并重新 `add`。

