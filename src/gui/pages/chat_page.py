"""
AI助手对话页面（WorkBuddy风格最终版）
- 输入框内嵌模型选择器（配置自定义模型）
- @ 引用文件（本地/大纲库/提示词库）
- / 调用技能与指令
- "+"菜单：添加文件/专家/技能/连接器
- 无emoji的清爽界面
"""

import json
import os
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QScrollArea, QFrame, QSizePolicy, QPushButton,
    QMenu, QListWidget, QListWidgetItem, QLineEdit, QFileDialog,
    QSplitter, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QSize

from ..icons import get_icon, theme_icon_color
from src.data.chat_history_manager import get_chat_history_manager, ChatSession


# ==================== 输入框 ====================

class ChatInput(QTextEdit):
    """回车发送、Shift+回车换行、Esc关闭弹层"""

    submitted = pyqtSignal()
    escaped = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.escaped.emit()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) \
                and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submitted.emit()
            return
        super().keyPressEvent(event)


# ==================== 后台生成线程 ====================

class ChatWorker(QThread):
    """后台流式生成线程，支持技能注入、MCP工具与本地项目工具"""

    chunk = pyqtSignal(str)
    failed = pyqtSignal(str)
    tool_event = pyqtSignal(str)

    def __init__(self, provider, model, messages, system_prompt="",
                 connectors=None, tool_groups=None, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.model = model
        self.messages = messages
        self.system_prompt = system_prompt
        self.connectors = connectors or []
        # tool_groups: ["project"] / ["outline"] / ["project","outline"] / None(不启用本地工具)
        self.tool_groups = tool_groups

    def run(self):
        try:
            from src.utils.llm import LLMClient
            client = LLMClient(self.provider, self.model)

            # 本地项目数据工具（按启用的组注入，默认不启用）
            project_tools = []
            project_handler = None
            if self.tool_groups:
                from src.tools.project_tools import get_project_tools, get_project_tool_handler
                project_tools = get_project_tools(self.tool_groups)
                project_handler = get_project_tool_handler(self.tool_groups)

            tools = []
            mcp_handler = None
            if self.connectors:
                from src.mcp import get_mcp_manager
                manager = get_mcp_manager()
                for name in self.connectors:
                    status = manager.server_status().get(name, "")
                    if not status.startswith("已连接"):
                        self.tool_event.emit(f"正在连接 {name} ...")
                        # 短超时 + 失败跳过继续：避免单个服务器挂起拖垮整轮聊天
                        try:
                            manager.connect(name, timeout=15)
                            self.tool_event.emit(f"{name} 已连接")
                        except Exception as e:
                            self.tool_event.emit(f"{name} 连接失败，已跳过：{e}")
                            continue

                mcp_tools = manager.to_openai_tools()
                if mcp_tools:
                    tools.extend(mcp_tools)
                    mcp_handler = manager.tool_handler()

            # 合并本地项目工具
            tools.extend(project_tools)

            if tools:
                messages = []
                if self.system_prompt:
                    messages.append({"role": "system", "content": self.system_prompt})
                messages.extend(self.messages)

                local_names = {t["function"]["name"] for t in project_tools}

                def combined_handler(name: str, arguments_json: str) -> str:
                    if name in local_names:
                        return project_handler(name, arguments_json)
                    if mcp_handler is not None:
                        return mcp_handler(name, arguments_json)
                    return f"未知工具：{name}"

                text = client.chat_with_tools_stream(
                    messages, tools, combined_handler,
                    on_tool_event=lambda e: self.tool_event.emit(e))
                for piece in text:
                    if self.isInterruptionRequested():
                        break
                    self.chunk.emit(piece)
                    self.msleep(8)
                return

            history = self.messages[:-1]
            for piece in client.chat_stream(
                    self.messages[-1]["content"],
                    system_prompt=self.system_prompt or None,
                    history=history):
                if self.isInterruptionRequested():
                    break
                self.chunk.emit(piece)

        except Exception as e:
            self.failed.emit(str(e))


class WorkflowWorker(QThread):
    """全流程生成后台任务：创意→大纲→逐章生成→保存"""

    done = pyqtSignal(str, str)   # (小说文本, 摘要)
    failed = pyqtSignal(str)

    def __init__(self, idea, num_chapters, parent=None):
        super().__init__(parent)
        self.idea = idea
        self.num_chapters = num_chapters

    def run(self):
        try:
            from src.workflows.novel_workflow import NovelWorkflow
            workflow = NovelWorkflow()
            state = workflow.run(self.idea, self.num_chapters)

            title = state.story_bible.title if state.story_bible else "未命名"
            summary = f"《{title}》生成完成：{len(state.chapters)}章，共{state.total_words}字"

            # 保存到写作空间
            try:
                import os as _os
                from src.data.writing_space import get_writing_space
                ws = get_writing_space()
                if not ws.list_tree():
                    ws.create_book(title)
                ws.save(_os.path.join(ws.root, title, "全流程生成.md"), workflow.get_novel_text())
            except Exception:
                pass

            self.done.emit(workflow.get_novel_text(), summary)
        except Exception as e:
            self.failed.emit(str(e))


# ==================== 消息气泡 ====================

class MessageRow(QFrame):
    """单条消息气泡（支持 Markdown 渲染，高度自适应内容）"""

    def __init__(self, role: str, text: str = "", parent=None):
        super().__init__(parent)
        self.role = role
        self._markdown_text = ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        from PyQt6.QtWidgets import QTextBrowser
        self.bubble = QTextBrowser(self)
        self.bubble.setReadOnly(True)
        self.bubble.setOpenLinks(False)
        self.bubble.setFrameShape(QFrame.Shape.NoFrame)
        self.bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bubble.setMaximumWidth(720)
        self.bubble.setMinimumWidth(300)
        self.bubble.setMinimumHeight(28)
        # 水平：尽量占满可用宽度（≤720）；垂直：固定高度由 _resize_to_content 控制
        self.bubble.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if role == "system":
            self.bubble.setObjectName("bubble_system")
        else:
            self.bubble.setObjectName("bubble_user" if role == "user" else "bubble_ai")

        if role == "user":
            layout.addStretch()
            layout.addWidget(self.bubble)
        elif role == "system":
            layout.addStretch()
            layout.addWidget(self.bubble)
            layout.addStretch()
        else:
            layout.addWidget(self.bubble)
            layout.addStretch()

        self.set_text(text)

    def _resize_to_content(self):
        """根据文档实际高度调整气泡高度（延迟到宽度就绪后由定时器调用）"""
        try:
            width = self.bubble.width()
            if width < 300:
                # 宽度未就绪，稍后重试
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(30, self._resize_to_content)
                return
            self.bubble.document().setTextWidth(width - 8)
            doc_height = self.bubble.document().size().height()
            target = max(28, int(doc_height) + 12)
            if self.bubble.height() != target:
                self.bubble.setFixedHeight(target)
                self.updateGeometry()
        except Exception:
            pass

    def showEvent(self, event):
        """显示后（宽度已确定）重新校准高度"""
        super().showEvent(event)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._resize_to_content)

    def append_text(self, piece: str):
        self._markdown_text += piece
        self.bubble.setMarkdown(self._markdown_text)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._resize_to_content)

    def set_text(self, text: str):
        self._markdown_text = text or ""
        self.bubble.setMarkdown(self._markdown_text)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._resize_to_content)

    def text(self) -> str:
        return self._markdown_text


