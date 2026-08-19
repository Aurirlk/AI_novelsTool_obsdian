"""
写作工作台（知乎/Markdown编辑器风格）
图标工具栏（标准Markdown格式） + 标题/正文编辑区 + 右侧创作助手面板
支持文内插入图片
"""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QTextEdit, QSplitter, QPushButton, QLineEdit, QDialog,
    QMessageBox, QScrollArea, QFrame, QSizePolicy, QFileDialog,
    QMenu, QTreeWidget, QTreeWidgetItem, QInputDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QTextCursor, QTextImageFormat

from ..professional_components import ProfessionalTextEdit as ModernTextEdit
from ..icons import get_icon, theme_icon_color
from ..i18n import tr


class AssistWorker(QThread):
    """创作助手后台调用（部分任务走真实智能体）"""

    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, task_prompt, content, task_key=None, parent=None):
        super().__init__(parent)
        self.task_prompt = task_prompt
        self.content = content
        self.task_key = task_key

    def run(self):
        try:
            if self.task_key == "title":
                result = self._agent_title()
            elif self.task_key == "intro":
                result = self._agent_intro()
            else:
                from src.utils.llm import LLMClient
                client = LLMClient()
                result = client.chat(self.content, system_prompt=self.task_prompt)
            self.done.emit(result)
        except Exception as e:
            self.failed.emit(str(e))

    def _agent_title(self) -> str:
        """智能标题：走运营智能体的钩子标题生成"""
        from src.agents.polisher_agent import PolisherAgent
        agent = PolisherAgent()
        return agent.generate_hook_title(self.content)

    def _agent_intro(self) -> str:
        """提取导语：走运营智能体的章节摘要生成"""
        from src.models.schemas import Chapter
        from src.agents.polisher_agent import PolisherAgent
        agent = PolisherAgent()
        chapter = Chapter(number=1, title="章节", content=self.content, word_count=len(self.content))
        return agent.generate_chapter_summary(chapter)


class MemoryExtractWorker(QThread):
    """章节记忆提取后台任务：保存后自动提取角色/钩子/事件变更"""

    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, chapter_text, book_name="", chapter_num=0, parent=None):
        super().__init__(parent)
        self.chapter_text = chapter_text
        self.book_name = book_name
        self.chapter_num = chapter_num

    def run(self):
        try:
            from src.data.memory_extractor import extract_memory_changes
            changes = extract_memory_changes(self.chapter_text, self.book_name, self.chapter_num)
            self.done.emit(changes)
        except Exception as e:
            self.failed.emit(str(e))


