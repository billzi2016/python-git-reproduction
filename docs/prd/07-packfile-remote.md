# 07. Packfile 与远端同步

Packfile 和远端同步是高级阶段目标，但最终必须实现，因为它们决定 `.pygit` 是否具备完整分布式版本控制能力。

## pack 文件

`.pack` 文件必须包含：

- 4 字节魔数 `PACK`。
- 4 字节版本号，目标为 version 2。
- 4 字节对象数量。
- 连续对象实体。
- 文件尾部 SHA-1 校验。

## idx 文件

`.idx` Version 2 必须包含：

- 魔数与版本。
- 256 项 fan-out table。
- 按 SHA-1 升序排列的对象名。
- CRC32 表。
- offset 表。
- pack checksum。
- idx checksum。

## fetch

fetch 需要完成远端引用发现、本地已有对象计算、want/have 协商、pack 接收、idx 生成和远端追踪分支更新。

## push

push 需要完成远端引用发现、非快进拒绝、本地缺失对象计算、增量 pack 生成、pack 发送和远端引用更新。

## clone

clone 是 `init`、配置 origin、`fetch`、`checkout` 的组合工作流。

