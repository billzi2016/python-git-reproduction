"""纯 Python 复现 Git 的包入口。

本包只暴露项目版本号，具体能力由 repository、objects、refs、index
等模块按职责拆分实现。这里保持轻量，避免包导入时产生文件系统副作用。
"""

__version__ = "0.1.0"

