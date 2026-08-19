"""
角色页面
管理故事中的角色
"""

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QGroupBox, QFormLayout, QLineEdit,
    QTextEdit, QMessageBox, QInputDialog, QComboBox,
    QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit


class CharacterPage(QWidget):
    """角色页面"""

    open_chapter_requested = pyqtSignal(str)  # 反向链接跳转：章节路径

    def __init__(self, parent=None):
        super().__init__(parent)
        from src.data.character_store import CharacterStore
        self.store = CharacterStore()
        self._current_id = None
        self._loading = False
        self._init_ui()
        self._load_books()
        self._refresh_list()

    def _current_book_name(self) -> str:
        """当前选中的书籍名（「全部」返回空）"""
        book = self.book_filter.currentText()
        return "" if book in ("全部", "") else book
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("角色管理")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        
        add_btn = ModernButton("添加角色", "primary")
        add_btn.clicked.connect(self._add_character)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # 主体区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：角色列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 书籍过滤
        book_filter_layout = QHBoxLayout()
        book_filter_label = QLabel("书籍:")
        book_filter_layout.addWidget(book_filter_label)

        self.book_filter = QComboBox()
        self.book_filter.addItem("全部")
        self.book_filter.currentTextChanged.connect(lambda _: self._filter_characters(self.type_filter.currentText()))
        book_filter_layout.addWidget(self.book_filter)

        left_layout.addLayout(book_filter_layout)

        # 角色类型过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("类型:")
        filter_layout.addWidget(filter_label)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部", "主角", "配角", "反派", "龙套"])
        self.type_filter.currentTextChanged.connect(lambda _: self._filter_characters(self.type_filter.currentText()))
        filter_layout.addWidget(self.type_filter)
        
        left_layout.addLayout(filter_layout)
        
        # 角色列表
        self.character_list = QListWidget()
        self.character_list.currentTextChanged.connect(self._on_character_selected)
        left_layout.addWidget(self.character_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        delete_btn = ModernButton("删除", "danger")
        delete_btn.clicked.connect(self._delete_character)
        btn_layout.addWidget(delete_btn)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # 右侧：角色详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_form = QFormLayout(basic_group)
        
        self.name_input = ModernInput("角色名称")
        basic_form.addRow("名称", self.name_input)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["主角", "配角", "反派", "龙套"])
        basic_form.addRow("角色类型", self.role_combo)
        
        self.personality_input = ModernInput("性格特点")
        basic_form.addRow("性格", self.personality_input)
        
        self.background_input = ModernTextEdit("角色背景故事...")
        self.background_input.setFixedHeight(80)
        basic_form.addRow("背景", self.background_input)
        
        right_layout.addWidget(basic_group)
        
        # 状态信息
        status_group = QGroupBox("状态信息")
        status_form = QFormLayout(status_group)
        
        self.location_input = ModernInput("当前位置")
        status_form.addRow("位置", self.location_input)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["存活", "死亡", "失踪", "受伤"])
        status_form.addRow("状态", self.status_combo)
        
        self.appearance_input = ModernInput("外貌描述")
        status_form.addRow("外貌", self.appearance_input)
        
        right_layout.addWidget(status_group)
        
        # 能力和物品
        abilities_group = QGroupBox("能力和物品")
        abilities_layout = QVBoxLayout(abilities_group)

        abilities_label = QLabel("能力列表（名称 + 效果说明）:")
        abilities_layout.addWidget(abilities_label)

        self.abilities_list = QListWidget()
        self.abilities_list.setFixedHeight(90)
        abilities_layout.addWidget(self.abilities_list)

        abilities_btn_layout = QHBoxLayout()

        add_ability_btn = ModernButton("添加能力", "secondary")
        add_ability_btn.clicked.connect(self._add_ability)
        abilities_btn_layout.addWidget(add_ability_btn)

        edit_ability_btn = ModernButton("编辑能力", "secondary")
        edit_ability_btn.clicked.connect(self._edit_ability)
        abilities_btn_layout.addWidget(edit_ability_btn)

        delete_ability_btn = ModernButton("删除能力", "danger")
        delete_ability_btn.clicked.connect(self._delete_ability)
        abilities_btn_layout.addWidget(delete_ability_btn)

        abilities_layout.addLayout(abilities_btn_layout)

        abilities_layout.addWidget(QLabel("物品列表（名称 + 用途/来历）:"))
        self.items_list = QListWidget()
        self.items_list.setFixedHeight(90)
        abilities_layout.addWidget(self.items_list)

        items_btn_layout = QHBoxLayout()
        add_item_btn = ModernButton("添加物品", "secondary")
        add_item_btn.clicked.connect(self._add_item)
        items_btn_layout.addWidget(add_item_btn)

        edit_item_btn = ModernButton("编辑物品", "secondary")
        edit_item_btn.clicked.connect(self._edit_item)
        items_btn_layout.addWidget(edit_item_btn)

        delete_item_btn = ModernButton("删除物品", "danger")
        delete_item_btn.clicked.connect(self._delete_item)
        items_btn_layout.addWidget(delete_item_btn)

        abilities_layout.addLayout(items_btn_layout)

        right_layout.addWidget(abilities_group)

        # 人物关系
        rel_group = QGroupBox("人物关系")
        rel_layout = QVBoxLayout(rel_group)

        self.relationships_list = QListWidget()
        self.relationships_list.setFixedHeight(90)
        rel_layout.addWidget(self.relationships_list)

        rel_btn_layout = QHBoxLayout()
        add_rel_btn = ModernButton("添加关系", "secondary")
        add_rel_btn.clicked.connect(self._add_relationship)
        rel_btn_layout.addWidget(add_rel_btn)

        edit_rel_btn = ModernButton("编辑关系", "secondary")
        edit_rel_btn.clicked.connect(self._edit_relationship)
        rel_btn_layout.addWidget(edit_rel_btn)

        delete_rel_btn = ModernButton("删除关系", "danger")
        delete_rel_btn.clicked.connect(self._delete_relationship)
        rel_btn_layout.addWidget(delete_rel_btn)

        rel_layout.addLayout(rel_btn_layout)
        right_layout.addWidget(rel_group)

        # 反向链接：角色出现在哪些章节（Obsidian 式）
        backlinks_group = QGroupBox("出现章节（反向链接）")
        backlinks_layout = QVBoxLayout(backlinks_group)

        backlinks_hint = QLabel("选中角色后自动扫描全书，点击章节名可跳转到写作工作台查看")
        backlinks_hint.setWordWrap(True)
        backlinks_hint.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        backlinks_layout.addWidget(backlinks_hint)

        self.backlinks_list = QListWidget()
        self.backlinks_list.setFixedHeight(120)
        self.backlinks_list.itemDoubleClicked.connect(self._on_backlink_open)
        backlinks_layout.addWidget(self.backlinks_list)

        right_layout.addWidget(backlinks_group)

        # 保存按钮
        save_btn = ModernButton("保存角色", "primary")
        save_btn.clicked.connect(self._save_character)
        right_layout.addWidget(save_btn)

        right_layout.addStretch()

        # 右侧详情包进滚动区，防止窗口高度不足时表单挤压重叠
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

    def _filter_characters(self, type_name):
        """过滤角色"""
        self._refresh_list(type_name)

    def _store_for_book(self):
        """按当前选中书返回 store（「全部」时用旧全局 store 但过滤 book 字段）"""
        from src.data.character_store import CharacterStore
        book = self._current_book_name()
        if book:
            return CharacterStore(book=book)
        return CharacterStore()

    def _all_characters(self):
        """获取角色数据：选中书读书目录；全部时遍历所有书"""
        from src.data.character_store import load_all_books_characters
        book = self._current_book_name()
        if book:
            return self._store_for_book().load_all()
        try:
            return load_all_books_characters()
        except Exception:
            return self.store.load_all()

    def _refresh_list(self, type_name="全部"):
        """从存储加载角色列表（按书籍+类型过滤）"""
        self._loading = True
        self.character_list.clear()
        for c in self._all_characters():
            if type_name != "全部" and c.get("role_type") != type_name:
                continue
            self.character_list.addItem(f"{c.get('name', '未命名')} ({c.get('role_type', '龙套')})")
        if self.character_list.count() == 0:
            if self._current_book_name():
                self.character_list.addItem("本书暂无角色，点击「添加角色」创建")
            else:
                self.character_list.addItem("请先选择书籍以查看角色")
        self._loading = False

    def _on_character_selected(self, selected_text):
        """角色选中事件"""
        if self._loading or not selected_text:
            return
        name = selected_text.rsplit(" (", 1)[0]
        # 找到对应角色并回填表单
        for c in self._all_characters():
            if c.get("name") == name:
                self._current_id = c.get("id")
                self.name_input.setText(c.get("name", ""))
                idx = self.role_combo.findText(c.get("role_type", "配角"))
                if idx >= 0:
                    self.role_combo.setCurrentIndex(idx)
                self.personality_input.setText(c.get("personality", ""))
                self.background_input.setPlainText(c.get("background", ""))
                idx = self.status_combo.findText(c.get("status", "存活"))
                if idx >= 0:
                    self.status_combo.setCurrentIndex(idx)
                self.location_input.setText(c.get("location", ""))
                self.appearance_input.setText(c.get("appearance", ""))
                self.abilities_list.clear()
                for ability in c.get("abilities", []):
                    self.abilities_list.addItem(self._fmt_named(ability))
                self.items_list.clear()
                for item in c.get("items", []):
                    self.items_list.addItem(self._fmt_named(item))
                self.relationships_list.clear()
                for rel in c.get("relationships", []):
                    self.relationships_list.addItem(self._fmt_relation(rel))
                # 反向链接：扫描全书找该角色出现的章节
                self.backlinks_list.clear()
                try:
                    from src.data.search_index import find_backlinks
                    # 角色名可能含别名（如 "Seed / 魏进赫"），逐个拆开匹配
                    search_names = [n.strip() for n in re.split(r"[/／]", c.get("name", "")) if n.strip()]
                    for sname in search_names:
                        for bl in find_backlinks(sname):
                            item = QListWidgetItem(f"{bl['book']} / {bl['chapter']}")
                            item.setToolTip(bl["preview"])
                            item.setData(Qt.ItemDataRole.UserRole, bl.get("path", ""))
                            self.backlinks_list.addItem(item)
                except Exception:
                    pass
                if self.backlinks_list.count() == 0:
                    self.backlinks_list.addItem("（未在章节中找到该角色）")
                return

    def _on_backlink_open(self, item):
        """双击反向链接：跳转到写作工作台打开该章节"""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.open_chapter_requested.emit(path)

    def select_character(self, name: str):
        """编程式选中角色（双链跳转入口）"""
        # 先刷新列表确保数据最新
        self._refresh_list(self.type_filter.currentText())
        for i in range(self.character_list.count()):
            if self.character_list.item(i).text().startswith(name):
                self.character_list.setCurrentRow(i)
                # 触发选中逻辑（当前文本变更不一定触发，手动调用）
                self._on_character_selected(self.character_list.item(i).text())
                return True
        return False

    def _add_character(self):
        """添加角色（写入当前选中书的目录；「全部」时提示先选书）"""
        name, ok = QInputDialog.getText(self, "添加角色", "角色名称:")
        if not ok or not name.strip():
            return
        book = self._current_book_name()
        if not book:
            QMessageBox.warning(self, "提示", "请先在顶部选择一本书籍，再添加角色")
            return
        self._store_for_book().add({
            "name": name.strip(),
            "book": book,
            "role_type": "龙套",
            "personality": "",
            "background": "",
            "status": "存活",
            "location": "",
            "appearance": "",
            "abilities": [],
            "items": [],
            "relationships": [],
        })
        self._refresh_list(self.type_filter.currentText())
        # 选中新角色
        for i in range(self.character_list.count()):
            if self.character_list.item(i).text().startswith(name.strip()):
                self.character_list.setCurrentRow(i)
                break

    def _delete_character(self):
        """删除角色"""
        selected = self.character_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的角色")
            return

        reply = QMessageBox.question(self, "确认删除", f"确定要删除 '{selected.text()}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self._current_id:
                self._store_for_book().delete(self._current_id)
                self._current_id = None
            self._refresh_list(self.type_filter.currentText())

    @staticmethod
    def _fmt_named(item) -> str:
        """格式化 能力/物品 条目（兼容 str 或 {"name","description"}）"""
        if isinstance(item, dict):
            name = item.get("name", "")
            desc = item.get("description", "")
            return f"{name}：{desc}" if desc else name
        return str(item)

    @staticmethod
    def _fmt_relation(rel) -> str:
        """格式化人物关系条目"""
        if isinstance(rel, dict):
            name = rel.get("name", "")
            relation = rel.get("relation", "")
            return f"{name}：{relation}" if relation else name
        return str(rel)

    @staticmethod
    def _parse_named(text: str) -> dict:
        """解析「名称：描述」文本 → {"name","description"}"""
        text = text.strip()
        if "：" in text:
            name, _, desc = text.partition("：")
            return {"name": name.strip(), "description": desc.strip()}
        return {"name": text, "description": ""}

    @staticmethod
    def _parse_relation(text: str) -> dict:
        text = text.strip()
        if "：" in text:
            name, _, relation = text.partition("：")
            return {"name": name.strip(), "relation": relation.strip()}
        return {"name": text, "relation": ""}

    def _collect_named(self, list_widget) -> list:
        """收集列表所有条目为 {"name","description"} 结构"""
        result = []
        for i in range(list_widget.count()):
            result.append(self._parse_named(list_widget.item(i).text()))
        return result

    def _collect_relations(self) -> list:
        result = []
        for i in range(self.relationships_list.count()):
            result.append(self._parse_relation(self.relationships_list.item(i).text()))
        return result

    def _add_ability(self):
        """添加能力（名称 + 效果说明）"""
        name, ok = QInputDialog.getText(self, "添加能力", "能力名称:")
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "能力说明", "能力效果/限制说明（可留空）:")
        if ok2:
            item = name.strip()
            if desc.strip():
                item = f"{name.strip()}：{desc.strip()}"
            self.abilities_list.addItem(item)

    def _edit_ability(self):
        """编辑能力"""
        selected = self.abilities_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要编辑的能力")
            return
        parsed = self._parse_named(selected.text())
        name, ok = QInputDialog.getText(self, "编辑能力", "能力名称:", text=parsed["name"])
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "能力说明", "能力效果/限制说明:", text=parsed["description"])
        if ok2:
            item = name.strip()
            if desc.strip():
                item = f"{name.strip()}：{desc.strip()}"
            selected.setText(item)

    def _delete_ability(self):
        """删除能力"""
        selected = self.abilities_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的能力")
            return
        self.abilities_list.takeItem(self.abilities_list.row(selected))

    # ==================== 物品 ====================

    def _add_item(self):
        """添加物品（名称 + 用途/来历）"""
        name, ok = QInputDialog.getText(self, "添加物品", "物品名称:")
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "物品说明", "用途/来历说明（可留空）:")
        if ok2:
            item = name.strip()
            if desc.strip():
                item = f"{name.strip()}：{desc.strip()}"
            self.items_list.addItem(item)

    def _edit_item(self):
        selected = self.items_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要编辑的物品")
            return
        parsed = self._parse_named(selected.text())
        name, ok = QInputDialog.getText(self, "编辑物品", "物品名称:", text=parsed["name"])
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "物品说明", "用途/来历说明:", text=parsed["description"])
        if ok2:
            item = name.strip()
            if desc.strip():
                item = f"{name.strip()}：{desc.strip()}"
            selected.setText(item)

    def _delete_item(self):
        selected = self.items_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的物品")
            return
        self.items_list.takeItem(self.items_list.row(selected))

    # ==================== 人物关系 ====================

    def _add_relationship(self):
        """添加人物关系（对象 + 关系描述）"""
        name, ok = QInputDialog.getText(self, "添加关系", "关系对象（角色名）:")
        if not ok or not name.strip():
            return
        relation, ok2 = QInputDialog.getText(self, "关系描述", "关系描述（如：仇敌/师兄妹/单恋对象）:")
        if ok2:
            item = name.strip()
            if relation.strip():
                item = f"{name.strip()}：{relation.strip()}"
            self.relationships_list.addItem(item)

    def _edit_relationship(self):
        selected = self.relationships_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要编辑的关系")
            return
        parsed = self._parse_relation(selected.text())
        name, ok = QInputDialog.getText(self, "编辑关系", "关系对象（角色名）:", text=parsed["name"])
        if not ok or not name.strip():
            return
        relation, ok2 = QInputDialog.getText(self, "关系描述", "关系描述:", text=parsed["relation"])
        if ok2:
            item = name.strip()
            if relation.strip():
                item = f"{name.strip()}：{relation.strip()}"
            selected.setText(item)

    def _delete_relationship(self):
        selected = self.relationships_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的关系")
            return
        self.relationships_list.takeItem(self.relationships_list.row(selected))

    def _save_character(self):
        """保存角色（写入当前选中书的目录）"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请先输入角色名称")
            return

        book = self._current_book_name()
        if not book:
            QMessageBox.warning(self, "提示", "请先在顶部选择一本书籍，再保存角色")
            return
        store = self._store_for_book()

        data = {
            "name": name,
            "book": book,
            "role_type": self.role_combo.currentText(),
            "personality": self.personality_input.text(),
            "background": self.background_input.toPlainText(),
            "status": self.status_combo.currentText(),
            "location": self.location_input.text(),
            "appearance": self.appearance_input.text(),
            "abilities": self._collect_named(self.abilities_list),
            "items": self._collect_named(self.items_list),
            "relationships": self._collect_relations(),
        }

        if self._current_id:
            store.update(self._current_id, data)
        else:
            saved = store.add(data)
            self._current_id = saved.get("id")

        self._refresh_list(self.type_filter.currentText())
        # 重选当前角色
        for i in range(self.character_list.count()):
            if self.character_list.item(i).text().startswith(name):
                self.character_list.setCurrentRow(i)
                break
        QMessageBox.information(self, "成功", f"角色 '{name}' 已保存")
