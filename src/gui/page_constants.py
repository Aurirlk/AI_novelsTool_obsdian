"""
页面索引常量
所有页面导航统一引用此处，避免魔数散布。
"""

from enum import IntEnum


class Page(IntEnum):
    """主窗口页面索引（与 QStackedWidget 顺序一一对应）"""
    HOME = 0            # 概览
    BOOKS = 1           # 书籍管理
    WRITER = 2          # 写作工作台
    OUTLINE = 3         # 大纲编辑
    CHARACTER = 4       # 角色管理
    HOOK = 5            # 悬念管理
    EVENT = 6           # 故事时间线
    CRITIC = 7          # 批评师
    BOOK_ANALYSIS = 8   # 拆书分析
    EXPORT = 9          # 导出中心
    HISTORY = 10        # 历史记录
    MEMORY = 11         # 共享记忆
    SETTINGS = 12       # 系统设置
    CHAT = 13           # AI助手
    EXTENSIONS = 14     # 扩展中心
