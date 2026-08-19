"""
导出页面
导出小说为不同格式
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFormLayout, QComboBox, QCheckBox,
    QMessageBox, QFileDialog, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit


class ExportPage(QWidget):
    """导出页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._books = {}  # 书名 -> 章节列表
        self._init_ui()
        self._load_books()
    
    def _load_books(self):
        """从写作空间加载书籍列表"""
        try:
            from src.data.writing_space import get_writing_space
            ws = get_writing_space()
            tree = ws.list_tree()
        except Exception:
            tree = []
        
        self.book_combo.blockSignals(True)
        self.book_combo.clear()
        self._books = {}
        for node in tree:
            if node.get("type") != "book":
                continue
            self._books[node["name"]] = self._collect_chapters(node)
            self.book_combo.addItem(node["name"])
        if self.book_combo.count() == 0:
            self.book_combo.addItem("（无作品，请先到写作工作台创建）")
        self.book_combo.blockSignals(False)
        self._on_book_changed(self.book_combo.currentText())
    
    def _collect_chapters(self, book_node: dict) -> list[dict]:
        """递归收集一本书下的所有章节 [{number, title, content}]"""
        chapters = []
        for child in book_node.get("children", []):
            if child.get("type") == "chapter":
                title = child.get("name", f"第{len(chapters)+1}章")
                content = ""
                try:
                    with open(child["path"], "r", encoding="utf-8") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    try:
                        with open(child["path"], "r", encoding="gbk") as f:
                            content = f.read()
                    except (OSError, UnicodeDecodeError):
                        content = ""
                chapters.append({
                    "number": len(chapters) + 1,
                    "title": title,
                    "content": content,
                    "summary": "",
                })
            elif child.get("type") == "folder":
                chapters.extend(self._collect_chapters(child))
        return chapters

    def _on_book_changed(self, book_name):
        """作品切换：更新章节范围"""
        chapters = self._books.get(book_name, [])
        self.start_chapter.blockSignals(True)
        self.end_chapter.blockSignals(True)
        self.start_chapter.clear()
        self.end_chapter.clear()
        if not chapters:
            self.start_chapter.addItem("1")
            self.end_chapter.addItem("1")
        else:
            count = len(chapters)
            self.start_chapter.addItems([str(i) for i in range(1, count + 1)])
            self.end_chapter.addItems([str(i) for i in range(1, count + 1)])
            self.end_chapter.setCurrentIndex(count - 1)
        self.start_chapter.blockSignals(False)
        self.end_chapter.blockSignals(False)
    
    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(container)
        outer.addWidget(scroll)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("导出")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # 导出设置
        export_group = QGroupBox("导出设置")
        export_form = QFormLayout(export_group)
        
        # 作品选择
        self.book_combo = QComboBox()
        self.book_combo.currentTextChanged.connect(self._on_book_changed)
        export_form.addRow("选择作品", self.book_combo)

        # 格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["TXT", "Markdown", "Word", "PDF"])
        export_form.addRow("导出格式", self.format_combo)
        
        # 文件名
        self.filename_input = ModernInput("导出文件名")
        export_form.addRow("文件名", self.filename_input)
        
        # 保存位置
        location_layout = QHBoxLayout()
        
        self.location_input = ModernInput("保存位置")
        location_layout.addWidget(self.location_input)
        
        browse_btn = ModernButton("浏览", "secondary")
        browse_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(browse_btn)
        
        export_form.addRow("保存位置", location_layout)
        
        # 章节选择
        chapter_group = QGroupBox("章节选择")
        chapter_layout = QVBoxLayout(chapter_group)
        
        self.all_chapters_check = QCheckBox("导出所有章节")
        self.all_chapters_check.setChecked(True)
        chapter_layout.addWidget(self.all_chapters_check)
        
        range_layout = QHBoxLayout()
        
        self.start_chapter = QComboBox()
        self.start_chapter.addItems([str(i) for i in range(1, 101)])
        range_layout.addWidget(QLabel("从"))
        range_layout.addWidget(self.start_chapter)
        
        self.end_chapter = QComboBox()
        self.end_chapter.addItems([str(i) for i in range(1, 101)])
        self.end_chapter.setCurrentIndex(9)
        range_layout.addWidget(QLabel("到"))
        range_layout.addWidget(self.end_chapter)
        
        chapter_layout.addLayout(range_layout)
        
        export_form.addRow("章节", chapter_group)
        
        # 导出选项
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout(options_group)
        
        self.include_title_check = QCheckBox("包含标题")
        self.include_title_check.setChecked(True)
        options_layout.addWidget(self.include_title_check)
        
        self.include_summary_check = QCheckBox("包含摘要")
        options_layout.addWidget(self.include_summary_check)
        
        self.include_metadata_check = QCheckBox("包含元数据")
        options_layout.addWidget(self.include_metadata_check)
        
        export_form.addRow("选项", options_group)
        
        layout.addWidget(export_group)
        
        # 预览
        preview_label = QLabel("预览")
        preview_label.setObjectName("section_title")
        layout.addWidget(preview_label)
        
        self.preview = ModernTextEdit("点击预览查看导出内容...")
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        preview_btn = ModernButton("预览", "secondary")
        preview_btn.clicked.connect(self._preview_export)
        btn_layout.addWidget(preview_btn)
        
        self.email_btn = ModernButton("投递到编辑邮箱", "secondary")
        self.email_btn.clicked.connect(self._send_to_editor)
        btn_layout.addWidget(self.email_btn)

        export_btn = ModernButton("导出", "primary")
        export_btn.clicked.connect(self._export)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)

    def retranslate(self):
        """语言切换后刷新界面文字"""
        from ..i18n import tr
        self.email_btn.setText(tr("email.send_to_editor"))
    
    def _browse_location(self):
        """浏览保存位置"""
        directory = QFileDialog.getExistingDirectory(self, "选择保存位置")
        if directory:
            self.location_input.setText(directory)
    
    def _selected_chapters(self) -> list[dict]:
        """获取当前选中的章节列表"""
        book_name = self.book_combo.currentText()
        chapters = self._books.get(book_name, [])
        if not chapters:
            return []
        if self.all_chapters_check.isChecked():
            return chapters
        start = max(1, int(self.start_chapter.currentText()))
        end = min(len(chapters), int(self.end_chapter.currentText()))
        return chapters[start - 1:end]

    def _preview_export(self):
        """预览导出"""
        chapters = self._selected_chapters()
        if not chapters:
            self.preview.setPlainText("当前作品没有可导出的章节。请先到写作工作台创建章节。")
            return

        lines = []
        for ch in chapters:
            lines.append(f"## {ch['title']}\n")
            content = ch.get("content", "").strip()
            lines.append(content if content else "（空章节）")
            lines.append("\n---\n")
        self.preview.setPlainText("\n".join(lines))

    def _export(self):
        """导出"""
        # 获取导出设置
        export_format = self.format_combo.currentText()
        filename = self.filename_input.text().strip()
        location = self.location_input.text().strip()
        book_name = self.book_combo.currentText()

        if not book_name or book_name.startswith("（"):
            QMessageBox.warning(self, "警告", "请先选择要导出的作品")
            return

        if not filename:
            QMessageBox.warning(self, "警告", "请输入文件名")
            return

        if not location:
            QMessageBox.warning(self, "警告", "请选择保存位置")
            return

        chapters = self._selected_chapters()
        if not chapters:
            QMessageBox.warning(self, "警告", "当前作品没有可导出的章节")
            return

        # 显示进度条
        self.progress.setVisible(True)
        self.progress.setValue(10)

        try:
            from src.utils.exporter import NovelExporter

            exporter = NovelExporter(output_dir=location)
            if export_format == "TXT":
                filepath = exporter.export_txt(book_name, chapters, filename=f"{filename}.txt")
            elif export_format == "Markdown":
                filepath = exporter.export_markdown(book_name, chapters, filename=f"{filename}.md")
            elif export_format == "Word":
                filepath = exporter.export_word(book_name, chapters, filename=f"{filename}.docx")
            elif export_format == "PDF":
                filepath = exporter.export_pdf(book_name, chapters, filename=filename)
                if filepath.endswith(".docx"):
                    QMessageBox.warning(self, "提示", "未检测到 Microsoft Word，已降级导出为 DOCX 格式")
            else:
                QMessageBox.warning(self, "警告", f"暂不支持导出为 {export_format} 格式")
                self.progress.setVisible(False)
                return

            self.progress.setValue(100)
            QMessageBox.information(self, "导出成功", f"已导出 {len(chapters)} 个章节到：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误：\n{e}")
        finally:
            self.progress.setVisible(False)

    def _send_to_editor(self):
        """一键投递到编辑邮箱：导出章节并作为附件发送"""
        from ..i18n import tr
        from src.utils.email_sender import get_email_config

        book_name = self.book_combo.currentText()
        if not book_name or book_name.startswith("（"):
            QMessageBox.warning(self, "警告", "请先选择要投递的作品")
            return

        chapters = self._selected_chapters()
        if not chapters:
            QMessageBox.warning(self, "警告", tr("email.no_chapters"))
            return

        cfg = get_email_config()
        if not cfg.get("sender_email") or not cfg.get("auth_code"):
            QMessageBox.warning(self, "未配置邮箱", tr("email.no_config"))
            return
        if not cfg.get("editor_email"):
            QMessageBox.warning(self, "未配置编辑邮箱", tr("email.no_editor"))
            return

        # 询问是否附带章节文件附件
        reply = QMessageBox.question(
            self, tr("email.confirm"),
            f"将把《{book_name}》的 {len(chapters)} 个章节投递到编辑邮箱 {cfg['editor_email']}，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 生成附件（TXT，临时目录）
        import tempfile
        tmp_dir = tempfile.mkdtemp(prefix="novel_delivery_")
        attachments = []
        try:
            from src.utils.exporter import NovelExporter
            exporter = NovelExporter(output_dir=tmp_dir)
            filepath = exporter.export_txt(book_name, chapters, filename=f"{book_name}_投稿.txt")
            attachments = [filepath]
        except Exception:
            attachments = []

        self.progress.setVisible(True)
        self.progress.setValue(50)

        try:
            from src.utils.email_sender import send_chapter_to_editor
            body_text = chapters[0].get("content", "") if len(chapters) == 1 else ""
            ok, msg = send_chapter_to_editor(
                book_title=book_name,
                chapter_title=f"共{len(chapters)}章",
                content=body_text,
                attachments=attachments,
            )
            if ok:
                self.progress.setValue(100)
                QMessageBox.information(self, tr("email.delivered"), msg)
            else:
                QMessageBox.critical(self, tr("email.failed"), msg)
        except Exception as e:
            QMessageBox.critical(self, tr("email.failed"), f"投递过程中发生错误：\n{e}")
        finally:
            self.progress.setVisible(False)
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
