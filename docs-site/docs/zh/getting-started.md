# 快速开始

这一页是中文读者最合适的起点。目标不是一句“运行这个命令”就结束，而是让你在真正动手之前先知道：这个项目现在能做什么、不能做什么、应该怎么安全地试。

## 你现在运行的是什么

这是一个纯 Python 3 的 Git 复现项目。它创建的版本控制目录名叫 `.pygit`。

它不是调用官方 `git` 命令来代劳，也不是在 Git 外面包一层教学脚本。它会自己计算对象哈希、自己写 loose object、自己读写 Index V2、自己维护 refs、自己做 merge、自己做 pack 读写，并且支持本地路径远端和自建 `.pygit` TCP 服务端。

## 当前已经支持什么

当前项目已经支持一条完整而严肃的本地工作流：

- 初始化仓库；
- `add` 暂存文件；
- `commit` 创建提交；
- `log` 查看历史；
- `branch`、`checkout`、`switch` 管理分支；
- `tag` 创建标签；
- `reset` 回退状态；
- `stash` 暂存工作现场；
- `merge` 合并分支；
- `clone`、`fetch`、`push` 同步本地路径远端；
- 通过 `pygit://host:port` 同步自建服务端远端。

底层能力也已经具备：

- loose object 的压缩写入与完整性校验；
- 从 index 生成 tree；
- 从 tree 重建 index；
- pack v2 与 idx v2 基础能力；
- merge 冲突 stage 1/2/3；
- 非快进 push 拒绝；
- 对危险工作区改写命令的路径边界保护。

## 当前不支持什么

这个边界一定要先看清：

- 不支持 GitHub 远端；
- 不支持 SSH Git；
- 不支持 HTTP Git；
- 不支持官方 Git wire protocol；
- 不支持 Git LFS。

所以，正确理解应该是：

- 这是一个“本地可用 + 自建 pygit 服务器可用”的 Git 复现项目；
- 它不是一个“今天就能无缝替代官方 Git 客户端接 GitHub”的项目。

## 最小可运行闭环

从仓库根目录直接运行：

```bash
python3 -m pygit.cli init
```

然后试一个最小提交流程：

```bash
echo "hello" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "initial commit"
python3 -m pygit.cli log --oneline
python3 -m pygit.cli status
```

这一小段流程其实已经覆盖了很多核心链路：

- 仓库初始化；
- blob 写入；
- index 更新；
- tree 生成；
- commit 创建；
- ref 更新；
- 历史读取；
- 工作区状态比较。

如果这条链路跑通，说明项目最关键的本地闭环已经活了。

## 看底层对象

如果你想直接观察对象层，可以用这些命令：

```bash
echo "hello" > hello.txt
python3 -m pygit.cli hash-object -w hello.txt
python3 -m pygit.cli cat-file -t <object-id>
python3 -m pygit.cli cat-file -s <object-id>
python3 -m pygit.cli cat-file -p <object-id>
```

这一组命令很重要，因为它能帮助你从“Git 管文件”切换到“Git 管对象”的思维模式。

## 试一个分支与合并流程

```bash
python3 -m pygit.cli branch dev
python3 -m pygit.cli switch dev
echo "change" > hello.txt
python3 -m pygit.cli add hello.txt
python3 -m pygit.cli commit -m "update hello"
python3 -m pygit.cli switch main
python3 -m pygit.cli merge dev
```

这条流程会触发：

- 分支创建；
- `HEAD` 移动；
- 第二次提交；
- 从另一条提交链返回；
- merge-base 查找；
- 工作区重写与合并逻辑。

## 标签、reset 和 stash

```bash
python3 -m pygit.cli tag v1.0.0
python3 -m pygit.cli tag -a v1.0.1 -m "release v1.0.1"
python3 -m pygit.cli reset --hard v1.0.0
python3 -m pygit.cli stash push -m "temporary work"
python3 -m pygit.cli stash pop
```

这里要特别强调：`reset --hard` 在任何 Git 类系统里都是危险操作。这个项目已经对路径边界和删除行为做了保守保护，但你依然应该优先在测试仓库或临时目录里练习。

## 本地路径远端

如果你不想先搭服务端，也可以直接测试本地路径远端：

```bash
python3 -m pygit.cli clone /path/to/source-repo /path/to/clone
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

这个方式非常适合教学，因为源仓库和目标仓库都在本机，出了问题也容易观察对象库、refs 和 pack 文件状态。

## 自建 `.pygit` 专用服务器

服务端：

```bash
python3 -m pygit.cli serve --host 127.0.0.1 --port 9419 /path/to/repo
```

客户端：

```bash
python3 -m pygit.cli clone pygit://127.0.0.1:9419 /path/to/clone
cd /path/to/clone
python3 -m pygit.cli fetch
python3 -m pygit.cli push
```

这个协议是项目自定义的 `.pygit` 专用协议，不是官方 Git wire protocol。好处是它足够小，适合教学和本地自建实验。

## 如何验证环境没问题

项目测试用的是 Python 标准库 `unittest`，并且强调核心行为不用 mock 冒充。

运行全部测试：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

当前文档记录的验证结果是：

```text
Ran 62 tests

OK
```

这说明测试覆盖的不是“假装的 Git 行为”，而是真实临时目录、真实 `.pygit`、真实对象文件、真实 index 和真实工作区状态。

## 读完这一页之后看什么

接下来你可以按目的选择方向：

- 想先学 Git 原理：回英文主导航里的 `Git Teaching`
- 想先学怎么用 Python 实现：回英文主导航里的 `Build Git Teaching`
- 想看项目规则和当前边界：看[项目总览](project/index.md)
- 想看正式规格：看[PRD 总览](prd/index.md)
