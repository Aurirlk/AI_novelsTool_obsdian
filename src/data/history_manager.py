"""
历史对话存储管理器
管理不同功能的历史对话记录
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class HistoryRecord:
    """历史对话记录"""
    id: str
    function_type: str  # 功能类型：outline/chapter/outline_critic/chapter_critic/knowledge_check
    project_name: str   # 项目名称
    title: str          # 对话标题
    content: str        # 输入内容
    result: str         # 输出结果
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HistoryRecord':
        """从字典创建"""
        return cls(**data)


class HistoryManager:
    """历史对话存储管理器"""
    
    # 功能类型映射
    FUNCTION_TYPES = {
        "outline": "大纲生成",
        "chapter": "章节生成",
        "outline_critic": "大纲批评",
        "chapter_critic": "章节批评",
        "knowledge_check": "知识库检查",
    }
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化历史管理器
        
        Args:
            base_dir: 基础存储目录
        """
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "历史对话")
        
        self.base_dir = base_dir
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        # 创建基础目录
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 为每种功能类型创建目录
        for func_type in self.FUNCTION_TYPES.keys():
            func_dir = os.path.join(self.base_dir, func_type)
            os.makedirs(func_dir, exist_ok=True)
    
    def save_record(self, record: HistoryRecord) -> str:
        """
        保存历史记录
        
        Args:
            record: 历史记录
        
        Returns:
            保存的文件路径
        """
        # 获取功能类型目录
        func_dir = os.path.join(self.base_dir, record.function_type)
        
        # 创建项目目录
        project_dir = os.path.join(func_dir, record.project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{record.id}_{timestamp}.json"
        filepath = os.path.join(project_dir, filename)
        
        # 保存为JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"[历史管理] 保存记录: {filepath}")
        return filepath
    
    def load_record(self, filepath: str) -> Optional[HistoryRecord]:
        """
        加载历史记录
        
        Args:
            filepath: 文件路径
        
        Returns:
            历史记录
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return HistoryRecord.from_dict(data)
        except Exception as e:
            print(f"[历史管理] 加载记录失败: {e}")
            return None
    
    def list_projects(self, function_type: Optional[str] = None) -> List[Dict]:
        """
        列出项目
        
        Args:
            function_type: 功能类型过滤
        
        Returns:
            项目列表
        """
        projects = []
        
        # 确定要扫描的目录
        if function_type:
            func_types = [function_type]
        else:
            func_types = list(self.FUNCTION_TYPES.keys())
        
        for func_type in func_types:
            func_dir = os.path.join(self.base_dir, func_type)
            if not os.path.exists(func_dir):
                continue
            
            # 扫描项目目录
            for project_name in os.listdir(func_dir):
                project_dir = os.path.join(func_dir, project_name)
                if not os.path.isdir(project_dir):
                    continue
                
                # 统计记录数量
                records = [f for f in os.listdir(project_dir) if f.endswith('.json')]
                
                projects.append({
                    "function_type": func_type,
                    "function_name": self.FUNCTION_TYPES.get(func_type, func_type),
                    "project_name": project_name,
                    "record_count": len(records),
                    "project_dir": project_dir,
                })
        
        return projects
    
    def list_records(self, function_type: str, project_name: str) -> List[HistoryRecord]:
        """
        列出项目的历史记录
        
        Args:
            function_type: 功能类型
            project_name: 项目名称
        
        Returns:
            历史记录列表
        """
        records = []
        
        project_dir = os.path.join(self.base_dir, function_type, project_name)
        if not os.path.exists(project_dir):
            return records
        
        # 扫描JSON文件
        for filename in sorted(os.listdir(project_dir), reverse=True):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(project_dir, filename)
            record = self.load_record(filepath)
            if record:
                records.append(record)
        
        return records
    
    def delete_record(self, function_type: str, project_name: str, record_id: str) -> bool:
        """
        删除历史记录
        
        Args:
            function_type: 功能类型
            project_name: 项目名称
            record_id: 记录ID
        
        Returns:
            是否删除成功
        """
        project_dir = os.path.join(self.base_dir, function_type, project_name)
        if not os.path.exists(project_dir):
            return False
        
        # 查找并删除记录
        for filename in os.listdir(project_dir):
            if filename.startswith(record_id) and filename.endswith('.json'):
                filepath = os.path.join(project_dir, filename)
                os.remove(filepath)
                print(f"[历史管理] 删除记录: {filepath}")
                return True
        
        return False
    
    def delete_project(self, function_type: str, project_name: str) -> bool:
        """
        删除项目
        
        Args:
            function_type: 功能类型
            project_name: 项目名称
        
        Returns:
            是否删除成功
        """
        import shutil
        
        project_dir = os.path.join(self.base_dir, function_type, project_name)
        if not os.path.exists(project_dir):
            return False
        
        shutil.rmtree(project_dir)
        print(f"[历史管理] 删除项目: {project_dir}")
        return True
    
    def search_records(self, keyword: str, function_type: Optional[str] = None) -> List[HistoryRecord]:
        """
        搜索历史记录
        
        Args:
            keyword: 搜索关键词
            function_type: 功能类型过滤
        
        Returns:
            匹配的历史记录列表
        """
        results = []
        
        # 确定要扫描的目录
        if function_type:
            func_types = [function_type]
        else:
            func_types = list(self.FUNCTION_TYPES.keys())
        
        for func_type in func_types:
            func_dir = os.path.join(self.base_dir, func_type)
            if not os.path.exists(func_dir):
                continue
            
            # 扫描项目目录
            for project_name in os.listdir(func_dir):
                project_dir = os.path.join(func_dir, project_name)
                if not os.path.isdir(project_dir):
                    continue
                
                # 扫描记录文件
                for filename in os.listdir(project_dir):
                    if not filename.endswith('.json'):
                        continue
                    
                    filepath = os.path.join(project_dir, filename)
                    record = self.load_record(filepath)
                    if record and (keyword in record.title or keyword in record.content or keyword in record.result):
                        results.append(record)
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_projects": 0,
            "total_records": 0,
            "by_function_type": {},
        }
        
        for func_type in self.FUNCTION_TYPES.keys():
            func_dir = os.path.join(self.base_dir, func_type)
            if not os.path.exists(func_dir):
                continue
            
            func_stats = {
                "project_count": 0,
                "record_count": 0,
            }
            
            # 统计项目和记录
            for project_name in os.listdir(func_dir):
                project_dir = os.path.join(func_dir, project_name)
                if not os.path.isdir(project_dir):
                    continue
                
                func_stats["project_count"] += 1
                stats["total_projects"] += 1
                
                # 统计记录
                records = [f for f in os.listdir(project_dir) if f.endswith('.json')]
                func_stats["record_count"] += len(records)
                stats["total_records"] += len(records)
            
            stats["by_function_type"][func_type] = {
                "name": self.FUNCTION_TYPES.get(func_type, func_type),
                **func_stats,
            }
        
        return stats
    
    def generate_index(self) -> str:
        """
        生成索引内容（Markdown格式）
        
        Returns:
            索引内容
        """
        stats = self.get_statistics()
        
        lines = [
            "# 历史对话索引",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 统计概览",
            "",
            f"- 总项目数: {stats['total_projects']}",
            f"- 总记录数: {stats['total_records']}",
            "",
            "## 按功能分类",
            "",
        ]
        
        for func_type, func_stats in stats["by_function_type"].items():
            lines.append(f"### {func_stats['name']}")
            lines.append("")
            lines.append(f"- 项目数: {func_stats['project_count']}")
            lines.append(f"- 记录数: {func_stats['record_count']}")
            lines.append("")
            
            # 列出项目
            projects = self.list_projects(func_type)
            for project in projects:
                lines.append(f"#### {project['project_name']}")
                lines.append("")
                
                # 列出记录
                records = self.list_records(func_type, project['project_name'])
                for record in records[:5]:  # 只显示最近5条
                    lines.append(f"- {record.title} ({record.created_at[:10]})")
                
                if len(records) > 5:
                    lines.append(f"- ... 还有 {len(records) - 5} 条记录")
                
                lines.append("")
        
        return "\n".join(lines)


# 全局实例
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """获取历史管理器单例"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager
