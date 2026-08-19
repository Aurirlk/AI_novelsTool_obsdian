"""
大纲页面
左侧为历史大纲库（小说大纲/目录），右侧查看与编辑
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QComboBox, QPushButton, QInputDialog, QFileDialog
)
from PyQt6.QtCore import Qt
import os

from ..professional_components import ProfessionalTextEdit as ModernTextEdit


class OutlinePage(QWidget):
    """大纲页面（接入历史大纲库）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_work = None
        self._init_ui()
        self._load_library()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("大纲库")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self._load_library)
        header.addWidget(refresh_btn)

        backup_btn = QPushButton("备份")
        backup_btn.setObjectName("btn_secondary")
        backup_btn.setFixedHeight(36)
        backup_btn.clicked.connect(self._backup_library)
        header.addWidget(backup_btn)

        restore_btn = QPushButton("恢复")
        restore_btn.setObjectName("btn_secondary")
        restore_btn.setFixedHeight(36)
        restore_btn.clicked.connect(self._restore_library)
        header.addWidget(restore_btn)

        layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：库浏览
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.category_combo)

        # 分类操作
        cat_btn_row = QHBoxLayout()
        new_cat_btn = QPushButton("新建分类")
        new_cat_btn.setObjectName("btn_secondary")
        new_cat_btn.setFixedHeight(30)
        new_cat_btn.clicked.connect(self._create_category)
        cat_btn_row.addWidget(new_cat_btn)

        del_cat_btn = QPushButton("删除分类")
        del_cat_btn.setObjectName("btn_danger")
        del_cat_btn.setFixedHeight(30)
        del_cat_btn.clicked.connect(self._delete_category)
        cat_btn_row.addWidget(del_cat_btn)
        left_layout.addLayout(cat_btn_row)

        self.work_list = QListWidget()
        self.work_list.currentItemChanged.connect(self._on_work_selected)
        left_layout.addWidget(self.work_list)

        # 作品操作
        work_btn_row = QHBoxLayout()
        new_work_btn = QPushButton("新建作品")
        new_work_btn.setObjectName("btn_primary")
        new_work_btn.setFixedHeight(30)
        new_work_btn.clicked.connect(self._create_work)
        work_btn_row.addWidget(new_work_btn)

        rename_work_btn = QPushButton("重命名")
        rename_work_btn.setObjectName("btn_secondary")
        rename_work_btn.setFixedHeight(30)
        rename_work_btn.clicked.connect(self._rename_work)
        work_btn_row.addWidget(rename_work_btn)

        del_work_btn = QPushButton("删除作品")
        del_work_btn.setObjectName("btn_danger")
        del_work_btn.setFixedHeight(30)
        del_work_btn.clicked.connect(self._delete_work)
        work_btn_row.addWidget(del_work_btn)
        left_layout.addLayout(work_btn_row)

        self.count_label = QLabel("")
        self.count_label.setObjectName("chat_hint")
        left_layout.addWidget(self.count_label)

        splitter.addWidget(left_panel)

        # 右侧：查看/编辑
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        info_layout = QHBoxLayout()

        self.work_title_label = QLabel("选择左侧作品查看大纲")
        self.work_title_label.setObjectName("section_title")
        info_layout.addWidget(self.work_title_label)
        info_layout.addStretch()

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["大纲", "细纲"])
        self.kind_combo.currentTextChanged.connect(self._on_kind_changed)
        info_layout.addWidget(self.kind_combo)

        save_btn = QPushButton("保存修改")
        save_btn.setObjectName("btn_primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save_content)
        info_layout.addWidget(save_btn)

        right_layout.addLayout(info_layout)

        self.content_edit = ModernTextEdit("大纲内容将显示在这里...")
        right_layout.addWidget(self.content_edit)

        self.status_label = QLabel("")
        self.status_label.setObjectName("chat_hint")
        right_layout.addWidget(self.status_label)

        splitter.addWidget(right_panel)
        splitter.setSizes([280, 720])

        layout.addWidget(splitter)

    # ==================== 数据加载 ====================

    def _load_library(self):
        from src.data.outline_library import get_outline_library
        library = get_outline_library()
        library.refresh()

        current = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("全部分类")
        for category in library.list_categories():
            self.category_combo.addItem(category)
        idx = self.category_combo.findText(current)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)

        self._refresh_work_list()

    def _backup_library(self):
        """备份大纲库：将整个 小说大纲 目录打包为 zip"""
        import shutil
        from datetime import datetime
        from src.data.outline_library import get_outline_library

        library_dir = get_outline_library().library_dir
        default_name = f"大纲库备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "备份大纲库", default_name, "ZIP压缩包 (*.zip)"
        )
        if not file_path:
            return
        if not file_path.endswith(".zip"):
            file_path += ".zip"

        try:
            shutil.make_archive(file_path[:-4], "zip", library_dir)
            QMessageBox.information(self, "备份完成", f"大纲库已备份到：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"备份失败：{e}")

    def _restore_library(self):
        """恢复大纲库：从 zip 解压合并回 小说大纲 目录"""
        import shutil
        import tempfile
        import zipfile
        from src.data.outline_library import get_outline_library

        reply = QMessageBox.question(
            self, "确认恢复",
            "恢复会将备份中的分类/作品合并进当前大纲库（同名作品将被覆盖）。确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "", "ZIP压缩包 (*.zip)"
        )
        if not file_path:
            return

        library_dir = get_outline_library().library_dir

        try:
            tmp_dir = tempfile.mkdtemp(prefix="outline_restore_")
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extractall(tmp_dir)
            os.makedirs(library_dir, exist_ok=True)
            restored = 0
            for entry in os.listdir(tmp_dir):
                src = os.path.join(tmp_dir, entry)
                dst = os.path.join(library_dir, entry)
                if os.path.isdir(src):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    restored += 1
                elif os.path.isfile(src):
                    shutil.copy2(src, dst)
                    restored += 1
            shutil.rmtree(tmp_dir, ignore_errors=True)
            self._load_library()
            QMessageBox.information(self, "恢复完成", f"已恢复 {restored} 个分类/文件")
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"恢复失败：{e}")

    def _refresh_work_list(self):
        from src.data.outline_library import get_outline_library
        library = get_outline_library()

        category = self.category_combo.currentText()
        works = library.list_works(None if category == "全部分类" else category)

        self.work_list.clear()
        for work in works:
            item = QListWidgetItem(f"{work.title}")
            item.setData(Qt.ItemDataRole.UserRole, work)
            item.setToolTip(f"{work.category} / {work.title}")
            self.work_list.addItem(item)

        self.count_label.setText(f"共 {len(works)} 部作品")

    # ==================== 分类增删 ====================

    def _create_category(self):
        name, ok = QInputDialog.getText(self, "新建分类", "分类名称（如：玄幻、无限流）:")
        if not ok or not name.strip():
            return
        from src.data.outline_library import get_outline_library
        success, msg = get_outline_library().create_category(name)
        if success:
            self._load_library()
            self.category_combo.setCurrentText(msg)
        else:
            QMessageBox.warning(self, "失败", msg)

    def _delete_category(self):
        category = self.category_combo.currentText()
        if not category or category == "全部分类":
            QMessageBox.warning(self, "提示", "请先选择一个具体分类")
            return
        from src.data.outline_library import get_outline_library
        library = get_outline_library()
        works = library.list_works(category)
        if works:
            QMessageBox.warning(
                self, "无法删除",
                f"分类「{category}」下还有 {len(works)} 部作品。\n请先删除该分类下的所有作品，再删除分类。")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定删除空分类「{category}」吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        success, msg = library.delete_category(category)
        if success:
            self._load_library()
        else:
            QMessageBox.warning(self, "失败", msg)

    # ==================== 作品增删改 ====================

    def _create_work(self):
        category = self.category_combo.currentText()
        if not category or category == "全部分类":
            QMessageBox.warning(self, "提示", "请先选择一个具体分类，再新建作品")
            return
        title, ok = QInputDialog.getText(self, "新建作品", "作品名称:")
        if not ok or not title.strip():
            return
        from src.data.outline_library import get_outline_library
        success, result = get_outline_library().create_work(category, title)
        if success:
            self._load_library()
            # 选中新作品
            for i in range(self.work_list.count()):
                item = self.work_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole).title == result.title:
                    self.work_list.setCurrentItem(item)
                    break
        else:
            QMessageBox.warning(self, "失败", result)

    def _rename_work(self):
        if self._current_work is None:
            QMessageBox.warning(self, "提示", "请先选择一部作品")
            return
        new_title, ok = QInputDialog.getText(
            self, "重命名作品", "新名称:", text=self._current_work.title)
        if not ok or not new_title.strip() or new_title == self._current_work.title:
            return
        from src.data.outline_library import get_outline_library
        success, result = get_outline_library().rename_work(self._current_work, new_title)
        if success:
            self._load_library()
            self._current_work = result
            self.work_title_label.setText(f"{result.category} / {result.title}")
        else:
            QMessageBox.warning(self, "失败", result)

    def _delete_work(self):
        if self._current_work is None:
            QMessageBox.warning(self, "提示", "请先选择一部作品")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除作品「{self._current_work.title}」吗？\n将删除其大纲和细纲文件，不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        from src.data.outline_library import get_outline_library
        success, msg = get_outline_library().delete_work(self._current_work)
        if success:
            self._current_work = None
            self.work_title_label.setText("选择左侧作品查看大纲")
            self.content_edit.setPlainText("")
            self._load_library()
        else:
            QMessageBox.warning(self, "失败", msg)

    # ==================== 事件 ====================

    def _on_category_changed(self, _):
        self._refresh_work_list()

    def _on_work_selected(self, current, _previous):
        if current is None:
            return
        self._current_work = current.data(Qt.ItemDataRole.UserRole)
        self.work_title_label.setText(f"{self._current_work.category} / {self._current_work.title}")
        self._show_content()

    def _on_kind_changed(self, _):
        if self._current_work is not None:
            self._show_content()

    def _show_content(self):
        from src.data.outline_library import get_outline_library
        library = get_outline_library()

        kind = "outline" if self.kind_combo.currentText() == "大纲" else "detail"
        content = library.read_work(self._current_work, kind)
        self.content_edit.setPlainText(content)
        self.status_label.setText(f"{len(content)} 字")

    def _save_content(self):
        if self._current_work is None:
            QMessageBox.warning(self, "警告", "请先选择一部作品")
            return

        kind = self.kind_combo.currentText()
        file_path = self._current_work.outline_file if kind == "大纲" else self._current_work.detail_file
        if not file_path:
            QMessageBox.warning(self, "警告", f"该作品没有{kind}文件")
            return

        reply = QMessageBox.question(
            self, "确认保存",
            f"将把修改写回：\n{file_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.content_edit.toPlainText())
            self.status_label.setText("已保存")
        except OSError as e:
            QMessageBox.warning(self, "保存失败", str(e))
