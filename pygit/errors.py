"""项目统一异常定义。

Git 复现项目会频繁处理二进制对象、路径边界、锁文件和仓库状态。
这些错误如果全部使用内置异常，命令层很难给用户输出稳定、可测试的
错误信息，因此在这里集中定义语义明确的异常类型。
"""


class PygitError(Exception):
    """所有可预期业务错误的基类。"""


class RepositoryError(PygitError):
    """仓库不存在、重复初始化或仓库结构不合法时抛出。"""


class ObjectError(PygitError):
    """对象读取、解码、校验或类型不匹配时抛出。"""


class PathSafetyError(PygitError):
    """路径逃逸工作区或存在危险路径语义时抛出。"""


class LockError(PygitError):
    """锁文件创建、提交或清理失败时抛出。"""

