"""
扩展中心页面
管理 Skills 技能、MCP 服务器、提示词模板库
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QListWidget, QListWidgetItem, QTextBrowser, QPushButton,
    QMessageBox, QInputDialog, QSplitter, QLineEdit, QComboBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class ExtensionsPage(QWidget):
    """扩展中心：Skills / MCP / 提示词库"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._refresh_skills()
        self._refresh_mcp_servers()
        self._refresh_prompts()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("扩展中心")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self._create_skills_tab()
        self._create_mcp_tab()
        self._create_prompts_tab()
        layout.addWidget(self.tabs)

    # ==================== Skills 标签 ====================

    def _create_skills_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左：技能列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.skill_list = QListWidget()
        self.skill_list.currentItemChanged.connect(self._on_skill_selected)
        self.skill_list.itemChanged.connect(self._on_skill_check_changed)
        left_layout.addWidget(self.skill_list)

        btn_row = QHBoxLayout()
        for text, handler in [("刷新", self._refresh_skills), ("新建", self._create_skill),
                              ("删除", self._delete_skill), ("导入GitHub", self._import_skill_github)]:
            btn = QPushButton(text)
            btn.setObjectName("btn_secondary" if text != "导入GitHub" else "btn_primary")
            btn.setFixedHeight(32)
            btn.clicked.connect(handler)
            btn_row.addWidget(btn)
        left_layout.addLayout(btn_row)

        splitter.addWidget(left)

        # 右：技能详情
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.skill_name_label = QLabel("选择一个技能查看详情")
        self.skill_name_label.setObjectName("section_title")
        right_layout.addWidget(self.skill_name_label)

        self.skill_trigger_label = QLabel("")
        self.skill_trigger_label.setObjectName("chat_hint")
        self.skill_trigger_label.setWordWrap(True)
        right_layout.addWidget(self.skill_trigger_label)

        self.skill_detail = QTextBrowser()
        right_layout.addWidget(self.skill_detail)

        splitter.addWidget(right)
        splitter.setSizes([320, 680])
        layout.addWidget(splitter)

        self.tabs.addTab(tab, "Skills 技能")

    def _refresh_skills(self):
        from src.skills import get_skill_manager
        sm = get_skill_manager()
        sm.refresh()

        self.skill_list.blockSignals(True)
        self.skill_list.clear()
        for skill in sm.list_skills():
            item = QListWidgetItem(f"{skill.name}")
            item.setData(Qt.ItemDataRole.UserRole, skill)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if sm.is_enabled(skill.name) else Qt.CheckState.Unchecked)
            item.setToolTip(skill.description)
            self.skill_list.addItem(item)
        self.skill_list.blockSignals(False)

    def _on_skill_selected(self, current, _previous):
        if current is None:
            return
        skill = current.data(Qt.ItemDataRole.UserRole)
        self.skill_name_label.setText(skill.name)
        triggers = "、".join(skill.triggers[:10])
        self.skill_trigger_label.setText(f"触发词：{triggers}")
        self.skill_detail.setPlainText(f"# {skill.name}\n\n{skill.description}\n\n---\n\n{skill.content[:4000]}")

    def _on_skill_check_changed(self, item):
        skill = item.data(Qt.ItemDataRole.UserRole)
        if skill is None:
            return
        from src.skills import get_skill_manager
        get_skill_manager().set_enabled(skill.name, item.checkState() == Qt.CheckState.Checked)

    def _create_skill(self):
        name, ok = QInputDialog.getText(self, "新建技能", "技能名称（英文小写）:")
        if not ok or not name:
            return
        desc, ok = QInputDialog.getText(self, "新建技能", "技能描述（一句话说明何时触发）:")
        if not ok:
            return
        from src.skills import get_skill_manager
        get_skill_manager().create_skill(
            name=name, description=desc,
            content="# 在这里编写技能指令\n\n你是……\n\n## 工作方式\n\n1. ",
            triggers=[name])
        self._refresh_skills()
        QMessageBox.information(self, "成功", f"技能 {name} 已创建，可在 skills/{name}/SKILL.md 中编辑内容")

    def _delete_skill(self):
        item = self.skill_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "警告", "请先选择技能")
            return
        skill = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定删除技能 {skill.name} 吗？将删除整个目录。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from src.skills import get_skill_manager
            get_skill_manager().delete_skill(skill.name)
            self._refresh_skills()

    def _import_skill_github(self):
        url, ok = QInputDialog.getText(
            self, "导入GitHub技能", "仓库地址（https://github.com/用户名/仓库）:",
            text="https://github.com/")
        if not ok or "github.com" not in url:
            return

        class ImportWorker(QThread):
            done = pyqtSignal(list)
            failed = pyqtSignal(str)

            def __init__(self, repo_url):
                super().__init__()
                self.repo_url = repo_url

            def run(self):
                try:
                    from src.skills import get_skill_manager
                    imported = get_skill_manager().import_from_github(self.repo_url)
                    self.done.emit(imported)
                except Exception as e:
                    self.failed.emit(str(e))

        self._import_worker = ImportWorker(url)
        self._import_worker.done.connect(
            lambda names: (self._refresh_skills(),
                           QMessageBox.information(self, "导入成功", f"已导入 {len(names)} 个技能：\n" + "、".join(names))))
        self._import_worker.failed.connect(
            lambda err: QMessageBox.warning(self, "导入失败", err))
        self._import_worker.start()

    # ==================== MCP 标签 ====================

    def _create_mcp_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左：服务器列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.mcp_list = QListWidget()
        self.mcp_list.currentItemChanged.connect(self._on_mcp_selected)
        left_layout.addWidget(self.mcp_list)

        btn_row = QHBoxLayout()
        for text, handler in [("添加", self._add_mcp_server), ("删除", self._remove_mcp_server),
                              ("启用/禁用", self._toggle_mcp_server)]:
            btn = QPushButton(text)
            btn.setObjectName("btn_secondary")
            btn.setFixedHeight(32)
            btn.clicked.connect(handler)
            btn_row.addWidget(btn)
        left_layout.addLayout(btn_row)

        connect_btn = QPushButton("连接并获取工具")
        connect_btn.setObjectName("btn_primary")
        connect_btn.setFixedHeight(36)
        connect_btn.clicked.connect(self._connect_mcp_server)
        left_layout.addWidget(connect_btn)

        splitter.addWidget(left)

        # 右：状态与工具
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.mcp_status_label = QLabel("MCP 服务器通过 stdio 连接，工具可在 AI 助手对话中调用")
        self.mcp_status_label.setObjectName("section_title")
        self.mcp_status_label.setWordWrap(True)
        right_layout.addWidget(self.mcp_status_label)

        self.mcp_detail = QTextBrowser()
        right_layout.addWidget(self.mcp_detail)

        splitter.addWidget(right)
        splitter.setSizes([320, 680])
        layout.addWidget(splitter)

        self.tabs.addTab(tab, "MCP 服务")

    def _refresh_mcp_servers(self):
        from src.mcp import get_mcp_manager
        manager = get_mcp_manager()
        status = manager.server_status()

        self.mcp_list.clear()
        for config in manager.list_server_configs():
            state = status.get(config.name, "")
            item = QListWidgetItem(f"{config.name}  [{state}]")
            item.setData(Qt.ItemDataRole.UserRole, config)
            self.mcp_list.addItem(item)

    def _on_mcp_selected(self, current, _previous):
        if current is None:
            return
        config = current.data(Qt.ItemDataRole.UserRole)
        env_text = "\n".join(f"  {k}={v}" for k, v in config.env.items()) or "  (无)"
        self.mcp_detail.setPlainText(
            f"名称: {config.name}\n"
            f"命令: {config.command} {' '.join(config.args)}\n"
            f"环境变量:\n{env_text}\n"
            f"状态: {'启用' if config.enabled else '禁用'}\n"
            f"说明: {config.description}\n")

    def _add_mcp_server(self):
        name, ok = QInputDialog.getText(self, "添加MCP服务器", "服务器名称:")
        if not ok or not name:
            return
        command, ok = QInputDialog.getText(self, "添加MCP服务器", "启动命令（如 npx）:", text="npx")
        if not ok or not command:
            return
        args, ok = QInputDialog.getText(self, "添加MCP服务器", "参数（空格分隔，如 -y 包名）:", text="-y ")
        if not ok:
            return

        from src.mcp import MCPServerConfig, get_mcp_manager
        get_mcp_manager().add_server(MCPServerConfig(
            name=name, command=command,
            args=[a for a in args.split(" ") if a],
            enabled=True))
        self._refresh_mcp_servers()

    def _remove_mcp_server(self):
        item = self.mcp_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "警告", "请先选择服务器")
            return
        config = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定删除服务器 {config.name} 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from src.mcp import get_mcp_manager
            get_mcp_manager().remove_server(config.name)
            self._refresh_mcp_servers()

    def _toggle_mcp_server(self):
        item = self.mcp_list.currentItem()
        if item is None:
            return
        config = item.data(Qt.ItemDataRole.UserRole)
        from src.mcp import get_mcp_manager
        get_mcp_manager().set_enabled(config.name, not config.enabled)
        self._refresh_mcp_servers()

    def _connect_mcp_server(self):
        item = self.mcp_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "警告", "请先选择服务器")
            return
        config = item.data(Qt.ItemDataRole.UserRole)

        self.mcp_status_label.setText(f"正在连接 {config.name} ...")

        class ConnectWorker(QThread):
            done = pyqtSignal(int)
            failed = pyqtSignal(str)

            def __init__(self, server_name):
                super().__init__()
                self.server_name = server_name

            def run(self):
                try:
                    from src.mcp import get_mcp_manager
                    count = get_mcp_manager().connect(self.server_name, timeout=90)
                    self.done.emit(count)
                except Exception as e:
                    self.failed.emit(str(e))

        def on_done(count):
            self.mcp_status_label.setText(f"{config.name} 已连接，发现 {count} 个工具，可在 AI 助手中启用 MCP 使用")
            self._refresh_mcp_servers()
            tools = get_mcp_manager().list_tools()
            lines = [f"- {t['full_name']}: {t['description'][:60]}" for t in tools]
            self.mcp_detail.setPlainText("可用工具：\n" + "\n".join(lines))

        def on_failed(err):
            self.mcp_status_label.setText(f"{config.name} 连接失败")
            self.mcp_detail.setPlainText(f"错误：{err}\n\n请检查：\n1. 命令是否存在（npx 需要 Node.js）\n2. 网络是否可用\n3. 配置参数是否正确")
            self._refresh_mcp_servers()

        from src.mcp import get_mcp_manager
        self._connect_worker = ConnectWorker(config.name)
        self._connect_worker.done.connect(on_done)
        self._connect_worker.failed.connect(on_failed)
        self._connect_worker.start()

    # ==================== 提示词库标签 ====================

    def _create_prompts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左：搜索+列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_row = QHBoxLayout()
        self.prompt_search = QLineEdit()
        self.prompt_search.setObjectName("input")
        self.prompt_search.setPlaceholderText("搜索模板名...")
        self.prompt_search.textChanged.connect(self._refresh_prompt_list)
        search_row.addWidget(self.prompt_search)

        self.prompt_pack_combo = QComboBox()
        self.prompt_pack_combo.currentTextChanged.connect(self._refresh_prompt_list)
        search_row.addWidget(self.prompt_pack_combo)
        left_layout.addLayout(search_row)

        self.prompt_list = QListWidget()
        self.prompt_list.currentItemChanged.connect(self._on_prompt_selected)
        left_layout.addWidget(self.prompt_list)

        self.prompt_count_label = QLabel("")
        self.prompt_count_label.setObjectName("chat_hint")
        left_layout.addWidget(self.prompt_count_label)

        splitter.addWidget(left)

        # 右：内容预览
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.prompt_name_label = QLabel("选择一个模板查看内容")
        self.prompt_name_label.setObjectName("section_title")
        right_layout.addWidget(self.prompt_name_label)

        self.prompt_detail = QTextBrowser()
        right_layout.addWidget(self.prompt_detail)

        copy_btn = QPushButton("复制全部内容")
        copy_btn.setObjectName("btn_primary")
        copy_btn.setFixedHeight(36)
        copy_btn.clicked.connect(self._copy_prompt)
        right_layout.addWidget(copy_btn)

        splitter.addWidget(right)
        splitter.setSizes([320, 680])
        layout.addWidget(splitter)

        self.tabs.addTab(tab, "提示词库")

    def _refresh_prompts(self):
        from src.data.prompt_library import get_prompt_library
        library = get_prompt_library()
        library.refresh()

        self.prompt_pack_combo.blockSignals(True)
        self.prompt_pack_combo.clear()
        self.prompt_pack_combo.addItem("全部")
        for pack in library.list_packs():
            self.prompt_pack_combo.addItem(pack)
        self.prompt_pack_combo.blockSignals(False)

        self._refresh_prompt_list()

    def _refresh_prompt_list(self):
        from src.data.prompt_library import get_prompt_library
        library = get_prompt_library()

        keyword = self.prompt_search.text().strip()
        pack = self.prompt_pack_combo.currentText()
        pack = None if pack in ("全部", "") else pack

        templates = library.search(keyword) if keyword else library.list_templates(pack)
        if keyword and pack:
            templates = [t for t in templates if t.pack == pack]

        self.prompt_list.clear()
        for t in templates:
            item = QListWidgetItem(t.name)
            item.setData(Qt.ItemDataRole.UserRole, t)
            item.setToolTip(f"{t.pack} / {t.name}")
            self.prompt_list.addItem(item)

        self.prompt_count_label.setText(f"共 {len(templates)} 个模板")

    def _on_prompt_selected(self, current, _previous):
        if current is None:
            return
        template = current.data(Qt.ItemDataRole.UserRole)
        self.prompt_name_label.setText(f"{template.pack} / {template.name}")

        self.prompt_detail.setPlainText("正在解析 docx ...")

        class ParseWorker(QThread):
            done = pyqtSignal(str)

            def run(self):
                from src.data.prompt_library import get_prompt_library
                self.done.emit(get_prompt_library().read_text(template))

        self._parse_worker = ParseWorker(self)
        self._parse_worker.done.connect(self.prompt_detail.setPlainText)
        self._parse_worker.start()

    def _copy_prompt(self):
        from PyQt6.QtWidgets import QApplication
        text = self.prompt_detail.toPlainText()
        if text and not text.startswith("正在解析"):
            QApplication.clipboard().setText(text)
            self.prompt_count_label.setText("已复制到剪贴板")
