"""
智能体基类
定义所有智能体的通用接口
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.models.schemas import NovelState


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, llm_provider: Optional[str] = None):
        """
        初始化智能体
        
        Args:
            name: 智能体名称
            llm_provider: LLM提供商
        """
        self.name = name
        self.llm_provider = llm_provider
        self._llm_client = None
    
    @property
    def llm(self):
        """懒加载LLM客户端"""
        if self._llm_client is None:
            from src.utils.llm import get_llm_client
            self._llm_client = get_llm_client(self.llm_provider)
        return self._llm_client
    
    @abstractmethod
    def execute(self, state: NovelState, **kwargs) -> dict:
        """
        执行智能体任务
        
        Args:
            state: 小说状态
            **kwargs: 额外参数
        
        Returns:
            更新后的状态或结果
        """
        pass
    
    def _build_context(self, state: NovelState, max_chapters: int = 3) -> str:
        """
        构建上下文信息
        
        Args:
            state: 小说状态
            max_chapters: 最近章节数量
        
        Returns:
            上下文字符串
        """
        context_parts = []
        
        # 故事设定
        if state.story_bible:
            bible = state.story_bible
            context_parts.append(f"""
【故事设定】
标题: {bible.title}
题材: {bible.genre}
主题: {bible.theme}
世界观: {bible.worldview[:500]}...
力量体系: {bible.power_system[:300]}...
""")
        
        # 主要角色
        if state.characters:
            context_parts.append("【主要角色】")
            for char in list(state.characters.values())[:5]:  # 最多5个角色
                context_parts.append(f"- {char.name}({char.role.value}): {char.personality}")
        
        # 最近章节摘要
        if state.chapters:
            recent = state.chapters[-max_chapters:]
            context_parts.append(f"\n【最近{len(recent)}章摘要】")
            for ch in recent:
                context_parts.append(f"第{ch.number}章 {ch.title}: {ch.summary[:100]}...")
        
        # 未回收钩子
        active_hooks = state.get_active_hooks()
        if active_hooks:
            context_parts.append("\n【未回收的悬念】")
            for hook in active_hooks[:5]:  # 最多5个
                context_parts.append(f"- {hook.content}")
        
        return "\n".join(context_parts)
    
    def _log(self, message: str):
        """日志输出"""
        print(f"[{self.name}] {message}")