# 06. 分支合并

merge 负责把目标分支或目标 commit 合并到当前分支。

## 最近公共祖先

系统必须从 ours 和 theirs 两个 commit 出发，沿 parent 反向遍历 DAG，寻找最近公共祖先 base。

## 快进合并

如果 base 等于 ours，说明当前分支没有额外提交，可以直接把当前分支引用移动到 theirs，并刷新 index 和工作区。

## 三方合并

非快进情况下，必须比较 base、ours、theirs 三个 tree：

- base 到 ours 的变化。
- base 到 theirs 的变化。
- 两边是否修改同一路径。
- 同一路径是否出现重叠行修改。

## 冲突处理

发生冲突时必须：

1. 在 index 中写入 Stage 1、Stage 2、Stage 3 条目。
2. 在工作区文件中注入标准冲突标记。
3. 阻止 `commit`，直到用户解决冲突并重新 `add`。

冲突标记格式：

```text
<<<<<<< HEAD
[ours content]
=======
[theirs content]
>>>>>>> [branch or sha1]
```

