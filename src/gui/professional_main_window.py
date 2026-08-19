"""
企业级主窗口
专业、成熟、高效的UI设计
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QSplitter, QStatusBar, QMenuBar, QMenu, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QAction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .professional_theme import ProfessionalTheme
from .professional_components import (
    ProfessionalButton, ProfessionalLabel, ProfessionalCard,
    ProfessionalDivider
)
from .icons import get_icon, theme_icon_color
from .i18n import tr, load_from_settings as i18n_load
from .page_constants import Page
from .pages import (
    HomePage, WriterPage, OutlinePage,
    CharacterPage, HookPage, EventPage, BookPage,
    ExportPage, HistoryPage, SharedMemoryPage, SettingsPage,
    ChatPage, ExtensionsPage, BookLibraryPage
)
from .pages.critic_page import CriticPage


class ProfessionalMainWindow(QMainWindow):
    """企业级主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI写作助手 - 专业版")
        self.setMinimumSize(1200, 800)

        self.theme_name = self._load_theme_preference()
        i18n_load()

        # 初始化UI
        self._init_ui()
        self._init_status_bar()
        self._apply_theme()

        # 切换到首页
        self._switch_page(Page.HOME)

    def _load_theme_preference(self) -> str:
        """读取主题偏好（默认浅色）"""
        try:
            from src.data.settings_manager import get_settings_manager
            return get_settings_manager().get_setting("general", "theme", "light")
        except Exception:
            return "light"
    
    def _init_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 主内容区
        self.content = QStackedWidget()
        main_layout.addWidget(self.content)
        
        # 创建所有页面
        self._create_pages()
    
    def _create_sidebar(self) -> QWidget:
        """创建侧边栏：分组可折叠 + 导航区可滚动 + 底部设置固定"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(6)

        # Logo区域（纯文字）
        logo_text = QLabel("AI写作助手")
        logo_text.setObjectName("logo")
        layout.addWidget(logo_text)
        self._sidebar_logo = logo_text

        # ---- 导航区（可滚动） ----
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        nav_container = QWidget()
        self.nav_container_layout = QVBoxLayout(nav_container)
        self.nav_container_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_container_layout.setSpacing(2)

        self.nav_buttons = []
        self._nav_groups = []  # [(header_btn, [item_btns], expanded)]

        # 分组定义：(组名key, [(文本key, 页面索引, 图标名)])
        P = Page
        groups = [
            ("sidebar.workspace", [
                ("nav.home", P.HOME, "home"),
                ("nav.ai_chat", P.CHAT, "chat"),
                ("nav.books", P.BOOKS, "book-open"),
                ("nav.writer", P.WRITER, "writer"),
                ("nav.outline", P.OUTLINE, "outline"),
                ("nav.character", P.CHARACTER, "character"),
                ("nav.hook", P.HOOK, "hook"),
                ("nav.event", P.EVENT, "event"),
                ("nav.critic", P.CRITIC, "critic"),
            ]),
            ("sidebar.tools", [
                ("nav.extensions", P.EXTENSIONS, "extensions"),
                ("nav.book", P.BOOK_ANALYSIS, "book"),
                ("nav.export", P.EXPORT, "export"),
                ("nav.history", P.HISTORY, "history"),
                ("nav.memory", P.MEMORY, "memory"),
            ]),
        ]

        for group_key, items in groups:
            header = self._create_group_header(tr(group_key))
            header.setProperty("tr_key", group_key)
            self.nav_container_layout.addWidget(header)

            item_btns = []
            for text_key, idx, icon_name in items:
                btn = QPushButton(f"  {tr(text_key)}")
                btn.setObjectName("nav_item")
                btn.setFixedHeight(36)
                btn.setProperty("icon_name", icon_name)
                btn.setProperty("tr_key", text_key)
                btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
                self.nav_container_layout.addWidget(btn)
                self.nav_buttons.append((btn, idx))
                item_btns.append(btn)

            self._nav_groups.append([header, item_btns, True, group_key])
            header.clicked.connect(lambda _, g=self._nav_groups[-1]: self._toggle_group(g))

        self.nav_container_layout.addStretch()
        self.nav_scroll.setWidget(nav_container)
        layout.addWidget(self.nav_scroll, 1)

        # ---- 底部固定区（覆盖在滚动区下方） ----
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(4)

        divider = ProfessionalDivider()
        bottom_layout.addWidget(divider)

        # 折叠按钮
        self._collapse_btn = QPushButton()
        self._collapse_btn.setObjectName("nav_item")
        self._collapse_btn.setFixedHeight(36)
        self._collapse_btn.setProperty("icon_name", "collapse")
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        bottom_layout.addWidget(self._collapse_btn)

        settings_btn = QPushButton(f"  {tr('nav.settings')}")
        settings_btn.setObjectName("nav_item")
        settings_btn.setFixedHeight(36)
        settings_btn.setProperty("icon_name", "settings")
        settings_btn.setProperty("tr_key", "nav.settings")
        settings_btn.clicked.connect(lambda: self._switch_page(Page.SETTINGS))
        bottom_layout.addWidget(settings_btn)
        self.nav_buttons.append((settings_btn, Page.SETTINGS))

        version = QLabel("v2.0.0 专业版")
        version.setObjectName("version")
        bottom_layout.addWidget(version)
        self._sidebar_version = version

        layout.addWidget(bottom_container, 0)

        self._sidebar_collapsed = False
        self._refresh_nav_icons()

        # 加载持久化的侧边栏折叠状态
        try:
            from src.data.settings_manager import get_settings_manager
            saved = get_settings_manager().get_setting("general", "sidebar_collapsed", "false")
            self._sidebar_collapsed = str(saved).lower() == "true"
        except Exception:
            pass
        if self._sidebar_collapsed:
            self.sidebar.setFixedWidth(56)
            self._sidebar_logo.setText("AI")
            for btn, _idx in self.nav_buttons:
                key = btn.property("tr_key")
                if key:
                    btn.setText("")
            for header, _items, _expanded, _group_key in self._nav_groups:
                header.setText("")
            self._sidebar_version.setVisible(False)
            self._collapse_btn.setText("")
            self._collapse_btn.setProperty("icon_name", "expand")

        return sidebar

    def _refresh_nav_icons(self):
        """按当前主题刷新导航图标"""
        color = theme_icon_color(self.theme_name)
        for btn, _idx in self.nav_buttons:
            icon_name = btn.property("icon_name")
            if icon_name:
                btn.setIcon(get_icon(icon_name, color, 16))
                btn.setIconSize(QSize(16, 16))
        # 折叠按钮图标
        if hasattr(self, "_collapse_btn"):
            collapse_icon = "expand" if self._sidebar_collapsed else "collapse"
            self._collapse_btn.setIcon(get_icon(collapse_icon, color, 16))
            self._collapse_btn.setIconSize(QSize(16, 16))

    def _create_group_header(self, name: str) -> QPushButton:
        """创建可折叠的分组标题"""
        header = QPushButton(f"▾  {name}")
        header.setObjectName("nav_group_header")
        header.setFixedHeight(28)
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        return header

    def _toggle_group(self, group: list):
        """折叠/展开分组"""
        header, item_btns, expanded, group_key = group
        expanded = not expanded
        group[2] = expanded
        for btn in item_btns:
            btn.setVisible(expanded)
        header.setText(f"{'▾' if expanded else '▸'}  {tr(group_key)}")

    def retranslate(self):
        """语言切换后刷新主界面文字"""
        self.setWindowTitle(tr("app.title"))
        for btn, _idx in self.nav_buttons:
            key = btn.property("tr_key")
            if key:
                # 折叠状态下只保留图标，不恢复文字
                if getattr(self, "_sidebar_collapsed", False):
                    btn.setText("")
                else:
                    btn.setText(f"  {tr(key)}")
        for header, _items, expanded, group_key in self._nav_groups:
            if getattr(self, "_sidebar_collapsed", False):
                header.setText("")
            else:
                header.setText(f"{'▾' if expanded else '▸'}  {tr(group_key)}")
        # 折叠按钮 tooltip
        if hasattr(self, "_collapse_btn"):
            self._collapse_btn.setToolTip(
                tr("sidebar.expand") if self._sidebar_collapsed else tr("sidebar.collapse"))
        self.status_label.setText(tr("status.ready"))
        self.agent_status.setText(tr("status.agent_idle"))
        # 聊天页同步
        if hasattr(self, "chat_page") and hasattr(self.chat_page, "retranslate"):
            self.chat_page.retranslate()
    
    def _create_pages(self):
        """创建所有页面"""
        # 创建概览页面并连接导航信号
        self.home_page = HomePage()
        self.home_page.navigate_to_page.connect(self._switch_page)

        # AI助手对话页
        self.chat_page = ChatPage()
        self.chat_page.goto_settings.connect(lambda: self._switch_page(Page.SETTINGS))
        self.chat_page.goto_extensions.connect(lambda: self._switch_page(Page.EXTENSIONS))

        self.writer_page = WriterPage()
        self.character_page = CharacterPage()
        self.book_library_page = BookLibraryPage()
        # 角色页反向链接跳转 → 打开写作工作台对应章节
        self.character_page.open_chapter_requested.connect(self._open_chapter_in_writer)
        # 编辑器双链 [[角色名]] → 跳转到角色页选中
        self.writer_page.open_character_requested.connect(self._goto_character)
        # 书籍管理页：左键打开书籍 → 切写作工作台加载
        self.book_library_page.book_opened.connect(self._open_book_in_writer)

        pages = [
            self.home_page,           # 0 - 概览
            self.book_library_page,   # 1 - 书籍管理
            self.writer_page,         # 2 - 写作工作台
            OutlinePage(),            # 3 - 大纲编辑
            self.character_page,      # 4 - 角色管理
            HookPage(),               # 5 - 悬念管理
            EventPage(),              # 6 - 故事时间线
            CriticPage(),             # 7 - 批评师
            BookPage(),               # 8 - 拆书分析
            ExportPage(),             # 9 - 导出中心
            HistoryPage(),            # 10 - 历史记录
            SharedMemoryPage(),       # 11 - 共享记忆
            SettingsPage(),           # 12 - 系统设置
            self.chat_page,           # 13 - AI助手
            ExtensionsPage(),         # 14 - 扩展中心
        ]
        self._pages = pages  # 供 closeEvent 终止后台线程

        # 故事时间线 → 写作工作台跳转
        for page in pages:
            if hasattr(page, "open_chapter_requested"):
                page.open_chapter_requested.connect(self._open_chapter_in_writer)

        for page in pages:
            self.content.addWidget(page)

    def closeEvent(self, event):
        """关闭应用：终止运行中的后台线程，防止写文件/API调用被截断"""
        for page in getattr(self, "_pages", []):
            shutdown = getattr(page, "shutdown", None)
            if callable(shutdown):
                try:
                    shutdown()
                except Exception:
                    pass
        event.accept()
    
    def _toggle_sidebar(self):
        """折叠/展开侧边栏（220px ↔ 56px 图标条）"""
        collapsed = not getattr(self, "_sidebar_collapsed", False)
        self._sidebar_collapsed = collapsed
        self.sidebar.setFixedWidth(56 if collapsed else 220)
        # Logo 文字
        if hasattr(self, "_sidebar_logo"):
            self._sidebar_logo.setText("AI" if collapsed else "AI写作助手")
        # 导航按钮：折叠只留图标（清空文字），展开恢复文字
        for btn, idx in self.nav_buttons:
            key = btn.property("tr_key")
            if key:
                if collapsed:
                    btn.setText("")
                else:
                    btn.setText(f"  {tr(key)}")
        # 分组头：折叠只留箭头，展开恢复文字
        for header, _items, expanded, group_key in self._nav_groups:
            if collapsed:
                header.setText("")
            else:
                header.setText(f"{'▾' if expanded else '▸'}  {tr(group_key)}")
        # 版本号隐藏
        if hasattr(self, "_sidebar_version"):
            self._sidebar_version.setVisible(not collapsed)
        # 折叠按钮图标切换
        color = theme_icon_color(self.theme_name)
        if hasattr(self, "_collapse_btn"):
            self._collapse_btn.setText("")
            icon_name = "expand" if collapsed else "collapse"
            self._collapse_btn.setProperty("icon_name", icon_name)
            self._collapse_btn.setIcon(get_icon(icon_name, color, 16))
            self._collapse_btn.setIconSize(QSize(16, 16))
            self._collapse_btn.setToolTip(
                tr("sidebar.expand") if collapsed else tr("sidebar.collapse"))
        # 持久化
        try:
            from src.data.settings_manager import get_settings_manager
            get_settings_manager().set_setting("general", "sidebar_collapsed", "true" if collapsed else "false")
        except Exception:
            pass

    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态标签
        self.status_label = QLabel(tr("status.ready"))
        self.status_bar.addWidget(self.status_label)
        
        # 智能体状态
        self.agent_status = QLabel(tr("status.agent_idle"))
        self.status_bar.addPermanentWidget(self.agent_status)
    
    def _switch_page(self, index):
        """切换页面"""
        self.content.setCurrentIndex(index)

        # 更新导航状态
        for btn, idx in self.nav_buttons:
            if idx == index:
                btn.setObjectName("nav_item_active")
            else:
                btn.setObjectName("nav_item")
            btn.style().polish(btn)

        # 更新状态栏（用 i18n 键）
        page_keys = [
            "nav.home", "nav.books", "nav.writer", "nav.outline",
            "nav.character", "nav.hook", "nav.event", "nav.critic",
            "nav.book", "nav.export", "nav.history", "nav.memory",
            "nav.settings", "nav.ai_chat", "nav.extensions"
        ]

        if 0 <= index < len(page_keys):
            self.status_label.setText(f"{tr('status.current_page')}: {tr(page_keys[index])}")

    def _open_book_in_writer(self, book_name: str):
        """书籍管理页左键打开书籍 → 写作工作台加载该书"""
        try:
            self.writer_page.open_book(book_name)
            self._switch_page(Page.WRITER)
        except Exception:
            pass

    def _open_chapter_in_writer(self, path: str):
        """从故事时间线/角色页跳转到写作工作台打开章节文件"""
        try:
            # 先尝试 writer_page 自身方法（含文件树高亮等）
            if self.writer_page.open_chapter_path(path):
                self._switch_page(Page.WRITER)
                return
            # 降级：直接读文件写编辑器
            self._switch_page(Page.WRITER)
            content = ""
            for enc in ("utf-8", "gbk"):
                try:
                    with open(path, "r", encoding=enc) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, OSError):
                    continue
            import os as _os
            self.writer_page.title_input.setText(_os.path.basename(path)[:-3])
            self.writer_page.editor.setPlainText(content)
        except Exception:
            pass

    def _goto_character(self, name: str):
        """从编辑器双链 [[角色名]] 跳转到角色页并选中"""
        try:
            self._switch_page(Page.CHARACTER)
            found = self.character_page.select_character(name)
            if not found:
                self.status_label.setText(f"角色「{name}」不在角色库中")
        except Exception:
            pass
    
    def _apply_theme(self):
        """应用主题"""
        self.setStyleSheet(ProfessionalTheme.get_stylesheet(self.theme_name))

    def _set_theme(self, theme_name: str):
        """切换主题并保存偏好"""
        self.theme_name = theme_name
        self._apply_theme()
        self._refresh_nav_icons()
        if hasattr(self, "chat_page"):
            self.chat_page.refresh_icons()
        if hasattr(self, "writer_page"):
            self.writer_page.refresh_icons()
        try:
            from src.data.settings_manager import get_settings_manager
            get_settings_manager().set_setting("general", "theme", theme_name)
        except Exception:
            pass
