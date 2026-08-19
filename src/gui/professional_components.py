"""
企业级组件库
专业、成熟、高效的UI组件
"""

from PyQt6.QtWidgets import (
    QPushButton, QLineEdit, QTextEdit, QLabel,
    QFrame, QVBoxLayout, QHBoxLayout, QWidget,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor


class ProfessionalButton(QPushButton):
    """企业级按钮"""
    
    def __init__(self, text, style="primary", icon=None, parent=None):
        super().__init__(text, parent)
        self.style_type = style
        self.setObjectName(f"btn_{style}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.setMinimumWidth(80)


class ProfessionalInput(QLineEdit):
    """企业级输入框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setObjectName("input")
        self.setFixedHeight(36)
        self.setMinimumWidth(200)


class ProfessionalTextEdit(QTextEdit):
    """企业级文本编辑框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setObjectName("text_edit")


class ProfessionalLabel(QLabel):
    """企业级标签"""
    
    def __init__(self, text="", style="normal", parent=None):
        super().__init__(text, parent)
        self.style_type = style
        
        if style == "title":
            self.setObjectName("page_title")
        elif style == "subtitle":
            self.setObjectName("page_subtitle")
        elif style == "section":
            self.setObjectName("section_title")
        elif style == "muted":
            self.setStyleSheet("color: #606060; font-size: 12px;")
        else:
            self.setObjectName("label")


class ProfessionalCard(QFrame):
    """企业级卡片"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
        
        # 标题
        if title:
            self.title_label = ProfessionalLabel(title, "section")
            self.main_layout.addWidget(self.title_label)
        
        # 内容区域
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)
    
    def add_widget(self, widget):
        """添加组件"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """添加布局"""
        self.content_layout.addLayout(layout)


class ProfessionalSection(QWidget):
    """企业级区域"""
    
    def __init__(self, title="", description="", parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 标题
        if title:
            self.title_label = ProfessionalLabel(title, "section")
            layout.addWidget(self.title_label)
        
        # 描述
        if description:
            self.desc_label = ProfessionalLabel(description, "muted")
            layout.addWidget(self.desc_label)
        
        # 内容区域
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
    
    def add_widget(self, widget):
        """添加组件"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """添加布局"""
        self.content_layout.addLayout(layout)


class ProfessionalDivider(QFrame):
    """企业级分割线"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class ProfessionalBadge(QLabel):
    """企业级徽章"""
    
    def __init__(self, text, style="default", parent=None):
        super().__init__(text, parent)
        self.style_type = style
        self.setObjectName(f"badge_{style}")


class ProfessionalProgressBar(QFrame):
    """企业级进度条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setStyleSheet("""
            background-color: #1a1a2e;
            border-radius: 4px;
        """)
        
        # 进度条
        self.progress_bar = QFrame(self)
        self.progress_bar.setStyleSheet("""
            background-color: #4a90d9;
            border-radius: 4px;
        """)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setFixedWidth(0)
        
        # 动画
        self.animation = QPropertyAnimation(self.progress_bar, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def set_progress(self, value):
        """设置进度"""
        target_width = int(self.width() * value / 100)
        self.animation.setStartValue(self.progress_bar.width())
        self.animation.setEndValue(target_width)
        self.animation.start()


class ProfessionalToast(QLabel):
    """企业级提示框"""
    
    def __init__(self, text, style="info", parent=None):
        super().__init__(text, parent)
        self.style_type = style
        self.setObjectName(f"toast_{style}")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(40)
        self.setMinimumWidth(200)
        
        # 自动隐藏
        self.hide()
    
    def show_toast(self, duration=3000):
        """显示提示"""
        self.show()
        
        # 动画
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.hide)
        self.animation.start()