# ==================== 选择面板 ====================

class SelectorPanel(QFrame):
    """浮层选择面板：搜索框 + 列表 + 底部按钮"""

    item_picked = pyqtSignal(object)

    def __init__(self, parent=None, footer_buttons=None, passive=False):
        """
        passive=True 时使用 ToolTip 窗口（不抢焦点），用于 @ / 内联触发
        """
        flags = Qt.WindowType.ToolTip if passive else Qt.WindowType.Popup
        super().__init__(parent, flags | Qt.WindowType.FramelessWindowHint)
        if passive:
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setObjectName("card")
        self.setFixedSize(400, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("input")
        self.search.setPlaceholderText("搜索...")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_clicked)
        layout.addWidget(self.list_widget)

        for text, handler in (footer_buttons or []):
            btn = QPushButton(text)
            btn.setObjectName("btn_secondary")
            btn.setFixedHeight(32)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        self._all_items = []

    def set_items(self, items):
        """items: [(display_name, description, payload)]"""
        self._all_items = items
        self._render(items)

    def set_query(self, text):
        """外部驱动过滤（内联模式）"""
        self.search.blockSignals(True)
        self.search.setText(text)
        self.search.blockSignals(False)
        self._filter(text)

    def _render(self, items):
        self.list_widget.clear()
        for name, desc, payload in items:
            text = name if not desc else f"{name}\n{desc[:48]}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, payload)
            item.setToolTip(desc or name)
            self.list_widget.addItem(item)

    def _filter(self, keyword):
        keyword = keyword.strip().lower()
        filtered = [it for it in self._all_items
                    if keyword in it[0].lower() or keyword in it[1].lower()]
        self._render(filtered)

    def _on_clicked(self, item):
        self.item_picked.emit(item.data(Qt.ItemDataRole.UserRole))
        self.close()

    def show_near(self, widget: QWidget, align_right: bool = False):
        """在控件上方弹出，align_right 时与控件右对齐并限制在屏幕内"""
        from PyQt6.QtWidgets import QApplication
        pos = widget.mapToGlobal(QPoint(0, 0))
        if align_right:
            x = pos.x() + widget.width() - self.width()
        else:
            x = pos.x()
        screen = QApplication.primaryScreen().availableGeometry()
        x = max(screen.left() + 8, min(x, screen.right() - self.width() - 8))
        y = max(screen.top() + 8, pos.y() - self.height() - 8)
        self.move(x, y)
        self.show()


# ==================== 历史面板 ====================

