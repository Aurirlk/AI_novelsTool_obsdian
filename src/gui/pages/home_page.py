"""
概览页面
功能入口中心 + 快速开始引导
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..i18n import tr
from ..page_constants import Page


class FeatureCard(QFrame):
    """功能卡片"""

    clicked = pyqtSignal(int)  # 点击信号，传递页面索引

    def __init__(self, title, description, page_index, icon_name="", parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.setObjectName("feature_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(120)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # 标题行：图标 + 标题
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        if icon_name:
            from ..icons import get_icon
            icon_label = QLabel()
            icon_label.setStyleSheet("background: transparent; border: none;")
            icon_label.setPixmap(get_icon(icon_name, "#10a37f", 18).pixmap(18, 18))
            title_row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; background: transparent; border: none;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        # 描述
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #8e8e8e; font-size: 12px; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_index)
        super().mousePressEvent(event)


class HomePage(QWidget):
    """概览页面"""
    
    # 定义信号
    navigate_to_page = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(24)
        
        # 欢迎区域
        welcome_container = QWidget()
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(8)
        
        welcome = QLabel(tr("app.title"))
        welcome.setStyleSheet("font-size: 28px; font-weight: bold;")
        welcome_layout.addWidget(welcome)
        
        subtitle = QLabel("专业的AI小说创作平台 - 让AI成为你的写作陪练，而不是代笔")
        subtitle.setStyleSheet("color: #a0a0a0; font-size: 14px;")
        welcome_layout.addWidget(subtitle)
        
        main_layout.addWidget(welcome_container)

        # ---- 快速开始引导 ----
        quick_start = QFrame()
        quick_start.setObjectName("quick_start")
        qs_layout = QHBoxLayout(quick_start)
        qs_layout.setContentsMargins(20, 16, 20, 16)
        qs_layout.setSpacing(24)

        steps = [
            ("home.step1", "home.step1_desc", Page.SETTINGS, "settings"),
            ("home.step2", "home.step2_desc", Page.BOOKS, "book-open"),
            ("home.step3", "home.step3_desc", Page.WRITER, "writer"),
        ]
        for title_key, desc_key, page_idx, icon_name in steps:
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(4)

            title_lbl = QLabel(tr(title_key))
            title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent; border: none;")
            step_layout.addWidget(title_lbl)

            desc_lbl = QLabel(tr(desc_key))
            desc_lbl.setStyleSheet("color: #8e8e8e; font-size: 12px; background: transparent; border: none;")
            desc_lbl.setWordWrap(True)
            step_layout.addWidget(desc_lbl)

            step_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            step_widget.mousePressEvent = lambda e, idx=page_idx: self.navigate_to_page.emit(idx) if e.button() == Qt.MouseButton.LeftButton else None
            qs_layout.addWidget(step_widget)

        main_layout.addWidget(quick_start)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(32)

        P = Page
        # 工作区模块
        workspace_section = self._create_section(tr("sidebar.workspace"), [
            (tr("nav.home"), "查看项目状态和统计数据", P.HOME, "home"),
            (tr("nav.ai_chat"), "AI对话助手，支持专家/技能/连接器", P.CHAT, "chat"),
            (tr("nav.books"), "创建、打开、管理书籍", P.BOOKS, "book-open"),
            (tr("nav.writer"), "核心写作界面，AI辅助创作", P.WRITER, "writer"),
            (tr("nav.outline"), "创建和编辑故事大纲", P.OUTLINE, "outline"),
            (tr("nav.character"), "管理角色信息、状态、关系", P.CHARACTER, "character"),
            (tr("nav.hook"), "追踪悬念、伏笔、钩子", P.HOOK, "hook"),
            (tr("nav.event"), "管理大事记和时间线", P.EVENT, "event"),
        ])
        scroll_layout.addWidget(workspace_section)
        
        # AI工具模块
        ai_section = self._create_section("AI工具", [
            (tr("nav.critic"), "大纲批评、章节批评、写作陪练", P.CRITIC, "critic"),
            (tr("nav.book"), "分析网文模式，学习写作技巧", P.BOOK_ANALYSIS, "book"),
            (tr("nav.memory"), "智能体记忆共享和协作", P.MEMORY, "memory"),
        ])
        scroll_layout.addWidget(ai_section)
        
        # 输出模块
        output_section = self._create_section("输出", [
            (tr("nav.export"), "导出为TXT、Markdown、Word等格式", P.EXPORT, "export"),
            (tr("nav.history"), "查看历史对话和操作记录", P.HISTORY, "history"),
            (tr("nav.extensions"), "MCP连接器、技能包管理", P.EXTENSIONS, "extensions"),
        ])
        scroll_layout.addWidget(output_section)
        
        # 系统模块
        system_section = self._create_section("系统", [
            (tr("nav.settings"), "LLM配置、个性化设置、快捷键", P.SETTINGS, "settings"),
        ])
        scroll_layout.addWidget(system_section)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def _create_section(self, title, cards_data):
        """创建模块区域"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(16)
        
        # 区域标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title_label)
        
        # 卡片网格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)
        
        for i, (name, desc, page_idx, icon_name) in enumerate(cards_data):
            card = FeatureCard(name, desc, page_idx, icon_name)
            card.clicked.connect(self.navigate_to_page)
            
            row = i // 3
            col = i % 3
            grid_layout.addWidget(card, row, col)
        
        section_layout.addLayout(grid_layout)
        
        return section
