"""
图标库
加载 assets/icons 下的 Feather SVG 图标，按主题色渲染为 QIcon
"""

import os
from functools import lru_cache

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assets", "icons")

# 图标名映射（语义名 -> feather文件名）
ICON_NAMES = {
    "chat": "message-square",
    "home": "home",
    "project": "folder",
    "writer": "edit-3",
    "outline": "file-text",
    "character": "users",
    "hook": "target",
    "event": "calendar",
    "critic": "eye",
    "extensions": "package",
    "book": "book-open",
    "export": "download",
    "history": "clock",
    "memory": "database",
    "settings": "settings",
    "plus": "plus",
    "send": "send",
    "model": "cpu",
    "attach": "paperclip",
    "expand": "chevron-down",
    "collapse": "chevron-right",
    # 编辑器工具栏
    "undo": "rotate-ccw",
    "redo": "rotate-cw",
    "clear": "x",
    "bold": "bold",
    "italic": "italic",
    "underline": "underline",
    "strike": "minus",
    "list": "list",
    "list_ordered": "list-ordered",
    "quote": "align-left",
    "code": "code",
    "link": "link",
    "image": "image",
    "table": "table",
    "heading": "type",
    "divider": "minus",
    "save": "save",
    "import": "upload",
    "new_doc": "file-plus",
    "todo": "check-square",
}


@lru_cache(maxsize=128)
def get_icon(name: str, color: str = "#5d5d5d", size: int = 16) -> QIcon:
    """获取图标，按指定颜色渲染

    Args:
        name: 语义名（chat/home/settings...）或 feather 文件名
        color: 图标颜色（跟随主题）
        size: 渲染尺寸
    """
    filename = ICON_NAMES.get(name, name)
    path = os.path.join(_ICONS_DIR, f"{filename}.svg")
    if not os.path.isfile(path):
        return QIcon()

    with open(path, "r", encoding="utf-8") as f:
        svg = f.read().replace("currentColor", color)

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size * 2, size * 2)  # 2x 高清渲染
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2.0)

    return QIcon(pixmap)


def theme_icon_color(theme_name: str = "light") -> str:
    """按主题返回图标颜色"""
    return "#b4b4b4" if theme_name == "dark" else "#5d5d5d"
