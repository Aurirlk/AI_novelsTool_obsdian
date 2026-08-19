"""
拆书页面
导入网文并分析其结构模式（规则分析，零LLM成本）
"""

import os
import re
import shutil
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QFileDialog, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit

_BOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "books")


def _split_chapters(text: str) -> list[dict]:
    """按'第X章'标题切分章节，返回 [{number, title, content}]"""
    pattern = re.compile(r"^(第[零一二三四五六七八九十百千万0-9]+[章回节卷][^。\n]{0,20})[ \t]*\n?", re.M)
    matches = list(pattern.finditer(text))

    chapters = []
    if not matches:
        return [{"number": 1, "title": "全文", "content": text}]

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapters.append({
            "number": i + 1,
            "title": m.group(1).strip(),
            "content": text[start:end].strip(),
        })
    return chapters


class AnalyzeWorker(QThread):
    """拆书分析后台任务"""

    done = pyqtSignal(object, str)  # (analysis, error)
    failed = pyqtSignal(str)

    def __init__(self, title, chapters, author, genre, parent=None):
        super().__init__(parent)
        self.title = title
        self.chapters = chapters
        self.author = author
        self.genre = genre

    def run(self):
        try:
            from src.learning.book_analyzer import BookAnalyzer
            analyzer = BookAnalyzer()
            analysis = analyzer.analyze_book(self.title, self.chapters, self.author, self.genre)
            self.done.emit(analysis, "")
        except Exception as e:
            self.failed.emit(str(e))


