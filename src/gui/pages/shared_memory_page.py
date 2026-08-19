"""
共享记忆页面
查看和管理共享记忆系统
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QSplitter, QMessageBox,
    QInputDialog
)
from PyQt6.QtCore import Qt

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalTextEdit as ModernTextEdit


class SharedMemoryPage(QWidget):
    """共享记忆页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("共享记忆")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        
        refresh_btn = ModernButton("刷新", "secondary")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # 主体区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：智能体列表和访问规则
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 智能体列表
        agents_label = QLabel("注册智能体")
        agents_label.setObjectName("section_title")
        left_layout.addWidget(agents_label)
        
        self.shared_memory_agents_list = QListWidget()
        self.shared_memory_agents_list.currentTextChanged.connect(self._on_shared_memory_agent_selected)
        left_layout.addWidget(self.shared_memory_agents_list)
        
        # 访问规则
        rules_label = QLabel("访问规则")
        rules_label.setObjectName("section_title")
        left_layout.addWidget(rules_label)
        
        self.shared_memory_rules_list = QListWidget()
        left_layout.addWidget(self.shared_memory_rules_list)
        
        # 添加规则按钮
        add_rule_btn = ModernButton("添加规则", "primary")
        add_rule_btn.clicked.connect(self._add_access_rule)
        left_layout.addWidget(add_rule_btn)
        
        splitter.addWidget(left_panel)
        
        # 右侧：共享记忆和统计
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 统计信息
        stats_label = QLabel("统计信息")
        stats_label.setObjectName("section_title")
        right_layout.addWidget(stats_label)
        
        self.shared_memory_stats = ModernTextEdit("点击刷新查看统计信息...")
        self.shared_memory_stats.setReadOnly(True)
        right_layout.addWidget(self.shared_memory_stats)
        
        # 共享记忆列表
        memories_label = QLabel("共享记忆")
        memories_label.setObjectName("section_title")
        right_layout.addWidget(memories_label)
        
        self.shared_memory_memories_list = QListWidget()
        self.shared_memory_memories_list.currentTextChanged.connect(self._on_shared_memory_selected)
        right_layout.addWidget(self.shared_memory_memories_list)
        
        # 记忆详情
        detail_label = QLabel("详情")
        detail_label.setObjectName("section_title")
        right_layout.addWidget(detail_label)
        
        self.shared_memory_detail = ModernTextEdit("选择一条记忆查看详情...")
        self.shared_memory_detail.setReadOnly(True)
        right_layout.addWidget(self.shared_memory_detail)
        
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def _load_data(self):
        """加载数据"""
        from src.memory.shared_memory import get_shared_memory
        
        sm = get_shared_memory()
        
        # 更新智能体列表
        self.shared_memory_agents_list.clear()
        self.shared_memory_agents = []
        
        for agent_id, agent_state in sm.agent_states.items():
            display_text = f"{agent_id} ({agent_state.agent_role}) - {agent_state.status}"
            self.shared_memory_agents_list.addItem(display_text)
            self.shared_memory_agents.append((agent_id, agent_state))
        
        # 更新访问规则列表
        self.shared_memory_rules_list.clear()
        self.shared_memory_rules = sm.access_rules
        
        for rule in sm.access_rules:
            display_text = f"{rule.agent_id} -> {rule.target_function_type}/{rule.target_project} ({rule.access_level})"
            self.shared_memory_rules_list.addItem(display_text)
        
        # 更新统计信息
        stats = sm.get_statistics()
        stats_text = f"""统计信息:

总智能体数: {stats['total_agents']}
总记忆数: {stats['total_memories']}

按类型统计:
{chr(10).join(f'- {k}: {v}' for k, v in stats['by_type'].items())}

按智能体统计:
{chr(10).join(f'- {k}: {v}' for k, v in stats['by_agent'].items())}"""
        
        self.shared_memory_stats.setText(stats_text)
        
        # 更新共享记忆列表
        self.shared_memory_memories_list.clear()
        self.shared_memory_memories = list(sm.memories.values())
        
        for memory in self.shared_memory_memories:
            display_text = f"{memory.id} - {memory.source_agent} ({memory.memory_type})"
            self.shared_memory_memories_list.addItem(display_text)
    
    def _on_shared_memory_agent_selected(self, selected_text):
        """智能体选中事件"""
        if not selected_text or not hasattr(self, 'shared_memory_agents'):
            return
        
        # 查找选中的智能体
        for agent_id, agent_state in self.shared_memory_agents:
            display_text = f"{agent_id} ({agent_state.agent_role}) - {agent_state.status}"
            if display_text == selected_text:
                # 显示智能体详情
                detail_text = f"""智能体详情:

ID: {agent_id}
角色: {agent_state.agent_role}
状态: {agent_state.status}
当前任务: {agent_state.current_task}
总任务数: {agent_state.total_tasks}
完成任务数: {agent_state.completed_tasks}
失败任务数: {agent_state.failed_tasks}
最后活动: {agent_state.last_active}"""
                
                self.shared_memory_detail.setText(detail_text)
                break
    
    def _on_shared_memory_selected(self, selected_text):
        """记忆选中事件"""
        if not selected_text or not hasattr(self, 'shared_memory_memories'):
            return
        
        # 查找选中的记忆
        for memory in self.shared_memory_memories:
            display_text = f"{memory.id} - {memory.source_agent} ({memory.memory_type})"
            if display_text == selected_text:
                # 显示记忆详情
                detail_text = f"""记忆详情:

ID: {memory.id}
来源智能体: {memory.source_agent}
记忆类型: {memory.memory_type}
内容: {memory.content}
相关智能体: {', '.join(memory.related_agents)}
相关任务: {memory.related_task}
章节: {memory.chapter_num}
重要程度: {memory.importance}
创建时间: {memory.created_at}"""
                
                self.shared_memory_detail.setText(detail_text)
                break
    
    def _add_access_rule(self):
        """添加访问规则"""
        # 获取智能体ID
        agent_id, ok = QInputDialog.getText(self, "添加访问规则", "智能体ID:")
        if not ok or not agent_id:
            return
        
        # 获取目标功能类型
        function_types = ["outline", "chapter", "outline_critic", "chapter_critic", "knowledge_check"]
        function_type, ok = QInputDialog.getItem(self, "添加访问规则", "目标功能类型:", function_types, 0, False)
        if not ok:
            return
        
        # 获取目标项目
        project, ok = QInputDialog.getText(self, "添加访问规则", "目标项目 (*表示所有):")
        if not ok:
            return
        
        # 获取访问级别
        access_levels = ["read", "write", "full"]
        access_level, ok = QInputDialog.getItem(self, "添加访问规则", "访问级别:", access_levels, 0, False)
        if not ok:
            return
        
        # 添加规则
        from src.memory.shared_memory import get_shared_memory
        sm = get_shared_memory()
        
        if sm.add_access_rule(agent_id, function_type, project, access_level):
            self._load_data()
            QMessageBox.information(self, "成功", "访问规则已添加")
        else:
            QMessageBox.warning(self, "失败", "添加访问规则失败")
