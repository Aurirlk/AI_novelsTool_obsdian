"""
设置页面
包含LLM配置、生成参数、外观、数据、快捷键等设置
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QFormLayout, QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QInputDialog, QSlider, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt
import os

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalInput as ModernInput, ProfessionalTextEdit as ModernTextEdit


def _scrollable(widget: QWidget) -> QScrollArea:
    """把内容页包进滚动区，防止窗口高度不足时表单被挤压重叠"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setWidget(widget)
    return scroll


def _to_bool(value) -> bool:
    """设置库可能返回字符串型布尔值"""
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_settings()
        self._check_test_keys()

    def _check_test_keys(self):
        """启动时扫描测试密钥，命中则显示非阻塞警告条（上线前清理提醒）"""
        try:
            from src.utils.key_check import find_test_keys
            hits = find_test_keys()
        except Exception:
            hits = []
        if hits:
            try:
                from ..i18n import tr
                detail = "、".join(f"{h['source']}:{h['key_name']}" for h in hits)
                self.test_key_warning.setText(tr("settings.test_key_warning").format(detail=detail))
            except Exception:
                self.test_key_warning.setText(
                    f"检测到测试用 API 密钥，正式上线前请删除。")
            self.test_key_warning.setVisible(True)
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        title = QLabel("设置")
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 通用设置（合并原 个性化+外观+通用）
        self._create_general_tab()
        
        # LLM设置
        self._create_llm_tab()
        
        # 生成设置
        self._create_generation_tab()
        
        # 快捷键设置
        self._create_shortcuts_tab()
        
        # 邮箱投递设置
        self._create_email_tab()
        
        # 数据设置
        self._create_data_tab()
        
        layout.addWidget(self.tabs)
        
        # 保存按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = ModernButton("保存设置", "primary")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        reset_btn = ModernButton("重置默认", "secondary")
        reset_btn.clicked.connect(self._reset_settings)
        btn_layout.addWidget(reset_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_llm_tab(self):
        """创建LLM设置标签页（自带API密钥，即存即用）"""
        llm_tab = QWidget()
        llm_layout = QVBoxLayout(llm_tab)
        llm_layout.setContentsMargins(20, 20, 20, 20)

        # 测试密钥警告条（启动扫描命中时显示，非阻塞）
        self.test_key_warning = QLabel("")
        self.test_key_warning.setWordWrap(True)
        self.test_key_warning.setVisible(False)
        self.test_key_warning.setStyleSheet(
            "background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;"
            "border-radius: 8px; padding: 10px 14px; font-size: 13px;")
        llm_layout.addWidget(self.test_key_warning)

        provider_group = QGroupBox("API 配置")
        provider_form = QFormLayout(provider_group)
        provider_form.setSpacing(12)

        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_form.addRow("提供商", self.provider_combo)

        self.provider_desc_label = QLabel("")
        self.provider_desc_label.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        provider_form.addRow("", self.provider_desc_label)

        self.model_combo = QComboBox()
        provider_form.addRow("模型", self.model_combo)

        key_layout = QHBoxLayout()
        self.api_key_input = ModernInput("粘贴你的 API 密钥")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self.api_key_input)

        self.show_key_check = QCheckBox("显示")
        self.show_key_check.toggled.connect(
            lambda checked: self.api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
        key_layout.addWidget(self.show_key_check)
        provider_form.addRow("API密钥", key_layout)

        self.base_url_input = ModernInput("留空则使用官方默认地址")
        provider_form.addRow("接口地址", self.base_url_input)

        btn_row = QHBoxLayout()

        save_key_btn = ModernButton("保存配置", "primary")
        save_key_btn.clicked.connect(self._save_llm_config)
        btn_row.addWidget(save_key_btn)

        test_btn = ModernButton("测试连接", "secondary")
        test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(test_btn)

        btn_row.addStretch()
        provider_form.addRow("", btn_row)

        self.llm_status_label = QLabel("")
        self.llm_status_label.setWordWrap(True)
        provider_form.addRow("", self.llm_status_label)

        llm_layout.addWidget(provider_group)
        llm_layout.addStretch()

        self.tabs.addTab(_scrollable(llm_tab), "LLM")
    
    def _create_generation_tab(self):
        """创建生成设置标签页"""
        gen_tab = QWidget()
        gen_layout = QVBoxLayout(gen_tab)
        gen_layout.setContentsMargins(20, 20, 20, 20)
        
        gen_group = QGroupBox("生成参数")
        gen_form = QFormLayout(gen_group)
        gen_form.setSpacing(12)
        
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(70)
        self.temp_label = QLabel("0.7")
        self.temp_slider.valueChanged.connect(lambda v: self.temp_label.setText(f"{v/100:.1f}"))
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        gen_form.addRow("温度", temp_layout)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8000)
        self.max_tokens_spin.setValue(2000)
        self.max_tokens_spin.setSingleStep(100)
        gen_form.addRow("最大Token数", self.max_tokens_spin)
        
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setValue(3)
        gen_form.addRow("最大重试次数", self.retry_spin)
        
        self.words_spin = QSpinBox()
        self.words_spin.setRange(500, 5000)
        self.words_spin.setValue(2000)
        self.words_spin.setSingleStep(500)
        gen_form.addRow("每章字数", self.words_spin)
        
        gen_layout.addWidget(gen_group)
        gen_layout.addStretch()
        
        self.tabs.addTab(_scrollable(gen_tab), "生成")
    
    def _on_language_changed(self, text):
        """语言切换：立即保存并刷新主界面"""
        lang = "zh_CN" if text == "简体中文" else "en_US"
        from src.data.settings_manager import get_settings_manager
        get_settings_manager().set_setting("general", "language", lang)
        from ..i18n import set_language
        set_language(lang)
        window = self.window()
        if hasattr(window, "retranslate"):
            window.retranslate()

    def _on_theme_changed(self, text):
        """主题切换：立即应用并保存"""
        theme = "light" if text == "浅色" else "dark"
        from src.data.settings_manager import get_settings_manager
        get_settings_manager().set_setting("general", "theme", theme)
        window = self.window()
        if hasattr(window, "_set_theme"):
            window._set_theme(theme)
    
    def _create_general_tab(self):
        """创建通用设置标签页（合并原 个性化+外观+通用）"""
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(20, 20, 20, 20)
        general_layout.setSpacing(16)

        # ---- 语言 & 外观 ----
        appearance_group = QGroupBox("外观与语言")
        appearance_form = QFormLayout(appearance_group)
        appearance_form.setSpacing(12)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        appearance_form.addRow("语言", self.language_combo)

        language_hint = QLabel("切换后主界面立即生效，部分页面重启后生效")
        language_hint.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        appearance_form.addRow("", language_hint)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        appearance_form.addRow("主题", self.theme_combo)

        theme_hint = QLabel("主题切换立即生效并自动保存")
        theme_hint.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        appearance_form.addRow("", theme_hint)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 20)
        self.font_size_spin.setValue(14)
        appearance_form.addRow("字体大小", self.font_size_spin)

        general_layout.addWidget(appearance_group)

        # ---- 用户信息 ----
        user_group = QGroupBox("用户信息")
        user_form = QFormLayout(user_group)
        user_form.setSpacing(12)

        self.nickname_input = ModernInput("输入昵称")
        user_form.addRow("昵称", self.nickname_input)

        self.avatar_combo = QComboBox()
        self.avatar_combo.addItems(["默认头像", "头像1", "头像2", "头像3"])
        user_form.addRow("头像", self.avatar_combo)

        general_layout.addWidget(user_group)

        # ---- 写作偏好 ----
        writing_group = QGroupBox("写作偏好")
        writing_form = QFormLayout(writing_group)
        writing_form.setSpacing(12)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["玄幻", "都市", "科幻", "历史", "言情", "悬疑", "其他"])
        writing_form.addRow("默认题材", self.genre_combo)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["轻松", "严肃", "幽默", "热血", "其他"])
        writing_form.addRow("写作风格", self.style_combo)

        self.perspective_combo = QComboBox()
        self.perspective_combo.addItems(["第一人称", "第三人称", "上帝视角"])
        writing_form.addRow("叙事视角", self.perspective_combo)

        general_layout.addWidget(writing_group)

        # ---- 通用行为 ----
        general_group = QGroupBox("通用设置")
        general_form = QFormLayout(general_group)
        general_form.setSpacing(12)

        self.auto_save_check = QCheckBox("自动保存")
        self.auto_save_check.setChecked(True)
        general_form.addRow("", self.auto_save_check)

        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(60, 3600)
        self.auto_save_interval_spin.setValue(300)
        self.auto_save_interval_spin.setSingleStep(60)
        general_form.addRow("自动保存间隔（秒）", self.auto_save_interval_spin)

        self.recent_projects_spin = QSpinBox()
        self.recent_projects_spin.setRange(5, 50)
        self.recent_projects_spin.setValue(10)
        general_form.addRow("最近项目数量", self.recent_projects_spin)

        self.default_project_dir = ModernInput("默认项目目录")
        general_form.addRow("项目目录", self.default_project_dir)

        general_layout.addWidget(general_group)

        # ---- AI助手设置 ----
        ai_group = QGroupBox("AI助手设置")
        ai_form = QFormLayout(ai_group)
        ai_form.setSpacing(12)

        self.criticism_level_combo = QComboBox()
        self.criticism_level_combo.addItems(["温和", "中等", "严厉"])
        ai_form.addRow("批评程度", self.criticism_level_combo)

        self.coaching_style_combo = QComboBox()
        self.coaching_style_combo.addItems(["鼓励型", "指导型", "挑战型"])
        ai_form.addRow("陪练风格", self.coaching_style_combo)

        self.auto_critique_check = QCheckBox("自动批评")
        self.auto_critique_check.setChecked(False)
        ai_form.addRow("", self.auto_critique_check)

        general_layout.addWidget(ai_group)

        general_layout.addStretch()

        self.tabs.addTab(_scrollable(general_tab), "通用")
    
    def _create_shortcuts_tab(self):
        """创建快捷键设置标签页"""
        shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_tab)
        shortcuts_layout.setContentsMargins(20, 20, 20, 20)
        
        shortcuts_group = QGroupBox("快捷键设置")
        shortcuts_layout_inner = QVBoxLayout(shortcuts_group)
        
        # 快捷键列表
        self.shortcuts_list = QListWidget()
        shortcuts_layout_inner.addWidget(self.shortcuts_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        edit_shortcut_btn = ModernButton("编辑快捷键", "primary")
        edit_shortcut_btn.clicked.connect(self._edit_shortcut)
        btn_layout.addWidget(edit_shortcut_btn)
        
        reset_shortcuts_btn = ModernButton("重置默认", "secondary")
        reset_shortcuts_btn.clicked.connect(self._reset_shortcuts)
        btn_layout.addWidget(reset_shortcuts_btn)
        
        shortcuts_layout_inner.addLayout(btn_layout)
        
        shortcuts_layout.addWidget(shortcuts_group)
        shortcuts_layout.addStretch()
        
        self.tabs.addTab(_scrollable(shortcuts_tab), "快捷键")
    
    def _create_email_tab(self):
        """创建邮箱投递设置标签页"""
        email_tab = QWidget()
        email_layout = QVBoxLayout(email_tab)
        email_layout.setContentsMargins(20, 20, 20, 20)
        email_layout.setSpacing(12)

        # 发件配置
        sender_group = QGroupBox("发件配置（SMTP）")
        sender_form = QFormLayout(sender_group)
        sender_form.setSpacing(12)

        self.email_preset_combo = QComboBox()
        from src.utils.email_sender import SMTP_PRESETS
        for name in SMTP_PRESETS:
            self.email_preset_combo.addItem(name)
        self.email_preset_combo.currentTextChanged.connect(self._on_email_preset_changed)
        sender_form.addRow("邮箱服务商", self.email_preset_combo)

        self.smtp_host_input = ModernInput("smtp.qq.com")
        sender_form.addRow("SMTP服务器", self.smtp_host_input)

        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(465)
        sender_form.addRow("SMTP端口", self.smtp_port_spin)

        self.smtp_ssl_check = QCheckBox("使用 SSL 加密连接")
        self.smtp_ssl_check.setChecked(True)
        sender_form.addRow("加密", self.smtp_ssl_check)

        self.sender_email_input = ModernInput("你的发件邮箱")
        sender_form.addRow("发件邮箱", self.sender_email_input)

        self.auth_code_input = ModernInput("16位授权码")
        self.auth_code_input.setEchoMode(QLineEdit.EchoMode.Password)
        sender_form.addRow("授权码", self.auth_code_input)

        email_layout.addWidget(sender_group)

        # 收件配置
        receiver_group = QGroupBox("收件配置")
        receiver_form = QFormLayout(receiver_group)
        receiver_form.setSpacing(12)

        self.editor_email_input = ModernInput("编辑的收稿邮箱")
        receiver_form.addRow("编辑邮箱", self.editor_email_input)

        self.sender_name_input = ModernInput("AI写作助手")
        receiver_form.addRow("署名", self.sender_name_input)

        email_layout.addWidget(receiver_group)

        # 操作按钮
        email_btn_layout = QHBoxLayout()

        test_btn = ModernButton("测试连接", "secondary")
        test_btn.clicked.connect(self._test_email_connection)
        email_btn_layout.addWidget(test_btn)

        email_btn_layout.addStretch()
        email_layout.addLayout(email_btn_layout)

        # 提示
        hint = QLabel(
            "提示：授权码不是登录密码。QQ邮箱：设置→账户→开启SMTP服务→生成授权码；\n"
            "163邮箱：设置→POP3/SMTP/IMAP→开启服务→设置客户端授权密码。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        email_layout.addWidget(hint)

        self.email_status_label = QLabel("")
        self.email_status_label.setWordWrap(True)
        self.email_status_label.setStyleSheet("color: #8e8e8e; font-size: 12px;")
        email_layout.addWidget(self.email_status_label)

        email_layout.addStretch()

        self.tabs.addTab(_scrollable(email_tab), "邮箱投递")

    def _on_email_preset_changed(self, preset):
        """邮箱服务商切换：自动填充 SMTP 服务器和端口"""
        from src.utils.email_sender import SMTP_PRESETS
        cfg = SMTP_PRESETS.get(preset)
        if not cfg:
            return
        self.smtp_host_input.setText(cfg["host"])
        self.smtp_port_spin.setValue(cfg["port"])
        self.smtp_ssl_check.setChecked(cfg["ssl"])

    def _test_email_connection(self):
        """测试邮箱连接"""
        from src.utils.email_sender import test_connection
        sender = self.sender_email_input.text().strip()
        auth = self.auth_code_input.text().strip()
        if not sender or not auth:
            QMessageBox.warning(self, "提示", "请先填写发件邮箱和授权码")
            return
        host = self.smtp_host_input.text().strip() or "smtp.qq.com"
        port = self.smtp_port_spin.value()
        ssl = self.smtp_ssl_check.isChecked()
        self.email_status_label.setText("正在测试连接...")
        ok, msg = test_connection(sender, auth, host, port, ssl)
        self.email_status_label.setText(msg)
        self.email_status_label.setStyleSheet(
            "color: #2e7d32;" if ok else "color: #c62828;")

    def _create_data_tab(self):
        """创建数据设置标签页"""
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setContentsMargins(20, 20, 20, 20)
        
        data_group = QGroupBox("数据管理")
        data_form = QFormLayout(data_group)
        data_form.setSpacing(12)
        
        self.data_dir_input = ModernInput("数据目录")
        data_form.addRow("数据目录", self.data_dir_input)
        
        self.backup_check = QCheckBox("启用自动备份")
        self.backup_check.setChecked(_to_bool(True))
        data_form.addRow("", self.backup_check)
        
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 20)
        self.backup_count_spin.setValue(5)
        data_form.addRow("备份数量", self.backup_count_spin)

        self.history_limit_spin = QSpinBox()
        self.history_limit_spin.setRange(30, 60)
        self.history_limit_spin.setValue(50)
        self.history_limit_spin.setToolTip("历史对话数量达到上限后需删除部分对话才能新建")
        data_form.addRow("历史对话上限", self.history_limit_spin)

        self.memory_mode_combo = QComboBox()
        self.memory_mode_combo.addItems(["自动写入", "确认后写入", "关闭"])
        self.memory_mode_combo.setToolTip("保存章节后自动提取角色/钩子/事件变更：自动写入=直接入库；确认后写入=弹窗确认；关闭=不提取")
        data_form.addRow("记忆自动更新", self.memory_mode_combo)

        self.hook_remind_combo = QComboBox()
        self.hook_remind_combo.addItems(["打开章节时警示", "仅标记超期", "关闭"])
        self.hook_remind_combo.setToolTip("伏笔超期提醒：打开章节时弹窗警示；仅标记=只在悬念页显示超期标记；关闭=不提醒")
        data_form.addRow("伏笔超期提醒", self.hook_remind_combo)

        data_layout.addWidget(data_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        backup_btn = ModernButton("立即备份", "secondary")
        backup_btn.clicked.connect(self._backup_data)
        btn_layout.addWidget(backup_btn)
        
        restore_btn = ModernButton("恢复数据", "secondary")
        restore_btn.clicked.connect(self._restore_data)
        btn_layout.addWidget(restore_btn)

        cleanup_btn = ModernButton("垃圾清理", "secondary")
        cleanup_btn.clicked.connect(self._cleanup_junk)
        btn_layout.addWidget(cleanup_btn)
        
        clear_btn = ModernButton("清除数据", "danger")
        clear_btn.clicked.connect(self._clear_data)
        btn_layout.addWidget(clear_btn)
        
        data_layout.addLayout(btn_layout)
        data_layout.addStretch()
        
        self.tabs.addTab(_scrollable(data_tab), "数据")
    
    def _load_settings(self):
        """加载设置"""
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()
        
        # 加载个性化设置
        nickname = sm.get_setting("personal", "nickname", "")
        self.nickname_input.setText(nickname)
        
        avatar = sm.get_setting("personal", "avatar", "默认头像")
        self.avatar_combo.setCurrentText(avatar)
        
        genre = sm.get_setting("personal", "genre", "玄幻")
        self.genre_combo.setCurrentText(genre)
        
        style = sm.get_setting("personal", "style", "轻松")
        self.style_combo.setCurrentText(style)
        
        perspective = sm.get_setting("personal", "perspective", "第三人称")
        self.perspective_combo.setCurrentText(perspective)
        
        project_dir = sm.get_setting("personal", "project_dir", "./projects")
        self.default_project_dir.setText(project_dir)
        
        auto_save = sm.get_setting("personal", "auto_save", True)
        self.auto_save_check.setChecked(_to_bool(auto_save))
        
        auto_save_interval = sm.get_setting("personal", "auto_save_interval", 300)
        self.auto_save_interval_spin.setValue(int(auto_save_interval))
        
        criticism_level = sm.get_setting("personal", "criticism_level", "中等")
        self.criticism_level_combo.setCurrentText(criticism_level)
        
        coaching_style = sm.get_setting("personal", "coaching_style", "指导型")
        self.coaching_style_combo.setCurrentText(coaching_style)
        
        auto_critique = sm.get_setting("personal", "auto_critique", False)
        self.auto_critique_check.setChecked(_to_bool(auto_critique))
        
        # 加载LLM设置
        providers = sm.list_providers()
        self.provider_combo.clear()
        for provider in providers:
            self.provider_combo.addItem(provider["name"], provider["id"])
        
        # 加载生成设置
        temperature = sm.get_setting("generation", "temperature", 0.7)
        self.temp_slider.setValue(int(float(temperature) * 100))
        self.temp_label.setText(f"{float(temperature):.1f}")
        
        max_tokens = sm.get_setting("generation", "max_tokens", 2000)
        self.max_tokens_spin.setValue(int(max_tokens))
        
        max_retries = sm.get_setting("generation", "max_retries", 3)
        self.retry_spin.setValue(int(max_retries))
        
        words_per_chapter = sm.get_setting("generation", "words_per_chapter", 2000)
        self.words_spin.setValue(int(words_per_chapter))
        
        # 加载外观设置
        theme = sm.get_setting("general", "theme", "light")
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText("浅色" if theme == "light" else "深色")
        self.theme_combo.blockSignals(False)

        font_size = sm.get_setting("general", "font_size", 14)
        self.font_size_spin.setValue(int(font_size))

        # 加载通用设置
        language = sm.get_setting("general", "language", "zh_CN")
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentText("简体中文" if language == "zh_CN" else "English")
        self.language_combo.blockSignals(False)

        auto_save = sm.get_setting("general", "auto_save", True)
        self.auto_save_check.setChecked(_to_bool(auto_save))

        auto_save_interval = sm.get_setting("general", "auto_save_interval", 300)
        self.auto_save_interval_spin.setValue(int(auto_save_interval))

        recent_projects_limit = sm.get_setting("general", "recent_projects_limit", 10)
        self.recent_projects_spin.setValue(int(recent_projects_limit))
        
        # 加载数据设置
        data_dir = sm.get_setting("storage", "data_dir", "./data")
        self.data_dir_input.setText(data_dir)
        
        backup_enabled = sm.get_setting("storage", "backup_enabled", True)
        self.backup_check.setChecked(_to_bool(backup_enabled))
        
        backup_count = sm.get_setting("storage", "backup_count", 5)
        self.backup_count_spin.setValue(int(backup_count))
        history_limit = sm.get_setting("storage", "chat_history_limit", 50)
        self.history_limit_spin.setValue(int(history_limit))

        memory_mode = sm.get_setting("storage", "memory_auto_update", "confirm")
        memory_idx = {"auto": 0, "confirm": 1, "off": 2}.get(memory_mode, 1)
        self.memory_mode_combo.setCurrentIndex(memory_idx)

        hook_remind = sm.get_setting("storage", "hook_overdue_reminder", "warn")
        hook_idx = {"warn": 0, "mark": 1, "off": 2}.get(hook_remind, 0)
        self.hook_remind_combo.setCurrentIndex(hook_idx)
        
        # 加载快捷键
        self._load_shortcuts()

        # 加载邮箱投递设置
        preset = sm.get_setting("email", "preset", "QQ邮箱")
        self.email_preset_combo.blockSignals(True)
        idx = self.email_preset_combo.findText(preset)
        if idx >= 0:
            self.email_preset_combo.setCurrentIndex(idx)
        self.email_preset_combo.blockSignals(False)
        self.smtp_host_input.setText(sm.get_setting("email", "smtp_host", ""))
        self.smtp_port_spin.setValue(int(sm.get_setting("email", "smtp_port", "465") or 465))
        self.smtp_ssl_check.setChecked(_to_bool(sm.get_setting("email", "use_ssl", True)))
        self.sender_email_input.setText(sm.get_setting("email", "sender_email", ""))
        self.auth_code_input.setText(sm.get_setting("email", "auth_code", ""))
        self.editor_email_input.setText(sm.get_setting("email", "editor_email", ""))
        self.sender_name_input.setText(sm.get_setting("email", "sender_name", "AI写作助手"))

        # 加载LLM表单（密钥、接口地址）
        self._refresh_llm_form()
    
    def _load_shortcuts(self):
        """加载快捷键"""
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()
        
        shortcuts = sm.list_shortcuts()
        self.shortcuts_list.clear()
        
        for shortcut in shortcuts:
            display_text = f"{shortcut['description']}: {shortcut['key_sequence']}"
            self.shortcuts_list.addItem(display_text)
    
    def _on_provider_changed(self, provider_name):
        """提供商改变事件"""
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()

        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return

        # 更新模型列表
        models = sm.get_provider_models(provider_id)
        self.model_combo.clear()
        for model in models:
            self.model_combo.addItem(model["name"], model["id"])

        # 更新提供商描述
        info = sm.get_provider_info(provider_id)
        if info:
            self.provider_desc_label.setText(info.get("description", ""))

        # 加载该提供商已保存的密钥和接口地址
        self._refresh_llm_form()

    def _refresh_llm_form(self):
        """刷新LLM表单（加载已保存的密钥和接口地址）"""
        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()

        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return

        saved_key = sm.get_api_key(provider_id) or ""
        self.api_key_input.setText(saved_key)

        custom_url = sm.get_setting("llm", f"{provider_id}_base_url")
        default_url = sm.get_provider_base_url(provider_id)
        self.base_url_input.setText(custom_url or default_url or "")

    def _save_llm_config(self):
        """保存LLM配置（密钥即存即用）"""
        from src.data.settings_manager import get_settings_manager
        from src.utils.llm import reset_llm_client

        sm = get_settings_manager()
        provider = self.provider_combo.currentData()
        model = self.model_combo.currentData()
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()

        if not provider:
            QMessageBox.warning(self, "警告", "请先选择提供商")
            return

        info = sm.get_provider_info(provider)
        if info and info.get("requires_key") and not api_key:
            QMessageBox.warning(self, "警告", "请输入 API 密钥")
            return

        # 保存密钥
        if api_key:
            sm.set_api_key(provider, api_key, key_name=f"{provider}_default",
                           base_url=base_url or None, model=model, is_default=True)

        # 保存自定义接口地址
        default_url = sm.get_provider_base_url(provider)
        if base_url and base_url != default_url:
            sm.set_setting("llm", f"{provider}_base_url", base_url)

        # 保存默认提供商和模型
        sm.set_setting("generation", "default_provider", provider)
        if model:
            sm.set_setting("generation", "default_model", model)

        # 使新配置立即生效
        reset_llm_client()

        self.llm_status_label.setText("配置已保存，可前往「AI 助手」开始使用")
        QMessageBox.information(self, "成功", "API 配置已保存，立即生效")

    def _test_connection(self):
        """真实测试API连接（后台线程，不卡界面）"""
        from PyQt6.QtCore import QThread, pyqtSignal

        provider = self.provider_combo.currentData()
        model = self.model_combo.currentData()
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()

        if not provider:
            QMessageBox.warning(self, "警告", "请先选择提供商")
            return

        if not api_key:
            from src.data.settings_manager import get_settings_manager
            api_key = get_settings_manager().get_api_key(provider) or ""

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入 API 密钥")
            return

        self.llm_status_label.setText("正在测试连接...")

        class TestWorker(QThread):
            result = pyqtSignal(bool, str)

            def run(self_inner):
                try:
                    from openai import OpenAI
                    kwargs = {"api_key": api_key}
                    if base_url:
                        kwargs["base_url"] = base_url
                    client = OpenAI(**kwargs)
                    client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=5,
                    )
                    self_inner.result.emit(True, f"连接成功：{model}")
                except Exception as e:
                    self_inner.result.emit(False, f"连接失败：{e}")

        def on_result(ok, msg):
            self.llm_status_label.setText(msg)
            if ok:
                QMessageBox.information(self, "测试连接", msg)
            else:
                QMessageBox.warning(self, "测试连接", msg)

        self._test_worker = TestWorker(self)
        self._test_worker.result.connect(on_result)
        self._test_worker.start()
    
    def _edit_shortcut(self):
        """编辑快捷键"""
        selected = self.shortcuts_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要编辑的快捷键")
            return
        
        # 解析当前快捷键
        text = selected.text()
        parts = text.split(": ")
        if len(parts) != 2:
            return
        
        description = parts[0]
        current_key = parts[1]
        
        # 获取新的快捷键
        new_key, ok = QInputDialog.getText(self, "编辑快捷键", f"请输入新的快捷键序列:", text=current_key)
        if not ok or not new_key:
            return

        from src.data.settings_manager import get_settings_manager
        sm = get_settings_manager()
        action = sm.get_shortcut_key(description) if hasattr(sm, "get_shortcut_key") else None
        # 通过描述找到对应动作并保存
        for shortcut in sm.list_shortcuts():
            if shortcut.get("description") == description:
                sm.set_shortcut(shortcut.get("action"), new_key, description)
                break

        self._load_shortcuts()
        QMessageBox.information(self, "成功", f"快捷键已更新: {new_key}")
    
    def _reset_shortcuts(self):
        """重置快捷键"""
        reply = QMessageBox.question(self, "确认重置", "确定要重置所有快捷键为默认值吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            from src.data.settings_manager import get_settings_manager
            sm = get_settings_manager()
            sm.reset_shortcuts()
            self._load_shortcuts()
            QMessageBox.information(self, "成功", "快捷键已重置为默认值")
    
    def _backup_data(self):
        """备份数据：全量打包（写作空间 + data + 小说大纲）为 zip"""
        from datetime import datetime
        from src.utils.backup_manager import create_full_backup

        default_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择备份保存位置", default_name, "ZIP压缩包 (*.zip)"
        )
        if not file_path:
            return

        try:
            create_full_backup(file_path)
            QMessageBox.information(self, "备份完成", f"全部数据（写作空间/角色/钩子/时间线/设置/大纲库）已备份到：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"备份失败：{e}")

    def _cleanup_junk(self):
        """垃圾清理：扫描日志/临时文件/多余备份/遗留数据，确认后移入回收站"""
        from src.utils.cleanup import scan_cleanable, execute_cleanup, format_size

        scan = scan_cleanable()
        total = scan["total_size"]
        if total == 0:
            QMessageBox.information(self, "垃圾清理", "没有发现可清理的垃圾文件，当前很干净。")
            return

        # 构建摘要
        parts = []
        if scan["logs"]:
            parts.append(f"过期日志：{len(scan['logs'])} 个")
        if scan["temp"]:
            parts.append(f"临时文件（__pycache__/.pyc）：{len(scan['temp'])} 个")
        if scan["backups"]:
            parts.append(f"多余备份：{len(scan['backups'])} 个")
        if scan["legacy"]:
            parts.append(f"迁移遗留数据：{len(scan['legacy'])} 个")

        detail = "\n".join(parts)
        reply = QMessageBox.question(
            self, "垃圾清理",
            f"发现以下可清理内容（共 {format_size(total)}）：\n\n{detail}\n\n"
            "清理后文件将移入回收站（非永久删除），确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        result = execute_cleanup(scan)
        msg = f"清理完成：{result['count']} 项，释放 {format_size(result['size'])}"
        if result["failed"]:
            msg += f"\n（{result['failed']} 项清理失败，可能被占用）"
        QMessageBox.information(self, "垃圾清理", msg)

    def _restore_data(self):
        """恢复数据：从全量 zip 解压覆盖（写作空间 + data + 小说大纲）"""
        from src.utils.backup_manager import restore_full_backup

        reply = QMessageBox.question(
            self, "确认恢复",
            "恢复数据将覆盖当前所有数据（写作空间、设置、角色、钩子、时间线、大纲库等），且需要重启应用生效。确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "", "ZIP压缩包 (*.zip)"
        )
        if not file_path:
            return

        try:
            msg = restore_full_backup(file_path)
            QMessageBox.information(self, "恢复完成", f"{msg}。\n请重启应用使设置生效。")
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"恢复失败：{e}")

    def _clear_data(self):
        """清除数据：删除全部用户数据（谨慎操作，需二次确认）"""
        import shutil
        from src.data.database_manager import get_database_manager

        reply = QMessageBox.question(
            self, "确认清除",
            "将删除所有作品、角色、悬念、时间线、会话记录等用户数据，此操作不可恢复！\n（API密钥配置也会被清除）确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        reply2 = QMessageBox.question(
            self, "二次确认",
            "再次确认：真的要清除全部数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply2 != QMessageBox.StandardButton.Yes:
            return

        try:
            db = get_database_manager()
            data_dir = os.path.dirname(db.db_path)

            # 删除所有数据文件（保留 data 目录本身）
            for entry in os.listdir(data_dir):
                entry_path = os.path.join(data_dir, entry)
                if os.path.isdir(entry_path):
                    shutil.rmtree(entry_path, ignore_errors=True)
                else:
                    try:
                        os.remove(entry_path)
                    except OSError:
                        pass

            QMessageBox.information(self, "清除完成", "所有数据已清除，请重启应用。")
        except Exception as e:
            QMessageBox.critical(self, "清除失败", f"清除数据失败：{e}")
    
    def _save_settings(self):
        """保存设置"""
        from src.data.settings_manager import get_settings_manager
        
        sm = get_settings_manager()
        
        # 保存个性化设置
        sm.set_setting("personal", "nickname", self.nickname_input.text())
        sm.set_setting("personal", "avatar", self.avatar_combo.currentText())
        sm.set_setting("personal", "genre", self.genre_combo.currentText())
        sm.set_setting("personal", "style", self.style_combo.currentText())
        sm.set_setting("personal", "perspective", self.perspective_combo.currentText())
        sm.set_setting("personal", "project_dir", self.default_project_dir.text())
        sm.set_setting("personal", "auto_save", self.auto_save_check.isChecked())
        sm.set_setting("personal", "auto_save_interval", self.auto_save_interval_spin.value())
        sm.set_setting("personal", "criticism_level", self.criticism_level_combo.currentText())
        sm.set_setting("personal", "coaching_style", self.coaching_style_combo.currentText())
        sm.set_setting("personal", "auto_critique", self.auto_critique_check.isChecked())
        
        # 保存生成设置
        sm.set_setting("generation", "temperature", self.temp_slider.value() / 100)
        sm.set_setting("generation", "max_tokens", self.max_tokens_spin.value())
        sm.set_setting("generation", "max_retries", self.retry_spin.value())
        sm.set_setting("generation", "words_per_chapter", self.words_spin.value())
        
        # 保存外观设置（主题切换已在下拉框变更时即时生效，这里只保存字体）
        sm.set_setting("general", "font_size", self.font_size_spin.value())

        # 保存通用设置
        sm.set_setting("general", "auto_save", self.auto_save_check.isChecked())
        sm.set_setting("general", "auto_save_interval", self.auto_save_interval_spin.value())
        sm.set_setting("general", "recent_projects_limit", self.recent_projects_spin.value())
        
        # 保存数据设置
        sm.set_setting("storage", "data_dir", self.data_dir_input.text())
        sm.set_setting("storage", "backup_enabled", self.backup_check.isChecked())
        sm.set_setting("storage", "backup_count", self.backup_count_spin.value())
        sm.set_setting("storage", "chat_history_limit", self.history_limit_spin.value())
        sm.set_setting("storage", "memory_auto_update",
                       {0: "auto", 1: "confirm", 2: "off"}[self.memory_mode_combo.currentIndex()])
        sm.set_setting("storage", "hook_overdue_reminder",
                       {0: "warn", 1: "mark", 2: "off"}[self.hook_remind_combo.currentIndex()])
        
        # 保存邮箱投递设置
        sm.set_setting("email", "preset", self.email_preset_combo.currentText())
        sm.set_setting("email", "smtp_host", self.smtp_host_input.text().strip())
        sm.set_setting("email", "smtp_port", str(self.smtp_port_spin.value()))
        sm.set_setting("email", "use_ssl", "true" if self.smtp_ssl_check.isChecked() else "false")
        sm.set_setting("email", "sender_email", self.sender_email_input.text().strip())
        sm.set_setting("email", "auth_code", self.auth_code_input.text().strip())
        sm.set_setting("email", "editor_email", self.editor_email_input.text().strip())
        sm.set_setting("email", "sender_name", self.sender_name_input.text().strip() or "AI写作助手")
        
        # 保存默认提供商和模型
        provider = self.provider_combo.currentData()
        model = self.model_combo.currentData()
        if provider:
            sm.set_setting("generation", "default_provider", provider)
        if model:
            sm.set_setting("generation", "default_model", model)
        
        QMessageBox.information(self, "成功", "设置已保存")
    
    def _reset_settings(self):
        """重置设置：清空 settings 表并恢复默认值"""
        reply = QMessageBox.question(self, "确认重置", "确定要重置所有设置为默认值吗？\n（API密钥配置也会被清除）",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.data.database_manager import get_database_manager
                db = get_database_manager()
                conn = db.get_connection()
                conn.execute("DELETE FROM settings")
                conn.execute("DELETE FROM api_keys")
                conn.execute("DELETE FROM shortcuts")
                conn.commit()

                from src.utils.llm import reset_llm_client
                reset_llm_client()

                # 重新加载界面
                self._load_settings()
                self._load_shortcuts()
                self._refresh_llm_form()
                QMessageBox.information(self, "重置完成", "所有设置已重置为默认值")
            except Exception as e:
                QMessageBox.critical(self, "重置失败", f"重置设置失败：{e}")
