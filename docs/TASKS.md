# 开发任务清单

本文档用于跟踪 `python-git-reproduction` 的实现进度。已完成的任务使用 `[x]` 标记，未完成任务使用 `[ ]` 标记。

## 0. 文档与工程约束

- [x] 拆分 PRD 文档到 `docs/prd/`。
- [x] 编写项目目录结构规划 `docs/PROJECT_TREE.md`。
- [x] 编写 SDD 工程要求 `docs/SDD_REQUIREMENTS.md`。
- [x] 明确必须使用标准库 `unittest`。
- [x] 明确测试不得使用模拟对象替代核心 Git 行为。
- [x] 明确危险指令必须保护用户电脑，禁止误删仓库外文件。
- [x] 明确项目必须遵循 SOLID 和 DRY 原则。
- [x] 在 PRD 中明确项目必须遵循 SOLID 和 DRY 原则。
- [x] 明确 Python 代码必须有充分中文注释。
- [x] 在 PRD 中明确 Python 文件开头意图注释、函数注释、长难句和关键点注释要求。
- [x] 在 PRD 中明确 Git commit 信息必须中文、详细、清晰、主题集中。
- [x] 在 PRD 中明确项目不实现 Git LFS。
- [x] 编写根目录 `README.md`。

## 1. 项目基础骨架

- [x] 创建 `pyproject.toml`。
- [x] 创建 `pygit/` Python 包。
- [x] 创建 `tests/` 测试目录。
- [x] 创建 `.gitignore`，排除 Python 缓存和构建产物。
- [x] 建立统一异常模块 `pygit/errors.py`。
- [x] 建立仓库路径与安全路径模块 `pygit/paths.py`。
- [x] 建立锁文件与原子写入模块 `pygit/lockfile.py`。
- [x] 建立 CLI 入口 `pygit/cli.py`。

## 2. 仓库初始化

- [x] 实现 `.pygit` 仓库初始化。
- [x] 创建 `.pygit/HEAD`。
- [x] 创建 `.pygit/config`。
- [x] 创建 `.pygit/objects/info`。
- [x] 创建 `.pygit/objects/pack`。
- [x] 创建 `.pygit/refs/heads`。
- [x] 创建 `.pygit/refs/tags`。
- [x] 创建 `.pygit/refs/remotes`。
- [x] 实现从子目录向上发现 `.pygit` 仓库。
- [x] 拒绝重复初始化已有 `.pygit` 仓库。

## 3. 对象数据库

- [x] 实现 Git 对象 header 编码：`[type] [size]\x00[content]`。
- [x] 实现 blob 对象 SHA-1 计算。
- [x] 实现 loose object 路径：`.pygit/objects/xx/yyyy...`。
- [x] 实现 zlib 最高等级压缩写入。
- [x] 实现 loose object 解压读取。
- [x] 实现对象 header 解析。
- [x] 实现对象 size 校验。
- [x] 实现对象 SHA-1 反校验。
- [x] 实现唯一短 SHA-1 解析。
- [x] 实现损坏对象拒绝。
- [ ] 实现大文件流式 hash-object。
- [ ] 实现 packfile 内对象读取。

## 4. 管道命令

- [x] `hash-object`
- [x] `hash-object -w`
- [x] `cat-file -t`
- [x] `cat-file -s`
- [x] `cat-file -p` blob 输出。
- [x] `cat-file -p` tree 格式化输出。
- [x] `write-tree`
- [x] `read-tree`
- [x] `commit-tree`
- [x] `update-ref`

## 5. Index V2 暂存区

- [x] 实现 Index V2 header 编码。
- [x] 实现 Index V2 entry 编码。
- [x] 实现 entry 8 字节 padding。
- [x] 实现 index 尾部 SHA-1 checksum。
- [x] 实现 index 读取 checksum 校验。
- [x] 实现 index 条目路径排序。
- [x] 实现同路径 add 更新而不是重复追加。
- [ ] 实现 index stage 1/2/3 冲突条目写入。
- [ ] 实现 index 扩展区。

## 6. 本地提交闭环

- [x] `add` 写入 blob 并更新 index。
- [x] `write-tree` 从 index 递归生成 tree。
- [x] `commit-tree` 创建 commit 对象。
- [x] `commit -m` 从 index 创建提交并更新 HEAD 当前分支。
- [x] `log` 沿第一父链输出提交历史。
- [x] `log --oneline`。
- [ ] 支持多父 commit 的完整展示。
- [ ] 支持 author/committer 从 config 读取。

