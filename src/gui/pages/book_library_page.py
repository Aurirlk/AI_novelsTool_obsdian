"""
书籍管理页面
卡片式展示所有书籍（每行4本）：左键点击进入写作目录，右上角设置键或右键编辑元数据
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QScrollArea, QMessageBox, QFileDialog, QLineEdit,
    QTextEdit, QComboBox, QDialog, QDialogButtonBox, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap

from ..icons import get_icon, theme_icon_color


class BookCard(QFrame):
    """书籍卡片：封面 + 书名 + 元数据"""

    opened = pyqtSignal(str)   # 左键打开：书名
    edit_requested = pyqtSignal(str)  # 右键编辑：书名

    def __init__(self, book: dict, parent=None):
        super().__init__(parent)
        self.book = book
        self.setObjectName("assist_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(216)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 12)
        layout.setSpacing(8)

        # 右上角设置键（点击直接进入书籍设置）
        top_row = QHBoxLayout()
        top_row.addStretch()
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("card_gear")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setToolTip("书籍设置")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(
            lambda: self.edit_requested.emit(self.book.get("name", "")))
        try:
            from src.data.settings_manager import get_settings_manager
            theme = get_settings_manager().get_setting("general", "theme", "light")
        except Exception:
            theme = "light"
        self.settings_btn.setIcon(get_icon("settings", theme_icon_color(theme), 14))
        self.settings_btn.setIconSize(QSize(14, 14))
        top_row.addWidget(self.settings_btn)
        layout.addLayout(top_row)

        # 封面
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(120, 150)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background: #e8e8e8; border-radius: 6px; color: #999; font-size: 12px;")
        self._load_cover()
        layout.addWidget(self.cover_label, 0, Qt.AlignmentFlag.AlignHCenter)

        # 书名
        name_label = QLabel(book.get("name", ""))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # 元数据行
        meta_parts = [book.get("channel", ""), book.get("genre", "")]
        meta_parts = [p for p in meta_parts if p]
        meta_text = " · ".join(meta_parts) if meta_parts else "未分类"
        meta_label = QLabel(f"{meta_text} | {book.get('chapter_count', 0)}章")
        meta_label.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(meta_label)

    def _load_cover(self):
        try:
            from src.data.book_meta import get_cover_path
            path = get_cover_path(self.book.get("name", ""))
            if path:
                pix = QPixmap(path)
                if not pix.isNull():
                    self.cover_label.setPixmap(pix.scaled(
                        120, 160, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation))
                    return
        except Exception:
            pass
        self.cover_label.setText("无封面")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.opened.emit(self.book.get("name", ""))
        elif event.button() == Qt.MouseButton.RightButton:
            self.edit_requested.emit(self.book.get("name", ""))
        super().mousePressEvent(event)


class BookEditDialog(QDialog):
    """编辑书籍元数据对话框"""

    def __init__(self, book_name: str, parent=None):
        super().__init__(parent)
        self.book_name = book_name
        self.setWindowTitle(f"编辑《{book_name}》")
        self.setMinimumWidth(420)

        from src.data.book_meta import get_meta
        meta = get_meta(book_name)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 频道
        channel_row = QHBoxLayout()
        channel_row.addWidget(QLabel("频道:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["男频", "女频"])
        idx = self.channel_combo.findText(meta.get("channel", "男频"))
        if idx >= 0:
            self.channel_combo.setCurrentIndex(idx)
        channel_row.addWidget(self.channel_combo)
        layout.addLayout(channel_row)

        # 类型
        genre_row = QHBoxLayout()
        genre_row.addWidget(QLabel("类型:"))
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        self.genre_combo.addItems(
            ["都市", "玄幻", "仙侠", "穿越", "灵异", "科幻", "历史", "言情", "悬疑", "游戏", "其他"])
        self.genre_combo.setCurrentText(meta.get("genre", ""))
        genre_row.addWidget(self.genre_combo, 1)
        layout.addLayout(genre_row)

        # 封面
        cover_row = QHBoxLayout()
        cover_row.addWidget(QLabel("封面:"))
        self.cover_path = ""
        cover_btn = QPushButton("上传封面...")
        cover_btn.setObjectName("btn_secondary")
        cover_btn.clicked.connect(self._pick_cover)
        cover_row.addWidget(cover_btn)
        layout.addLayout(cover_row)

        # 简介
        layout.addWidget(QLabel("简介:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("书籍简介...")
        self.desc_input.setFixedHeight(120)
        self.desc_input.setPlainText(meta.get("description", ""))
        layout.addWidget(self.desc_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择封面图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.webp *.gif);;所有文件 (*)")
        if path:
            self.cover_path = path

    def values(self) -> dict:
        return {
            "channel": self.channel_combo.currentText(),
            "genre": self.genre_combo.currentText().strip(),
            "description": self.desc_input.toPlainText(),
            "cover": self.cover_path,
        }


class BookLibraryPage(QWidget):
    """书籍管理页面"""

    book_opened = pyqtSignal(str)  # 打开书籍：切到写作工作台加载

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("书籍管理")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        new_book_btn = QPushButton("新建书籍")
        new_book_btn.setObjectName("btn_secondary")
        new_book_btn.setFixedHeight(34)
        new_book_btn.clicked.connect(self._new_book)
        header.addWidget(new_book_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        hint = QLabel("左键点击书籍进入写作目录 · 右上角设置键或右键点击编辑封面/频道/类型/简介")
        hint.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        layout.addWidget(hint)

        # 卡片网格滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setSpacing(16)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self._cards = []
        self._refresh()

    def _refresh(self):
        """刷新书籍卡片"""
        from src.data.book_meta import list_books
        books = list_books()

        # 清空旧卡片
        for card in self._cards:
            self.grid.removeWidget(card)
            card.deleteLater()
        self._cards = []

        if not books:
            empty = QLabel("暂无书籍。点击右上角「新建书籍」创建，或在写作工作台导入已有目录。")
            empty.setStyleSheet("color: #a0a0a0; font-size: 13px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(empty, 0, 0)
            return

        cols = 4
        # 4列均分宽度，保证每行从左到右正好4本
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        for i, book in enumerate(books):
            card = BookCard(book)
            card.opened.connect(self.book_opened.emit)
            card.edit_requested.connect(self._edit_book)
            self.grid.addWidget(card, i // cols, i % cols)
            self._cards.append(card)

    def _new_book(self):
        """新建书籍：输入书名，在写作空间创建"""
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建书籍", "书名:")
        if not ok or not name.strip():
            return
        from src.data.writing_space import get_writing_space
        ws = get_writing_space()
        ok2, msg = ws.create_book(name.strip())
        if not ok2:
            QMessageBox.warning(self, "提示", str(msg))
            return
        # 立即进入编辑元数据
        self._edit_book(name.strip())
        self._refresh()

    def _edit_book(self, book_name: str):
        """编辑书籍元数据"""
        dialog = BookEditDialog(book_name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            vals = dialog.values()
            try:
                from src.data.book_meta import save_meta, set_cover
                save_meta(book_name, channel=vals["channel"], genre=vals["genre"],
                          description=vals["description"])
                if vals["cover"]:
                    set_cover(book_name, vals["cover"])
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存书籍信息失败：{e}")

    def open_book(self, book_name: str):
        """外部调用：直接打开某本书（进入写作目录）"""
        self.book_opened.emit(book_name)


def create_book_library_page():
    """创建书籍管理页面"""
    return BookLibraryPage()
