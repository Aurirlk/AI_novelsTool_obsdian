"""
批评师页面
提供大纲批评、章节批评、写作陪练等功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QTextEdit, QGroupBox, QFormLayout,
    QComboBox, QMessageBox, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit


def _scrollable(widget):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setWidget(widget)
    return scroll


class OutlineCriticWorker(QThread):
    """大纲批评后台任务"""

    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, outline_text, parent=None):
        super().__init__(parent)
        self.outline_text = outline_text

    def run(self):
        try:
            from src.agents.outline_critic import OutlineCritic
            critic = OutlineCritic()
            result = critic.critique_outline(self.outline_text)
            self.done.emit(result.get("report", "批评完成，但未生成报告。"))
        except Exception as e:
            self.failed.emit(str(e))


class ChapterCriticWorker(QThread):
    """章节批评后台任务"""

    done = pyqtSignal(object)  # {"report": str, "issues": list}
    failed = pyqtSignal(str)

    def __init__(self, chapter_text, parent=None):
        super().__init__(parent)
        self.chapter_text = chapter_text

    def run(self):
        try:
            from src.agents.chapter_critic import ChapterCritic
            critic = ChapterCritic()
            result = critic.execute(None, chapter_text=self.chapter_text, chapter_num=0)
            self.done.emit({
                "report": result.get("report", "批评完成，但未生成报告。"),
                "issues": result.get("issues", []),
            })
        except Exception as e:
            self.failed.emit(str(e))


class ChapterReworkWorker(QThread):
    """按审核意见重写章节（手动触发回炉）"""

    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, chapter_text, issues, parent=None):
        super().__init__(parent)
        self.chapter_text = chapter_text
        self.issues = issues

    def run(self):
        try:
            from src.utils.llm import get_llm_client
            client = get_llm_client()
            issues_text = "\n".join(
                f"- [{i.get('severity', '中')}] {i.get('description', '')}"
                for i in self.issues[:15])
            prompt = f"""请根据以下审核意见重写章节。保留原有剧情、人物设定和行文节奏，只修正意见中指出的问题。
【审核意见】
{issues_text or "无具体问题，请整体优化文笔与节奏"}