## 7. 引用与分支

- [x] 读取 HEAD。
- [x] 支持符号引用 HEAD。
- [x] 支持游离 HEAD。
- [x] 原子更新 refs。
- [x] 支持轻量标签引用。
- [x] 支持附注标签对象引用。
- [x] 修订名解析支持分支名。
- [x] 修订名解析支持轻量标签。
- [x] 修订名解析支持附注标签剥离到 commit。
- [x] `branch` 列出本地分支。
- [x] `branch <name>` 创建本地分支。
- [x] `branch -d <name>` 删除非当前分支。
- [x] 拒绝空仓库创建分支。
- [x] 拒绝删除当前分支。
- [ ] 支持分支重命名。
- [ ] 支持上游分支追踪信息。

## 8. 工作区状态与删除

- [x] `status` 比较 HEAD tree vs index。
- [x] `status` 比较 index vs 工作区。
- [x] `status` 显示 staged added。
- [x] `status` 显示 staged modified。
- [x] `status` 显示 staged deleted。
- [x] `status` 显示 unstaged modified。
- [x] `status` 显示 unstaged deleted。
- [x] `status` 显示 untracked。
- [x] `rm --cached` 只从 index 删除。
- [x] `rm` 删除已追踪工作区文件并更新 index。
- [x] `rm` 删除前做工作区边界检查。
- [x] `rm` 不递归删除目录，避免误删用户文件。
- [ ] 支持 ignore 规则。
- [ ] 支持更接近 Git 的 status 输出格式。

## 9. 切换工作区

- [x] `checkout <branch>` 切换本地分支。
- [x] `checkout <commit>` 进入游离 HEAD。
- [x] `switch <branch>` 切换本地分支。
- [x] `switch` 拒绝裸 commit，避免误入游离 HEAD。
- [x] checkout 前拒绝脏工作区。
- [x] checkout 前先校验目标 commit/tree/blob。
- [x] checkout 只删除旧 index 中登记的追踪文件。
- [x] checkout 写入目标 tree 文件。
- [x] checkout 刷新 index。
- [x] checkout 最后更新 HEAD。
- [ ] 实现 Git 更细粒度的冲突前置校验。
- [ ] 实现 `checkout -- <path>`。
- [ ] 实现 `switch -c <branch>`。

## 10. 尚未实现的瓷器命令

- [x] `tag` 列出标签。
- [x] `tag <name>` 创建轻量标签。
- [x] `tag -a <name> -m <message>` 创建附注标签。
- [x] `reset --soft`
- [x] `reset --mixed`
- [x] `reset --hard`
- [x] `reset --hard` 保留未追踪文件，避免误删用户数据。
- [x] `stash push`
- [x] `stash apply`
- [x] `stash pop`
- [x] stash 栈写入 `.pygit/refs/stash`。
- [x] stash push 后恢复到 HEAD。
- [ ] stash apply/pop 三方合并式应用。

## 11. 合并

- [x] commit DAG BFS 遍历。
- [x] 最近公共祖先 LCA。
- [x] fast-forward merge。
- [x] 三方合并。
- [x] 非快进无冲突合并创建双父 merge commit。
- [x] 冲突文件标记。
- [x] index stage 1/2/3。
- [x] 未解决冲突禁止 commit。

## 12. Packfile 与远端

- [ ] pack v2 读取。
- [ ] idx v2 读取。
- [ ] pack 对象随机寻址。
- [ ] delta 对象解析。
- [ ] pack 生成。
- [ ] `clone`
- [ ] `fetch`
- [ ] `push`
- [ ] 非快进 push 拒绝。
- [x] 明确不实现 Git LFS。

## 13. 测试

- [x] `tests/test_repository.py`
- [x] `tests/test_objects.py`
- [x] `tests/test_cli.py`
- [x] `tests/test_index.py`
- [x] `tests/test_working_tree.py`
- [x] `tests/test_refs_commit.py`
- [x] `tests/test_status_rm.py`
- [x] `tests/test_branch.py`
- [x] `tests/test_checkout.py`
- [x] `tests/test_reset.py`
- [x] `tests/test_tag.py`
- [x] `tests/test_merge.py`
- [ ] `tests/test_pack.py`
- [ ] `tests/test_remote.py`
