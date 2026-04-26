"""数据库相关工具函数"""


def escape_like(s: str) -> str:
    """转义 SQL LIKE/ILIKE 中的特殊通配符，防止用户输入 % 或 _ 导致过滤绕过。

    用法::

        from utils.db import escape_like
        query.filter(Model.name.ilike(f"%{escape_like(user_input)}%"))
    """
    return (
        s.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