class BookPage(QWidget):
    """拆书页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()
        self._refresh_books()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("拆书分析")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        import_btn = ModernButton("导入小说", "primary")
        import_btn.clicked.connect(self._import_book)
        header.addWidget(import_btn)

        analyze_btn = ModernButton("分析模式", "secondary")
        analyze_btn.clicked.connect(self._analyze_patterns)
        header.addWidget(analyze_btn)

        layout.addLayout(header)

        # 主体区域
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：小说列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 小说类型过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("类型:")
        filter_layout.addWidget(filter_label)

        self.genre_filter = QComboBox()
        self.genre_filter.addItems(["全部", "玄幻", "都市", "科幻", "历史", "言情"])
        self.genre_filter.currentTextChanged.connect(self._filter_books)
        filter_layout.addWidget(self.genre_filter)

        left_layout.addLayout(filter_layout)

        # 小说列表
        self.book_list = QListWidget()
        self.book_list.currentTextChanged.connect(self._on_book_selected)
        left_layout.addWidget(self.book_list)

        # 操作按钮
        btn_layout = QHBoxLayout()

        delete_btn = ModernButton("删除", "danger")
        delete_btn.clicked.connect(self._delete_book)
        btn_layout.addWidget(delete_btn)

        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # 右侧：分析结果
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 小说信息
        info_group = QGroupBox("小说信息")
        info_form = QFormLayout(info_group)

        self.title_input = ModernInput("小说标题")
        info_form.addRow("标题", self.title_input)

        self.author_input = ModernInput("作者")
        info_form.addRow("作者", self.author_input)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["玄幻", "都市", "科幻", "历史", "言情", "其他"])
        info_form.addRow("类型", self.genre_combo)

        self.description_input = ModernTextEdit("小说简介...")
        self.description_input.setFixedHeight(80)
        info_form.addRow("简介", self.description_input)

        right_layout.addWidget(info_group)

        # 分析结果
        analysis_group = QGroupBox("分析结果")
        analysis_layout = QVBoxLayout(analysis_group)

        # 模式分析
        patterns_label = QLabel("发现的模式:")
        analysis_layout.addWidget(patterns_label)

        self.patterns_list = QListWidget()
        self.patterns_list.setFixedHeight(150)
        self.patterns_list.currentTextChanged.connect(self._on_pattern_selected)
        analysis_layout.addWidget(self.patterns_list)

        # 详细分析
        detail_label = QLabel("详细分析:")
        analysis_layout.addWidget(detail_label)

        self.analysis_detail = ModernTextEdit("选择一个模式查看详情...")
        self.analysis_detail.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_detail)

        # 操作按钮
        btn_layout = QHBoxLayout()

        apply_btn = ModernButton("应用到写作", "primary")
        apply_btn.clicked.connect(self._apply_to_writing)
        btn_layout.addWidget(apply_btn)

        export_btn = ModernButton("导出分析", "secondary")
        export_btn.clicked.connect(self._export_analysis)
        btn_layout.addWidget(export_btn)

        analysis_layout.addLayout(btn_layout)

        right_layout.addWidget(analysis_group)

        right_layout.addStretch()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        right_scroll.setWidget(right_panel)
        splitter.addWidget(right_scroll)

        # 设置分割比例
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    # ==================== 书籍管理 ====================

    def _book_dir(self, name: str) -> str:
        return os.path.join(_BOOKS_DIR, name)

    def _refresh_books(self):
        """从 data/books 扫描已导入书籍"""
        self.book_list.blockSignals(True)
        self.book_list.clear()
        if os.path.isdir(_BOOKS_DIR):
            for name in sorted(os.listdir(_BOOKS_DIR)):
                if os.path.isdir(self._book_dir(name)):
                    meta = self._load_meta(name)
                    genre = meta.get("genre", "")
                    self.book_list.addItem(f"{name} ({genre})" if genre else name)
        self.book_list.blockSignals(False)

    def _load_meta(self, name: str) -> dict:
        meta_path = os.path.join(self._book_dir(name), "meta.json")
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_meta(self, name: str, meta: dict):
        os.makedirs(self._book_dir(name), exist_ok=True)
        with open(os.path.join(self._book_dir(name), "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def _load_chapters(self, name: str) -> list[dict]:
        chapters_path = os.path.join(self._book_dir(name), "chapters.json")
        try:
            with open(chapters_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def _save_chapters(self, name: str, chapters: list[dict]):
        with open(os.path.join(self._book_dir(name), "chapters.json"), "w", encoding="utf-8") as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

    def _filter_books(self, genre):
        """过滤小说"""
        self.book_list.blockSignals(True)
        self.book_list.clear()
        if os.path.isdir(_BOOKS_DIR):
            for name in sorted(os.listdir(_BOOKS_DIR)):
                if not os.path.isdir(self._book_dir(name)):
                    continue
                meta = self._load_meta(name)
                if genre != "全部" and meta.get("genre") != genre:
                    continue
                self.book_list.addItem(f"{name} ({genre})" if genre else name)
        self.book_list.blockSignals(False)

    def _on_book_selected(self, selected_text):
        """小说选中事件"""
        if not selected_text:
            return
        name = selected_text.rsplit(" (", 1)[0]
        meta = self._load_meta(name)
        self.title_input.setText(meta.get("title", name))
        self.author_input.setText(meta.get("author", ""))
        idx = self.genre_combo.findText(meta.get("genre", "玄幻"))
        if idx >= 0:
            self.genre_combo.setCurrentIndex(idx)
        self.description_input.setPlainText(meta.get("description", ""))

        # 加载已有分析结果
        chapters = self._load_chapters(name)
        self.patterns_list.clear()
        if chapters:
            self.patterns_list.addItem(f"共 {len(chapters)} 章（点击右侧'分析模式'开始分析）")
        self.analysis_detail.setPlainText(meta.get("analysis_summary", ""))

    def _import_book(self):
        """导入小说：复制到 data/books 并切分章节"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择小说文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not file_path:
            return

        try:
            for encoding in ("utf-8", "gbk", "gb18030"):
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                QMessageBox.warning(self, "导入失败", "无法识别文件编码（支持 UTF-8 / GBK）")
                return
        except OSError as e:
            QMessageBox.warning(self, "导入失败", f"读取文件失败：{e}")
            return

        name = os.path.splitext(os.path.basename(file_path))[0]
        chapters = _split_chapters(text)

        book_dir = self._book_dir(name)
        os.makedirs(book_dir, exist_ok=True)
        # 保存原文副本
        try:
            shutil.copy2(file_path, os.path.join(book_dir, "原文.txt"))
        except OSError:
            pass
        self._save_chapters(name, chapters)
        self._save_meta(name, {
            "title": name,
            "author": "",
            "genre": self.genre_filter.currentText() if self.genre_filter.currentText() != "全部" else "玄幻",
            "description": f"共 {len(chapters)} 章",
            "analysis_summary": "",
        })

        self._refresh_books()
        QMessageBox.information(self, "导入成功", f"已导入 '{name}'（{len(chapters)} 个章节）")

    def _delete_book(self):
        """删除小说"""
        selected = self.book_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的小说")
            return

        name = selected.text().rsplit(" (", 1)[0]
        reply = QMessageBox.question(self, "确认删除", f"确定要删除 '{name}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            shutil.rmtree(self._book_dir(name), ignore_errors=True)
            self._refresh_books()

    # ==================== 分析 ====================

    def _analyze_patterns(self):
        """分析模式（规则分析，零成本）"""
        selected = self.book_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要分析的小说")
            return

        name = selected.text().rsplit(" (", 1)[0]
        chapters = self._load_chapters(name)
        if not chapters:
            QMessageBox.warning(self, "警告", "该书没有可分析的章节")
            return

        meta = self._load_meta(name)
        self.analysis_detail.setPlainText("正在分析小说模式（规则分析，无需API）...")

        self._worker = AnalyzeWorker(
            meta.get("title", name),
            chapters,
            meta.get("author", ""),
            meta.get("genre", ""),
        )
        self._worker.done.connect(lambda a, e: self._on_analysis_done(name, a))
        self._worker.failed.connect(self._on_analysis_failed)
        self._worker.start()

    def _on_analysis_done(self, name, analysis):
        """分析完成：填充模式列表和详情"""
        self.patterns_list.clear()

        def _add(key, label):
            items = getattr(analysis, key, [])
            if isinstance(items, str):
                items = [items]
            if items:
                self.patterns_list.addItem(label)
                for it in items[:6]:
                    self.patterns_list.addItem(f"  - {it}")

        _add("structure_pattern", "【结构模式】")
        _add("character_archetypes", "【人物原型】")
        _add("satisfaction_patterns", "【爽点模式】")
        _add("hook_patterns", "【钩子模式】")

        # 详情
        detail = []
        detail.append(f"## {analysis.title} 拆书分析")
        detail.append("")
        detail.append(f"- 章节数: {analysis.total_chapters}")
        detail.append(f"- 总字数: {analysis.total_words}")
        detail.append(f"- 平均每章: {analysis.avg_words_per_chapter} 字")
        detail.append("")
        if analysis.structure_pattern:
            detail.append(f"**结构模式**: {analysis.structure_pattern}")
        if analysis.key_takeaways:
            detail.append("")
            detail.append("**关键要点**:")
            for t in analysis.key_takeaways[:5]:
                detail.append(f"- {t}")
        if analysis.writing_style:
            detail.append("")
            detail.append(f"**写作风格**: {json.dumps(analysis.writing_style, ensure_ascii=False)[:300]}")
        if analysis.chapter_analyses:
            detail.append("")
            detail.append("**章节技法抽样**:")
            for ca in analysis.chapter_analyses[:5]:
                techniques = ca.techniques if isinstance(ca.techniques, list) else []
                detail.append(f"- 第{ca.chapter_num}章: {', '.join(techniques) if techniques else '常规写法'}")
        self.analysis_detail.setPlainText("\n".join(detail))

        # 保存分析摘要
        meta = self._load_meta(name)
        meta["analysis_summary"] = detail[0] + f"（{len(analysis.chapter_analyses)}章，{analysis.total_words}字）"
        self._save_meta(name, meta)

    def _on_analysis_failed(self, error):
        self.analysis_detail.setPlainText(f"分析失败：{error}")

    def _on_pattern_selected(self, text):
        """模式选中事件：展示选中模式对应详情"""
        pass

    # ==================== 应用/导出 ====================

    def _apply_to_writing(self):
        """应用到写作：生成仿写提示词并写入写作空间"""
        selected = self.book_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要应用的小说")
            return

        name = selected.text().rsplit(" (", 1)[0]
        meta = self._load_meta(name)
        analysis_summary = meta.get("analysis_summary", "")
        if not analysis_summary:
            QMessageBox.warning(self, "警告", "请先点击'分析模式'完成分析，再应用到写作")
            return

        try:
            from src.learning.book_analyzer import BookAnalyzer
            analyzer = BookAnalyzer()
            analysis = analyzer.analyze_book(
                meta.get("title", name),
                self._load_chapters(name),
                meta.get("author", ""),
                meta.get("genre", ""),
            )
            prompt = analyzer.generate_imitation_prompt(analysis)
        except Exception:
            prompt = f"请模仿《{meta.get('title', name)}》的写作风格进行创作。\n\n{analysis_summary}"

        from src.data.writing_space import get_writing_space
        ws = get_writing_space()
        try:
            import os as _os
            ws.save(_os.path.join(ws.root, "拆书仿写提示.md"), prompt)
        except Exception:
            # 无该书目录则创建
            ws.create_book("拆书分析")
            ws.save(_os.path.join(ws.root, "拆书分析", "拆书仿写提示.md"), prompt)

        QMessageBox.information(self, "已应用", "仿写提示已生成到写作空间：拆书仿写提示.md")

    def _export_analysis(self):
        """导出分析：保存 JSON 到用户选择位置"""
        selected = self.book_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要导出的小说")
            return

        name = selected.text().rsplit(" (", 1)[0]
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分析结果", f"{name}_分析.json", "JSON文件 (*.json)"
        )
        if not file_path:
            return
        if not file_path.endswith(".json"):
            file_path += ".json"

        try:
            from src.learning.book_analyzer import BookAnalyzer
            analysis = BookAnalyzer().analyze_book(
                name, self._load_chapters(name),
                self._load_meta(name).get("author", ""),
                self._load_meta(name).get("genre", ""),
            )
            BookAnalyzer().save_analysis(analysis, file_path)
            QMessageBox.information(self, "导出成功", f"分析结果已导出到：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出失败：{e}")


def create_book_page():
    """创建拆书页面"""
    return BookPage()
