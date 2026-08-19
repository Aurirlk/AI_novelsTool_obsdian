"""
Multi-Agent 记忆共享机制
实现智能体之间的记忆共享、状态追踪、知识传递
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading


class AgentRole(Enum):
    """智能体角色"""
    OUTLINE = "outline"           # 大纲师
    WRITER = "writer"             # 码字工
    REVIEWER = "reviewer"         # 督察
    POLISHER = "polisher"         # 运营
    CRITIC = "critic"             # 评论家
    OUTLINE_CRITIC = "outline_critic"   # 大纲批评师
    CHAPTER_CRITIC = "chapter_critic"   # 章节批评师
    KNOWLEDGE_CHECKER = "knowledge_checker"  # 知识库检查器


class MemoryType(Enum):
    """记忆类型"""
    FACT = "fact"                 # 事实（确定的信息）
    OPINION = "opinion"           # 观点（智能体的判断）
    FEEDBACK = "feedback"         # 反馈（对其他智能体的反馈）
    KNOWLEDGE = "knowledge"       # 知识（从知识库获取）
    CONTEXT = "context"           # 上下文（当前任务上下文）


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    source_agent: str             # 来源智能体
    memory_type: str              # 记忆类型
    content: str                  # 记忆内容
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 关联信息
    related_agents: List[str] = field(default_factory=list)  # 相关智能体
    related_task: str = ""        # 相关任务
    chapter_num: int = 0          # 相关章节
    
    # 时间信息
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    
    # 重要程度
    importance: int = 5           # 1-10
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        return cls(**data)


@dataclass
class AgentState:
    """智能体状态"""
    agent_id: str
    agent_role: str
    
    # 当前状态
    status: str = "idle"          # idle/working/completed/error
    current_task: str = ""
    progress: float = 0.0
    
    # 历史统计
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    # 最后活动
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    last_task: str = ""
    
    # 知识积累
    learned_patterns: List[str] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AccessRule:
    """访问规则"""
    agent_id: str
    target_function_type: str  # 目标功能类型
    target_project: str        # 目标项目（*表示所有项目）
    access_level: str = "read" # read/write/full
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SharedMemory:
    """Multi-Agent 共享记忆系统"""
    
    def __init__(self, project_dir: str):
        """
        初始化共享记忆系统
        
        Args:
            project_dir: 项目目录
        """
        self.project_dir = project_dir
        self.shared_dir = os.path.join(project_dir, "shared_memory")
        os.makedirs(self.shared_dir, exist_ok=True)
        
        # 记忆存储
        self.memories: Dict[str, MemoryEntry] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.access_rules: List[AccessRule] = []
        
        # 索引
        self.agent_memory_index: Dict[str, Set[str]] = {}  # agent_id -> memory_ids
        self.type_memory_index: Dict[str, Set[str]] = {}   # memory_type -> memory_ids
        self.chapter_memory_index: Dict[int, Set[str]] = {}  # chapter_num -> memory_ids
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 加载数据
        self._load_all()
    
    def _load_all(self):
        """加载所有数据"""
        # 加载记忆
        memories_file = os.path.join(self.shared_dir, "memories.json")
        if os.path.exists(memories_file):
            with open(memories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for memory_data in data:
                    memory = MemoryEntry.from_dict(memory_data)
                    self.memories[memory.id] = memory
                    self._index_memory(memory)
        
        # 加载智能体状态
        states_file = os.path.join(self.shared_dir, "agent_states.json")
        if os.path.exists(states_file):
            with open(states_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for state_data in data:
                    state = AgentState(**state_data)
                    self.agent_states[state.agent_id] = state
        
        # 加载访问规则
        rules_file = os.path.join(self.shared_dir, "access_rules.json")
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for rule_data in data:
                    rule = AccessRule(**rule_data)
                    self.access_rules.append(rule)
        
        print(f"[共享记忆] 加载完成: {len(self.memories)} 条记忆, {len(self.agent_states)} 个智能体, {len(self.access_rules)} 条规则")
    
    def _save_all(self):
        """保存所有数据"""
        # 保存记忆
        memories_file = os.path.join(self.shared_dir, "memories.json")
        with open(memories_file, 'w', encoding='utf-8') as f:
            json.dump([m.to_dict() for m in self.memories.values()], f, ensure_ascii=False, indent=2)
        
        # 保存智能体状态
        states_file = os.path.join(self.shared_dir, "agent_states.json")
        with open(states_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in self.agent_states.values()], f, ensure_ascii=False, indent=2)
        
        # 保存访问规则
        rules_file = os.path.join(self.shared_dir, "access_rules.json")
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in self.access_rules], f, ensure_ascii=False, indent=2)
    
    def _index_memory(self, memory: MemoryEntry):
        """索引记忆"""
        # 按智能体索引
        if memory.source_agent not in self.agent_memory_index:
            self.agent_memory_index[memory.source_agent] = set()
        self.agent_memory_index[memory.source_agent].add(memory.id)
        
        # 按类型索引
        if memory.memory_type not in self.type_memory_index:
            self.type_memory_index[memory.memory_type] = set()
        self.type_memory_index[memory.memory_type].add(memory.id)
        
        # 按章节索引
        if memory.chapter_num > 0:
            if memory.chapter_num not in self.chapter_memory_index:
                self.chapter_memory_index[memory.chapter_num] = set()
            self.chapter_memory_index[memory.chapter_num].add(memory.id)
    
    # ==================== 记忆管理 ====================
    
    def add_memory(self, memory: MemoryEntry) -> str:
        """
        添加记忆
        
        Args:
            memory: 记忆条目
        
        Returns:
            记忆ID
        """
        with self._lock:
            self.memories[memory.id] = memory
            self._index_memory(memory)
            self._save_all()
            
            print(f"[共享记忆] 添加记忆: {memory.id} (来自 {memory.source_agent})")
            return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取记忆"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.accessed_at = datetime.now().isoformat()
            memory.access_count += 1
        return memory
    
    def search_memories(self, 
                       query: str = "",
                       source_agent: Optional[str] = None,
                       memory_type: Optional[str] = None,
                       chapter_num: Optional[int] = None,
                       limit: int = 10) -> List[MemoryEntry]:
        """
        搜索记忆
        
        Args:
            query: 搜索关键词
            source_agent: 来源智能体过滤
            memory_type: 记忆类型过滤
            chapter_num: 章节过滤
            limit: 返回数量限制
        
        Returns:
            匹配的记忆列表
        """
        results = []
        
        # 获取候选记忆ID
        candidate_ids = set(self.memories.keys())
        
        if source_agent:
            agent_ids = self.agent_memory_index.get(source_agent, set())
            candidate_ids = candidate_ids.intersection(agent_ids)
        
        if memory_type:
            type_ids = self.type_memory_index.get(memory_type, set())
            candidate_ids = candidate_ids.intersection(type_ids)
        
        if chapter_num and chapter_num > 0:
            chapter_ids = self.chapter_memory_index.get(chapter_num, set())
            candidate_ids = candidate_ids.intersection(chapter_ids)
        
        # 过滤和排序
        for memory_id in candidate_ids:
            memory = self.memories[memory_id]
            
            # 关键词匹配
            if query and query.lower() not in memory.content.lower():
                continue
            
            results.append(memory)
        
        # 按重要程度和时间排序
        results.sort(key=lambda m: (m.importance, m.created_at), reverse=True)
        
        return results[:limit]
    
    def get_agent_memories(self, agent_id: str, limit: int = 20) -> List[MemoryEntry]:
        """获取智能体的记忆"""
        memory_ids = self.agent_memory_index.get(agent_id, set())
        memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[:limit]
    
    def get_chapter_memories(self, chapter_num: int) -> List[MemoryEntry]:
        """获取章节相关的记忆"""
        memory_ids = self.chapter_memory_index.get(chapter_num, set())
        memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]
        memories.sort(key=lambda m: m.importance, reverse=True)
        return memories
    
    # ==================== 智能体状态管理 ====================
    
    def register_agent(self, agent_id: str, agent_role: str):
        """注册智能体"""
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = AgentState(
                agent_id=agent_id,
                agent_role=agent_role
            )
            self._save_all()
            print(f"[共享记忆] 注册智能体: {agent_id} ({agent_role})")
    
    def update_agent_state(self, agent_id: str, **kwargs):
        """更新智能体状态"""
        if agent_id in self.agent_states:
            state = self.agent_states[agent_id]
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            state.last_active = datetime.now().isoformat()
            self._save_all()
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """获取智能体状态"""
        return self.agent_states.get(agent_id)
    
    def get_all_agent_states(self) -> Dict[str, AgentState]:
        """获取所有智能体状态"""
        return self.agent_states.copy()
    
    # ==================== 知识传递 ====================
    
    def share_knowledge(self, 
                       source_agent: str, 
                       target_agents: List[str],
                       content: str,
                       knowledge_type: str = "fact",
                       importance: int = 5,
                       chapter_num: int = 0) -> str:
        """
        在智能体之间共享知识
        
        Args:
            source_agent: 来源智能体
            target_agents: 目标智能体列表
            content: 知识内容
            knowledge_type: 知识类型
            importance: 重要程度
            chapter_num: 相关章节
        
        Returns:
            记忆ID
        """
        import uuid
        memory_id = str(uuid.uuid4())[:8]
        
        memory = MemoryEntry(
            id=memory_id,
            source_agent=source_agent,
            memory_type=knowledge_type,
            content=content,
            related_agents=target_agents,
            chapter_num=chapter_num,
            importance=importance,
            metadata={
                "shared_from": source_agent,
                "shared_to": target_agents,
            }
        )
        
        return self.add_memory(memory)
    
    def get_shared_knowledge(self, agent_id: str) -> List[MemoryEntry]:
        """获取其他智能体分享给该智能体的知识"""
        results = []
        
        for memory in self.memories.values():
            if agent_id in memory.related_agents:
                results.append(memory)
        
        results.sort(key=lambda m: (m.importance, m.created_at), reverse=True)
        return results
    
    # ==================== 反馈机制 ====================
    
    def add_feedback(self,
                    source_agent: str,
                    target_agent: str,
                    feedback_type: str,
                    content: str,
                    chapter_num: int = 0) -> str:
        """
        添加反馈
        
        Args:
            source_agent: 来源智能体
            target_agent: 目标智能体
            feedback_type: 反馈类型（praise/critique/suggestion）
            content: 反馈内容
            chapter_num: 相关章节
        
        Returns:
            记忆ID
        """
        import uuid
        memory_id = str(uuid.uuid4())[:8]
        
        memory = MemoryEntry(
            id=memory_id,
            source_agent=source_agent,
            memory_type=MemoryType.FEEDBACK.value,
            content=content,
            related_agents=[target_agent],
            chapter_num=chapter_num,
            importance=7,
            metadata={
                "feedback_type": feedback_type,
                "target_agent": target_agent,
            }
        )
        
        return self.add_memory(memory)
    
    def get_feedback(self, agent_id: str) -> List[MemoryEntry]:
        """获取其他智能体对该智能体的反馈"""
        results = []
        
        for memory in self.memories.values():
            if (memory.memory_type == MemoryType.FEEDBACK.value and 
                memory.metadata.get("target_agent") == agent_id):
                results.append(memory)
        
        results.sort(key=lambda m: m.created_at, reverse=True)
        return results
    
    # ==================== 统计和分析 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total_memories": len(self.memories),
            "total_agents": len(self.agent_states),
            "by_type": {},
            "by_agent": {},
            "by_chapter": {},
        }
        
        # 按类型统计
        for memory in self.memories.values():
            memory_type = memory.memory_type
            stats["by_type"][memory_type] = stats["by_type"].get(memory_type, 0) + 1
        
        # 按智能体统计
        for agent_id, memory_ids in self.agent_memory_index.items():
            stats["by_agent"][agent_id] = len(memory_ids)
        
        # 按章节统计
        for chapter_num, memory_ids in self.chapter_memory_index.items():
            stats["by_chapter"][chapter_num] = len(memory_ids)
        
        return stats
    
    def generate_context_for_agent(self, agent_id: str, chapter_num: int = 0) -> str:
        """
        为智能体生成上下文信息
        
        Args:
            agent_id: 智能体ID
            chapter_num: 当前章节
        
        Returns:
            上下文字符串
        """
        context_parts = []
        
        # 1. 智能体自身的记忆
        agent_memories = self.get_agent_memories(agent_id, limit=5)
        if agent_memories:
            context_parts.append("【你的历史记忆】")
            for memory in agent_memories:
                context_parts.append(f"- {memory.content[:100]}...")
        
        # 2. 其他智能体分享的知识
        shared_knowledge = self.get_shared_knowledge(agent_id)
        if shared_knowledge:
            context_parts.append("\n【其他智能体分享的知识】")
            for memory in shared_knowledge[:5]:
                context_parts.append(f"- 来自{memory.source_agent}: {memory.content[:100]}...")
        
        # 3. 收到的反馈
        feedback = self.get_feedback(agent_id)
        if feedback:
            context_parts.append("\n【收到的反馈】")
            for memory in feedback[:3]:
                feedback_type = memory.metadata.get("feedback_type", "unknown")
                context_parts.append(f"- [{feedback_type}] {memory.content[:100]}...")
        
        # 4. 章节相关记忆
        if chapter_num > 0:
            chapter_memories = self.get_chapter_memories(chapter_num)
            if chapter_memories:
                context_parts.append(f"\n【第{chapter_num}章相关记忆】")
                for memory in chapter_memories[:5]:
                    context_parts.append(f"- {memory.content[:100]}...")
        
        return "\n".join(context_parts) if context_parts else "暂无相关记忆"
    
    # ==================== 访问权限控制 ====================
    
    def add_access_rule(self, agent_id: str, target_function_type: str,
                        target_project: str = "*", access_level: str = "read") -> bool:
        """
        添加访问规则
        
        Args:
            agent_id: 智能体ID
            target_function_type: 目标功能类型
            target_project: 目标项目（*表示所有项目）
            access_level: 访问级别（read/write/full）
        
        Returns:
            是否添加成功
        """
        # 检查是否已存在
        for rule in self.access_rules:
            if (rule.agent_id == agent_id and 
                rule.target_function_type == target_function_type and
                rule.target_project == target_project):
                # 更新规则
                rule.access_level = access_level
                rule.enabled = True
                self._save_all()
                return True
        
        # 创建新规则
        rule = AccessRule(
            agent_id=agent_id,
            target_function_type=target_function_type,
            target_project=target_project,
            access_level=access_level
        )
        
        self.access_rules.append(rule)
        self._save_all()
        
        print(f"[共享记忆] 添加访问规则: {agent_id} -> {target_function_type}/{target_project}")
        return True
    
    def remove_access_rule(self, agent_id: str, target_function_type: str,
                           target_project: str = "*") -> bool:
        """
        移除访问规则
        
        Args:
            agent_id: 智能体ID
            target_function_type: 目标功能类型
            target_project: 目标项目
        
        Returns:
            是否移除成功
        """
        for i, rule in enumerate(self.access_rules):
            if (rule.agent_id == agent_id and 
                rule.target_function_type == target_function_type and
                rule.target_project == target_project):
                self.access_rules.pop(i)
                self._save_all()
                return True
        
        return False
    
    def check_access(self, agent_id: str, target_function_type: str,
                     target_project: str, required_level: str = "read") -> bool:
        """
        检查访问权限
        
        Args:
            agent_id: 智能体ID
            target_function_type: 目标功能类型
            target_project: 目标项目
            required_level: 需要的访问级别
        
        Returns:
            是否有权限
        """
        # 查找匹配的规则
        for rule in self.access_rules:
            if (rule.agent_id == agent_id and 
                rule.target_function_type == target_function_type and
                (rule.target_project == "*" or rule.target_project == target_project)):
                
                if not rule.enabled:
                    return False
                
                # 检查访问级别
                level_hierarchy = {"read": 1, "write": 2, "full": 3}
                
                rule_level = level_hierarchy.get(rule.access_level, 0)
                required = level_hierarchy.get(required_level, 0)
                
                return rule_level >= required
        
        # 默认允许读取
        if required_level == "read":
            return True
        
        return False
    
    def get_access_rules(self, agent_id: Optional[str] = None) -> List[AccessRule]:
        """
        获取访问规则
        
        Args:
            agent_id: 智能体ID过滤
        
        Returns:
            访问规则列表
        """
        if agent_id:
            return [r for r in self.access_rules if r.agent_id == agent_id]
        return self.access_rules
    
    # ==================== 历史对话记录共享 ====================
    
    def share_history_record(self, source_agent: str, record_type: str,
                             project_name: str, title: str, content: str,
                             result: str, metadata: Dict[str, Any] = None) -> str:
        """
        共享历史对话记录
        
        Args:
            source_agent: 来源智能体
            record_type: 记录类型（history/knowledge/critique/generation）
            project_name: 项目名称
            title: 记录标题
            content: 输入内容
            result: 输出结果
            metadata: 元数据
        
        Returns:
            记忆ID
        """
        import uuid
        memory_id = str(uuid.uuid4())[:8]
        
        memory = MemoryEntry(
            id=memory_id,
            source_agent=source_agent,
            memory_type=record_type,
            content=content,
            metadata={
                "record_type": record_type,
                "project_name": project_name,
                "title": title,
                "result": result,
                **(metadata or {}),
            }
        )
        
        return self.add_memory(memory)
    
    def get_history_records(self, agent_id: str, record_type: Optional[str] = None,
                           project_name: Optional[str] = None,
                           limit: int = 50) -> List[MemoryEntry]:
        """
        获取历史对话记录（带权限检查）
        
        Args:
            agent_id: 查询智能体ID
            record_type: 记录类型过滤
            project_name: 项目名称过滤
            limit: 返回数量限制
        
        Returns:
            匹配的历史记录列表
        """
        results = []
        
        for memory in self.memories.values():
            # 检查是否是历史记录类型
            if memory.metadata.get("record_type") not in ["history", "knowledge", "critique", "generation"]:
                continue
            
            # 记录类型过滤
            if record_type and memory.metadata.get("record_type") != record_type:
                continue
            
            # 项目名称过滤
            if project_name and memory.metadata.get("project_name") != project_name:
                continue
            
            # 权限检查
            memory_function_type = memory.metadata.get("function_type", "")
            memory_project = memory.metadata.get("project_name", "")
            
            if not self.check_access(agent_id, memory_function_type, memory_project, "read"):
                continue
            
            results.append(memory)
        
        # 按时间排序
        results.sort(key=lambda m: m.created_at, reverse=True)
        
        return results[:limit]
    
    # ==================== 主动调用机制 ====================
    
    def call_agent(self, caller_id: str, target_id: str, 
                   action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用其他智能体
        
        Args:
            caller_id: 调用者ID
            target_id: 目标智能体ID
            action: 调用动作
            params: 参数
        
        Returns:
            调用结果
        """
        # 检查目标智能体是否存在
        target = self.agent_states.get(target_id)
        if not target:
            return {"error": f"目标智能体不存在: {target_id}"}
        
        # 检查目标智能体状态
        if target.status == "offline":
            return {"error": f"目标智能体离线: {target_id}"}
        
        # 检查调用权限
        target_role = target.agent_role
        if not self.check_access(caller_id, target_role, "*", "read"):
            return {"error": f"没有权限调用: {target_id}"}
        
        # 记录调用日志
        import uuid
        call_id = str(uuid.uuid4())[:8]
        
        call_memory = MemoryEntry(
            id=call_id,
            source_agent=caller_id,
            memory_type="context",
            content=f"调用 {target_id} 执行 {action}",
            metadata={
                "call_type": "agent_call",
                "target": target_id,
                "action": action,
                "params": params or {},
            }
        )
        
        self.add_memory(call_memory)
        
        # 返回调用信息（实际调用由具体智能体实现）
        return {
            "success": True,
            "call_id": call_id,
            "target": target_id,
            "action": action,
            "params": params or {},
        }


# 全局实例
_shared_memory: Optional[SharedMemory] = None


def get_shared_memory(project_dir: Optional[str] = None) -> SharedMemory:
    """获取共享记忆系统单例"""
    global _shared_memory
    if _shared_memory is None:
        if project_dir is None:
            project_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "projects", "default")
        _shared_memory = SharedMemory(project_dir)
    return _shared_memory