class ChatHistoryPanel(QFrame):
    """AI 助手左侧历史面板:搜索 + 列表 + 新建/删除"""

    session_picked = pyqtSignal(str)        # session_id
    session_deleted = pyqtSignal(str)       # session_id
    new_chat_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("history_panel")
        self.setMinimumWidth(200)
        self.setMaximumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(8)

        # 顶部:标题 + 新建按钮
        top_row = QHBoxLayout()
        title = QLabel("历史对话")
        title.setObjectName("panel_title")
        title.setMinimumHeight(30)
        top_row.addWidget(title)
        top_row.addStretch()

        new_btn = QPushButton("新建")
        new_btn.setObjectName("btn_secondary")
        new_btn.setFixedHeight(28)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.new_chat_requested.emit)
        top_row.addWidget(new_btn)
        layout.addLayout(top_row)

        # 搜索框
        self.search = QLineEdit()
        self.search.setObjectName("input")
        self.search.setPlaceholderText("搜索对话...")
        self.search.textChanged.connect(self._on_search)
        layout.addWidget(self.search)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("history_list")
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget, 1)

        self._manager = get_chat_history_manager()
        self._all_sessions: list[ChatSession] = []
        self.refresh()

    # ---------- 数据 ----------

    def refresh(self):
        """从磁盘重新加载"""
        self._all_sessions = self._manager.list_sessions()
        self._render(self._all_sessions)

    def _render(self, sessions):
        self.list_widget.clear()
        for s in sessions:
            try:
                dt = s.updated_at[:16].replace("T", " ")
            except Exception:
                dt = ""
            item = QListWidgetItem(f"{s.title}\n{dt}")
            item.setData(Qt.ItemDataRole.UserRole, s.id)
            item.setToolTip(s.title)
            self.list_widget.addItem(item)

    def _on_search(self, keyword):
        keyword = keyword.strip()
        if not keyword:
            self._render(self._all_sessions)
        else:
            self._render(self._manager.search(keyword))

    # ---------- 事件 ----------

    def _on_item_clicked(self, item):
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id:
            self.session_picked.emit(session_id)

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item is None:
            return
        session_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        load_act = menu.addAction("打开")
        del_act = menu.addAction("删除")
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == load_act:
            self.session_picked.emit(session_id)
        elif action == del_act:
            ret = QMessageBox.question(
                self, "删除对话", "确定删除这条历史对话?此操作不可恢复。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                if self._manager.delete_session(session_id):
                    self.session_deleted.emit(session_id)
                    self.refresh()

    def select_session(self, session_id: str):
        """外部调用,高亮某个 session"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                self.list_widget.setCurrentItem(item)
                return


# ==================== 聊天页 ====================

class ChatPage(QWidget):
    """AI助手对话页面（WorkBuddy风格）"""

    goto_settings = pyqtSignal()
    goto_extensions = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self._worker = None
        self._current_ai_row = None
        self.active_expert = None
        self.active_pack = None           # SkillPack
        self.active_connectors = set()
        # 本地工具组开关（默认开启，方便用户直接讨论小说）
        self.project_tools_enabled = True    # 项目数据（书籍/章节/角色/钩子/事件/邮箱）
        self.outline_tools_enabled = True    # 大纲库
        self.attachments = []
        self.current_provider = "deepseek"
        self.current_model = ""
        self._inline_panel = None
        self._inline_symbol = None
        self._updating_text = False
        self._has_messages = False
        self._current_session: ChatSession | None = None
        self._history_manager = get_chat_history_manager()
        self._init_ui()
        self._load_model_choice()
        self.setAcceptDrops(True)
        self._check_vector_availability()

    def _check_vector_availability(self):
        """ChromaDB 未安装时给出可见提示（RAG 记忆增强不可用）"""
        try:
            from src.core.vector_store import CHROMADB_AVAILABLE
        except Exception:
            return
        if not CHROMADB_AVAILABLE:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(300, lambda: self._add_system_note(
                "提示：向量检索库 ChromaDB 未安装，AI 助手的记忆增强（RAG）暂不可用。"
                "安装 chromadb（pip install chromadb）后重启应用即可启用。"))

    def shutdown(self):
        """关闭应用前终止后台生成线程（短超时等待）"""
        for attr in ("_worker", "_workflow_worker"):
            worker = getattr(self, attr, None)
            if worker is not None and worker.isRunning():
                worker.requestInterruption()
                worker.wait(2000)

    # ---------- UI ----------

    def _init_ui(self):
        # 顶层:水平 splitter(左历史 / 右聊天)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧:历史面板
        self.history_panel = ChatHistoryPanel()
        self.history_panel.session_picked.connect(self._on_history_picked)
        self.history_panel.session_deleted.connect(self._on_history_deleted)
        self.history_panel.new_chat_requested.connect(self._new_chat_guard)
        splitter.addWidget(self.history_panel)

        # 右侧:聊天主区
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.title_label = QLabel("AI 助手")
        self.title_label.setObjectName("page_title")
        header.addWidget(self.title_label)
        header.addStretch()

        self.history_btn = QPushButton()
        self.history_btn.setObjectName("btn_secondary")
        self.history_btn.setFixedHeight(34)
        self.history_btn.setToolTip("历史对话")
        self.history_btn.clicked.connect(lambda: self._show_history_panel(self.history_btn))
        header.addWidget(self.history_btn)

        self.clear_btn = QPushButton("新对话")
        self.clear_btn.setObjectName("btn_secondary")
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.clicked.connect(self._new_chat_guard)
        header.addWidget(self.clear_btn)

        # 书籍选择器（选中后自动注入上下文）
        header.addWidget(QLabel("  讨论书籍:"))
        self.book_combo = QComboBox()
        self.book_combo.setMinimumWidth(160)
        self.book_combo.setFixedHeight(34)
        self.book_combo.currentTextChanged.connect(self._on_book_changed)
        header.addWidget(self.book_combo)
        self._refresh_books()

        layout.addLayout(header)

        # ==================== 消息滚动区（有对话时显示） ====================
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.chat_container)
        layout.addWidget(self.scroll, 1)
        self.scroll.hide()

        # ==================== 输入块（chips + 输入区，可在居中/底部间移动） ====================
        self.input_block = QWidget()
        block_layout = QVBoxLayout(self.input_block)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(6)

        self.chips_row = QHBoxLayout()
        self.chips_row.setSpacing(6)
        self.chips_row.addStretch()
        block_layout.addLayout(self.chips_row)

        self.input_area = self._create_input_area()
        block_layout.addWidget(self.input_area)

        # ==================== 空状态（输入框居中放大） ====================
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(16)

        empty_layout.addStretch(2)

        greeting = QLabel("我是你的网文创作伙伴")
        greeting.setObjectName("chat_empty")
        greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.greeting_label = greeting
        empty_layout.addWidget(greeting)

        sub = QLabel("@ 引用文件，/ 调用技能与指令，+ 选择专家与连接器")
        sub.setObjectName("chat_hint")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label = sub
        empty_layout.addWidget(sub)

        empty_layout.addSpacing(8)

        # 居中大输入框（限宽720，水平居中）
        center_row = QHBoxLayout()
        center_row.addStretch(1)
        self.center_holder = QWidget()
        self.center_holder.setFixedWidth(720)
        center_v = QVBoxLayout(self.center_holder)
        center_v.setContentsMargins(0, 0, 0, 0)
        center_row.addWidget(self.center_holder, 0)
        center_row.addStretch(1)
        empty_layout.addLayout(center_row)

        empty_layout.addSpacing(8)

        chips_row = QHBoxLayout()
        chips_row.addStretch()
        quick_actions = [
            ("写黄金三章", "用黄金三章的方法，帮我规划新书开篇。我的创意是："),
            ("去AI味", "帮我去掉这段文字的AI味：\n"),
            ("设计爽点", "帮我设计一个爽点打脸桥段。当前剧情："),
            ("写大纲", "帮我设计小说大纲。我的创意是："),
        ]
        for text, prompt in quick_actions:
            chip = QPushButton(text)
            chip.setObjectName("btn_secondary")
            chip.setFixedHeight(36)
            chip.clicked.connect(lambda _, p=prompt: self._fill_input(p))
            chips_row.addWidget(chip)
        chips_row.addStretch()
        empty_layout.addLayout(chips_row)

        empty_layout.addStretch(3)
        layout.addWidget(self.empty_widget, 1)

        # ==================== 底部输入容器（有对话时显示） ====================
        self.bottom_holder = QWidget()
        bottom_v = QVBoxLayout(self.bottom_holder)
        bottom_v.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.bottom_holder, 0)
        self.bottom_holder.hide()

        # 装配 splitter
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 980])
        main_layout.addWidget(splitter)

        # 初始：输入块放居中
        self._update_input_placement()
        self.refresh_icons()

    def _create_input_area(self) -> QFrame:
        """创建输入区（+、输入框、模型选择、发送）"""
        input_area = QFrame()
        input_area.setObjectName("chat_input_area")
        input_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        self.plus_btn = QPushButton()
        self.plus_btn.setObjectName("btn_secondary")
        self.plus_btn.setFixedSize(36, 36)
        self.plus_btn.setToolTip("添加文件 / 专家 / 技能 / 连接器")
        self.plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plus_btn.clicked.connect(lambda: self._show_plus_menu(self.plus_btn))
        input_layout.addWidget(self.plus_btn)

        self.input = ChatInput()
        self.input.setObjectName("chat_input")
        self.input.setPlaceholderText("今天帮你想做些什么？ @ 引用文件，/ 调用技能与指令")
        self.input.setFixedHeight(72)
        self.input.submitted.connect(self._send)
        self.input.escaped.connect(self._close_inline_panel)
        self.input.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.input)

        self.model_btn = QPushButton("选择模型")
        self.model_btn.setObjectName("btn_secondary")
        self.model_btn.setFixedHeight(36)
        self.model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_btn.clicked.connect(lambda: self._show_model_panel(self.model_btn))
        input_layout.addWidget(self.model_btn, 0, Qt.AlignmentFlag.AlignBottom)

        self.send_btn = QPushButton()
        self.send_btn.setObjectName("btn_send")
        self.send_btn.setFixedSize(40, 36)
        self.send_btn.setToolTip("发送")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._send)
        input_layout.addWidget(self.send_btn, 0, Qt.AlignmentFlag.AlignBottom)

        return input_area

    def _update_input_placement(self):
        """根据是否有消息，切换输入块位置（居中大框 <-> 底部）"""
        if self._has_messages:
            # 移到底部
            self.center_holder.layout().removeWidget(self.input_block)
            self.bottom_holder.layout().addWidget(self.input_block)
            self.input.setFixedHeight(48)
            self.empty_widget.hide()
            self.scroll.show()
            self.bottom_holder.show()
        else:
            # 移到居中大框
            self.bottom_holder.layout().removeWidget(self.input_block)
            self.center_holder.layout().addWidget(self.input_block)
            self.input.setFixedHeight(96)
            self.scroll.hide()
            self.bottom_holder.hide()
            self.empty_widget.show()

    def refresh_icons(self):
        """按当前主题刷新图标"""
        try:
            from src.data.settings_manager import get_settings_manager
            theme = get_settings_manager().get_setting("general", "theme", "light")
        except Exception:
            theme = "light"
        color = theme_icon_color(theme)
        self.plus_btn.setIcon(get_icon("plus", color, 16))
        self.plus_btn.setIconSize(QSize(16, 16))
        self.send_btn.setIcon(get_icon("send", "#ffffff", 16))
        self.send_btn.setIconSize(QSize(16, 16))
        self.model_btn.setIcon(get_icon("model", color, 14))
        self.model_btn.setIconSize(QSize(14, 14))
        self.history_btn.setIcon(get_icon("history", color, 16))
        self.history_btn.setIconSize(QSize(16, 16))

    # ---------- 书籍选择器 ----------

    def _refresh_books(self):
        """从写作空间加载书籍列表"""
        self.book_combo.blockSignals(True)
        current = self.book_combo.currentText()
        self.book_combo.clear()
        self.book_combo.addItem("（不指定书籍）")
        try:
            from src.data.writing_space import get_writing_space
            for n in get_writing_space().list_tree():
                if n.get("type") == "book":
                    self.book_combo.addItem(n["name"])
        except Exception:
            pass
        idx = self.book_combo.findText(current)
        if idx >= 0:
            self.book_combo.setCurrentIndex(idx)
        self.book_combo.blockSignals(False)
        self._selected_book = self.book_combo.currentText() if self.book_combo.currentIndex() > 0 else ""

    def _on_book_changed(self, text):
        """书籍选择变更"""
        self._selected_book = text if text != "（不指定书籍）" else ""

    def _build_book_context(self) -> str:
        """构建选中书籍的上下文（注入 system prompt）"""
        book = getattr(self, "_selected_book", "")
        if not book:
            return ""
        parts = [f"\n# 当前讨论书籍：《{book}》\n"]
        try:
            from src.data.writing_space import get_writing_space
            ws = get_writing_space()
            tree = ws.list_tree()
            for node in tree:
                if node.get("type") != "book" or node["name"] != book:
                    continue
                # 章节列表
                chapters = []
                for child in node.get("children", []):
                    if child.get("type") == "chapter":
                        chapters.append(child["name"])
                    elif child.get("type") == "folder":
                        for sub in child.get("children", []):
                            if sub.get("type") == "chapter":
                                chapters.append(sub["name"])
                if chapters:
                    parts.append(f"章节目录：{', '.join(chapters[:30])}")
                    # 最近一章预览
                    last_ch = None
                    for child in reversed(node.get("children", [])):
                        if child.get("type") == "chapter":
                            last_ch = child
                            break
                        elif child.get("type") == "folder":
                            for sub in reversed(child.get("children", [])):
                                if sub.get("type") == "chapter":
                                    last_ch = sub
                                    break
                    if last_ch:
                        content = ws.read(last_ch["path"])
                        parts.append(f"最近章节《{last_ch['name']}》前200字：{content[:200]}")
                break
        except Exception:
            pass
        # 角色摘要
        try:
            from src.data.character_store import CharacterStore
            chars = CharacterStore(book=book).load_all()
            if chars:
                char_lines = []
                for c in chars[:10]:
                    name = c.get("name", "?")
                    role = c.get("role_type", "")
                    personality = c.get("personality", "")[:20]
                    char_lines.append(f"  - {name}（{role}，{personality}）")
                parts.append("角色：\n" + "\n".join(char_lines))
        except Exception:
            pass
        return "\n".join(parts)

    def retranslate(self):
        """语言切换后刷新界面文字"""
        from ..i18n import tr
        self.title_label.setText(tr("chat.title"))
        self.clear_btn.setText(tr("chat.new"))
        self.greeting_label.setText(tr("chat.greeting"))
        self.subtitle_label.setText(tr("chat.subtitle"))
        self.input.setPlaceholderText(tr("chat.placeholder"))
        self.plus_btn.setToolTip(f"{tr('chat.add_file')} / {tr('chat.expert')} / {tr('chat.skill')} / {tr('chat.connector')}")
        self.send_btn.setToolTip(tr("chat.send"))

    # ---------- 历史会话 ----------
    def _show_history_panel(self, anchor):
        """历史会话面板（与左侧历史面板同一存储）"""
        from src.data.chat_history_manager import get_chat_history_manager
        import time as time_module

        sessions = get_chat_history_manager().list_sessions()
        if not sessions:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "历史对话", "暂无历史对话记录")
            return

        items = []
        for s in sessions:
            try:
                dt = time_module.strptime(s.updated_at[:16].replace("T", " "), "%Y-%m-%d %H:%M")
                time_str = time_module.strftime("%m-%d %H:%M", dt)
            except Exception:
                time_str = s.updated_at[:16]
            items.append((s.title, f"{time_str} · {len(s.messages)}条消息 · {s.model}", s.id))

        panel = SelectorPanel(self)
        panel.set_items(items)
        panel.item_picked.connect(self._load_history_session)
        panel.show_near(anchor)

    
    def _load_history_session(self, session_id):
        """载入历史会话"""
        from src.data.chat_history_manager import get_chat_history_manager
        session = get_chat_history_manager().load_session(session_id)
        if not session:
            return

        self._clear_chat()
        self._session_id = session_id
        self.messages = list(session.messages)
        for msg in self.messages:
            role = msg.get("role", "user")
            if role in ("user", "assistant"):
                self._add_message_row(role, msg.get("content", ""))

    def _save_current_session(self):
        """自动保存当前会话"""
        if not self.messages:
            return
        from src.data.chat_session_store import get_chat_session_store
        self._session_id = get_chat_session_store().save_session(
            self.messages, self.current_provider, self.current_model,
            session_id=getattr(self, "_session_id", None))

    def _fill_input(self, text):
        self.input.setPlainText(text)
        self.input.setFocus()
        cursor = self.input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.input.setTextCursor(cursor)

    # ---------- 模型选择 ----------

    def _load_model_choice(self):
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()
        self.current_provider = sm.get_setting("generation", "default_provider", "deepseek")
        self.current_model = sm.get_setting("generation", "default_model", "glm-4-flash")
        self._update_model_btn()

    def _update_model_btn(self):
        self.model_btn.setText(self.current_model or "选择模型")

    def _show_model_panel(self, anchor):
        """模型选择面板：只列出已配置密钥（自带API）的提供商，只显示模型名"""
        from src.data.settings_manager import get_settings_manager
        from src.utils.llm import has_api_key
        sm = get_settings_manager()

        items = []
        for p in sm.list_providers():
            if not has_api_key(p["id"]):
                continue  # 测试阶段：只保留自带API的提供商
            for m in p["models"]:
                items.append((m["name"], "", (p["id"], m["id"])))

        # 一个都没配密钥时列出全部，引导用户去配置
        if not items:
            for p in sm.list_providers():
                for m in p["models"]:
                    items.append((m["name"], "", (p["id"], m["id"])))

        panel = SelectorPanel(self, footer_buttons=[
            ("配置自定义模型", self._goto_settings_from_panel),
        ])
        panel.set_items(items)
        panel.item_picked.connect(self._on_model_picked)
        panel.show_near(anchor, align_right=True)

    def _goto_settings_from_panel(self):
        self.goto_settings.emit()

    def _on_model_picked(self, payload):
        provider, model = payload
        self.current_provider = provider
        self.current_model = model
        self._update_model_btn()
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()
        sm.set_setting("generation", "default_provider", provider)
        sm.set_setting("generation", "default_model", model)

    # ---------- "+" 菜单 ----------

    def _show_plus_menu(self, anchor):
        menu = QMenu(self)

        file_menu = menu.addMenu("添加文件")
        file_menu.addAction("本地文件...", self._add_attachment)
        file_menu.addAction("从大纲库选择...", lambda: self._show_library_panel(anchor, "outline"))
        file_menu.addAction("从提示词库选择...", lambda: self._show_library_panel(anchor, "prompt"))

        expert_menu = menu.addMenu("专家")
        from src.agents.experts import get_expert
        for name in self._recent_experts():
            expert = get_expert(name)
            if expert:
                expert_menu.addAction(expert.name,
                                      lambda _, e=expert: self._on_expert_picked(e))
        expert_menu.addSeparator()
        expert_menu.addAction("更多专家...", lambda: self._show_expert_panel(anchor))

        menu.addAction("技能", lambda: self._show_skill_panel(anchor))
        menu.addAction("连接器", lambda: self._show_connector_panel(anchor))
        menu.addSeparator()
        # 本地工具组开关（独立勾选，默认关闭）
        project_act = menu.addAction(
            ("✓ " if self.project_tools_enabled else "") + "项目数据工具（读写我的书/人物/悬念/邮箱）")
        project_act.triggered.connect(lambda: self._toggle_tool_group("project"))
        outline_act = menu.addAction(
            ("✓ " if self.outline_tools_enabled else "") + "大纲库工具（读写大纲）")
        outline_act.triggered.connect(lambda: self._toggle_tool_group("outline"))

        from ..i18n import tr as _tr
        menu.addSeparator()
        menu.addAction(_tr("chat.workflow"), lambda: self._start_workflow())

        pos = anchor.mapToGlobal(QPoint(0, 0))
        menu.exec(QPoint(pos.x(), pos.y() - menu.sizeHint().height() - 8))

    def _recent_experts(self):
        from src.data.settings_manager import get_settings_manager
        raw = get_settings_manager().get_setting("chat", "recent_experts", "")
        try:
            recents = json.loads(raw) if raw else []
        except json.JSONDecodeError:
            recents = []
        if not recents:
            recents = ["大纲师", "码字工", "督察", "评论家", "读者模拟"]
        return recents[:5]

    def _push_recent_expert(self, name):
        from src.data.settings_manager import get_settings_manager
        recents = [n for n in self._recent_experts() if n != name]
        recents.insert(0, name)
        get_settings_manager().set_setting("chat", "recent_experts", json.dumps(recents[:5], ensure_ascii=False))

    def _show_expert_panel(self, anchor):
        from src.agents.experts import list_experts
        panel = SelectorPanel(self)
        panel.set_items([(e.name, e.description, e) for e in list_experts()])
        panel.item_picked.connect(self._on_expert_picked)
        panel.show_near(anchor)

    def _show_skill_panel(self, anchor):
        from src.skills import get_skill_manager
        packs = get_skill_manager().list_packs()
        panel = SelectorPanel(self, footer_buttons=[
            ("管理技能", self._open_extensions),
        ])
        panel.set_items([
            (p.name, f"{p.description}（整包注入）", p) for p in packs
        ])
        panel.item_picked.connect(self._on_pack_picked)
        panel.show_near(anchor)

    def _show_connector_panel(self, anchor):
        from src.mcp import get_mcp_manager
        manager = get_mcp_manager()
        status = manager.server_status()
        panel = SelectorPanel(self, footer_buttons=[
            ("管理连接器", self._open_extensions),
        ])
        items = []
        for cfg in manager.list_server_configs():
            state = status.get(cfg.name, "")
            mark = "[已选] " if cfg.name in self.active_connectors else ""
            items.append((f"{mark}{cfg.name}", f"{cfg.description} [{state}]", cfg.name))
        panel.set_items(items)
        panel.item_picked.connect(self._on_connector_picked)
        panel.show_near(anchor)

    def _show_library_panel(self, anchor, kind):
        panel = SelectorPanel(self)
        if kind == "outline":
            from src.data.outline_library import get_outline_library
            works = get_outline_library().list_works()
            panel.set_items([(w.title, f"大纲库 / {w.category}", ("outline", w)) for w in works])
        else:
            from src.data.prompt_library import get_prompt_library
            templates = get_prompt_library().list_templates()
            panel.set_items([(t.name, f"提示词 / {t.pack}", ("prompt", t)) for t in templates])
        panel.item_picked.connect(self._on_library_picked)
        panel.show_near(anchor)

    def _open_extensions(self):
        self.goto_extensions.emit()

    # ---------- @ / 内联触发 ----------

    def _on_text_changed(self):
        if self._updating_text:
            return
        cursor = self.input.textCursor()
        text = self.input.toPlainText()[:cursor.position()]
        match = re.search(r"([@/])([^\s@/]*)$", text)
        if match:
            symbol, query = match.group(1), match.group(2)
            self._show_inline_panel(symbol, query)
        else:
            self._close_inline_panel()
        # 正则自动检测 《书名》 并切换书籍选择器
        book_match = re.search(r"《([^》]+)》", text)
        if book_match:
            book_name = book_match.group(1)
            for i in range(self.book_combo.count()):
                if self.book_combo.itemText(i) == book_name:
                    if self.book_combo.currentIndex() != i:
                        self.book_combo.setCurrentIndex(i)
                    break

    def _show_inline_panel(self, symbol, query):
        if self._inline_panel is None or self._inline_symbol != symbol:
            self._close_inline_panel()
            self._inline_symbol = symbol
            self._inline_panel = SelectorPanel(self, passive=True)

            if symbol == "@":
                items = [("本地文件...", "浏览本地文件", ("local", None))]
                from src.data.outline_library import get_outline_library
                for w in get_outline_library().list_works():
                    items.append((w.title, f"大纲库 / {w.category}", ("outline", w)))
                from src.data.prompt_library import get_prompt_library
                for t in get_prompt_library().list_templates():
                    items.append((t.name, f"提示词 / {t.pack}", ("prompt", t)))
                self._inline_panel.set_items(items)
                self._inline_panel.item_picked.connect(self._on_inline_at_picked)
            else:
                from src.skills import get_skill_manager
                items = [(p.name, f"{p.description}（整包注入）", p)
                         for p in get_skill_manager().list_packs()]
                self._inline_panel.set_items(items)
                self._inline_panel.item_picked.connect(self._on_inline_pack_picked)

            self._inline_panel.show_near(self.input)
        else:
            self._inline_panel.set_query(query)
            if not self._inline_panel.isVisible():
                self._inline_panel.show_near(self.input)

    def _close_inline_panel(self):
        if self._inline_panel is not None:
            self._inline_panel.close()
            self._inline_panel = None
            self._inline_symbol = None

    def _consume_inline_token(self):
        """删除输入框中的 @xxx 或 /xxx 触发文本"""
        from PyQt6.QtGui import QTextCursor
        self._updating_text = True
        cursor = self.input.textCursor()
        text = self.input.toPlainText()
        pos = cursor.position()
        match = re.search(r"([@/])([^\s@/]*)$", text[:pos])
        if match:
            start = pos - (match.end() - match.start())
            cursor.setPosition(start)
            cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        self._updating_text = False

    def _on_inline_at_picked(self, payload):
        self._consume_inline_token()
        self._close_inline_panel()
        kind = payload[0]
        if kind == "local":
            self._add_attachment()
        else:
            self._on_library_picked(payload)

    def _on_inline_pack_picked(self, pack):
        self._consume_inline_token()
        self._close_inline_panel()
        self._on_pack_picked(pack)

    # ---------- 选择结果 ----------

    def _on_expert_picked(self, expert):
        self.active_expert = expert
        self._push_recent_expert(expert.name)
        self._add_system_note(f"已选择专家：{expert.name}")
        self._refresh_chips()

    def _on_pack_picked(self, pack):
        self.active_pack = pack
        self._add_system_note(f"已加载技能包：{pack.name}（整包强制注入）")
        self._refresh_chips()

    def _on_connector_picked(self, name):
        if name in self.active_connectors:
            self.active_connectors.discard(name)
        else:
            self.active_connectors.add(name)
        self._refresh_chips()

    def _toggle_tool_group(self, group: str):
        """切换本地工具组启用状态（默认关闭）"""
        if group == "project":
            self.project_tools_enabled = not self.project_tools_enabled
            state = "已启用" if self.project_tools_enabled else "已关闭"
            self._add_system_note(f"项目数据工具{state}（读写我的书/人物/悬念/事件/邮箱投递）")
        elif group == "outline":
            self.outline_tools_enabled = not self.outline_tools_enabled
            state = "已启用" if self.outline_tools_enabled else "已关闭"
            self._add_system_note(f"大纲库工具{state}（读写大纲库）")
        self._refresh_chips()

    def _start_workflow(self):
        """全流程生成：创意→大纲→章节，后台执行"""
        from PyQt6.QtWidgets import QInputDialog

        idea, ok = QInputDialog.getText(self, "全流程生成", "请输入一句话创意（例如：废柴少年觉醒隐藏血脉）：")
        if not ok or not idea.strip():
            return

        from src.utils.llm import has_api_key
        if not has_api_key():
            self._add_message_row("assistant", "尚未配置 API 密钥。请前往「系统设置 → LLM」填入密钥后即可全流程生成。")
            return

        chapters, ok = QInputDialog.getInt(self, "全流程生成", "生成章节数：", 3, 1, 10, 1)
        if not ok:
            return

        self._add_message_row("user", f"全流程生成：《{idea.strip()[:20]}...》（{chapters}章）")
        self._add_message_row("assistant", f"正在运行全流程：创意 → 大纲 → 逐章撰写（{chapters}章）→ 审核 → 错别字修正，请稍候...")

        self._workflow_worker = WorkflowWorker(idea.strip(), chapters, self)
        self._workflow_worker.done.connect(self._on_workflow_done)
        self._workflow_worker.failed.connect(self._on_workflow_failed)
        self._workflow_worker.start()

    def _on_workflow_done(self, novel_text, summary):
        preview = novel_text[:4000]
        if len(novel_text) > 4000:
            preview += f"\n\n...（共{len(novel_text)}字，已保存到写作空间）"
        self._add_message_row("assistant", f"{summary}\n\n{preview}")

    def _on_workflow_failed(self, error):
        self._add_message_row("assistant", f"全流程生成失败：{error}")

    def _on_library_picked(self, payload):
        kind, obj = payload
        if kind == "outline":
            from src.data.outline_library import get_outline_library
            content = get_outline_library().read_work(obj, "outline")
            self.attachments.append((f"{obj.title}_大纲.md", content))
        else:
            from src.data.prompt_library import get_prompt_library
            content = get_prompt_library().read_text(obj)
            self.attachments.append((f"{obj.name}.txt", content))
        self._refresh_chips()

    def _add_attachment(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "文本文件 (*.txt *.md *.docx);;所有文件 (*)")
        for path in paths:
            text = self._read_attachment(path)
            if text:
                self.attachments.append((os.path.basename(path), text))
        if paths:
            self._refresh_chips()

    @staticmethod
    def _read_attachment(path):
        if path.lower().endswith(".docx"):
            try:
                import docx
                doc = docx.Document(path)
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception:
                return ""
        for encoding in ("utf-8", "gbk"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, OSError):
                continue
        return ""

    # ---------- 拖拽 ----------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                text = self._read_attachment(path)
                if text:
                    self.attachments.append((os.path.basename(path), text))
        self._refresh_chips()

    # ---------- chips ----------

    def _refresh_chips(self):
        while self.chips_row.count() > 1:
            item = self.chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        chips = []
        if self.active_expert:
            chips.append((f"专家:{self.active_expert.name}", self._clear_expert))
        if self.active_pack:
            chips.append((f"技能包:{self.active_pack.name}", self._clear_pack))
        for name in sorted(self.active_connectors):
            chips.append((f"连接器:{name}", lambda n=name: self._on_connector_picked(n)))
        for fname, _text in self.attachments:
            chips.append((fname, lambda f=fname: self._remove_attachment(f)))

        for text, remover in chips:
            chip = QPushButton(f"{text} ×")
            chip.setObjectName("btn_secondary")
            chip.setFixedHeight(28)
            chip.clicked.connect(remover)
            self.chips_row.insertWidget(self.chips_row.count() - 1, chip)

    def _clear_expert(self):
        self.active_expert = None
        self._refresh_chips()

    def _clear_pack(self):
        self.active_pack = None
        self._refresh_chips()

    def _remove_attachment(self, fname):
        self.attachments = [(f, t) for f, t in self.attachments if f != fname]
        self._refresh_chips()

    # ---------- 消息 ----------

    def _add_message_row(self, role: str, text: str = "") -> MessageRow:
        if not self._has_messages:
            self._has_messages = True
            self._update_input_placement()
        row = MessageRow(role, text)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        self._scroll_to_bottom()
        return row

    def _add_system_note(self, text: str):
        self._add_message_row("system", text)

    def _scroll_to_bottom(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _build_system_prompt(self, pack) -> str:
        parts = ["你是「AI写作助手」的专业中文网文创作伙伴，熟悉起点/番茄/晋江等平台的网文生态。"]
        # 注入选中书籍的上下文（角色、章节、大纲）
        book_ctx = self._build_book_context()
        if book_ctx:
            parts.append(book_ctx)
        # 仅在用户启用了工具组时才声明工具能力，且严格限制调用条件
        enabled_groups = []
        if self.project_tools_enabled:
            enabled_groups.append("项目数据（书籍/章节/角色/悬念/事件/邮箱投递）")
        if self.outline_tools_enabled:
            enabled_groups.append("大纲库")
        if enabled_groups:
            parts.append(
                "你当前启用了以下本地工具：" + "、".join(enabled_groups) + "。\n"
                "严格规则（必须遵守）：\n"
                "1. 仅当用户**明确要求**查看/读取/总结/讨论 你的大纲、你的书、你的章节、你的角色、你的悬念、你的故事线，或明确要求投递到邮箱时，才调用对应工具读取真实数据。\n"
                "2. 普通创作讨论（如'帮我想一个西幻世界观''讨论剧情走向'）**禁止**调用任何本地工具，直接用你的创作知识回答。\n"
                "3. 用户要求保存大纲/人物/伏笔/事件/章节或投递邮箱时，调用对应工具执行并确认结果。"
            )
        if self.active_expert:
            parts.append(self.active_expert.system_prompt)
        if pack:
            from src.skills import get_skill_manager
            content = get_skill_manager().get_pack_content(pack)
            parts.append(f"\n# 当前激活技能包（必须严格遵循其全部指令）\n\n{content}")
        # 注入共享记忆（项目级上下文）
        try:
            from src.memory.shared_memory import get_shared_memory
            sm = get_shared_memory()
            knowledge = sm.get_shared_knowledge("chat")
            if knowledge:
                mem_lines = [f"- {m.content[:200]}" for m in knowledge[:8]]
                parts.append("\n# 项目共享记忆（供参考，可能有陈旧信息）\n" + "\n".join(mem_lines))
        except Exception:
            pass
        return "\n\n".join(parts)

    def _send(self):
        text = self.input.toPlainText().strip()
        if not text or self._worker is not None:
            return

        from src.utils.llm import has_api_key
        if not has_api_key(self.current_provider):
            self._add_message_row("assistant",
                "尚未配置该提供商的 API 密钥。请前往「系统设置 → LLM」填入你自己的密钥后即可开始对话。")
            self.goto_settings.emit()
            return

        full_text = text
        if self.attachments:
            blocks = [f"【附件：{fname}】\n{content[:15000]}" for fname, content in self.attachments]
            full_text = "\n\n".join(blocks) + "\n\n【用户消息】\n" + text
            self.attachments.clear()

        # 技能包：显式选择优先，否则关键词自动匹配（一次性）
        pack = self.active_pack
        if pack is None:
            from src.skills import get_skill_manager
            matched = get_skill_manager().match_pack(text)
            if matched:
                pack = matched
                self._add_system_note(f"已自动匹配技能包：{pack.name}（仅本次）")

        self.input.clear()
        self._add_message_row("user", text)
        self.messages.append({"role": "user", "content": full_text})
        self._refresh_chips()

        self._current_ai_row = self._add_message_row("assistant", "…")
        self.send_btn.setEnabled(False)
        self.input.setEnabled(False)

        system_prompt = self._build_system_prompt(pack)
        connectors = sorted(self.active_connectors)

        # 收集启用的本地工具组（默认无）
        tool_groups = []
        if self.project_tools_enabled:
            tool_groups.append("project")
        if self.outline_tools_enabled:
            tool_groups.append("outline")

        self._worker = ChatWorker(self.current_provider, self.current_model,
                                  list(self.messages), system_prompt, connectors,
                                  tool_groups if tool_groups else None, self)
        self._worker.chunk.connect(self._on_chunk)
        self._worker.failed.connect(self._on_failed)
        self._worker.tool_event.connect(self._add_system_note)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_chunk(self, piece: str):
        if self._current_ai_row is None:
            return
        if self._current_ai_row.text() == "…":
            self._current_ai_row.set_text(piece)
        else:
            self._current_ai_row.append_text(piece)
        self._scroll_to_bottom()

    def _on_failed(self, error: str):
        if self._current_ai_row is not None:
            self._current_ai_row.set_text(f"调用失败：{error}")

    def _on_finished(self):
        if self._current_ai_row is not None:
            text = self._current_ai_row.text()
            if text and not text.startswith("调用失败") and text != "…":
                self.messages.append({"role": "assistant", "content": text})
        self._current_ai_row = None
        self._worker = None
        self.send_btn.setEnabled(True)
        self.input.setEnabled(True)
        self.input.setFocus()
        self._save_current_session()
        self._save_current_session()

    def _new_chat_guard(self):
        """新建对话前检查历史会话数上限（超过则禁止新建，引导删除）"""
        try:
            from src.data.settings_manager import get_settings_manager
            limit = int(get_settings_manager().get_setting(
                "storage", "chat_history_limit", 50))
            count = len(self._history_manager.list_sessions(limit=5000))
        except Exception:
            limit, count = 50, 0
        if count >= limit:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "历史对话已达上限",
                f"历史对话已达上限（{limit} 条）。\n请先在左侧历史面板删除部分对话后，再新建对话。")
            return
        self._clear_chat()

    def _clear_chat(self):
        self.messages.clear()
        self._session_id = None
        self.active_pack = None
        self.active_expert = None
        self.attachments.clear()
        self._refresh_chips()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._has_messages = False
        self._update_input_placement()

    # ---------- 历史对话 ----------

    def _save_current_session(self):
        """把当前 messages 保存到历史(有 user 消息才保存)"""
        if not any(m.get("role") == "user" for m in self.messages):
            return
        if self._current_session is None:
            self._current_session = self._history_manager.create_session(
                provider=self.current_provider, model=self.current_model)
        self._current_session.messages = list(self.messages)
        self._current_session.provider = self.current_provider
        self._current_session.model = self.current_model
        self._history_manager.save_session(self._current_session)
        self.history_panel.refresh()
        self.history_panel.select_session(self._current_session.id)

    def _on_history_picked(self, session_id: str):
        """加载一条历史对话"""
        session = self._history_manager.load_session(session_id)
        if session is None:
            return
        # 先清空当前(不触发保存,因为已自动保存)
        self._clear_chat()
        self._current_session = session
        self.messages = list(session.messages)
        # 恢复 UI
        for msg in self.messages:
            role = msg.get("role", "")
            if role in ("user", "assistant"):
                self._add_message_row(role, msg.get("content", ""))
        self.history_panel.select_session(session_id)

    def _on_history_deleted(self, session_id: str):
        """历史被删除:如果是当前 session 则清空"""
        if self._current_session and self._current_session.id == session_id:
            self._clear_chat()
