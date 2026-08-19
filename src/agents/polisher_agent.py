"""
运营智能体
负责错别字修正、标题生成和预告
"""

from typing import Optional
from src.agents.base import BaseAgent
from src.models.schemas import NovelState, Chapter, ChapterStatus


class PolisherAgent(BaseAgent):
    """运营智能体 - 负责错别字修正和包装"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("运营", llm_provider)
    
    def execute(self, state: NovelState, chapter_num: int = 0, **kwargs) -> dict:
        """
        错别字修正 + 包装章节
        
        Args:
            state: 小说状态
            chapter_num: 章节号
        
        Returns:
            更新后的状态
        """
        if chapter_num == 0:
            chapter_num = state.current_chapter
        
        if chapter_num > len(state.chapters):
            return {"error": f"第{chapter_num}章不存在"}
        
        chapter = state.chapters[chapter_num - 1]
        
        self._log(f"开始错别字修正第{chapter_num}章: {chapter.title}")
        
        # 1. 优化标题
        new_title = self._optimize_title(chapter)
        
        # 2. 生成章末预告
        preview = self._generate_preview(state, chapter)
        
        # 3. 错别字修正（可选）
        fixed_content = self._fix_typos(chapter)
        
        # 更新章节
        chapter.title = new_title
        if fixed_content:
            chapter.content = fixed_content
        chapter.status = ChapterStatus.POLISHED
        
        # 添加预告到内容末尾
        if preview:
            chapter.content += f"\n\n【下章预告】{preview}"
        
        self._log(f"第{chapter_num}章错别字修正完成: {new_title}")
        
        return {
            "state": state,
            "chapter": chapter,
            "preview": preview,
        }
    
    def _optimize_title(self, chapter: Chapter) -> str:
        """优化章节标题"""
        # 简化处理，不调用LLM
        current_title = chapter.title
        
        # 如果标题已经是"第X章"格式，保持不变
        if current_title.startswith(f"第{chapter.number}章"):
            return current_title
        
        # 否则生成新标题
        return f"第{chapter.number}章 {current_title}"
    
    def _generate_preview(self, state: NovelState, chapter: Chapter) -> str:
        """生成下章预告"""
        # 简化处理
        next_chapter = chapter.number + 1
        
        # 检查是否有下章大纲
        if state.story_bible and next_chapter in state.story_bible.chapter_outlines:
            outline = state.story_bible.chapter_outlines[next_chapter]
            # 从大纲中提取预告
            return f"第{next_chapter}章即将到来..."
        
        return ""
    
    def _fix_typos(self, chapter: Chapter) -> str:
        """错别字修正（真实调用LLM）——只改错别字和笔误，严禁润色"""
        if not chapter.content:
            return ""
        
        prompt = f"""
请检查以下网文章节的错别字和笔误：
1. 错别字、形近字误用（如「戴着/带着」「拼劲全力/拼尽全力」）
2. 人名、地名前后不一致（同一角色写法不同）
3. 明显的字词笔误
4. 只允许修正错别字和笔误，严禁润色、改写、扩写、优化任何句子表达

【原文】
{chapter.content[:2500]}...

请直接输出修正后的完整正文，只改错别字处，其余文字逐字保留，不要解释。
"""
        try:
            return self.llm.chat(prompt, system_prompt="你是严谨的文字校对员，只改错别字和笔误，禁止任何润色和改写，保持原文逐字不变。")
        except Exception as e:
            self._log(f"LLM错别字修正失败: {e}")
            return ""
    
    def generate_hook_title(self, content: str) -> str:
        """生成吸引眼球的标题"""
        prompt = f"""
根据以下章节内容，生成一个吸引眼球的标题：

{content[:500]}...

要求：
1. 10字以内
2. 有悬念感
3. 能吸引读者点击

请直接输出标题。
"""
        try:
            return self.llm.chat(prompt)
        except Exception:
            return "精彩章节"
    
    def generate_chapter_summary(self, chapter: Chapter) -> str:
        """生成章节摘要（用于推荐）"""
        prompt = f"""
请为以下章节生成一段50字以内的摘要：

标题：{chapter.title}
内容：{chapter.content[:500]}...

要求：
1. 50字以内
2. 突出亮点
3. 吸引读者

请直接输出摘要。
"""
        try:
            return self.llm.chat(prompt)
        except Exception:
            return chapter.content[:50] + "..."