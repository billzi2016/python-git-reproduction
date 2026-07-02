# Index V2

对很多实现者来说，Index V2 是 Git 复现项目第一次真正碰到“严肃二进制格式”的地方。

## 为什么 Index V2 难

难点不是“存几项数据”，而是它同时要求你处理：

- 固定头部；
- 变长条目；
- 路径排序；
- flags；
- stage 位；
- 8 字节对齐；
- 尾部 checksum；
- 扩展区。

只要其中一项处理不准，整个 index 文件就可能不可读，或者产生非常诡异的状态行为。

## 为什么不能自造一个文本格式代替

你当然可以为了偷快写一个：

```text
path sha1
```

但这样会丢掉大量 Git 真实语义：

- 暂存区不是只有路径映射；
- merge conflict 需要 stage；
- 状态比较会依赖元数据；
- `write-tree` / `read-tree` / `status` 的很多行为都需要更真实的结构。

所以如果目标是“复现 Git”，而不是“写一个像 Git 的小工具”，那就不应该绕开 Index V2。

## 实现时最容易出错的地方

最常见的坑包括：

- header 写错；
- 路径长度和 flags 处理错；
- padding 错；
- entry 顺序错；
- checksum 漏校验；
- conflict stage 处理不完整。

这些问题很多不会立刻爆炸，但会在后续 `status`、merge、`write-tree` 或 `checkout` 时表现成很难追的问题。

## 为什么 index 是状态核心

一旦你真正实现 index，就会理解 Git 的很多行为其实都围着它转：

- `add` 改的是 index；
- `commit` 读的是 index；
- `status` 比较 index；
- merge conflict 也要写 index stage；
- `read-tree` 会重建 index；
- `write-tree` 会从 index 生成 tree。

所以 index 不是“中间文件”，而是整个工作流状态机的核心部件之一。
