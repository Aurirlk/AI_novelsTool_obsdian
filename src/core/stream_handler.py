"""
流式输出处理模块
支持LLM流式响应和实时UI更新
"""

import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StreamStatus(Enum):
    """流状态"""
    IDLE = "idle"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamChunk:
    """流数据块"""
    content: str
    chunk_type: str = "text"  # text/thinking/tool/error
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class StreamState:
    """流状态"""
    status: str = StreamStatus.IDLE.value
    chunks: list = field(default_factory=list)
    full_content: str = ""
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    # 统计
    total_chunks: int = 0
    total_tokens: int = 0
    
    @property
    def duration(self) -> float:
        """持续时间"""
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return 0
    
    @property
    def tokens_per_second(self) -> float:
        """每秒token数"""
        duration = self.duration
        if duration > 0:
            return self.total_tokens / duration
        return 0


class StreamHandler:
    """流式输出处理器"""
    
    def __init__(self):
        self.state = StreamState()
        self.callbacks: list[Callable] = []
        self._buffer = ""
    
    def start(self):
        """开始流式输出"""
        self.state = StreamState()
        self.state.status = StreamStatus.STREAMING.value
        self.state.start_time = time.time()
        self._buffer = ""
        
        self._notify_callbacks("start", {})
    
    def add_chunk(self, content: str, chunk_type: str = "text"):
        """添加数据块"""
        chunk = StreamChunk(
            content=content,
            chunk_type=chunk_type,
        )
        
        self.state.chunks.append(chunk)
        self.state.full_content += content
        self.state.total_chunks += 1
        self.state.total_tokens += len(content)  # 简化计算
        
        self._buffer += content
        
        # 通知回调
        self._notify_callbacks("chunk", {
            "content": content,
            "chunk_type": chunk_type,
            "full_content": self.state.full_content,
        })
    
    def complete(self):
        """完成流式输出"""
        self.state.status = StreamStatus.COMPLETED.value
        self.state.end_time = time.time()
        
        self._notify_callbacks("complete", {
            "full_content": self.state.full_content,
            "duration": self.state.duration,
            "total_chunks": self.state.total_chunks,
            "total_tokens": self.state.total_tokens,
            "tokens_per_second": self.state.tokens_per_second,
        })
    
    def error(self, error_msg: str):
        """错误"""
        self.state.status = StreamStatus.ERROR.value
        self.state.error = error_msg
        self.state.end_time = time.time()
        
        self._notify_callbacks("error", {"error": error_msg})
    
    def register_callback(self, callback: Callable):
        """注册回调函数"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, event: str, data: dict):
        """通知回调"""
        for callback in self.callbacks:
            try:
                callback(event, data)
            except Exception as e:
                print(f"[流处理] 回调错误: {e}")
    
    def get_progress(self) -> dict:
        """获取进度"""
        return {
            "status": self.state.status,
            "chunks": self.state.total_chunks,
            "tokens": self.state.total_tokens,
            "duration": self.state.duration,
            "speed": self.state.tokens_per_second,
        }


class StreamingWriter:
    """流式写作器"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.stream_handler = StreamHandler()
    
    def write_stream(self, prompt: str, system_prompt: str = "",
                     on_chunk: Callable = None) -> str:
        """
        流式写作
        
        Args:
            prompt: 写作提示
            system_prompt: 系统提示
            on_chunk: 数据块回调
        
        Returns:
            完整内容
        """
        if on_chunk:
            self.stream_handler.register_callback(on_chunk)
        
        self.stream_handler.start()
        
        try:
            if self.llm:
                # 使用真实LLM
                response = self._call_llm_stream(prompt, system_prompt)
            else:
                # 模拟流式输出
                response = self._simulate_stream(prompt)
            
            self.stream_handler.complete()
            return response
            
        except Exception as e:
            self.stream_handler.error(str(e))
            raise
    
    def _call_llm_stream(self, prompt: str, system_prompt: str) -> str:
        """调用LLM流式接口"""
        # 这里应该调用实际的LLM流式API
        # 示例：使用openai的stream参数
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        full_response = ""
        
        # 模拟流式调用
        response = self.llm.chat(prompt, system_prompt)
        
        # 模拟分块返回
        chunk_size = 10
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i+chunk_size]
            self.stream_handler.add_chunk(chunk, "text")
            full_response += chunk
            time.sleep(0.05)  # 模拟延迟
        
        return full_response
    
    def _simulate_stream(self, prompt: str) -> str:
        """模拟流式输出"""
        # 模拟AI生成内容
        simulated_response = f"""
第一章 初入修仙界

青云镇，一个偏僻的小镇，位于东荒大陆的边缘。

清晨的阳光洒在青石板路上，一个少年正蹲在路边，手中拿着一本破旧的书籍，眉头紧锁。

"灵气感应术，第三层……"少年喃喃自语，"为什么我总是无法突破？"

这个少年名叫林云，是青云镇林家的庶子。在这个修仙为尊的世界里，他却是一个公认的废物——十六岁了，连灵气感应术的第一层都没有突破。

"林云！又在这里偷懒！"一个尖锐的声音传来。

林云抬头，看到一个身穿锦衣的少年正朝他走来，身后跟着两个家丁。

"林浩。"林云淡淡地叫了一声，继续看书。

林浩是林家嫡子，天赋异禀，十二岁就突破了灵气感应术第三层，被誉为林家百年难遇的天才。

"废物就是废物，"林浩冷笑，"三个月后的家族考核，你要是还突破不了第一层，就给我滚出林家！"

林云没有说话，只是握紧了手中的书。

他知道，三个月后的家族考核，是他唯一的机会……
"""
        
        # 模拟分块返回
        chunk_size = 20
        for i in range(0, len(simulated_response), chunk_size):
            chunk = simulated_response[i:i+chunk_size]
            self.stream_handler.add_chunk(chunk, "text")
            time.sleep(0.1)  # 模拟延迟
        
        return simulated_response


class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self):
        self.steps = []
        self.current_step = -1
    
    def add_step(self, name: str, description: str = ""):
        """添加步骤"""
        self.steps.append({
            "name": name,
            "description": description,
            "status": "pending",
            "start_time": None,
            "end_time": None,
        })
    
    def start_step(self, name: str):
        """开始步骤"""
        for i, step in enumerate(self.steps):
            if step["name"] == name:
                step["status"] = "running"
                step["start_time"] = time.time()
                self.current_step = i
                break
    
    def complete_step(self, name: str):
        """完成步骤"""
        for step in self.steps:
            if step["name"] == name:
                step["status"] = "completed"
                step["end_time"] = time.time()
                break
    
    def fail_step(self, name: str, error: str = ""):
        """步骤失败"""
        for step in self.steps:
            if step["name"] == name:
                step["status"] = "failed"
                step["end_time"] = time.time()
                step["error"] = error
                break
    
    def get_progress(self) -> dict:
        """获取进度"""
        completed = sum(1 for s in self.steps if s["status"] == "completed")
        total = len(self.steps)
        
        return {
            "current_step": self.current_step,
            "total_steps": total,
            "completed": completed,
            "progress": completed / total if total > 0 else 0,
            "steps": self.steps,
        }