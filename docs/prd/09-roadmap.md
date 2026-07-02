# 09. 实现路线

虽然最终目标是复现 Git 全部核心功能，但实现必须分阶段推进，避免一开始把对象库、合并、packfile 和远端协议混在一起导致不可验证。

## MVP：本地对象与提交闭环

- `init`
- `hash-object`
- `cat-file`
- loose object 读写和校验
- Git Index V2 基础读写
- `add`
- `write-tree`
- `commit-tree`
- `commit`
- `log`

完成 MVP 后，项目必须能从空仓库创建提交，并能查看提交历史。

## V1：本地工作流完整化

- `status`
- `rm`
- `branch`
- `checkout`
- `switch`
- `tag`
- `reset`
- ignore 规则基础支持

完成 V1 后，项目应具备单机 Git 常用工作流。

## V2：合并与冲突

- commit DAG 遍历。
- LCA 查找。
- fast-forward merge。
- 三方合并。
- 冲突文件标记。
- index stage 1/2/3。
- 禁止未解决冲突提交。

完成 V2 后，项目应支持多分支并行开发。

## V3：stash 与高级状态管理

- `stash push`
- `stash apply`
- `stash pop`
- stash commit 结构。
- stash 与工作区/index 的恢复逻辑。

## V4：Packfile

- pack v2 读取。
- idx v2 读取。
- pack 随机对象定位。
- pack 生成。
- delta 对象解析和生成。

## V5：远端同步

- `clone`
- `fetch`
- `push`
- 远端引用协商。
- want/have 对象协商。
- 非快进拒绝。
- pack 网络传输。

## 验收原则

每个阶段都必须配套测试，并尽量使用官方 Git 对生成数据进行交叉验证。凡是生成的对象、index、ref、packfile 不能被 Git 识别的情况，都必须作为兼容性缺陷处理。

