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

## pygit 专用服务器边界

项目不实现 GitHub、SSH Git、HTTP Git、`git-upload-pack` 或 `git-receive-pack` 官方 wire protocol。自建服务器目标是 `.pygit` 专用服务器，使用 Python 标准库 socket 提供 refs、fetch、push 和非快进拒绝。

本地路径远端和 `pygit://host:port` 专用服务器必须可用于项目自身的分布式同步。官方 Git 服务器兼容不是本项目目标。

## fetch

fetch 需要完成远端引用发现、对象接收和远端追踪分支更新。对于本地路径远端，允许直接复制对象数据库；对于 pygit 专用服务器，必须通过 socket 请求获取 refs 和对象负载。

## push

push 需要完成远端引用发现、非快进拒绝、对象发送和远端引用更新。对于 pygit 专用服务器，服务端必须验证旧引用，拒绝非快进更新。

## clone

clone 是 `init`、配置 origin、`fetch`、`checkout` 的组合工作流，必须支持本地路径远端和 pygit 专用服务器。
