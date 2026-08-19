"""
历史对话页面
查看和管理历史对话记录
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QComboBox, QSplitter,
    QMessageBox
)
from PyQt6.QtCore import Qt

from ..professional_components import ProfessionalButton as ModernButton, ProfessionalTextEdit as ModernTextEdit


class HistoryPage(QWidget):
    """历史对话页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_history()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("历史对话")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        
        refresh_btn = ModernButton("刷新", "secondary")
        refresh_btn.clicked.connect(self._load_history)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # 主体区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：项目列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 功能类型过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("功能类型:")
        filter_layout.addWidget(filter_label)
        
        self.history_filter = QComboBox()
        self.history_filter.addItems(["全部", "大纲生成", "章节生成", "大纲批评", "章节批评", "知识库检查"])
        self.history_filter.currentTextChanged.connect(self._filter_history)
        filter_layout.addWidget(self.history_filter)
        
        left_layout.addLayout(filter_layout)
        
        # 项目列表
        self.history_project_list = QListWidget()
        self.history_project_list.currentTextChanged.connect(self._on_history_project_selected)
        left_layout.addWidget(self.history_project_list)
        
        splitter.addWidget(left_panel)
        
        # 右侧：记录详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 记录列表
        records_label = QLabel("对话记录")
        records_label.setObjectName("section_title")
        right_layout.addWidget(records_label)
        
        self.history_records_list = QListWidget()
        self.history_records_list.currentTextChanged.connect(self._on_history_record_selected)
        right_layout.addWidget(self.history_records_list)
        
        # 记录详情
        detail_label = QLabel("详情")
        detail_label.setObjectName("section_title")
        right_layout.addWidget(detail_label)
        
        self.history_detail = ModernTextEdit("选择一条记录查看详情...")
        self.history_detail.setReadOnly(True)
        right_layout.addWidget(self.history_detail)
        
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def _load_history(self):
        """加载历史对话"""
        from src.data.history_manager import get_history_manager
        
        hm = get_history_manager()
        projects = hm.list_projects()
        
        self.history_project_list.clear()
        self.history_projects = projects
        
        for project in projects:
            display_text = f"{project['function_name']} - {project['project_name']} ({project['record_count']}条)"
            self.history_project_list.addItem(display_text)
    
    def _filter_history(self, filter_text):
        """过滤历史对话"""
        from src.data.history_manager import get_history_manager
        
        hm = get_history_manager()
        
        # 映射显示名称到功能类型
        filter_map = {
            "全部": None,
            "大纲生成": "outline",
            "章节生成": "chapter",
            "大纲批评": "outline_critic",
            "章节批评": "chapter_critic",
            "知识库检查": "knowledge_check",
        }
        
        function_type = filter_map.get(filter_text)
        projects = hm.list_projects(function_type)
        
        self.history_project_list.clear()
        self.history_projects = projects
        
        for project in projects:
            display_text = f"{project['function_name']} - {project['project_name']} ({project['record_count']}条)"
            self.history_project_list.addItem(display_text)
    
    def _on_history_project_selected(self, selected_text):
        """项目选中事件"""
        if not selected_text or not hasattr(self, 'history_projects'):
            return
        
        # 查找选中的项目
        for project in self.history_projects:
            display_text = f"{project['function_name']} - {project['project_name']} ({project['record_count']}条)"
            if display_text == selected_text:
                # 加载项目的记录
                from src.data.history_manager import get_history_manager
                hm = get_history_manager()
                records = hm.list_records(project['function_type'], project['project_name'])
                
                self.history_records_list.clear()
                self.history_records = records
                
                for record in records:
                    display_text = f"{record.title} ({record.created_at[:10]})"
                    self.history_records_list.addItem(display_text)
                
                break
    
    def _on_history_record_selected(self, selected_text):
        """记录选中事件"""
        if not selected_text or not hasattr(self, 'history_records'):
            return
        
        # 查找选中的记录
        for record in self.history_records:
            display_text = f"{record.title} ({record.created_at[:10]})"
            if display_text == selected_text:
                # 显示记录详情
                detail_text = f"""标题: {record.title}
功能类型: {record.function_type}
项目名称: {record.project_name}
创建时间: {record.created_at}

{'='*50}

输入内容:
{record.content}

{'='*50}

输出结果:
{record.result}"""
                
                self.history_detail.setText(detail_text)
                break
