"""
故事时间线页面（思维导图版）
数据源三合一：
- 事件（TimelineStore：章节/类型/标题/内容/重要性/角色）
- 细纲（OutlineLibrary：同名作品的细纲 md，解析每章核心事件/出场人物/章末钩子）
- 写作空间章节文件（点击事件 → 跳转对应章节）

布局：顶部书籍下拉（分书查看）→ 左侧思维导图（书→章节→事件）→ 右侧详情面板 + 分支回退
"""

import os
import re
import time

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QDialog, QFormLayout, QSpinBox, QMessageBox, QInputDialog, QSplitter,
    QScrollArea, QGroupBox, QListWidget, QListWidgetItem, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QGraphicsPathItem, QDialogButtonBox
)

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit

EVENT_TYPES = ["战斗", "突破", "情感", "剧情转折", "日常", "伏笔", "其他"]

# 事件类型 → 节点颜色
_TYPE_COLORS = {
    "战斗": "#e05050", "突破": "#a060e0", "情感": "#e080a0", "剧情转折": "#4c7ef3",
    "日常": "#909090", "伏笔": "#40a060", "其他": "#b08850",
}
_CHAPTER_COLOR = "#3d8b5f"
_ROOT_COLOR = "#4c7ef3"


def _chapter_no_from_title(title: str) -> int:
    """从章节标题提取章节号：「第12章 xxx」→12；「第一章」→1；无则0"""
    if not title:
        return 0
    m = re.search(r"第\s*(\d+)\s*章", title)
    if m:
        return int(m.group(1))
    cn = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    m2 = re.search(r"第\s*([一二三四五六七八九十]+)\s*章", title)
    if m2:
        num = 0
        for ch in m2.group(1):
            if ch == "十":
                num = num * 10 if num else 10
            else:
                num += cn.get(ch, 0)
        return num
    return 0


def _chapter_no_from_path(path: str) -> int:
    """从章节文件路径提取章节号（「第12章」或纯数字文件名）"""
    stem = os.path.splitext(os.path.basename(path or ""))[0]
    if stem.isdigit():
        return int(stem)
    return _chapter_no_from_title(stem)


