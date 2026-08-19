"""
关系图谱页面（人物关系图）
可视化 角色 ↔ 角色 的人物关系网络，节点展示角色关键信息
点击角色节点 → 跳转到角色管理页并选中该角色
"""

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsItem,
    QPushButton, QComboBox, QGraphicsPathItem, QGraphicsSimpleTextItem
)

# 角色类型 → 颜色
_TYPE_COLORS = {
    "主角": "#4c7ef3", "配角": "#34c759", "反派": "#e05050", "龙套": "#9aa0a6",
}


class _CharNode(QGraphicsItem):
    """角色节点：圆 + 名字 + 人物信息摘要，点击回调"""

    def __init__(self, name, info, color, callback):
        super().__init__()
        self.char_name = name
        self.info = info
        self.color = color
        self.callback = callback
        self._w = 150
        self._h = 52
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(-80, -26, self._w, self._h)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        # 圆
        painter.setBrush(QBrush(QColor(self.color)))
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawEllipse(QRectF(-12, -12, 24, 24))
        # 名字
        painter.setPen(QColor("#222222"))
        font = QFont("Microsoft YaHei", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(16, -22, self._w - 20, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         self.char_name[:10])
        # 人物信息
        painter.setPen(QColor("#8e8e8e"))
        info_font = QFont("Microsoft YaHei", 8)
        painter.setFont(info_font)
        painter.drawText(QRectF(16, 2, self._w - 16, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         self.info[:20])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.callback:
            self.callback(self.char_name)
        super().mousePressEvent(event)


class GraphPage(QWidget):
    """关系图谱：人物关系网络"""

    character_selected = pyqtSignal(str)  # 点击角色节点 → 跳转角色管理

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._render()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("关系图谱")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(QLabel("书籍:"))
        self.book_filter = QComboBox()
        self.book_filter.setMinimumWidth(180)
        self.book_filter.currentTextChanged.connect(lambda _: self._render())
        header.addWidget(self.book_filter)

        refresh_btn = QPushButton("刷新图谱")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._render)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        hint = QLabel("人物关系图：圆点=角色（颜色按类型：主角蓝/配角绿/反派红/龙套灰），连线=人物关系。点击角色节点跳转到角色管理")
        hint.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.view = QGraphicsView()
        self.view.setRenderHint(self.view.renderHints())
        self.view.setBackgroundBrush(QBrush(QColor("#fafafa")))
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        layout.addWidget(self.view, 1)

        self._load_books()
        self._render()

    def _load_books(self):
        books = set()
        try:
            from src.data.writing_space import get_writing_space
            for n in get_writing_space().list_tree():
                if n.get("type") == "book":
                    books.add(n["name"])
        except Exception:
            pass
        current = self.book_filter.currentText()
        self.book_filter.blockSignals(True)
        self.book_filter.clear()
        self.book_filter.addItem("全部书籍")
        for b in sorted(books):
            self.book_filter.addItem(b)
        idx = self.book_filter.findText(current)
        if idx >= 0:
            self.book_filter.setCurrentIndex(idx)
        self.book_filter.blockSignals(False)

    def _render(self):
        """渲染人物关系图"""
        self.scene.clear()
        try:
            from src.data.character_store import CharacterStore, load_all_books_characters
        except Exception as e:
            self.scene.addText(f"图谱渲染失败：{e}")
            return

        book = self.book_filter.currentText()
        try:
            if book != "全部书籍":
                chars = CharacterStore(book=book).load_all()
            else:
                chars = load_all_books_characters()
        except Exception as e:
            self.scene.addText(f"图谱渲染失败：{e}")
            return

        if not chars:
            self.scene.addText("暂无角色数据：请先到「角色管理」创建角色并填写人物关系")
            return

        # 动态布局：根据角色数量调整半径，避免重叠
        import math
        n = len(chars)
        node_w = 150  # 节点宽度
        min_gap = 60  # 节点最小间距
        circumference = n * (node_w + min_gap)
        radius = max(180, circumference / (2 * math.pi))

        cx, cy = radius + 80, radius + 80
        pos = {}
        nodes = {}
        for i, c in enumerate(chars):
            cid = c.get("id") or f"char_{i}"
            angle = 2 * math.pi * i / n - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            pos[cid] = QPointF(x, y)

            # 节点信息：性格 + 位置
            info_parts = []
            if c.get("personality"):
                info_parts.append(c["personality"][:8])
            if c.get("location"):
                info_parts.append(c["location"][:6])
            info = " · ".join(info_parts)
            color = _TYPE_COLORS.get(c.get("role_type", "龙套"), "#9aa0a6")
            node = _CharNode(c.get("name", ""), info, color, self._on_char_clicked)
            node.setPos(x, y)
            self.scene.addItem(node)
            nodes[cid] = node

        # 连线：人物关系（双向：A 的 relationships 里有 B 就画线）
        drawn = set()
        for c in chars:
            cid = c.get("id") or ""
            for rel in c.get("relationships", []) or []:
                rel_name = rel.get("name", "") if isinstance(rel, dict) else str(rel)
                target = next((x for x in chars if x.get("name") == rel_name), None)
                if target is None:
                    continue
                tid = target.get("id") or ""
                if not cid or not tid or tid == cid:
                    continue
                key = tuple(sorted([cid, tid]))
                if key in drawn:
                    continue
                drawn.add(key)
                line = QGraphicsLineItem(pos[cid].x(), pos[cid].y(),
                                         pos[tid].x(), pos[tid].y())
                line.setPen(QPen(QColor("#c8c8c8"), 1))
                self.scene.addItem(line)

                # 关系描述文字（画在中点旁）
                if isinstance(rel, dict) and rel.get("relation"):
                    mx = (pos[cid].x() + pos[tid].x()) / 2
                    my = (pos[cid].y() + pos[tid].y()) / 2
                    rel_label = QGraphicsSimpleTextItem(rel["relation"][:8])
                    rel_label.setFont(QFont("Microsoft YaHei", 8))
                    rel_label.setBrush(QBrush(QColor("#888888")))
                    rel_label.setPos(mx + 6, my - 6)
                    self.scene.addItem(rel_label)

        # 自适应场景大小
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_char_clicked(self, name: str):
        """点击角色节点 → 跳转角色管理页选中该角色"""
        self.character_selected.emit(name)

    def refresh(self):
        """外部刷新（角色数据变化后调用）"""
        self._load_books()
        self._render()


def create_graph_page():
    """创建关系图谱页面"""
    return GraphPage()
