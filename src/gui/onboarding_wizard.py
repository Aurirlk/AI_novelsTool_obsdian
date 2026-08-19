"""
使用向导（首次启动引导配置 API）
检测到未配置任何 API 密钥时弹出，引导用户完成配置，防止 AI 功能不可用
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class ConnectionTestWorker(QThread):
    """连接测试后台任务"""

    result = pyqtSignal(bool, str)

    def __init__(self, provider, model, api_key, base_url, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def run(self):
        try:
            from openai import OpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            client = OpenAI(**kwargs)
            client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            self.result.emit(True, f"连接成功：{self.model}")
        except Exception as e:
            self.result.emit(False, f"连接失败：{e}")


class OnboardingWizard(QDialog):
    """首次启动配置向导"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用 AI 写作助手")
        self.setModal(True)
        self.setMinimumWidth(560)
        self._test_worker = None
        self._init_ui()
        self._load_providers()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 标题
        title = QLabel("欢迎使用 AI 写作助手")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "本工具的所有 AI 功能（对话、写作、批评、拆书等）都需要调用大模型 API。\n"
            "请先配置你自己的 API 密钥（自带API，即存即用），否则 AI 功能将无法使用。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8e8e8e; font-size: 13px;")
        layout.addWidget(desc)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(line)

        # 配置表单
        form = QFormLayout()
        form.setSpacing(12)

        self.provider_combo = QComboBox()
        form.addRow("提供商", self.provider_combo)

        self.model_combo = QComboBox()
        form.addRow("模型", self.model_combo)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("粘贴你的 API 密钥")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API 密钥", self.key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("可选，留空使用默认接口地址")
        form.addRow("接口地址(可选)", self.base_url_input)

        layout.addLayout(form)

        # 测试连接
        test_btn = QPushButton("测试连接")
        test_btn.setObjectName("btn_secondary")
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 提示
        hint = QLabel(
            "提示：没有 API 密钥？可先到对应官网免费注册获取（如 DeepSeek / 智谱AI / OpenAI）。\n"
            "跳过配置后，AI 功能不可用，可随时到「系统设置 → LLM」补充配置。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        layout.addWidget(hint)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        skip_btn = QPushButton("跳过")
        skip_btn.setObjectName("btn_secondary")
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)

        save_btn = QPushButton("保存并开始使用")
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self._save_and_continue)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_providers(self):
        """加载提供商列表（仅 BYOK：需要用户自己密钥的）"""
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()

        default_provider = "deepseek"
        try:
            default_provider = sm.get_setting("generation", "default_provider", "deepseek")
        except Exception:
            pass

        self._provider_data = {}
        default_idx = 0
        for idx, p in enumerate(sm.list_providers()):
            # 跳过本地服务（ollama/glm 本地不需要密钥，不引导）
            if not p.get("requires_key", True):
                continue
            self._provider_data[p["id"]] = p
            self.provider_combo.addItem(p["name"], p["id"])
            if p["id"] == default_provider:
                default_idx = self.provider_combo.count() - 1

        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        if self.provider_combo.count() > 0:
            self.provider_combo.setCurrentIndex(default_idx)
        self._on_provider_changed()

    def _on_provider_changed(self):
        """提供商切换：更新模型列表"""
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return
        p = self._provider_data.get(provider_id, {})
        self.model_combo.clear()
        for m in p.get("models", []):
            self.model_combo.addItem(m.get("name", m.get("id")), m.get("id"))

    def _test_connection(self):
        """测试连接"""
        provider_id = self.provider_combo.currentData()
        api_key = self.key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API 密钥")
            return

        model = self.model_combo.currentData()
        base_url = self.base_url_input.text().strip() or None

        self.status_label.setText("正在测试连接...")
        self._test_worker = ConnectionTestWorker(provider_id, model, api_key, base_url, self)
        self._test_worker.result.connect(self._on_test_result)
        self._test_worker.start()

    def _on_test_result(self, ok, msg):
        self.status_label.setText(msg)
        if ok:
            self.status_label.setStyleSheet("color: #2e7d32; font-size: 12px;")
        else:
            self.status_label.setStyleSheet("color: #c62828; font-size: 12px;")

    def _save_and_continue(self):
        """保存配置并进入应用"""
        provider_id = self.provider_combo.currentData()
        api_key = self.key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API 密钥（或点「跳过」稍后配置）")
            return

        model = self.model_combo.currentData()
        base_url = self.base_url_input.text().strip() or None

        try:
            from src.data.settings_manager import get_settings_manager
            sm = get_settings_manager()
            sm.set_api_key(
                provider=provider_id,
                api_key=api_key,
                base_url=base_url,
                model=model,
                is_default=True,
            )
            sm.set_setting("generation", "default_provider", provider_id)
            if model:
                sm.set_setting("generation", "default_model", model)

            from src.utils.llm import reset_llm_client
            reset_llm_client()

            QMessageBox.information(self, "配置完成", "API 密钥已保存，可以开始使用了！")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置失败：{e}")


def needs_onboarding() -> bool:
    """检查是否需要展示使用向导（未配置任何 API 密钥）"""
    try:
        from src.utils.llm import has_api_key
        return not has_api_key()
    except Exception:
        return True


def show_onboarding_if_needed(parent=None) -> bool:
    """
    启动时调用：需要向导则弹出并阻塞等待结果

    Returns:
        True - 已完成配置或用户已跳过（继续进入主界面）
    """
    if not needs_onboarding():
        return True
    wizard = OnboardingWizard(parent)
    wizard.exec()
    return True
