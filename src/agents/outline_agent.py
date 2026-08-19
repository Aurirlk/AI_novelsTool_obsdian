"""
大纲师智能体
负责生成故事大纲和章节细纲
"""

from typing import Optional
from src.agents.base import BaseAgent
from src.models.schemas import NovelState, StoryBible, Character, CharacterRole


class OutlineAgent(BaseAgent):
    """大纲师智能体 - 负责故事规划"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("大纲师", llm_provider)
    
    def execute(self, state: NovelState, idea: str = "", **kwargs) -> dict:
        """
        生成故事大纲
        
        Args:
            state: 小说状态
            idea: 用户的一句话创意
        
        Returns:
            更新后的状态
        """
        self._log(f"开始生成大纲，创意: {idea[:50]}...")
        
        # 构建Prompt
        prompt = self._build_outline_prompt(idea)
        
        # 调用LLM
        response = self.llm.chat(prompt, system_prompt=self._get_system_prompt())
        
        # 解析响应
        story_bible = self._parse_outline(response, idea)
        
        # 更新状态
        state.story_bible = story_bible
        
        self._log(f"大纲生成完成: {story_bible.title}")
        
        return {"state": state, "story_bible": story_bible}
    
    def generate_chapter_outline(self, state: NovelState, chapter_num: int) -> dict:
        """
        生成章节细纲
        
        Args:
            state: 小说状态
            chapter_num: 章节号
        
        Returns:
            章节细纲
        """
        self._log(f"生成第{chapter_num}章细纲...")
        
        context = self._build_context(state)
        
        prompt = f"""
{context}

请为第{chapter_num}章生成详细细纲，包括：
1. 章节标题
2. 核心事件
3. 出场角色
4. 场景描述
5. 情节推进点
6. 是否埋下新钩子或回收旧钩子

请用JSON格式输出。
"""
        
        response = self.llm.chat(prompt, system_prompt=self._get_system_prompt())
        
        # 保存到story_bible
        if state.story_bible:
            state.story_bible.chapter_outlines[chapter_num] = response
        
        self._log(f"第{chapter_num}章细纲生成完成")
        
        return {"chapter_num": chapter_num, "outline": response}
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位专业的小说大纲师，擅长：
1. 设计引人入胜的故事结构
2. 创造有深度的角色
3. 构建完整的世界观
4. 规划合理的剧情节奏

你的任务是根据用户的一句话创意，生成完整的故事大纲。

要求：
- 黄金三章原则：前三章必须吸引读者
- 人物弧光：主角必须有成长
- 冲突设计：每个章节都要有冲突
- 钩子设置：每3-5章设置一个悬念

输出格式：使用JSON格式"""
    
    def _build_outline_prompt(self, idea: str) -> str:
        """构建大纲生成Prompt"""
        return f"""
请根据以下创意生成一个完整的小说大纲：

创意：{idea}

请生成以下内容：
1. 小说标题
2. 题材类型（如：玄幻、都市、科幻等）
3. 主题思想
4. 世界观设定（500字以内）
5. 力量体系（300字以内）
6. 主要角色（3-5个，包含名字、性格、背景）
7. 主线剧情大纲（20章，每章一句话概括）
8. 核心悬念和钩子

请用JSON格式输出。
"""
    
    def _parse_outline(self, response: str, idea: str) -> StoryBible:
        """解析LLM响应为StoryBible"""
        # 简化处理，实际应该解析JSON
        # 这里创建一个默认的StoryBible
        
        story_bible = StoryBible(
            title="AI生成的小说",
            genre="玄幻",
            theme="成长与冒险",
            worldview="一个充满灵气的修仙世界...",
            power_system="炼气、筑基、金丹、元婴、化神...",
            plot_outline=response[:500] if response else "",
        )
        
        # 创建默认主角
        protagonist = Character(
            id="char_001",
            name="林云",
            role=CharacterRole.PROTAGONIST,
            personality="坚韧不拔，聪明机智",
            background="普通少年，偶得机缘",
            current_location="青云镇",
        )
        
        story_bible.main_characters.append(protagonist.id)
        
        return story_bible