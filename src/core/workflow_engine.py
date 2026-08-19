"""
工作流引擎
使用状态机管理多智能体协作
"""

import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    AGENT = "agent"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str
    name: str
    node_type: str
    agent: Optional[str] = None  # 智能体名称
    config: dict = field(default_factory=dict)
    
    # 连接
    next_nodes: list = field(default_factory=list)  # 下一个节点ID列表
    condition: Optional[str] = None  # 条件表达式
    
    # 状态
    status: str = NodeStatus.PENDING.value
    result: Optional[dict] = None
    error: Optional[str] = None
    
    # 时间
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return 0


@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_id: str
    current_node: Optional[str] = None
    
    # 数据
    data: dict = field(default_factory=dict)  # 共享数据
    
    # 状态
    status: str = "idle"  # idle/running/completed/failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    # 历史
    execution_history: list = field(default_factory=list)


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.nodes: dict[str, WorkflowNode] = {}
        self.state: Optional[WorkflowState] = None
        self.agents: dict[str, Callable] = {}  # 智能体注册表
        self.callbacks: list[Callable] = []
    
    def register_agent(self, name: str, agent_func: Callable):
        """注册智能体"""
        self.agents[name] = agent_func
    
    def add_node(self, node: WorkflowNode):
        """添加节点"""
        self.nodes[node.id] = node
    
    def connect(self, from_id: str, to_id: str, condition: str = None):
        """连接节点"""
        if from_id in self.nodes:
            self.nodes[from_id].next_nodes.append({
                "node_id": to_id,
                "condition": condition,
            })
    
    def create_novel_workflow(self):
        """创建小说生成工作流"""
        # 清空现有节点
        self.nodes.clear()
        
        # 创建节点
        nodes = [
            WorkflowNode("start", "开始", NodeType.START.value),
            WorkflowNode("outline", "生成大纲", NodeType.AGENT.value, agent="outline_agent"),
            WorkflowNode("outline_check", "大纲审核", NodeType.CONDITION.value),
            WorkflowNode("chapter_write", "撰写章节", NodeType.AGENT.value, agent="writer_agent"),
            WorkflowNode("chapter_review", "章节审核", NodeType.AGENT.value, agent="reviewer_agent"),
            WorkflowNode("review_check", "审核通过?", NodeType.CONDITION.value),
            WorkflowNode("polish", "错别字修正", NodeType.AGENT.value, agent="polisher_agent"),
            WorkflowNode("update_memory", "更新记忆", NodeType.AGENT.value, agent="memory_updater"),
            WorkflowNode("chapter_done", "章节完成", NodeType.END.value),
        ]
        
        for node in nodes:
            self.add_node(node)
        
        # 连接节点
        self.connect("start", "outline")
        self.connect("outline", "outline_check")
        self.connect("outline_check", "chapter_write", condition="passed")
        self.connect("outline_check", "outline", condition="failed")
        self.connect("chapter_write", "chapter_review")
        self.connect("chapter_review", "review_check")
        self.connect("review_check", "polish", condition="passed")
        self.connect("review_check", "chapter_write", condition="failed")
        self.connect("polish", "update_memory")
        self.connect("update_memory", "chapter_done")
    
    def create_critic_workflow(self):
        """创建批评工作流（对抗式审核）"""
        # 清空现有节点
        self.nodes.clear()
        
        # 创建节点
        nodes = [
            WorkflowNode("start", "开始", NodeType.START.value),
            WorkflowNode("input", "输入大纲/章节", NodeType.AGENT.value, agent="input_handler"),
            WorkflowNode("outline_critique", "大纲批评", NodeType.AGENT.value, agent="outline_critic"),
            WorkflowNode("chapter_critique", "章节批评", NodeType.AGENT.value, agent="chapter_critic"),
            WorkflowNode("knowledge_check", "知识库检查", NodeType.AGENT.value, agent="knowledge_checker"),
            WorkflowNode("generate_report", "生成报告", NodeType.AGENT.value, agent="report_generator"),
            WorkflowNode("critique_done", "批评完成", NodeType.END.value),
        ]
        
        for node in nodes:
            self.add_node(node)
        
        # 连接节点
        self.connect("start", "input")
        self.connect("input", "outline_critique")
        self.connect("input", "chapter_critique")
        self.connect("input", "knowledge_check")
        self.connect("outline_critique", "generate_report")
        self.connect("chapter_critique", "generate_report")
        self.connect("knowledge_check", "generate_report")
        self.connect("generate_report", "critique_done")
    
    def start(self, initial_data: dict = None):
        """启动工作流"""
        self.state = WorkflowState(
            workflow_id=f"wf_{int(time.time())}",
            data=initial_data or {},
            status="running",
            start_time=time.time(),
        )
        
        # 找到起始节点
        start_node = None
        for node in self.nodes.values():
            if node.node_type == NodeType.START.value:
                start_node = node
                break
        
        if start_node:
            self.state.current_node = start_node.id
            self._execute_node(start_node)
    
    def _execute_node(self, node: WorkflowNode):
        """执行节点"""
        node.status = NodeStatus.RUNNING.value
        node.start_time = time.time()
        
        self._notify("node_start", {"node_id": node.id, "name": node.name})
        
        try:
            if node.node_type == NodeType.START.value:
                self._execute_start(node)
            elif node.node_type == NodeType.END.value:
                self._execute_end(node)
            elif node.node_type == NodeType.AGENT.value:
                self._execute_agent(node)
            elif node.node_type == NodeType.CONDITION.value:
                self._execute_condition(node)
            else:
                self._complete_node(node)
                
        except Exception as e:
            node.status = NodeStatus.FAILED.value
            node.error = str(e)
            node.end_time = time.time()
            
            self._notify("node_error", {"node_id": node.id, "error": str(e)})
    
    def _execute_start(self, node: WorkflowNode):
        """执行开始节点"""
        self._complete_node(node)
    
    def _execute_end(self, node: WorkflowNode):
        """执行结束节点"""
        self._complete_node(node)
        self.state.status = "completed"
        self.state.end_time = time.time()
        self._notify("workflow_complete", {"duration": self.state.end_time - self.state.start_time})
    
    def _execute_agent(self, node: WorkflowNode):
        """执行智能体节点"""
        agent_name = node.agent
        if agent_name and agent_name in self.agents:
            agent_func = self.agents[agent_name]
            result = agent_func(self.state.data)
            node.result = result
            self._complete_node(node)
        else:
            # 模拟执行
            time.sleep(0.5)
            node.result = {"status": "simulated"}
            self._complete_node(node)
    
    def _execute_condition(self, node: WorkflowNode):
        """执行条件节点"""
        # 默认通过
        self._complete_node(node)
    
    def _complete_node(self, node: WorkflowNode):
        """完成节点"""
        node.status = NodeStatus.COMPLETED.value
        node.end_time = time.time()
        
        # 记录历史
        self.state.execution_history.append({
            "node_id": node.id,
            "name": node.name,
            "duration": node.duration,
            "result": node.result,
        })
        
        self._notify("node_complete", {"node_id": node.id, "duration": node.duration})
        
        # 执行下一个节点
        self._move_to_next(node)
    
    def _move_to_next(self, current_node: WorkflowNode):
        """移动到下一个节点"""
        if not current_node.next_nodes:
            return
        
        # 简单实现：取第一个无条件的下一个节点
        for next_info in current_node.next_nodes:
            next_id = next_info["node_id"]
            condition = next_info.get("condition")
            
            # 检查条件
            if condition:
                # 简化：条件通过
                pass
            
            if next_id in self.nodes:
                self.state.current_node = next_id
                self._execute_node(self.nodes[next_id])
                return
    
    def _notify(self, event: str, data: dict):
        """通知回调"""
        for callback in self.callbacks:
            try:
                callback(event, data)
            except Exception:
                pass
    
    def register_callback(self, callback: Callable):
        """注册回调"""
        self.callbacks.append(callback)
    
    def get_status(self) -> dict:
        """获取状态"""
        if not self.state:
            return {"status": "未启动"}
        
        return {
            "workflow_id": self.state.workflow_id,
            "status": self.state.status,
            "current_node": self.state.current_node,
            "progress": len(self.state.execution_history) / len(self.nodes) if self.nodes else 0,
            "history_count": len(self.state.execution_history),
        }


class LangGraphAdapter:
    """LangGraph适配器（简化版）"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
    
    def create_graph(self):
        """创建图"""
        self.engine.create_novel_workflow()
        return self.engine
    
    def invoke(self, input_data: dict) -> dict:
        """执行工作流"""
        self.engine.start(input_data)
        
        # 等待完成
        while self.engine.state and self.engine.state.status == "running":
            time.sleep(0.1)
        
        return self.engine.state.data if self.engine.state else {}


# 全局实例
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎单例"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine