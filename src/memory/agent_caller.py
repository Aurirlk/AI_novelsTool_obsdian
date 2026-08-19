"""
智能体调用机制
实现智能体之间的相互调用和协作
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
from queue import Queue


class CallStatus(Enum):
    """调用状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentCall:
    """智能体调用记录"""
    call_id: str
    caller_id: str              # 调用者
    callee_id: str              # 被调用者
    method: str                 # 调用方法
    params: Dict[str, Any]      # 参数
    
    status: str = CallStatus.PENDING.value
    result: Any = None
    error: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    completed_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentCapability:
    """智能体能力描述"""
    agent_id: str
    agent_role: str
    description: str
    
    # 可调用的方法
    methods: List[Dict[str, Any]] = field(default_factory=list)
    
    # 依赖的其他智能体
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AgentCaller:
    """智能体调用器"""
    
    def __init__(self):
        # 智能体注册表
        self.agents: Dict[str, Any] = {}  # agent_id -> agent实例
        self.capabilities: Dict[str, AgentCapability] = {}  # agent_id -> capability
        
        # 调用历史
        self.call_history: List[AgentCall] = []
        
        # 调用队列
        self.call_queue: Queue = Queue()
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 回调函数
        self.before_call_callbacks: List[Callable] = []
        self.after_call_callbacks: List[Callable] = []
        
        print("[智能体调用器] 初始化完成")
    
    # ==================== 注册管理 ====================
    
    def register_agent(self, agent_id: str, agent_instance: Any, 
                      agent_role: str, description: str,
                      methods: List[Dict[str, Any]] = None,
                      dependencies: List[str] = None):
        """
        注册智能体
        
        Args:
            agent_id: 智能体ID
            agent_instance: 智能体实例
            agent_role: 智能体角色
            description: 描述
            methods: 可调用的方法列表
            dependencies: 依赖的其他智能体
        """
        self.agents[agent_id] = agent_instance
        
        capability = AgentCapability(
            agent_id=agent_id,
            agent_role=agent_role,
            description=description,
            methods=methods or [],
            dependencies=dependencies or []
        )
        self.capabilities[agent_id] = capability
        
        print(f"[智能体调用器] 注册智能体: {agent_id} ({agent_role})")
    
    def unregister_agent(self, agent_id: str):
        """注销智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
        if agent_id in self.capabilities:
            del self.capabilities[agent_id]
        print(f"[智能体调用器] 注销智能体: {agent_id}")
    
    # ==================== 调用管理 ====================
    
    def call_agent(self, caller_id: str, callee_id: str, 
                  method: str, params: Dict[str, Any] = None,
                  timeout: int = 60) -> AgentCall:
        """
        调用其他智能体
        
        Args:
            caller_id: 调用者ID
            callee_id: 被调用者ID
            method: 调用方法
            params: 参数
            timeout: 超时时间（秒）
        
        Returns:
            调用记录
        """
        import uuid
        call_id = str(uuid.uuid4())[:8]
        
        # 创建调用记录
        call = AgentCall(
            call_id=call_id,
            caller_id=caller_id,
            callee_id=callee_id,
            method=method,
            params=params or {}
        )
        
        # 检查被调用者是否存在
        if callee_id not in self.agents:
            call.status = CallStatus.FAILED.value
            call.error = f"智能体 {callee_id} 不存在"
            self.call_history.append(call)
            return call
        
        # 检查方法是否可用
        capability = self.capabilities.get(callee_id)
        if capability:
            available_methods = [m.get("name") for m in capability.methods]
            if method not in available_methods:
                call.status = CallStatus.FAILED.value
                call.error = f"方法 {method} 不可用，可用方法: {available_methods}"
                self.call_history.append(call)
                return call
        
        # 执行调用
        call.status = CallStatus.RUNNING.value
        call.started_at = datetime.now().isoformat()
        
        # 触发回调
        for callback in self.before_call_callbacks:
            try:
                callback(call)
            except Exception:
                pass
        
        try:
            # 获取智能体实例
            agent = self.agents[callee_id]
            
            # 获取方法
            if hasattr(agent, method):
                func = getattr(agent, method)
                
                # 执行调用
                if params:
                    result = func(**params)
                else:
                    result = func()
                
                call.result = result
                call.status = CallStatus.COMPLETED.value
            else:
                call.status = CallStatus.FAILED.value
                call.error = f"智能体 {callee_id} 没有方法 {method}"
        
        except Exception as e:
            call.status = CallStatus.FAILED.value
            call.error = str(e)
        
        call.completed_at = datetime.now().isoformat()
        
        # 触发回调
        for callback in self.after_call_callbacks:
            try:
                callback(call)
            except Exception:
                pass
        
        # 保存调用历史
        with self._lock:
            self.call_history.append(call)
        
        print(f"[智能体调用器] 调用完成: {caller_id} -> {callee_id}.{method} ({call.status})")
        
        return call
    
    def call_agent_async(self, caller_id: str, callee_id: str,
                        method: str, params: Dict[str, Any] = None,
                        callback: Callable = None) -> str:
        """
        异步调用其他智能体
        
        Args:
            caller_id: 调用者ID
            callee_id: 被调用者ID
            method: 调用方法
            params: 参数
            callback: 完成回调
        
        Returns:
            调用ID
        """
        import uuid
        call_id = str(uuid.uuid4())[:8]
        
        # 创建调用记录
        call = AgentCall(
            call_id=call_id,
            caller_id=caller_id,
            callee_id=callee_id,
            method=method,
            params=params or {}
        )
        
        # 添加到队列
        self.call_queue.put((call, callback))
        
        print(f"[智能体调用器] 异步调用已加入队列: {caller_id} -> {callee_id}.{method}")
        
        return call_id
    
    def process_queue(self):
        """处理调用队列"""
        while not self.call_queue.empty():
            call, callback = self.call_queue.get()
            
            # 执行调用
            result_call = self.call_agent(
                call.caller_id,
                call.callee_id,
                call.method,
                call.params
            )
            
            # 执行回调
            if callback:
                try:
                    callback(result_call)
                except Exception as e:
                    print(f"[智能体调用器] 回调执行失败: {e}")
    
    # ==================== 批量调用 ====================
    
    def call_multiple(self, caller_id: str, 
                     calls: List[Dict[str, Any]]) -> List[AgentCall]:
        """
        批量调用多个智能体
        
        Args:
            caller_id: 调用者ID
            calls: 调用列表 [{"callee_id": "...", "method": "...", "params": {...}}]
        
        Returns:
            调用结果列表
        """
        results = []
        
        for call_info in calls:
            result = self.call_agent(
                caller_id=caller_id,
                callee_id=call_info["callee_id"],
                method=call_info["method"],
                params=call_info.get("params")
            )
            results.append(result)
        
        return results
    
    def call_pipeline(self, caller_id: str, 
                     pipeline: List[Dict[str, Any]]) -> Any:
        """
        流水线调用（前一个的结果作为后一个的输入）
        
        Args:
            caller_id: 调用者ID
            pipeline: 流水线定义
        
        Returns:
            最终结果
        """
        current_result = None
        
        for step in pipeline:
            params = step.get("params", {})
            
            # 如果有前一步的结果，添加到参数中
            if current_result is not None:
                params["input"] = current_result
            
            result = self.call_agent(
                caller_id=caller_id,
                callee_id=step["callee_id"],
                method=step["method"],
                params=params
            )
            
            if result.status == CallStatus.FAILED.value:
                return result
            
            current_result = result.result
        
        return current_result
    
    # ==================== 查询功能 ====================
    
    def get_call_history(self, caller_id: str = None, 
                        callee_id: str = None,
                        limit: int = 50) -> List[AgentCall]:
        """获取调用历史"""
        history = self.call_history
        
        if caller_id:
            history = [c for c in history if c.caller_id == caller_id]
        
        if callee_id:
            history = [c for c in history if c.callee_id == callee_id]
        
        # 按时间倒序
        history.sort(key=lambda c: c.created_at, reverse=True)
        
        return history[:limit]
    
    def get_available_methods(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取智能体可用的方法"""
        capability = self.capabilities.get(agent_id)
        if capability:
            return capability.methods
        return []
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """获取所有注册的智能体"""
        agents = []
        
        for agent_id, capability in self.capabilities.items():
            agents.append({
                "agent_id": agent_id,
                "agent_role": capability.agent_role,
                "description": capability.description,
                "methods": capability.methods,
                "dependencies": capability.dependencies,
            })
        
        return agents
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total_agents": len(self.agents),
            "total_calls": len(self.call_history),
            "by_status": {},
            "by_caller": {},
            "by_callee": {},
        }
        
        for call in self.call_history:
            # 按状态统计
            stats["by_status"][call.status] = stats["by_status"].get(call.status, 0) + 1
            
            # 按调用者统计
            stats["by_caller"][call.caller_id] = stats["by_caller"].get(call.caller_id, 0) + 1
            
            # 按被调用者统计
            stats["by_callee"][call.callee_id] = stats["by_callee"].get(call.callee_id, 0) + 1
        
        return stats
    
    # ==================== 回调管理 ====================
    
    def register_before_call_callback(self, callback: Callable):
        """注册调用前回调"""
        self.before_call_callbacks.append(callback)
    
    def register_after_call_callback(self, callback: Callable):
        """注册调用后回调"""
        self.after_call_callbacks.append(callback)


# 全局实例
_agent_caller: Optional[AgentCaller] = None


def get_agent_caller() -> AgentCaller:
    """获取智能体调用器单例"""
    global _agent_caller
    if _agent_caller is None:
        _agent_caller = AgentCaller()
    return _agent_caller
