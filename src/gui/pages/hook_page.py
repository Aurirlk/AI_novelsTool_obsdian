"""
悬念页面
管理故事中的悬念和伏笔
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QInputDialog, QSpinBox, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit


class HookPage(QWidget):
    """悬念页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from src.data.hook_store import HookStore
        self.store = HookStore()
        self._current_id = None
        self._loading = False
        self._init_ui()
        self._refresh_list()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("悬念管理")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        
        add_btn = ModernButton("添加悬念", "primary")
        add_btn.clicked.connect(self._add_hook)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # 主体区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：悬念列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 书籍过滤
        book_filter_layout = QHBoxLayout()
        book_filter_label = QLabel("书籍:")
        book_filter_layout.addWidget(book_filter_label)

        self.book_filter = QComboBox()
        self.book_filter.addItem("全部")
        self.book_filter.currentTextChanged.connect(lambda _: self._filter_hooks(self.status_filter.currentText()))
        book_filter_layout.addWidget(self.book_filter)

        left_layout.addLayout(book_filter_layout)

        # 状态过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("状态:")
        filter_layout.addWidget(filter_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "已埋下", "发展中", "即将回收", "已回收", "已遗忘"])
        self.status_filter.currentTextChanged.connect(lambda _: self._filter_hooks(self.status_filter.currentText()))
        filter_layout.addWidget(self.status_filter)
        
        left_layout.addLayout(filter_layout)
        
        # 悬念列表
        self.hook_list = QListWidget()
        self.hook_list.currentTextChanged.connect(self._on_hook_selected)
        left_layout.addWidget(self.hook_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        delete_btn = ModernButton("删除", "danger")
        delete_btn.clicked.connect(self._delete_hook)
        btn_layout.addWidget(delete_btn)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # 右侧：悬念详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 基本信息
        basic_group = QGroupBox("悬念信息")
        basic_form = QFormLayout(basic_group)
        
        self.content_input = ModernTextEdit("悬念内容描述...")
        self.content_input.setFixedHeight(80)
        basic_form.addRow("内容", self.content_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["主线", "支线", "物品", "人物秘密"])
        basic_form.addRow("类型", self.type_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["已埋下", "发展中", "即将回收", "已回收", "已遗忘"])
        basic_form.addRow("状态", self.status_combo)
        
        right_layout.addWidget(basic_group)
        
        # 章节信息
        chapter_group = QGroupBox("章节信息")
        chapter_form = QFormLayout(chapter_group)
        
        self.planted_spin = QSpinBox()
        self.planted_spin.setRange(1, 1000)
        self.planted_spin.setValue(1)
        chapter_form.addRow("埋下章节", self.planted_spin)
        
        self.expected_spin = QSpinBox()
        self.expected_spin.setRange(1, 1000)
        self.expected_spin.setValue(10)
        chapter_form.addRow("预期回收章节", self.expected_spin)
        
        self.actual_spin = QSpinBox()
        self.actual_spin.setRange(0, 1000)
        self.actual_spin.setValue(0)
        chapter_form.addRow("实际回收章节", self.actual_spin)
        
        right_layout.addWidget(chapter_group)
        
        # 相关信息
        related_group = QGroupBox("相关信息")
        related_layout = QVBoxLayout(related_group)
        
        characters_label = QLabel("相关角色:")
        related_layout.addWidget(characters_label)
        
        self.characters_list = QListWidget()
        self.characters_list.setFixedHeight(100)
        related_layout.addWidget(self.characters_list)
        
        characters_btn_layout = QHBoxLayout()
        
        add_character_btn = ModernButton("添加角色", "secondary")
        add_character_btn.clicked.connect(self._add_character)
        characters_btn_layout.addWidget(add_character_btn)
        
        delete_character_btn = ModernButton("删除角色", "danger")
        delete_character_btn.clicked.connect(self._delete_character)
        characters_btn_layout.addWidget(delete_character_btn)
        
        related_layout.addLayout(characters_btn_layout)
        
        right_layout.addWidget(related_group)
        
        # 备注
        notes_label = QLabel("备注:")
        right_layout.addWidget(notes_label)
        
        self.notes_input = ModernTextEdit("添加备注...")
        self.notes_input.setFixedHeight(80)
        right_layout.addWidget(self.notes_input)
        
        # 保存按钮
        save_btn = ModernButton("保存悬念", "primary")
        save_btn.clicked.connect(self._save_hook)
        right_layout.addWidget(save_btn)
        
        right_layout.addStretch()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        right_scroll.setWidget(right_panel)
        splitter.addWidget(right_scroll)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def _load_books(self):
        """加载写作空间书籍列表到过滤下拉"""
        try:
            from src.data.writing_space import get_writing_space
            tree = get_writing_space().list_tree()
            books = [n["name"] for n in tree if n.get("type") == "book"]
        except Exception:
            books = []
        current = self.book_filter.currentText()
        self.book_filter.blockSignals(True)
        self.book_filter.clear()
        self.book_filter.addItem("全部")
        for b in books:
            self.book_filter.addItem(b)
        idx = self.book_filter.findText(current)
        if idx >= 0:
            self.book_filter.setCurrentIndex(idx)
        self.book_filter.blockSignals(False)

    def _filter_hooks(self, status):
        """过滤悬念"""
        self._refresh_list(status)

    def _current_book_name(self) -> str:
        """当前选中的书籍名（「全部」返回空）"""
        book = self.book_filter.currentText()
        return "" if book in ("全部", "") else book

    def _store_for_book(self):
        """按当前选中书返回 store（「全部」时用旧全局 store 但过滤 book 字段）"""
        from src.data.hook_store import HookStore
        book = self._current_book_name()
        if book:
            return HookStore(book=book)
        return HookStore()

    def _all_hooks(self):
        """获取钩子数据：选中书读书目录；全部时遍历所有书"""
        from src.data.hook_store import load_all_books_hooks
        book = self._current_book_name()
        if book:
            return self._store_for_book().load_all()
        try:
            return load_all_books_hooks()
        except Exception:
            return self.store.load_all()

    def _refresh_list(self, status="全部"):
        """从存储加载悬念列表（按书籍+状态过滤）"""
        self._loading = True
        self.hook_list.clear()
        for h in self._all_hooks():
            if status != "全部" and h.get("status") != status:
                continue
            content = h.get("content", "未命名悬念")
            label = f"{content[:20]} ({h.get('status', '已埋下')})"
            # mark 模式：超期未回收的钩子加「⚠️超期」标记
            if self._is_overdue(h):
                label = f"⚠️{label}"
            self.hook_list.addItem(label)
        if self.hook_list.count() == 0:
            if self._current_book_name():
                self.hook_list.addItem("本书暂无悬念，点击「添加悬念」创建")
            else:
                self.hook_list.addItem("请先选择书籍以查看悬念")
        self._loading = False

    def _is_overdue(self, h: dict) -> bool:
        """判断钩子是否超期未回收（仅当提醒模式含标记时生效）"""
        try:
            from src.data.settings_manager import get_settings_manager
            mode = get_settings_manager().get_setting("storage", "hook_overdue_reminder", "warn")
        except Exception:
            mode = "warn"
        if mode not in ("warn", "mark"):
            return False
        if h.get("status") == "已回收":
            return False
        expected = int(h.get("expected_chapter", 0) or 0)
        if expected <= 0:
            return False
        # 当前章节号：取本书钩子中已回收的最大实际章节（约等于已写进度）
        max_actual = max((int(x.get("actual_chapter", 0) or 0) for x in self._all_hooks()), default=0)
        return max_actual > 0 and expected < max_actual

    def _on_hook_selected(self, selected_text):
        """悬念选中事件"""
        if self._loading or not selected_text:
            return
        prefix = selected_text.rsplit(" (", 1)[0]
        # 找到对应悬念并回填表单
        for h in self._all_hooks():
            if h.get("content", "").startswith(prefix):
                self._current_id = h.get("id")
                self.content_input.setPlainText(h.get("content", ""))
                idx = self.type_combo.findText(h.get("type", "主线"))
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)
                idx = self.status_combo.findText(h.get("status", "已埋下"))
                if idx >= 0:
                    self.status_combo.setCurrentIndex(idx)
                self.planted_spin.setValue(int(h.get("planted_chapter", 1)))
                self.expected_spin.setValue(int(h.get("expected_chapter", 10)))
                self.actual_spin.setValue(int(h.get("actual_chapter", 0)))
                self.characters_list.clear()
                for ch in h.get("characters", []):
                    self.characters_list.addItem(ch)
                self.notes_input.setPlainText(h.get("notes", ""))
                return

    def _add_hook(self):
        """添加悬念（写入当前选中书的目录）"""
        content, ok = QInputDialog.getText(self, "添加悬念", "悬念内容:")
        if not ok or not content.strip():
            return
        book = self._current_book_name()
        if not book:
            QMessageBox.warning(self, "提示", "请先在顶部选择一本书籍，再添加悬念")
            return

        self._store_for_book().add({
            "content": content.strip(),
            "type": "主线",
            "status": "已埋下",
            "planted_chapter": 1,
            "expected_chapter": 10,
            "actual_chapter": 0,
            "characters": [],
            "notes": "",
            "book": book,
        })
        self._refresh_list(self.status_filter.currentText())
        # 选中新悬念
        for i in range(self.hook_list.count()):
            if self.hook_list.item(i).text().startswith(content.strip()[:20]):
                self.hook_list.setCurrentRow(i)
                break

    def _delete_hook(self):
        """删除悬念"""
        selected = self.hook_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的悬念")
            return

        reply = QMessageBox.question(self, "确认删除", f"确定要删除 '{selected.text()}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self._current_id:
                self._store_for_book().delete(self._current_id)
                self._current_id = None
            self._refresh_list(self.status_filter.currentText())

    def _add_character(self):
        """添加相关角色"""
        character, ok = QInputDialog.getText(self, "添加角色", "角色名称:")
        if not ok or not character:
            return

        self.characters_list.addItem(character)

    def _delete_character(self):
        """删除相关角色"""
        selected = self.characters_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的角色")
            return

        self.characters_list.takeItem(self.characters_list.row(selected))

    def _save_hook(self):
        """保存悬念（写入当前选中书的目录）"""
        content = self.content_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "警告", "请先输入悬念内容")
            return
        book = self._current_book_name()
        if not book:
            QMessageBox.warning(self, "提示", "请先在顶部选择一本书籍，再保存悬念")
            return

        data = {
            "content": content,
            "type": self.type_combo.currentText(),
            "status": self.status_combo.currentText(),
            "planted_chapter": self.planted_spin.value(),
            "expected_chapter": self.expected_spin.value(),
            "actual_chapter": self.actual_spin.value(),
            "characters": [self.characters_list.item(i).text() for i in range(self.characters_list.count())],
            "notes": self.notes_input.toPlainText(),
            "book": book,
        }

        if self._current_id:
            self._store_for_book().update(self._current_id, data)
        else:
            saved = self._store_for_book().add(data)
            self._current_id = saved.get("id")

        self._refresh_list(self.status_filter.currentText())
        # 重选当前悬念
        for i in range(self.hook_list.count()):
            if self.hook_list.item(i).text().startswith(content[:20]):
                self.hook_list.setCurrentRow(i)
                break
        QMessageBox.information(self, "成功", "悬念已保存")
