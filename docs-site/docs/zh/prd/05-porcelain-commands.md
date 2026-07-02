# 05. 瓷器命令

瓷器命令面向最终用户，通常组合多个管道命令完成一个完整工作流。

## init

创建 `.pygit` 目录、对象库目录、引用目录、默认 HEAD 和配置文件。

## add

递归处理文件或目录，把未忽略文件写入对象库，并更新 index 条目。

## rm

从 index 中删除指定路径。未指定 `--cached` 时，同时删除工作区文件。

## status

执行三方比较：

- HEAD tree vs index：识别已暂存新增、修改、删除。
- index vs working tree：识别未暂存修改和删除。
- working tree vs index：识别未追踪文件。

## commit

执行 `write-tree`，读取 HEAD 当前父提交，创建 commit 对象，并通过 `update-ref` 更新当前分支。

## log

从 HEAD 指向的 commit 开始沿 parent 链输出历史，支持 `-n` 和 `--oneline`。

## branch

无参数时列出本地分支；带分支名时基于当前 HEAD 创建分支；带 `-d` 时删除分支引用。

## checkout / switch

切换分支或 commit。切换前必须检查未提交变更，避免覆盖用户工作区。切换后重写 HEAD、工作区和 index。

## tag

支持轻量标签和附注标签。附注标签必须创建 tag 对象。

## reset

支持 `--soft`、`--mixed`、`--hard`。

- `--soft`：只移动当前分支引用。
- `--mixed`：移动引用并刷新 index。
- `--hard`：移动引用、刷新 index，并强制重写工作区。

## stash

支持 `push`、`apply`、`pop`。stash 应以 commit 对象保存临时状态，并通过 `.pygit/refs/stash` 维护栈。