【原章节】
{self.chapter_text[:4000]}"""
            result = client.chat(
                prompt,
                system_prompt="你是职业网文写手。重写时保持网文节奏与可读性，直接输出重写后的完整正文，不要任何解释。")
            self.done.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class WritingCoachWorker(QThread):
    """写作陪练后台任务"""

    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, text, mode, parent=None):
        super().__init__(parent)
        self.text = text
        self.mode = mode

    def run(self):
        try:
            mode_map = {
                "发现盲点": "find_blind_spots",
                "发现局限": "find_limitations",
                "改进建议": "suggest_improvements",
            }
            from src.agents.writing_coach import WritingCoach
            coach = WritingCoach()
            result = coach.execute(None, text=self.text, mode=mode_map.get(self.mode, "find_blind_spots"))
            self.done.emit(result.get("report", "分析完成，但未生成报告。"))
        except Exception as e:
            self.failed.emit(str(e))


class CriticPage(QWidget):
    """批评师页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._rework_worker = None
        self._last_chapter_issues = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("批评师")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

        # 创建标签页
        tabs = QTabWidget()

        # 大纲批评标签页
        outline_tab = self._create_outline_critic_tab()
        tabs.addTab(_scrollable(outline_tab), "大纲批评")

        # 章节批评标签页
        chapter_tab = self._create_chapter_critic_tab()
        tabs.addTab(_scrollable(chapter_tab), "章节批评")

        # 写作陪练标签页
        coach_tab = self._create_writing_coach_tab()
        tabs.addTab(_scrollable(coach_tab), "写作陪练")

        layout.addWidget(tabs)

    def _create_outline_critic_tab(self):
        """创建大纲批评标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 说明
        desc = QLabel("大纲批评：站在刁钻刻薄的角度，全盘挑错、批判你的大纲")
        desc.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        layout.addWidget(desc)

        # 输入区域
        input_group = QGroupBox("输入大纲")
        input_layout = QVBoxLayout(input_group)

        self.outline_input = ModernTextEdit("请粘贴你的大纲内容...")
        self.outline_input.setMinimumHeight(200)
        input_layout.addWidget(self.outline_input)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.outline_btn = ModernButton("开始批评", "primary")
        self.outline_btn.clicked.connect(self._critique_outline)
        btn_layout.addWidget(self.outline_btn)

        clear_btn = ModernButton("清空", "secondary")
        clear_btn.clicked.connect(lambda: self.outline_input.clear())
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)

        layout.addWidget(input_group)

        # 输出区域
        output_group = QGroupBox("批评结果")
        output_layout = QVBoxLayout(output_group)

        self.outline_output = ModernTextEdit("批评结果将显示在这里...")
        self.outline_output.setReadOnly(True)
        output_layout.addWidget(self.outline_output)

        layout.addWidget(output_group)

        return tab

    def _create_chapter_critic_tab(self):
        """创建章节批评标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 说明
        desc = QLabel("章节批评：检查逻辑漏洞、情节硬伤、常识错误")
        desc.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        layout.addWidget(desc)

        # 输入区域
        input_group = QGroupBox("输入章节")
        input_layout = QVBoxLayout(input_group)

        self.chapter_input = ModernTextEdit("请粘贴你的章节内容...")
        self.chapter_input.setMinimumHeight(200)
        input_layout.addWidget(self.chapter_input)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.chapter_btn = ModernButton("开始批评", "primary")
        self.chapter_btn.clicked.connect(self._critique_chapter)
        btn_layout.addWidget(self.chapter_btn)

        clear_btn = ModernButton("清空", "secondary")
        clear_btn.clicked.connect(lambda: self.chapter_input.clear())
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)

        layout.addWidget(input_group)

        # 输出区域
        output_group = QGroupBox("批评结果")
        output_layout = QVBoxLayout(output_group)

        self.chapter_output = ModernTextEdit("批评结果将显示在这里...")
        self.chapter_output.setReadOnly(True)
        output_layout.addWidget(self.chapter_output)

        # 回炉操作：按审核意见重写（手动触发）
        rework_row = QHBoxLayout()
        self.rework_btn = ModernButton("按审核意见重写", "secondary")
        self.rework_btn.setEnabled(False)
        self.rework_btn.setToolTip("把审核意见和原文交给写作智能体重写，修正指出的问题")
        self.rework_btn.clicked.connect(self._rework_chapter)
        rework_row.addWidget(self.rework_btn)

        copy_result_btn = ModernButton("复制结果", "secondary")
        copy_result_btn.clicked.connect(self._copy_chapter_result)
        rework_row.addWidget(copy_result_btn)

        rework_row.addStretch()
        output_layout.addLayout(rework_row)

        layout.addWidget(output_group)

        return tab

    def _rework_chapter(self):
        """按审核意见重写章节（手动触发回炉闭环）"""
        content = self.chapter_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "警告", "请先在输入区粘贴要重写的章节内容")
            return
        if not getattr(self, "_last_chapter_issues", None):
            QMessageBox.warning(self, "提示", "请先完成一次章节批评，再按审核意见重写")
            return
        if not self._check_api():
            return

        self.rework_btn.setEnabled(False)
        self.chapter_output.setText("正在按审核意见重写，请稍候...")

        self._rework_worker = ChapterReworkWorker(content, self._last_chapter_issues, self)
        self._rework_worker.done.connect(self._on_rework_done)
        self._rework_worker.failed.connect(lambda e: self._on_rework_failed(e))
        self._rework_worker.start()

    def _on_rework_done(self, text):
        self.chapter_output.setText(f"【重写结果】（可复制到输入区或直接采用）\n\n{text}")
        self.rework_btn.setEnabled(True)

    def _on_rework_failed(self, error):
        self.chapter_output.setText(f"重写失败：{error}")
        self.rework_btn.setEnabled(True)

    def _copy_chapter_result(self):
        from PyQt6.QtWidgets import QApplication
        text = self.chapter_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _create_writing_coach_tab(self):
        """创建写作陪练标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 说明
        desc = QLabel("写作陪练：帮助你发现写作盲点、局限，提供改进建议")
        desc.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        layout.addWidget(desc)

        # 模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("分析模式:")
        mode_layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "发现盲点",
            "发现局限",
            "改进建议"
        ])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()

        layout.addLayout(mode_layout)

        # 输入区域
        input_group = QGroupBox("输入文本")
        input_layout = QVBoxLayout(input_group)

        self.coach_input = ModernTextEdit("请粘贴你的文本内容...")
        self.coach_input.setMinimumHeight(200)
        input_layout.addWidget(self.coach_input)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.coach_btn = ModernButton("开始分析", "primary")
        self.coach_btn.clicked.connect(self._analyze_writing)
        btn_layout.addWidget(self.coach_btn)

        clear_btn = ModernButton("清空", "secondary")
        clear_btn.clicked.connect(lambda: self.coach_input.clear())
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)

        layout.addWidget(input_group)

        # 输出区域
        output_group = QGroupBox("分析结果")
        output_layout = QVBoxLayout(output_group)

        self.coach_output = ModernTextEdit("分析结果将显示在这里...")
        self.coach_output.setReadOnly(True)
        output_layout.addWidget(self.coach_output)

        layout.addWidget(output_group)

        return tab

    def _check_api(self) -> bool:
        """预检API密钥是否已配置"""
        try:
            from src.utils.llm import has_api_key
            if has_api_key():
                return True
            QMessageBox.warning(self, "未配置API", "请先到 设置 → LLM 配置API密钥")
            return False
        except Exception:
            QMessageBox.warning(self, "未配置API", "请先到 设置 → LLM 配置API密钥")
            return False

    def _critique_outline(self):
        """批评大纲"""
        content = self.outline_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "警告", "请先输入大纲内容")
            return
        if not self._check_api():
            return

        self.outline_btn.setEnabled(False)
        self.outline_output.setText("正在批评大纲，请稍候...")

        self._worker = OutlineCriticWorker(content)
        self._worker.done.connect(lambda r: self._on_outline_done(r))
        self._worker.failed.connect(lambda e: self._on_outline_failed(e))
        self._worker.start()

    def _on_outline_done(self, result):
        self.outline_output.setText(result)
        self.outline_btn.setEnabled(True)

    def _on_outline_failed(self, error):
        self.outline_output.setText(f"批评失败：{error}")
        self.outline_btn.setEnabled(True)

    def _critique_chapter(self):
        """批评章节"""
        content = self.chapter_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "警告", "请先输入章节内容")
            return
        if not self._check_api():
            return

        self.chapter_btn.setEnabled(False)
        self.rework_btn.setEnabled(False)
        self._last_chapter_issues = None
        self.chapter_output.setText("正在批评章节，请稍候...")

        self._worker = ChapterCriticWorker(content)
        self._worker.done.connect(lambda r: self._on_chapter_done(r))
        self._worker.failed.connect(lambda e: self._on_chapter_failed(e))
        self._worker.start()

    def _on_chapter_done(self, result):
        report = result.get("report", "") if isinstance(result, dict) else str(result)
        self.chapter_output.setText(report)
        self._last_chapter_issues = result.get("issues", []) if isinstance(result, dict) else []
        self.rework_btn.setEnabled(bool(self._last_chapter_issues))
        self.chapter_btn.setEnabled(True)

    def _on_chapter_failed(self, error):
        self.chapter_output.setText(f"批评失败：{error}")
        self.chapter_btn.setEnabled(True)

    def _analyze_writing(self):
        """分析写作"""
        content = self.coach_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "警告", "请先输入文本内容")
            return
        if not self._check_api():
            return

        mode = self.mode_combo.currentText()

        self.coach_btn.setEnabled(False)
        self.coach_output.setText(f"正在分析写作（模式：{mode}），请稍候...")

        self._worker = WritingCoachWorker(content, mode)
        self._worker.done.connect(lambda r: self._on_coach_done(r))
        self._worker.failed.connect(lambda e: self._on_coach_failed(e))
        self._worker.start()

    def _on_coach_done(self, result):
        self.coach_output.setText(result)
        self.coach_btn.setEnabled(True)

    def _on_coach_failed(self, error):
        self.coach_output.setText(f"分析失败：{error}")
        self.coach_btn.setEnabled(True)


def create_critic_page():
    """创建批评师页面"""
    return CriticPage()
