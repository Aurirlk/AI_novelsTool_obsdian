"""
界面多语言（i18n）
zh_CN / en_US，切换后主界面框架即时生效
"""

_current_language = "zh_CN"

STRINGS = {
    # ---------- 主窗口 ----------
    "app.title": {"zh_CN": "AI写作助手 - 专业版", "en_US": "AI Writing Studio - Pro"},
    "sidebar.workspace": {"zh_CN": "工作区", "en_US": "Workspace"},
    "sidebar.tools": {"zh_CN": "工具", "en_US": "Tools"},
    "nav.ai_chat": {"zh_CN": "AI 助手", "en_US": "AI Assistant"},
    "nav.home": {"zh_CN": "概览", "en_US": "Overview"},
    "nav.project": {"zh_CN": "项目管理", "en_US": "Projects"},
    "nav.writer": {"zh_CN": "写作工作台", "en_US": "Writer"},
    "nav.books": {"zh_CN": "书籍管理", "en_US": "Books"},
    "nav.outline": {"zh_CN": "大纲编辑", "en_US": "Outlines"},
    "nav.character": {"zh_CN": "角色管理", "en_US": "Characters"},
    "nav.hook": {"zh_CN": "悬念管理", "en_US": "Hooks"},
    "nav.event": {"zh_CN": "故事时间线", "en_US": "Story Timeline"},
    "nav.critic": {"zh_CN": "批评师", "en_US": "Critic"},
    "nav.extensions": {"zh_CN": "扩展中心", "en_US": "Extensions"},
    "nav.book": {"zh_CN": "拆书分析", "en_US": "Book Analysis"},
    "nav.export": {"zh_CN": "导出中心", "en_US": "Export"},
    "nav.history": {"zh_CN": "历史记录", "en_US": "History"},
    "nav.memory": {"zh_CN": "共享记忆", "en_US": "Shared Memory"},
    "nav.settings": {"zh_CN": "系统设置", "en_US": "Settings"},

    "status.ready": {"zh_CN": "就绪", "en_US": "Ready"},
    "status.current_page": {"zh_CN": "当前页面", "en_US": "Page"},
    "status.no_project": {"zh_CN": "未打开项目", "en_US": "No project"},
    "status.agent_idle": {"zh_CN": "智能体: 空闲", "en_US": "Agent: Idle"},
    "menu.file": {"zh_CN": "文件", "en_US": "File"},
    "menu.edit": {"zh_CN": "编辑", "en_US": "Edit"},
    "menu.view": {"zh_CN": "视图", "en_US": "View"},
    "menu.tools": {"zh_CN": "工具", "en_US": "Tools"},
    "menu.help": {"zh_CN": "帮助", "en_US": "Help"},
    "menu.theme": {"zh_CN": "主题", "en_US": "Theme"},
    "menu.dark": {"zh_CN": "深色主题", "en_US": "Dark"},
    "menu.light": {"zh_CN": "浅色主题", "en_US": "Light"},

    # ---------- AI助手页 ----------
    "chat.title": {"zh_CN": "AI 助手", "en_US": "AI Assistant"},
    "chat.new": {"zh_CN": "新对话", "en_US": "New Chat"},
    "chat.greeting": {"zh_CN": "我是你的网文创作伙伴", "en_US": "Your webnovel writing partner"},
    "chat.subtitle": {"zh_CN": "@ 引用文件，/ 调用技能与指令，+ 选择专家与连接器",
                      "en_US": "@ attach files, / skills & commands, + experts & connectors"},
    "chat.placeholder": {"zh_CN": "今天帮你想做些什么？ @ 引用文件，/ 调用技能与指令",
                         "en_US": "What can I help with? @ files, / skills"},
    "chat.send": {"zh_CN": "发送", "en_US": "Send"},
    "chat.pick_model": {"zh_CN": "选择模型", "en_US": "Select model"},
    "chat.config_model": {"zh_CN": "配置自定义模型", "en_US": "Configure models"},
    "chat.add_file": {"zh_CN": "添加文件", "en_US": "Add file"},
    "chat.expert": {"zh_CN": "专家", "en_US": "Experts"},
    "chat.skill": {"zh_CN": "技能", "en_US": "Skills"},
    "chat.connector": {"zh_CN": "连接器", "en_US": "Connectors"},
    "chat.local_file": {"zh_CN": "本地文件...", "en_US": "Local files..."},
    "chat.from_outline": {"zh_CN": "从大纲库选择...", "en_US": "From outline library..."},
    "chat.from_prompt": {"zh_CN": "从提示词库选择...", "en_US": "From prompt library..."},
    "chat.more_experts": {"zh_CN": "更多专家...", "en_US": "More experts..."},
    "chat.manage_skills": {"zh_CN": "管理技能", "en_US": "Manage skills"},
    "chat.manage_connectors": {"zh_CN": "管理连接器", "en_US": "Manage connectors"},
    "chat.expert_picked": {"zh_CN": "已选择专家", "en_US": "Expert selected"},
    "chat.skill_loaded": {"zh_CN": "已加载技能", "en_US": "Skill loaded"},
    "chat.skill_auto": {"zh_CN": "已自动匹配技能", "en_US": "Skill auto-matched"},
    "chat.no_key": {"zh_CN": "尚未配置该提供商的 API 密钥。请前往「系统设置 → LLM」填入你自己的密钥后即可开始对话。",
                    "en_US": "No API key configured for this provider. Go to Settings → LLM to add your own key."},
    "chat.workflow": {"zh_CN": "全流程生成（创意→大纲→章节）", "en_US": "Full Workflow (Idea→Outline→Chapters)"},
    "chat.workflow_idea": {"zh_CN": "全流程生成", "en_US": "Full Workflow"},
    "chat.workflow_idea_hint": {"zh_CN": "请输入一句话创意（例如：废柴少年觉醒隐藏血脉）：", "en_US": "Enter a one-line idea (e.g. A loser awakens a hidden bloodline):"},
    "chat.workflow_chapters": {"zh_CN": "生成章节数：", "en_US": "Chapters to generate:"},
    "chat.workflow_running": {"zh_CN": "正在运行全流程：创意 → 大纲 → 逐章撰写", "en_US": "Running workflow: idea → outline → chapters"},
    "chat.workflow_done": {"zh_CN": "生成完成", "en_US": "Generated"},
    "chat.workflow_failed": {"zh_CN": "全流程生成失败", "en_US": "Workflow failed"},
    "chat.workflow_need_key": {"zh_CN": "尚未配置 API 密钥。请前往「系统设置 → LLM」填入密钥后即可全流程生成。",
                               "en_US": "No API key configured. Go to Settings → LLM to enable the workflow."},

    # ---------- 邮箱投递（设置页 + 导出页） ----------
    "email.tab": {"zh_CN": "邮箱投递", "en_US": "Email Delivery"},
    "email.sender_group": {"zh_CN": "发件配置（SMTP）", "en_US": "Sender (SMTP)"},
    "email.receiver_group": {"zh_CN": "收件配置", "en_US": "Recipient"},
    "email.preset": {"zh_CN": "邮箱服务商", "en_US": "Provider"},
    "email.smtp_host": {"zh_CN": "SMTP服务器", "en_US": "SMTP Server"},
    "email.smtp_port": {"zh_CN": "SMTP端口", "en_US": "SMTP Port"},
    "email.ssl": {"zh_CN": "使用 SSL 加密连接", "en_US": "Use SSL"},
    "email.sender": {"zh_CN": "发件邮箱", "en_US": "Sender Email"},
    "email.auth_code": {"zh_CN": "授权码", "en_US": "Auth Code"},
    "email.editor": {"zh_CN": "编辑邮箱", "en_US": "Editor Email"},
    "email.sign": {"zh_CN": "署名", "en_US": "Signature"},
    "email.test": {"zh_CN": "测试连接", "en_US": "Test Connection"},
    "email.testing": {"zh_CN": "正在测试连接...", "en_US": "Testing connection..."},
    "email.hint": {"zh_CN": "提示：授权码不是登录密码。QQ邮箱：设置→账户→开启SMTP服务→生成授权码；163邮箱：设置→POP3/SMTP/IMAP→开启服务→设置客户端授权密码。",
                   "en_US": "Note: the auth code is NOT your login password. QQ: Settings→Account→enable SMTP→generate code. 163: Settings→POP3/SMTP/IMAP→enable→set client password."},
    "email.no_config": {"zh_CN": "请先到 系统设置 → 邮箱投递 配置发件邮箱和授权码（授权码不是登录密码）。",
                        "en_US": "Configure sender email & auth code in Settings → Email Delivery first."},
    "email.no_editor": {"zh_CN": "请先到 系统设置 → 邮箱投递 配置编辑收稿邮箱。",
                        "en_US": "Configure the editor email in Settings → Email Delivery first."},
    "email.send_to_editor": {"zh_CN": "投递到编辑邮箱", "en_US": "Deliver to Editor"},
    "email.confirm": {"zh_CN": "确认投递", "en_US": "Confirm Delivery"},
    "email.delivered": {"zh_CN": "投递成功", "en_US": "Delivered"},
    "email.failed": {"zh_CN": "投递失败", "en_US": "Delivery Failed"},
    "email.no_chapters": {"zh_CN": "当前作品没有可投递的章节", "en_US": "No chapters to deliver"},

    # ---------- 项目数据工具（AI助手能力说明） ----------
    "tools.capability": {"zh_CN": "你有能力读取和写入用户的项目数据（写作空间书籍/章节、大纲库、角色库、钩子库、时间线、邮箱投递）。",
                         "en_US": "You can read & write the user's project data (books/chapters, outlines, characters, hooks, timeline, email delivery)."},

    # ---------- 设置页 ----------
    "settings.title": {"zh_CN": "设置", "en_US": "Settings"},
    "settings.save": {"zh_CN": "保存设置", "en_US": "Save"},
    "settings.reset": {"zh_CN": "重置默认", "en_US": "Reset"},
    "settings.tab.personal": {"zh_CN": "个性化", "en_US": "Personal"},
    "settings.tab.llm": {"zh_CN": "LLM", "en_US": "LLM"},
    "settings.tab.generation": {"zh_CN": "生成", "en_US": "Generation"},
    "settings.tab.appearance": {"zh_CN": "外观", "en_US": "Appearance"},
    "settings.tab.general": {"zh_CN": "通用", "en_US": "General"},
    "settings.tab.shortcuts": {"zh_CN": "快捷键", "en_US": "Shortcuts"},
    "settings.tab.data": {"zh_CN": "数据", "en_US": "Data"},
    "settings.language": {"zh_CN": "语言", "en_US": "Language"},
    "settings.language_hint": {"zh_CN": "切换后主界面立即生效，部分页面重启后生效",
                               "en_US": "Applies immediately to the main UI; some pages need a restart"},
    "settings.theme": {"zh_CN": "主题", "en_US": "Theme"},
    "settings.theme_light": {"zh_CN": "浅色", "en_US": "Light"},
    "settings.theme_dark": {"zh_CN": "深色", "en_US": "Dark"},

    # ---------- 写作工作台（文件树/右键菜单/回收站） ----------
    "writer.workspace": {"zh_CN": "写作空间", "en_US": "Writing Space"},
    "writer.no_book": {"zh_CN": "未打开书籍", "en_US": "No book opened"},
    "writer.open_book": {"zh_CN": "打开书", "en_US": "Open Book"},
    "writer.search_placeholder": {"zh_CN": "搜索全书、大纲、角色、悬念...", "en_US": "Search books, outlines, characters, hooks..."},
    "writer.new_book": {"zh_CN": "新建书", "en_US": "New Book"},
    "writer.new_chapter": {"zh_CN": "新建章节", "en_US": "New Chapter"},
    "writer.new_folder": {"zh_CN": "新建卷/目录", "en_US": "New Volume/Folder"},
    "writer.rename": {"zh_CN": "重命名", "en_US": "Rename"},
    "writer.delete": {"zh_CN": "删除", "en_US": "Delete"},
    "writer.copy_path": {"zh_CN": "复制路径", "en_US": "Copy Path"},
    "writer.refresh": {"zh_CN": "刷新", "en_US": "Refresh"},
    "writer.refresh_tree": {"zh_CN": "刷新目录", "en_US": "Refresh Tree"},
    "writer.trash": {"zh_CN": "回收站", "en_US": "Trash"},
    "writer.trash_title": {"zh_CN": "回收站", "en_US": "Trash"},
    "writer.trash_hint": {"zh_CN": "回收站内容保留30天，到期自动清理。恢复时若目标位置已有同名节点，可选择覆盖。",
                          "en_US": "Trash keeps items for 30 days. If a node with the same name exists, you can choose to overwrite."},
    "writer.trash_empty_list": {"zh_CN": "回收站为空", "en_US": "Trash is empty"},
    "writer.trash_unknown_origin": {"zh_CN": "未知位置", "en_US": "Unknown location"},
    "writer.trash_deleted_at": {"zh_CN": "删除于", "en_US": "Deleted at"},
    "writer.trash_restore": {"zh_CN": "恢复选中", "en_US": "Restore Selected"},
    "writer.trash_empty": {"zh_CN": "清空回收站", "en_US": "Empty Trash"},
    "writer.trash_close": {"zh_CN": "关闭", "en_US": "Close"},
    "writer.trash_need_select": {"zh_CN": "请先选择要恢复的内容", "en_US": "Select an item to restore"},
    "writer.trash_conflict": {"zh_CN": "同名冲突", "en_US": "Name Conflict"},
    "writer.trash_conflict_msg": {"zh_CN": "目标位置已存在同名内容。是否覆盖？\n（选择「否」则取消恢复）",
                                  "en_US": "An item with the same name already exists. Overwrite?\n(No cancels the restore)"},
    "writer.trash_restored": {"zh_CN": "已恢复", "en_US": "Restored"},
    "writer.trash_restore_failed": {"zh_CN": "恢复失败", "en_US": "Restore Failed"},
    "writer.trash_confirm_empty": {"zh_CN": "确认清空", "en_US": "Confirm Empty"},
    "writer.trash_confirm_empty_msg": {"zh_CN": "清空回收站将永久删除其中的全部内容，不可恢复。确定继续吗？",
                                       "en_US": "Emptying the trash permanently deletes everything in it. Continue?"},
    "writer.trash_emptied": {"zh_CN": "已清空", "en_US": "Emptied"},
    "writer.trash_emptied_msg": {"zh_CN": "已永久删除 {count} 项回收站内容", "en_US": "{count} item(s) permanently deleted"},
    "writer.delete_confirm": {"zh_CN": "确定删除「{name}」吗？", "en_US": "Delete \"{name}\"?"},
    "writer.delete_confirm_children": {"zh_CN": "（含其下所有内容）", "en_US": "(including all children)"},
    "writer.delete_confirm_trash": {"zh_CN": "删除后可在「回收站」中恢复。", "en_US": "You can restore it from the Trash."},
    "writer.delete_failed": {"zh_CN": "失败", "en_US": "Failed"},
    "writer.assist_title": {"zh_CN": "创作助手", "en_US": "Assistant"},
    "writer.assist_output": {"zh_CN": "助手输出", "en_US": "Assistant Output"},
    "writer.apply_output": {"zh_CN": "插入到正文", "en_US": "Insert to Text"},
    "writer.copy_output": {"zh_CN": "复制", "en_US": "Copy"},

    # ---------- 测试密钥警告条 ----------
    "settings.test_key_warning": {
        "zh_CN": "检测到测试用 API 密钥（{detail}）。测试密钥仅限开发使用，正式上线前请删除，避免密钥泄露造成费用损失。可在下方 LLM 设置中替换为正式密钥。",
        "en_US": "Test API key detected ({detail}). Test keys are for development only — remove them before release to avoid leaks. Replace with a real key in the LLM settings below."},

    # ---------- 创作助手卡片 ----------
    "assist.critique": {"zh_CN": "批评检查", "en_US": "Critique"},
    "assist.critique_desc": {"zh_CN": "12项一致性检查", "en_US": "12-point consistency check"},
    "assist.title": {"zh_CN": "智能标题", "en_US": "Smart Title"},
    "assist.title_desc": {"zh_CN": "起5个抓眼标题", "en_US": "Generate 5 catchy titles"},
    "assist.intro": {"zh_CN": "提取导语", "en_US": "Extract Intro"},
    "assist.intro_desc": {"zh_CN": "生成黄金三行导语", "en_US": "Generate 3-line hook intro"},
    "assist.polish": {"zh_CN": "错别字修改", "en_US": "Typo Fix"},
    "assist.polish_desc": {"zh_CN": "只改错别字，不碰文风", "en_US": "Fix typos only, no style changes"},
    "assist.expand": {"zh_CN": "扩写内容", "en_US": "Expand"},
    "assist.expand_desc": {"zh_CN": "丰富细节描写", "en_US": "Enrich with details"},
    "assist.continue": {"zh_CN": "续写下文", "en_US": "Continue"},
    "assist.continue_desc": {"zh_CN": "接着当前内容续写", "en_US": "Continue from current text"},

    # ---------- 首页快速开始 ----------
    "home.quick_start": {"zh_CN": "快速开始", "en_US": "Quick Start"},
    "home.step1": {"zh_CN": "1. 配置 API 密钥", "en_US": "1. Configure API Key"},
    "home.step1_desc": {"zh_CN": "前往设置页，选择提供商并粘贴密钥", "en_US": "Go to Settings, select provider and paste your key"},
    "home.step2": {"zh_CN": "2. 创建书籍", "en_US": "2. Create a Book"},
    "home.step2_desc": {"zh_CN": "在书籍管理中创建你的第一本书", "en_US": "Create your first book in Book Management"},
    "home.step3": {"zh_CN": "3. 开始写作", "en_US": "3. Start Writing"},
    "home.step3_desc": {"zh_CN": "打开写作工作台，AI辅助你创作", "en_US": "Open the Writer, AI assists your创作"},

    # ---------- 侧边栏折叠 ----------
    "sidebar.collapse": {"zh_CN": "折叠侧边栏", "en_US": "Collapse sidebar"},
    "sidebar.expand": {"zh_CN": "展开侧边栏", "en_US": "Expand sidebar"},
}


def set_language(lang: str):
    global _current_language
    if lang in ("zh_CN", "en_US"):
        _current_language = lang


def get_language() -> str:
    return _current_language


def tr(key: str) -> str:
    """翻译，找不到时返回key本身"""
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(_current_language, entry.get("zh_CN", key))


def load_from_settings():
    """启动时从设置库读取语言"""
    try:
        from src.data.settings_manager import get_settings_manager
        set_language(get_settings_manager().get_setting("general", "language", "zh_CN"))
    except Exception:
        pass