class _NodeItem(QGraphicsItem):
    """思维导图节点：圆角矩形 + 标题 + 副标题，点击回调"""

    def __init__(self, data: dict, color: str, callback, parent=None):
        super().__init__(parent)
        self.data = data
        self.color = color
        self.callback = callback
        self._w = 190
        self._h = 44
        title = data.get("title", "")
        sub = data.get("sub", "")
        fm = QFontMetrics(QFont("Microsoft YaHei", 9))
        if len(title) > 12:
            title = title[:12] + "…"
        self._title = title
        self._sub = sub
        if sub:
            self._h = 58
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._w, self._h)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(1, 1, self._w - 2, self._h - 2)
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        painter.fillPath(path, QColor(self.color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawPath(path)
        painter.setPen(QColor("#ffffff"))
        font = QFont("Microsoft YaHei", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(8, 4, self._w - 16, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._title)
        if self._sub:
            sub_font = QFont("Microsoft YaHei", 8)
            painter.setFont(sub_font)
            painter.setPen(QColor(255, 255, 255, 220))
            painter.drawText(QRectF(8, 26, self._w - 16, 28), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self._sub)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.callback:
            self.callback(self.data)
        super().mousePressEvent(event)


class EventDialog(QDialog):
    """添加/编辑事件对话框"""

    def __init__(self, parent=None, event: dict = None, chapter_hint: int = 1):
        super().__init__(parent)
        self.setWindowTitle("编辑事件" if event else "添加事件")
        self.setMinimumWidth(420)
        self._event = event
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.chapter_spin = QSpinBox()
        self.chapter_spin.setRange(1, 9999)
        self.chapter_spin.setValue(int((event or {}).get("chapter", chapter_hint) or chapter_hint))
        form.addRow("章节", self.chapter_spin)

        self.type_combo = QComboBox()
        self.type_combo.addItems(EVENT_TYPES)
        if event and event.get("type") in EVENT_TYPES:
            self.type_combo.setCurrentText(event["type"])
        form.addRow("类型", self.type_combo)

        self.title_input = ModernInput("事件标题")
        if event:
            self.title_input.setText(event.get("title", ""))
        form.addRow("标题", self.title_input)

        self.content_input = ModernTextEdit("事件内容描述...")
        self.content_input.setFixedHeight(90)
        if event:
            self.content_input.setPlainText(event.get("content", ""))
        form.addRow("内容", self.content_input)

        self.importance_spin = QSpinBox()
        self.importance_spin.setRange(1, 10)
        self.importance_spin.setValue(int((event or {}).get("importance", 5) or 5))
        form.addRow("重要程度", self.importance_spin)

        self.characters_input = ModernInput("相关角色，逗号分隔")
        if event:
            self.characters_input.setText(", ".join(event.get("characters", []) or []))
        form.addRow("相关角色", self.characters_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def collect(self) -> dict:
        return {
            "chapter": self.chapter_spin.value(),
            "type": self.type_combo.currentText(),
            "title": self.title_input.text().strip(),
            "content": self.content_input.toPlainText().strip(),
            "importance": self.importance_spin.value(),
            "characters": [c.strip() for c in self.characters_input.text().split(",") if c.strip()],
        }


class EventPage(QWidget):
    """故事时间线：思维导图（书→章节→事件）+ 细纲详情 + 分支回退"""

    open_chapter_requested = __import__("PyQt6.QtCore", fromlist=["pyqtSignal"]).pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._events = []
        self._chapters = []       # [{no, title, core, chars, hook, path, events:[]}]
        self._unplaced = []       # 无章节号的事件
        self._branch_loaded = False
        self._init_ui()
        self._load_books()
        self._load_all()
        self._load_branches()

    # ==================== UI ====================

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 顶部：标题 + 书籍下拉 + 操作
        header = QHBoxLayout()
        title = QLabel("故事时间线")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(QLabel("书籍:"))
        self.book_filter = QComboBox()
        self.book_filter.setMinimumWidth(180)
        self.book_filter.currentTextChanged.connect(lambda _: self._load_all())
        header.addWidget(self.book_filter)

        add_btn = ModernButton("添加事件", "primary")
        add_btn.clicked.connect(self._add_event)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # 主体：左思维导图 + 右详情
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---------- 左：思维导图 ----------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel("思维导图：点击「章节」查看细纲，点击「事件」查看详情并可跳转对应章节")
        hint.setStyleSheet("color: #8e8e8e; font-size: 11px;")
        left_layout.addWidget(hint)

        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._view.setFrameShape(QGraphicsView.Shape.NoFrame)
        left_layout.addWidget(self._view, 1)

        splitter.addWidget(left_panel)

        # ---------- 右：详情 + 分支 ----------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 详情区
        self.detail_title = QLabel("点击节点查看详情")
        self.detail_title.setObjectName("section_title")
        right_layout.addWidget(self.detail_title)

        self.detail_content = ModernTextEdit("")
        self.detail_content.setReadOnly(True)
        self.detail_content.setMinimumHeight(200)
        right_layout.addWidget(self.detail_content)

        detail_btns = QHBoxLayout()
        self.open_chapter_btn = ModernButton("打开对应章节", "primary")
        self.open_chapter_btn.setEnabled(False)
        self.open_chapter_btn.clicked.connect(self._open_chapter)
        detail_btns.addWidget(self.open_chapter_btn)

        self.edit_event_btn = ModernButton("编辑事件", "secondary")
        self.edit_event_btn.setEnabled(False)
        self.edit_event_btn.clicked.connect(self._edit_current_event)
        detail_btns.addWidget(self.edit_event_btn)

        self.del_event_btn = ModernButton("删除事件", "danger")
        self.del_event_btn.setEnabled(False)
        self.del_event_btn.clicked.connect(self._delete_current_event)
        detail_btns.addWidget(self.del_event_btn)

        detail_btns.addStretch()
        right_layout.addLayout(detail_btns)

        # 分支面板（保留原功能）
        branch_box = QGroupBox("时间分支（写错了随时回退）")
        branch_layout = QVBoxLayout(branch_box)

        self.branch_list = QListWidget()
        self.branch_list.setMaximumHeight(120)
        branch_layout.addWidget(self.branch_list)

        branch_btn_row = QHBoxLayout()
        create_branch_btn = QPushButton("创建分支点")
        create_branch_btn.setObjectName("btn_primary")
        create_branch_btn.setFixedHeight(30)
        create_branch_btn.clicked.connect(self._create_branch)
        branch_btn_row.addWidget(create_branch_btn)

        restore_btn = QPushButton("回退到此")
        restore_btn.setObjectName("btn_secondary")
        restore_btn.setFixedHeight(30)
        restore_btn.clicked.connect(self._restore_branch)
        branch_btn_row.addWidget(restore_btn)

        del_branch_btn = QPushButton("删除")
        del_branch_btn.setObjectName("btn_danger")
        del_branch_btn.setFixedHeight(30)
        del_branch_btn.clicked.connect(self._delete_branch)
        branch_btn_row.addWidget(del_branch_btn)
        branch_layout.addLayout(branch_btn_row)

        branch_hint = QLabel("在改变剧情走向前创建分支点；反悔时一键回退（回退前自动备份当前进度）")
        branch_hint.setStyleSheet("color: #8e8e8e; font-size: 11px;")
        branch_hint.setWordWrap(True)
        branch_layout.addWidget(branch_hint)

        right_layout.addWidget(branch_box)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        right_scroll.setWidget(right_panel)
        splitter.addWidget(right_scroll)

        splitter.setSizes([760, 380])
        layout.addWidget(splitter)

        # 状态
        self._current_node = None   # 当前选中节点数据（含 type: chapter/event）
        self._chapter_path = None

    # ==================== 数据加载 ====================

    def _load_books(self):
        """书籍下拉：写作空间书籍 ∪ 大纲库作品 ∪ 事件中的 book"""
        books = set()
        try:
            from src.data.writing_space import get_writing_space
            for n in get_writing_space().list_tree():
                if n.get("type") == "book":
                    books.add(n["name"])
        except Exception:
            pass
        try:
            from src.data.outline_library import get_outline_library
            for w in get_outline_library().list_works():
                books.add(w.title)
        except Exception:
            pass
        try:
            from src.data.timeline_store import get_timeline_store
            for e in get_timeline_store().load_events():
                if e.get("book"):
                    books.add(e["book"])
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

    def _load_all(self):
        """加载事件 + 章节（细纲/写作空间），渲染思维导图"""
        self._events = []
        self._chapters = []
        self._unplaced = []
        book = self.book_filter.currentText()
        book_name = "" if book == "全部书籍" else book

        # 1. 事件（字段兼容：type/event_type、characters/related_characters）
        try:
            from src.data.timeline_store import TimelineStore, load_all_books_events
            if book_name:
                events = TimelineStore(book=book_name).load_events()
            else:
                events = load_all_books_events()
            for e in events:
                ev = dict(e)
                if not ev.get("type"):
                    ev["type"] = ev.get("event_type", "其他")
                if not ev.get("characters"):
                    ev["characters"] = ev.get("related_characters", [])
                self._events.append(ev)
        except Exception:
            pass

        # 2. 细纲章节（同名作品）
        detail_chapters = self._load_detail_chapters(book_name)

        # 3. 写作空间章节（用于跳转 + 补全章节）
        ws_chapters = self._load_ws_chapters(book_name)

        # 合并章节：细纲优先，写作空间补缺
        chapter_map = {}  # no -> chapter dict
        for ch in detail_chapters:
            chapter_map.setdefault(ch["no"], ch)
        for ch in ws_chapters:
            target = chapter_map.get(ch["no"])
            if target:
                target["path"] = target.get("path") or ch.get("path")
            else:
                chapter_map[ch["no"]] = ch

        # 4. 事件挂到章节
        for ev in self._events:
            no = int(ev.get("chapter", 0) or 0)
            ch = chapter_map.get(no)
            if ch:
                ch.setdefault("events", []).append(ev)
            else:
                self._unplaced.append(ev)

        self._chapters = [chapter_map[k] for k in sorted(chapter_map.keys()) if k > 0]
        self._render_map()
        self._clear_detail()

    def _load_detail_chapters(self, book_name: str) -> list:
        """从大纲库读取同名作品的细纲 md，解析每章信息"""
        if not book_name:
            return []
        try:
            from src.data.outline_library import get_outline_library
            lib = get_outline_library()
            work = next((w for w in lib.list_works() if w.title == book_name), None)
            if not work or not work.detail_file:
                return []
            text = lib.read_work(work, "detail")
        except Exception:
            return []

        chapters = []
        cur = None
        for line in (text or "").splitlines():
            stripped = line.strip()
            m = re.match(r"^#+\s*(第[\d一二三四五六七八九十百]+章[^\n]*)", stripped)
            if m:
                cur = {"no": _chapter_no_from_title(m.group(1)), "title": m.group(1).strip(),
                       "core": "", "chars": "", "hook": "", "path": None, "events": []}
                chapters.append(cur)
                continue
            if cur is None:
                continue
            # 细纲条目可能带 "- " / "* " 前缀（如 "- 核心事件：xxx"）
            entry = re.sub(r"^[-*]\s*", "", stripped)
            if entry.startswith("核心事件"):
                cur["core"] = entry.split("：", 1)[-1] if "：" in entry else entry
            elif entry.startswith("出场人物") or entry.startswith("出场角色"):
                cur["chars"] = entry.split("：", 1)[-1] if "：" in entry else entry
            elif entry.startswith("章末钩子"):
                cur["hook"] = entry.split("：", 1)[-1] if "：" in entry else entry
        return chapters

    def _load_ws_chapters(self, book_name: str) -> list:
        """从写作空间读取书籍的章节文件（提取章节号与路径）"""
        if not book_name:
            return []
        result = []
        try:
            from src.data.writing_space import get_writing_space
            for n in get_writing_space().list_tree():
                if n.get("name") != book_name or n.get("type") != "book":
                    continue
                for child in n.get("children", []):
                    if child.get("type") == "chapter":
                        result.append({"no": _chapter_no_from_path(child.get("path", "")),
                                       "title": child.get("name", ""), "core": "", "chars": "",
                                       "hook": "", "path": child.get("path"), "events": []})
                    elif child.get("type") == "folder":
                        for gc in child.get("children", []):
                            if gc.get("type") == "chapter":
                                result.append({"no": _chapter_no_from_path(gc.get("path", "")),
                                               "title": gc.get("name", ""), "core": "", "chars": "",
                                               "hook": "", "path": gc.get("path"), "events": []})
        except Exception:
            pass
        return result

    # ==================== 思维导图渲染 ====================

    def _render_map(self):
        self._scene.clear()
        if not self._chapters and not self._unplaced:
            self._scene.addText("当前书籍暂无细纲/事件。\n可先在大纲编辑页写细纲，或点击「添加事件」。",
                                QFont("Microsoft YaHei", 10))
            return

        book_name = self.book_filter.currentText()

        # 根节点
        root_item = _NodeItem({"type": "root", "title": book_name, "sub": f"{len(self._chapters)}章 · {len(self._events)}事件"},
                              _ROOT_COLOR, self._on_node_clicked)
        self._scene.addItem(root_item)
        root_item.setPos(20, 30)

        # 章节节点 + 事件节点（纵向布局）
        x_chapter = 260
        x_event = 500
        y = 20
        chapter_pos = []   # (chapter_no, center_y)
        event_pos = []     # (chapter_no, center_y)
        for ch in self._chapters:
            events = ch.get("events", [])
            sub = ""
            if ch.get("hook"):
                sub = f"钩子：{ch['hook'][:18]}"
            elif ch.get("core"):
                sub = f"{ch['core'][:18]}"
            elif events:
                sub = f"{len(events)}个事件"
            item = _NodeItem({"type": "chapter", "title": f"第{ch['no']}章", "sub": sub,
                              "no": ch.get("no")},
                             _CHAPTER_COLOR, self._on_node_clicked)
            self._scene.addItem(item)
            item.setPos(x_chapter, y)
            chapter_pos.append((ch["no"], y + 22))
            # 事件节点
            ey = y
            for ev in events:
                eitem = _NodeItem({"type": "event", "title": f"[{ev.get('type', '其他')}] {ev.get('title', '')[:10]}",
                                   "sub": f"第{ev.get('chapter', 0)}章", "id": ev.get("id")},
                                  _TYPE_COLORS.get(ev.get("type", "其他"), _TYPE_COLORS["其他"]),
                                  self._on_node_clicked)
                self._scene.addItem(eitem)
                eitem.setPos(x_event, ey)
                event_pos.append((ch["no"], ey + 22))
                ey += 64
            y = max(y + 70, ey + 10)

        # 连线：根→章
        for no, cy in chapter_pos:
            line = QGraphicsPathItem()
            path = QPainterPath()
            path.moveTo(210, 52)
            path.lineTo(x_chapter, cy)
            line.setPath(path)
            line.setPen(QPen(QColor("#9ab8d8"), 2))
            self._scene.addItem(line)
        # 连线：章→事件
        for no, ey in event_pos:
            cy = next((cy2 for n2, cy2 in chapter_pos if n2 == no), ey)
            path2 = QPainterPath()
            path2.moveTo(x_chapter + 190, cy)
            path2.lineTo(x_event, ey)
            line2 = QGraphicsPathItem()
            line2.setPath(path2)
            line2.setPen(QPen(QColor("#c8a060"), 2))
            self._scene.addItem(line2)

        # 未挂章节事件（独立一列）
        if self._unplaced:
            ux = x_event + 260
            uy = 20
            unplaced_label = _NodeItem({"type": "root", "title": "未分类事件", "sub": f"{len(self._unplaced)}个"},
                                       "#8e8e8e", None)
            self._scene.addItem(unplaced_label)
            unplaced_label.setPos(ux, uy)
            for ev in self._unplaced:
                uitem = _NodeItem({"type": "event", "title": f"[{ev.get('type', '其他')}] {ev.get('title', '')[:10]}",
                                   "sub": "未关联章节", "id": ev.get("id")},
                                  _TYPE_COLORS.get(ev.get("type", "其他"), _TYPE_COLORS["其他"]),
                                  self._on_node_clicked)
                self._scene.addItem(uitem)
                uitem.setPos(ux, uy + 60)
                uy += 64

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-20, -20, 40, 40))
        self._scene.update()

    # ==================== 节点点击 ====================

    def _on_node_clicked(self, data: dict):
        ntype = data.get("type")
        self._current_node = data
        self._chapter_path = None
        self.open_chapter_btn.setEnabled(False)
        self.edit_event_btn.setEnabled(False)
        self.del_event_btn.setEnabled(False)

        if ntype == "chapter":
            no = data.get("no")
            ch = next((c for c in self._chapters if c.get("no") == no), None)
            if ch:
                self._show_chapter_detail(ch)
        elif ntype == "event":
            ev_id = data.get("id")
            ev = next((e for e in self._events if e.get("id") == ev_id), None)
            if ev:
                self._show_event_detail(ev)

    def _show_chapter_detail(self, ch: dict):
        self.detail_title.setText(f"细纲 · 第{ch.get('no', 0)}章")
        parts = [f"章节：第{ch.get('no', 0)}章  {ch.get('title', '')}"]
        if ch.get("core"):
            parts.append(f"核心事件：{ch['core']}")
        if ch.get("chars"):
            parts.append(f"出场人物：{ch['chars']}")
        if ch.get("hook"):
            parts.append(f"章末钩子：{ch['hook']}")
        events = ch.get("events", [])
        if events:
            parts.append("")
            parts.append(f"本章事件（{len(events)}）：")
            for ev in events:
                parts.append(f"  · [{ev.get('type', '其他')}] {ev.get('title', '')}（重要度{ev.get('importance', 5)}）")
        else:
            parts.append("本章暂无关联事件")
        self.detail_content.setPlainText("\n".join(parts))
        self._chapter_path = ch.get("path")
        self.open_chapter_btn.setEnabled(bool(self._chapter_path))

    def _show_event_detail(self, ev: dict):
        self.detail_title.setText(f"事件详情 · 第{ev.get('chapter', 0)}章")
        parts = [
            f"标题：{ev.get('title', '')}",
            f"类型：{ev.get('type', '其他')}",
            f"章节：第{ev.get('chapter', 0)}章",
            f"重要程度：{ev.get('importance', 5)}/10",
        ]
        if ev.get("characters"):
            parts.append(f"相关角色：{', '.join(ev['characters'])}")
        parts.append("")
        parts.append(ev.get("content", ""))
        self.detail_content.setPlainText("\n".join(parts))
        self._current_event = ev
        self.edit_event_btn.setEnabled(True)
        self.del_event_btn.setEnabled(True)
        # 找对应章节路径
        self._chapter_path = None
        for ch in self._chapters:
            if ch.get("no") == int(ev.get("chapter", 0) or 0) and ch.get("path"):
                self._chapter_path = ch["path"]
                break
        self.open_chapter_btn.setEnabled(bool(self._chapter_path))

    def _clear_detail(self):
        self.detail_title.setText("点击节点查看详情")
        self.detail_content.setPlainText("")
        self.open_chapter_btn.setEnabled(False)
        self.edit_event_btn.setEnabled(False)
        self.del_event_btn.setEnabled(False)
        self._current_node = None
        self._current_event = None
        self._chapter_path = None

    def _open_chapter(self):
        if self._chapter_path:
            self.open_chapter_requested.emit(self._chapter_path)

    def _timeline_store(self):
        """按当前选中书返回 TimelineStore（「全部书籍」时用全局兼容 store）"""
        from src.data.timeline_store import TimelineStore
        book = self.book_filter.currentText()
        if book and book != "全部书籍":
            return TimelineStore(book=book)
        return TimelineStore()

    def _edit_current_event(self):
        ev = getattr(self, "_current_event", None)
        if not ev:
            return
        dlg = EventDialog(self, event=ev)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.collect()
            data["book"] = "" if self.book_filter.currentText() == "全部书籍" else self.book_filter.currentText()
            self._timeline_store().update_event(ev["id"], data)
            self._load_all()

    def _delete_current_event(self):
        ev = getattr(self, "_current_event", None)
        if not ev:
            return
        reply = QMessageBox.question(self, "确认删除", f"确定删除事件「{ev.get('title')}」吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._timeline_store().delete_event(ev["id"])
            self._clear_detail()
            self._load_all()

    def _add_event(self):
        hint = 1
        for ch in self._chapters:
            if ch.get("events"):
                hint = ch["no"]
                break
        dlg = EventDialog(self, chapter_hint=hint)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.collect()
            data["book"] = "" if self.book_filter.currentText() == "全部书籍" else self.book_filter.currentText()
            if not data["title"]:
                data["title"] = f"第{data['chapter']}章事件"
            self._timeline_store().add_event(data)
            self._load_all()

    # ==================== 分支（保留原功能） ====================

    def _load_branches(self):
        self.branch_list.clear()
        for b in self._timeline_store().list_branches():
            time_str = time.strftime("%m-%d %H:%M", time.localtime(b["created_at"]))
            item = QListWidgetItem(f"{b['name']}（{time_str} · {b['event_count']}个事件）")
            item.setData(Qt.ItemDataRole.UserRole, b)
            self.branch_list.addItem(item)

    def _create_branch(self):
        name, ok = QInputDialog.getText(
            self, "创建分支点", "分支名称（标记当前剧情走向，如：主角黑化前）:")
        if not ok or not name.strip():
            return
        self._timeline_store().create_branch(name.strip())
        self._load_branches()
        QMessageBox.information(self, "已创建", f"分支点「{name.strip()}」已创建。\n之后随时可回退到当前状态。")

    def _restore_branch(self):
        item = self.branch_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "提示", "请先选择一个分支点")
            return
        branch = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "确认回退",
            f"确定回退到分支「{branch['name']}」吗？\n\n"
            f"当前时间线（{len(self._events)}个事件）将被替换为该分支的状态（{branch['event_count']}个事件）。\n"
            f"放心：回退前会自动备份当前进度为新分支。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        success, msg = self._timeline_store().restore_branch(branch["id"], auto_backup=True)
        if success:
            self._clear_detail()
            self._load_all()
            self._load_branches()
            QMessageBox.information(self, "已回退", f"已回退到分支「{msg}」。\n原进度已自动备份，可随时再回退回来。")
        else:
            QMessageBox.warning(self, "失败", msg)

    def _delete_branch(self):
        item = self.branch_list.currentItem()
        if item is None:
            return
        branch = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定删除分支「{branch['name']}」吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._timeline_store().delete_branch(branch["id"])
            self._load_branches()