class AssistCard(QFrame):
    """创作助手功能卡片"""

    clicked = pyqtSignal(str)

    def __init__(self, name, description, task_key, parent=None):
        super().__init__(parent)
        self.task_key = task_key
        self.setObjectName("assist_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # 不设固定最小高度：高度完全由内容决定，避免文字上下被裁切
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        name_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout.addWidget(name_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #8e8e8e; font-size: 12px; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.task_key)
        super().mousePressEvent(event)


ASSIST_TASKS = {
    "critique": ("assist.critique", "assist.critique_desc", "你是网文一致性督察。对以下文本做一致性检查（时空/性格/能力体系/称谓/伏笔/逻辑），输出问题清单（严重/一般/建议，附原文引用）和修改建议。"),
    "title": ("assist.title", "assist.title_desc", "你是网文运营专家。根据以下内容起5个章节标题（悬念法/冲突法/数字法混搭），每个附一句起名理由。"),
    "intro": ("assist.intro", "assist.intro_desc", "你是网文运营专家。根据以下内容写一段书籍/章节导语（黄金三行，80字内），要求有钩子、有冲突、有期待感。"),
    "polish": ("assist.polish", "assist.polish_desc", "你是严谨的文字校对员。检查以下文本的错别字、误用字词、明显笔误（如「戴着/带着」「拼劲全力/拼尽全力」、人名前后不一致），逐处列出原文和修改建议。只允许修正错别字和笔误，严禁润色、改写、扩写、优化任何句子表达。输出格式：每行一条【原文 → 修改】+ 原因。没有错别字则输出「未发现错别字」。"),
    "expand": ("assist.expand", "assist.expand_desc", "你是网文扩写专家。对以下文本进行扩写，丰富细节描写、心理活动、环境渲染，保持原文情节走向不变。"),
    "continue": ("assist.continue", "assist.continue_desc", "你是网文续写专家。根据以下文本的走向和风格，自然续写500-1000字。保持人称、语气、节奏一致。"),
}


class TrashDialog(QDialog):
    """回收站对话框：列出已删除内容，支持恢复/清空"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("writer.trash_title"))
        self.setMinimumSize(480, 360)

        from src.data.writing_space import get_writing_space
        self.ws = get_writing_space()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel(tr("writer.trash_hint"))
        hint.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.trash_list = QListWidget()
        self.trash_list.setObjectName("input")
        layout.addWidget(self.trash_list, 1)

        btn_row = QHBoxLayout()
        restore_btn = QPushButton(tr("writer.trash_restore"))
        restore_btn.setObjectName("btn_primary")
        restore_btn.clicked.connect(self._restore_selected)
        btn_row.addWidget(restore_btn)

        empty_btn = QPushButton(tr("writer.trash_empty"))
        empty_btn.setObjectName("btn_danger")
        empty_btn.clicked.connect(self._empty_trash)
        btn_row.addWidget(empty_btn)

        btn_row.addStretch()
        close_btn = QPushButton(tr("writer.trash_close"))
        close_btn.setObjectName("btn_secondary")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._items = []
        self._reload()

    def _reload(self):
        """刷新回收站列表"""
        self.trash_list.clear()
        self._items = self.ws.list_trash()
        if not self._items:
            self.trash_list.addItem(tr("writer.trash_empty_list"))
            return
        for item in self._items:
            origin = item["origin"] or tr("writer.trash_unknown_origin")
            label = f"{item['name']}  ({tr('writer.trash_deleted_at')} {item['deleted_at']})\n{origin}"
            self.trash_list.addItem(label)

    def _restore_selected(self):
        """恢复选中条目；目标冲突时询问覆盖"""
        row = self.trash_list.currentRow()
        if row < 0 or row >= len(self._items):
            QMessageBox.information(self, tr("writer.trash_need_select"), tr("writer.trash_need_select"))
            return
        entry = self._items[row]["entry"]
        success, msg = self.ws.restore(entry)
        if not success and msg == "conflict":
            reply = QMessageBox.question(
                self, tr("writer.trash_conflict"), tr("writer.trash_conflict_msg"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            success, msg = self.ws.restore(entry, overwrite=True)
        if success:
            QMessageBox.information(self, tr("writer.trash_restored"), f"{tr('writer.trash_restored')}：\n{msg}")
            self._reload()
        else:
            QMessageBox.warning(self, tr("writer.trash_restore_failed"), str(msg))

    def _empty_trash(self):
        reply = QMessageBox.question(
            self, tr("writer.trash_confirm_empty"), tr("writer.trash_confirm_empty_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        count = self.ws.empty_trash()
        QMessageBox.information(self, tr("writer.trash_emptied"),
                                tr("writer.trash_emptied_msg").format(count=count))
        self._reload()


class WriterPage(QWidget):
    """写作工作台"""

    open_character_requested = pyqtSignal(str)  # 双链跳转：角色名

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._tool_buttons = []
        self._current_book = None   # 当前打开的书籍
        self._init_ui()
        self.refresh_icons()

    def shutdown(self):
        """关闭应用前终止运行中的创作助手线程（短超时等待）"""
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(2000)

    # ==================== UI ====================

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 先创建编辑控件（工具栏按钮需要绑定其方法）
        self.title_input = QLineEdit()
        self.title_input.setObjectName("input")
        self.title_input.setPlaceholderText("请输入章节标题")
        self.title_input.setFixedHeight(44)

        self.editor = ModernTextEdit("请输入正文，支持 Markdown 格式与插图...")
        self.editor.textChanged.connect(self._update_word_count)
        # Ctrl+点击 [[链接]] 双链跳转
        self.editor.installEventFilter(self)

        # ---------- 顶部Markdown工具栏 ----------
        toolbar = QFrame()
        toolbar.setObjectName("card")
        toolbar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 6, 12, 6)
        tb.setSpacing(2)

        def sep():
            s = QFrame()
            s.setFrameShape(QFrame.Shape.VLine)
            tb.addSpacing(6)
            tb.addWidget(s)
            tb.addSpacing(6)

        # 历史
        self._add_tool(tb, "undo", "撤销 (Ctrl+Z)", self.editor.undo)
        self._add_tool(tb, "redo", "重做 (Ctrl+Y)", self.editor.redo)
        sep()

        # 文字格式
        self._add_tool(tb, "bold", "加粗 **text**", lambda: self.wrap_selection("**"))
        self._add_tool(tb, "italic", "斜体 *text*", lambda: self.wrap_selection("*"))
        self._add_tool(tb, "strike", "删除线 ~~text~~", lambda: self.wrap_selection("~~"))
        self._add_tool(tb, "underline", "下划线 <u>text</u>", lambda: self.wrap_selection("<u>", "</u>"))
        sep()

        # 标题（下拉选 H1/H2/H3）
        heading_btn = QPushButton()
        heading_btn.setObjectName("tool_btn")
        heading_btn.setFixedSize(32, 32)
        heading_btn.setToolTip("标题")
        heading_menu = QMenu(self)
        for level in (1, 2, 3):
            heading_menu.addAction(f"H{level}  {'#' * level} 标题",
                                   lambda _, lv=level: self.insert_line_prefix("#" * lv + " "))
        heading_btn.setMenu(heading_menu)
        tb.addWidget(heading_btn)
        self._tool_buttons.append((heading_btn, "heading"))

        self._add_tool(tb, "list", "无序列表 - item", lambda: self.insert_line_prefix("- "))
        self._add_tool(tb, "quote", "引用 > text", lambda: self.insert_line_prefix("> "))
        self._add_tool(tb, "code", "行内代码 `code`", lambda: self.wrap_selection("`"))
        self._add_tool(tb, "table", "插入表格", self.insert_table)
        self._add_tool(tb, "link", "插入链接 [文字](url)", self.insert_link)
        self._add_tool(tb, "divider", "分割线 ---", lambda: self.insert_at_cursor("\n\n---\n\n"))
        sep()

        # 图片与文件
        self._add_tool(tb, "image", "插入图片", self.insert_image)
        self._add_tool(tb, "import", "导入文本文件", self.import_file)
        self._add_tool(tb, "save", "保存草稿 (Ctrl+S)", self.save_draft)

        tb.addStretch()

        self.word_count_label = QLabel("字数: 0")
        self.word_count_label.setObjectName("chat_hint")
        tb.addWidget(self.word_count_label)

        layout.addWidget(toolbar)

        # ---------- 主体 ----------
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左：章节文件树（Obsidian风格）
        tree_panel = QWidget()
        tree_layout = QVBoxLayout(tree_panel)
        tree_layout.setContentsMargins(8, 16, 4, 16)
        tree_layout.setSpacing(6)

        tree_title_row = QHBoxLayout()
        tree_title = QLabel(tr("writer.workspace"))
        tree_title.setObjectName("section_title")
        tree_title_row.addWidget(tree_title)
        tree_title_row.addStretch()
        # VSCode 风格图标操作栏（替代底部文字按钮）
        for icon_name, tip_key, handler in [
                ("new_doc", "writer.new_chapter", self._tree_new_chapter),
                ("folder", "writer.new_folder", self._tree_new_folder),
                ("writer", "writer.rename", self._tree_rename),
                ("clear", "writer.delete", self._tree_delete),
                ("undo", "writer.refresh_tree", self._refresh_tree)]:
            btn = QPushButton()
            btn.setObjectName("tool_btn")
            btn.setFixedSize(26, 26)
            btn.setToolTip(tr(tip_key))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(handler)
            tree_title_row.addWidget(btn)
            self._tool_buttons.append((btn, icon_name))
        tree_layout.addLayout(tree_title_row)

        # 当前书籍栏
        book_bar = QHBoxLayout()
        self.book_label = QLabel(tr("writer.no_book"))
        self.book_label.setObjectName("section_title")
        self.book_label.setStyleSheet("font-size: 13px; color: #4c7ef3;")
        book_bar.addWidget(self.book_label)
        book_bar.addStretch()
        open_book_btn = QPushButton(tr("writer.open_book"))
        open_book_btn.setObjectName("btn_secondary")
        open_book_btn.setFixedHeight(28)
        open_book_btn.clicked.connect(self._open_book_dialog)
        book_bar.addWidget(open_book_btn)
        tree_layout.addLayout(book_bar)

        # 全局搜索框（Obsidian 式全文搜索，300ms 防抖）
        from PyQt6.QtWidgets import QListWidget
        from PyQt6.QtCore import QTimer
        self.search_input = QLineEdit()
        self.search_input.setObjectName("input")
        self.search_input.setPlaceholderText(tr("writer.search_placeholder"))
        self.search_input.setFixedHeight(30)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._on_search)
        self.search_input.textChanged.connect(lambda _t: self._search_timer.start())
        tree_layout.addWidget(self.search_input)

        self.search_results = QListWidget()
        self.search_results.setObjectName("input")
        self.search_results.setVisible(False)
        self.search_results.itemDoubleClicked.connect(self._on_search_result_open)
        tree_layout.addWidget(self.search_results)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.currentItemChanged.connect(self._on_tree_select)
        # 右键菜单（Obsidian/VSCode 风格）：新建章节、重命名、删除等
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        tree_layout.addWidget(self.file_tree)

        splitter.addWidget(tree_panel)

        # 中：编辑区
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(12, 16, 12, 16)
        editor_layout.setSpacing(8)

        editor_layout.addWidget(self.title_input)
        editor_layout.addWidget(self.editor)

        splitter.addWidget(editor_panel)

        # 右：创作助手（滚动区防挤压）
        assist_scroll = QScrollArea()
        assist_scroll.setWidgetResizable(True)
        assist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        assist_scroll.setFixedWidth(340)

        assist_panel = QWidget()
        assist_layout = QVBoxLayout(assist_panel)
        assist_layout.setContentsMargins(12, 16, 20, 16)
        assist_layout.setSpacing(10)

        assist_title = QLabel("创作助手")
        assist_title.setObjectName("section_title")
        assist_layout.addWidget(assist_title)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(8)
        for i, key in enumerate(ASSIST_TASKS):
            name_key, desc_key, _prompt = ASSIST_TASKS[key]
            card = AssistCard(tr(name_key), tr(desc_key), key)
            card.clicked.connect(self._run_assist)
            cards_grid.addWidget(card, i // 2, i % 2)
        assist_layout.addLayout(cards_grid)

        output_title = QLabel(tr("writer.assist_output"))
        output_title.setObjectName("section_title")
        assist_layout.addWidget(output_title)

        self.assist_output = ModernTextEdit("选择上方功能，助手将基于当前正文生成内容...")
        self.assist_output.setReadOnly(True)
        self.assist_output.setMinimumHeight(220)
        assist_layout.addWidget(self.assist_output)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("插入到正文")
        apply_btn.setObjectName("btn_primary")
        apply_btn.setFixedHeight(34)
        apply_btn.clicked.connect(self._apply_output)
        btn_row.addWidget(apply_btn)

        copy_btn = QPushButton("复制")
        copy_btn.setObjectName("btn_secondary")
        copy_btn.setFixedHeight(34)
        copy_btn.clicked.connect(self._copy_output)
        btn_row.addWidget(copy_btn)
        assist_layout.addLayout(btn_row)
        assist_layout.addStretch()

        assist_scroll.setWidget(assist_panel)
        splitter.addWidget(assist_scroll)
        splitter.setSizes([200, 680, 320])

        layout.addWidget(splitter)

        self.current_file = None
        self._cleanup_trash()
        self._refresh_tree()

    def _add_tool(self, tb, icon_name, tooltip, handler):
        """添加工具栏图标按钮"""
        btn = QPushButton()
        btn.setObjectName("tool_btn")
        btn.setFixedSize(32, 32)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(handler)
        tb.addWidget(btn)
        self._tool_buttons.append((btn, icon_name))

    def refresh_icons(self):
        """按当前主题刷新工具栏图标"""
        try:
            from src.data.settings_manager import get_settings_manager
            theme = get_settings_manager().get_setting("general", "theme", "light")
        except Exception:
            theme = "light"
        color = theme_icon_color(theme)
        for btn, icon_name in self._tool_buttons:
            btn.setIcon(get_icon(icon_name, color, 16))
            btn.setIconSize(QSize(16, 16))

    # ==================== 章节文件树 ====================

    _TREE_ICONS = {"book": "book", "folder": "project", "chapter": "outline"}

    def _refresh_tree(self):
        """刷新文件树（只显示当前打开的书籍）"""
        from src.data.writing_space import get_writing_space
        try:
            from src.data.settings_manager import get_settings_manager
            theme = get_settings_manager().get_setting("general", "theme", "light")
        except Exception:
            theme = "light"
        color = theme_icon_color(theme)

        self.file_tree.clear()
        if not self._current_book:
            self.book_label.setText("未打开书籍")
            return

        tree = get_writing_space().list_tree()
        book_node = None
        for node in tree:
            if node.get("type") == "book" and node["name"] == self._current_book:
                book_node = node
                break
        if book_node is None:
            self.book_label.setText("未打开书籍")
            self._current_book = None
            return

        self.book_label.setText(self._current_book)
        # 书作为顶层节点（展开），卷/章节为子级
        item = self._make_tree_item(book_node, color)
        self.file_tree.addTopLevelItem(item)
        self._fill_tree_children(item, book_node, color)
        item.setExpanded(True)

    def open_book(self, book_name: str):
        """打开指定书籍（外部调用：书籍管理页）"""
        self._current_book = book_name
        self.current_file = None
        self._opened_mtime = None
        self._refresh_tree()
        # 清空编辑器
        self.title_input.setText("")
        self.editor.setPlainText("")

    def _open_book_dialog(self):
        """打开书：列出写作空间所有书籍供选择"""
        from src.data.writing_space import get_writing_space
        from PyQt6.QtWidgets import QInputDialog
        try:
            tree = get_writing_space().list_tree()
            books = [n["name"] for n in tree if n.get("type") == "book"]
        except Exception:
            books = []
        if not books:
            QMessageBox.information(self, "提示", "写作空间没有书籍，请先到「书籍管理」创建")
            return
        name, ok = QInputDialog.getItem(self, "打开书", "选择书籍：", books, 0, False)
        if ok and name:
            self.open_book(name)

    def open_current_book(self):
        """重新加载当前书（书籍管理页新增书后调用）"""

    def open_chapter_path(self, path: str) -> bool:
        """按章节文件路径打开（故事时间线/关系图谱跳转用）；成功返回 True"""
        if not path or not os.path.isfile(path):
            return False
        try:
            from src.data.writing_space import get_writing_space
            content = get_writing_space().read(path)
        except Exception:
            content = ""
        self.current_file = path
        self._opened_mtime = self._file_mtime(path)
        label = os.path.splitext(os.path.basename(path))[0]
        self.title_input.setText(label)
        lines = content.splitlines()
        if lines and lines[0].startswith("# "):
            content = "\n".join(lines[1:]).lstrip("\n")
        self.editor.setPlainText(content)
        return True

    def _make_tree_item(self, node, color):
        item = QTreeWidgetItem([node["name"]])
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        item.setIcon(0, get_icon(self._TREE_ICONS.get(node["type"], "outline"), color, 14))
        return item

    def _fill_tree_children(self, parent_item, parent_node, color):
        for child in parent_node.get("children", []):
            child_item = self._make_tree_item(child, color)
            parent_item.addChild(child_item)
            self._fill_tree_children(child_item, child, color)

    def _on_search(self, keyword=None):
        """全局搜索：输入防抖后切换文件树/结果列表"""
        from src.data.search_index import search_all

        if keyword is None:
            keyword = self.search_input.text()
        keyword = keyword.strip()
        if not keyword:
            self.search_results.setVisible(False)
            self.file_tree.setVisible(True)
            return

        results = search_all(keyword)
        self.search_results.clear()
        for r in results:
            item = QListWidgetItem(f"{r['title']}\n{r['preview'][:60]}")
            item.setData(Qt.ItemDataRole.UserRole, r)
            item.setToolTip(r["preview"])
            self.search_results.addItem(item)
        if not results:
            self.search_results.addItem("无结果")
        self.search_results.setVisible(True)
        self.file_tree.setVisible(False)

    def _on_search_result_open(self, item):
        """打开搜索结果：章节/大纲跳转到对应内容"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        rtype = data.get("type")
        path = data.get("path", "")

        if rtype in ("chapter", "outline") and path:
            content = ""
            for enc in ("utf-8", "gbk"):
                try:
                    with open(path, "r", encoding=enc) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, OSError):
                    continue
            label = os.path.basename(path)[:-3]
            self.title_input.setText((f"大纲：{label}" if rtype == "outline" else label))
            self.editor.setPlainText(content)
            # 同步 current_file：搜索结果打开的章节，保存时写回正确文件（防止写错位置）
            if rtype == "chapter":
                self.current_file = path
                self._opened_mtime = self._file_mtime(path)
                self._check_overdue_hooks()
            self._search_result_path = path
        else:
            # 角色/悬念/事件：只显示预览
            self.title_input.setText(data.get("title", ""))
            self.editor.setPlainText(data.get("preview", ""))

    def _on_tree_select(self, current, _previous):
        """点击章节文件时载入编辑器"""
        if current is None:
            return
        node = current.data(0, Qt.ItemDataRole.UserRole)
        if node["type"] != "chapter":
            return
        from src.data.writing_space import get_writing_space
        content = get_writing_space().read(node["path"])
        self.current_file = node["path"]
        self._opened_mtime = self._file_mtime(node["path"])
        self.title_input.setText(node["name"])
        # 去掉文件里的标题行，只留正文
        lines = content.splitlines()
        if lines and lines[0].startswith("# "):
            content = "\n".join(lines[1:]).lstrip("\n")
        self.editor.setPlainText(content)
        self._check_overdue_hooks()

    @staticmethod
    def _file_mtime(path):
        """获取文件修改时间（不存在返回 None）"""
        try:
            return os.path.getmtime(path)
        except OSError:
            return None

    def _check_external_change(self):
        """检测当前章节是否被外部修改（Obsidian 等）；变化则提示重新加载"""
        if not self.current_file or getattr(self, "_opened_mtime", None) is None:
            return
        cur = self._file_mtime(self.current_file)
        if cur is None or cur == self._opened_mtime:
            return
        reply = QMessageBox.question(
            self, "文件已被外部修改",
            "当前章节文件已被其他程序修改（如 Obsidian）。\n"
            "选择「是」重新加载最新内容；选择「否」保留当前编辑（保存时将覆盖外部修改）。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from src.data.writing_space import get_writing_space
            content = get_writing_space().read(self.current_file)
            lines = content.splitlines()
            if lines and lines[0].startswith("# "):
                content = "\n".join(lines[1:]).lstrip("\n")
            self.editor.setPlainText(content)
            self._opened_mtime = self._file_mtime(self.current_file)

    def showEvent(self, event):
        """切回写作工作台时检测外部修改"""
        super().showEvent(event)
        self._check_external_change()

    def _selected_node(self):
        item = self.file_tree.currentItem()
        return item.data(0, Qt.ItemDataRole.UserRole) if item else None

    def _on_tree_context_menu(self, pos):
        """文件树右键菜单（Obsidian/VSCode 风格）

        - 空白处：新建书 / 刷新
        - 书或分卷：新建章节 / 新建卷 / 重命名 / 删除 / 复制路径
        - 章节：重命名 / 删除 / 复制路径
        """
        item = self.file_tree.itemAt(pos)
        node = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        # 右键点击时同步当前选中项，保证 _selected_node() 取到正确节点
        if item is not None:
            self.file_tree.setCurrentItem(item)
        try:
            from src.data.settings_manager import get_settings_manager
            theme = get_settings_manager().get_setting("general", "theme", "light")
        except Exception:
            theme = "light"
        color = theme_icon_color(theme)

        menu = QMenu(self)
        if node is None:
            # 空白处右键：新建书 / 刷新
            menu.addAction(get_icon("book", color, 14), tr("writer.new_book"), self._tree_new_book)
            menu.addSeparator()
            menu.addAction(get_icon("undo", color, 14), tr("writer.refresh"), self._refresh_tree)
        else:
            if node["type"] in ("book", "folder"):
                menu.addAction(get_icon("new_doc", color, 14), tr("writer.new_chapter"), self._tree_new_chapter)
                menu.addAction(get_icon("folder", color, 14), tr("writer.new_folder"), self._tree_new_folder)
                menu.addSeparator()
            menu.addAction(get_icon("writer", color, 14), tr("writer.rename"), self._tree_rename)
            menu.addAction(get_icon("clear", color, 14), tr("writer.delete"), self._tree_delete)
            menu.addSeparator()
            menu.addAction(tr("writer.copy_path"), lambda: self._copy_node_path(node))
        menu.addSeparator()
        menu.addAction(get_icon("clock", color, 14), tr("writer.trash"), self._open_trash)
        menu.exec(self.file_tree.viewport().mapToGlobal(pos))

    def _copy_node_path(self, node):
        """复制节点路径到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        path = node.get("path", "")
        if path:
            QApplication.clipboard().setText(path)

    def _tree_new_book(self):
        name, ok = QInputDialog.getText(self, "新建书", "书名:")
        if not ok or not name.strip():
            return
        from src.data.writing_space import get_writing_space
        success, msg = get_writing_space().create_book(name)
        if not success:
            QMessageBox.warning(self, "失败", msg)
            return
        # 创建后自动打开该书
        self._current_book = name
        self._refresh_tree()

    def _tree_new_folder(self):
        node = self._selected_node()
        if not node or node["type"] not in ("book", "folder"):
            if getattr(self, "_current_book", None):
                QMessageBox.warning(self, "提示", "请先在左侧文件树中选中一本书或一个分卷目录")
            else:
                QMessageBox.warning(self, "提示", "请先点击右上角「打开书籍」选择一本书，再新建卷/目录")
            return
        name, ok = QInputDialog.getText(self, "新建卷/目录", "名称（如：第一卷）:")
        if not ok or not name.strip():
            return
        from src.data.writing_space import get_writing_space
        success, msg = get_writing_space().create_folder(node["path"], name)
        if not success:
            QMessageBox.warning(self, "失败", msg)
        self._refresh_tree()

    def _tree_new_chapter(self):
        node = self._selected_node()
        if not node or node["type"] not in ("book", "folder"):
            if getattr(self, "_current_book", None):
                QMessageBox.warning(self, "提示", "请先在左侧文件树中选中一本书或一个分卷目录")
            else:
                QMessageBox.warning(self, "提示", "请先点击右上角「打开书籍」选择一本书，再新建章节")
            return
        title, ok = QInputDialog.getText(self, "新建章节", "章节名（如：第1章 穿越）:")
        if not ok or not title.strip():
            return
        from src.data.writing_space import get_writing_space
        success, msg = get_writing_space().create_chapter(node["path"], title)
        if not success:
            QMessageBox.warning(self, "失败", msg)
        self._refresh_tree()

    def _tree_rename(self):
        node = self._selected_node()
        if not node:
            QMessageBox.warning(self, "提示", "请先在左侧文件树中选中要重命名的书籍/分卷/章节")
            return
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=node["name"])
        if not ok or not new_name.strip():
            return
        from src.data.writing_space import get_writing_space
        success, msg = get_writing_space().rename(node["path"], new_name)
        if not success:
            QMessageBox.warning(self, "失败", msg)
        else:
            if self.current_file == node["path"]:
                self.current_file = msg
        self._refresh_tree()

    def _tree_delete(self):
        node = self._selected_node()
        if not node:
            QMessageBox.warning(self, "提示", "请先在左侧文件树中选中要删除的书籍/分卷/章节")
            return
        msg_extra = ("（含其下所有内容）" if node["type"] != "chapter" else "")
        reply = QMessageBox.question(
            self, tr("writer.delete"),
            f"{tr('writer.delete_confirm').format(name=node['name'])}"
            + (tr("writer.delete_confirm_children") if msg_extra else "")
            + "\n" + tr("writer.delete_confirm_trash"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        from src.data.writing_space import get_writing_space
        success, msg = get_writing_space().delete(node["path"])
        if success and self.current_file == node["path"]:
            self.current_file = None
            self.editor.clear()
            self.title_input.clear()
        if not success:
            QMessageBox.warning(self, tr("writer.delete_failed"), msg)
        self._refresh_tree()

    # ==================== 回收站 ====================

    def _open_trash(self):
        """打开回收站对话框（恢复/清空）"""
        dialog = TrashDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_tree()

    def _cleanup_trash(self):
        """启动时清理过期回收站条目（保留30天）"""
        try:
            from src.data.writing_space import get_writing_space
            get_writing_space().cleanup_trash()
        except Exception:
            pass

    # ==================== Markdown 操作 ====================

    def wrap_selection(self, prefix, suffix=None):
        """用标记包裹选中文本"""
        suffix = suffix if suffix is not None else prefix
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=len(suffix))
            self.editor.setTextCursor(cursor)

    def insert_line_prefix(self, prefix):
        """行首插入前缀（标题/列表/引用）"""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText(prefix)

    def insert_at_cursor(self, text):
        self.editor.textCursor().insertText(text)

    def insert_table(self):
        template = "\n| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n|  |  |  |\n"
        self.insert_at_cursor(template)

    def insert_link(self):
        cursor = self.editor.textCursor()
        selected = cursor.selectedText() or "链接文字"
        cursor.insertText(f"[{selected}](https://)")

    def insert_image(self):
        """文内插入图片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "插入图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp)")
        if not path:
            return

        from PyQt6.QtGui import QImage
        image = QImage(path)
        if image.isNull():
            QMessageBox.warning(self, "失败", "无法读取该图片")
            return

        # 限制显示宽度
        max_width = min(600, max(300, self.editor.width() - 80))
        fmt = QTextImageFormat()
        fmt.setName(path)
        if image.width() > max_width:
            fmt.setWidth(max_width)
            fmt.setHeight(int(image.height() * max_width / image.width()))

        self.editor.textCursor().insertImage(fmt)
        self.editor.textCursor().insertText("\n")

    # ==================== 文件 ====================

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入文本", "", "文本文件 (*.txt *.md *.docx);;所有文件 (*)")
        if not path:
            return
        text = self._read_file(path)
        if text:
            self.editor.setPlainText(text)

    @staticmethod
    def _read_file(path):
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

    def save_draft(self):
        self._check_external_change()
        title = self.title_input.text().strip() or "未命名章节"
        content = f"# {title}\n\n{self.editor.toPlainText()}"

        # 已打开章节文件时直接写回
        if self.current_file:
            from src.data.writing_space import get_writing_space
            get_writing_space().save(self.current_file, content)
            self._opened_mtime = self._file_mtime(self.current_file)
            self._trigger_memory_extract()
            QMessageBox.information(self, "已保存", f"已写回：\n{self.current_file}")
            return

        # 否则提示先新建章节
        reply = QMessageBox.question(
            self, "保存", "当前没有打开的章节文件。\n是否在写作空间中新建一个章节保存？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._tree_new_chapter()
            if self.file_tree.currentItem():
                node = self._selected_node()
                if node and node["type"] == "chapter":
                    from src.data.writing_space import get_writing_space
                    get_writing_space().save(node["path"], content)
                    self.current_file = node["path"]
                    self._refresh_tree()
                    self._trigger_memory_extract()
                    QMessageBox.information(self, "已保存", f"已保存到：\n{node['path']}")

    # ==================== 记忆自动更新 ====================

    @staticmethod
    def _chapter_num_from_path(path):
        """从章节文件路径解析章节号（支持「第12章」「12.md」）；解析不到返回0"""
        if not path:
            return 0
        import re
        stem = os.path.splitext(os.path.basename(path))[0]
        m = re.search(r"第\s*(\d+)\s*章", stem)
        if m:
            return int(m.group(1))
        if stem.isdigit():
            return int(stem)
        return 0

    def _trigger_memory_extract(self):
        """保存章节后：按设置自动提取记忆变更（auto直接写 / confirm弹确认 / off关闭）"""
        try:
            from src.data.settings_manager import get_settings_manager
            mode = get_settings_manager().get_setting("storage", "memory_auto_update", "confirm")
        except Exception:
            mode = "confirm"
        if mode == "off":
            return
        content = self.editor.toPlainText().strip()
        if not content:
            return
        book = getattr(self, "_current_book", "") or ""
        chapter_num = self._chapter_num_from_path(self.current_file or "")

        self._memory_worker = MemoryExtractWorker(content, book, chapter_num, self)
        self._memory_worker.done.connect(lambda ch: self._on_memory_extract_done(ch, mode, book, chapter_num))
        self._memory_worker.failed.connect(lambda e: print(f"[记忆提取] 失败: {e}"))
        self._memory_worker.start()

    def _on_memory_extract_done(self, changes, mode, book, chapter_num):
        """记忆提取完成：auto直接入库，confirm弹确认框"""
        try:
            from src.data.memory_extractor import apply_to_stores, summarize_changes
            if not changes or not changes.get("ok"):
                return
            if mode == "auto":
                stats = apply_to_stores(changes, book, chapter_num)
                total = sum(stats.values())
                if total > 0:
                    self.assist_output.setPlainText(
                        f"✅ 记忆已自动更新：角色{stats['characters']}、新钩子{stats['new_hooks']}、"
                        f"回收{stats['resolved_hooks']}、事件{stats['events']}")
            else:  # confirm
                summary = summarize_changes(changes)
                if "未提取到" in summary:
                    return
                reply = QMessageBox.question(
                    self, "记忆变更确认",
                    f"本章检测到以下记忆变更：\n\n{summary}\n\n是否写入角色/钩子/事件库？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    stats = apply_to_stores(changes, book, chapter_num)
                    self.assist_output.setPlainText(
                        f"✅ 记忆已更新：角色{stats['characters']}、新钩子{stats['new_hooks']}、"
                        f"回收{stats['resolved_hooks']}、事件{stats['events']}")
        except Exception as e:
            print(f"[记忆提取] 应用失败: {e}")

    # ==================== 伏笔超期提醒 ====================

    def _check_overdue_hooks(self):
        """warn模式：当前书存在超过预期回收章节的未回收钩子时弹出提醒"""
        try:
            from src.data.settings_manager import get_settings_manager
            mode = get_settings_manager().get_setting("storage", "hook_overdue_reminder", "warn")
        except Exception:
            mode = "warn"
        if mode != "warn":
            return
        book = getattr(self, "_current_book", "") or ""
        chapter_num = self._chapter_num_from_path(self.current_file or "")
        if not book or chapter_num <= 0:
            return
        try:
            from src.data.hook_store import HookStore
            overdue = HookStore(book=book).get_overdue(chapter_num, book)
        except Exception:
            return
        if overdue:
            lines = [f"· {h.get('content', '')[:40]}（预期第{h.get('expected_chapter', 0)}章回收）"
                     for h in overdue[:5]]
            more = f"\n……还有{len(overdue) - 5}个" if len(overdue) > 5 else ""
            QMessageBox.information(
                self, "伏笔超期提醒",
                f"已写到第{chapter_num}章，以下伏笔超过预期回收章节仍未回收：\n\n"
                + "\n".join(lines) + more
                + "\n\n可在「悬念管理」中调整预期回收章节或标记已回收。")

    # ==================== 创作助手 ====================

    def eventFilter(self, obj, event):
        """拦截编辑器鼠标事件：Ctrl+点击 [[角色名]] 双链跳转"""
        if obj is self.editor and event.type() == event.Type.MouseButtonPress:
            from PyQt6.QtGui import QMouseEvent
            if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton \
                    and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                name = self._link_at_cursor(event.position().toPoint())
                if name:
                    self.open_character_requested.emit(name)
                    return True
        return super().eventFilter(obj, event)

    def _link_at_cursor(self, pos):
        """解析光标位置的 [[链接]] 文本，返回链接名（无则空串）"""
        try:
            cursor = self.editor.cursorForPosition(pos)
            text = self.editor.toPlainText()
            # 找到光标所在的 [[...]]
            for start in range(cursor.position(), -1, -1):
                if start == 0 or text[start - 1] == "[" and text[start - 2:start] == "[[":
                    break
            if start > 0 and text[start - 2:start] == "[[":
                end = text.find("]]", start)
                if end > start:
                    return text[start:end].strip()
        except Exception:
            pass
        return ""

    def _run_assist(self, task_key):
        content = self.editor.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请先在正文中输入内容")
            return

        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            content = cursor.selectedText()

        _name, _desc, prompt = ASSIST_TASKS[task_key]
        self.assist_output.setPlainText("生成中...")

        self._worker = AssistWorker(prompt, content, task_key, self)
        self._worker.done.connect(self.assist_output.setPlainText)
        self._worker.failed.connect(lambda e: self.assist_output.setPlainText(f"调用失败：{e}"))
        self._worker.start()

    def _apply_output(self):
        text = self.assist_output.toPlainText()
        if not text or text.startswith(("生成中", "调用失败", "选择上方")):
            return
        self.editor.textCursor().insertText(text)

    def _copy_output(self):
        from PyQt6.QtWidgets import QApplication
        text = self.assist_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _update_word_count(self):
        self.word_count_label.setText(f"字数: {len(self.editor.toPlainText())}")
