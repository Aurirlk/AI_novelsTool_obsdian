"""
码字工智能体
负责根据大纲撰写章节内容
"""

from typing import Optional
from src.agents.base import BaseAgent
from src.models.schemas import NovelState, Chapter, ChapterStatus


class WriterAgent(BaseAgent):
    """码字工智能体 - 负责章节写作"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("码字工", llm_provider)
    
    def execute(self, state: NovelState, chapter_num: int = 0, **kwargs) -> dict:
        """
        撰写章节
        
        Args:
            state: 小说状态
            chapter_num: 章节号
        
        Returns:
            更新后的状态
        """
        if chapter_num == 0:
            chapter_num = state.current_chapter + 1
        
        self._log(f"开始撰写第{chapter_num}章...")
        
        # 获取章节细纲
        outline = ""
        if state.story_bible and chapter_num in state.story_bible.chapter_outlines:
            outline = state.story_bible.chapter_outlines[chapter_num]
        
        # 构建上下文
        context = self._build_context(state)

        # RAG 检索增强：正则+关键字混合检索本地数据，注入相关角色/事件/悬念
        rag_context = self._get_rag_context(state, chapter_num)
        if rag_context:
            context = f"{context}\n\n【相关设定检索】\n{rag_context}"

        # 构建写作Prompt
        prompt = self._build_writing_prompt(context, outline, chapter_num)
        
        # 调用LLM生成内容
        content = self.llm.chat(prompt, system_prompt=self._get_system_prompt())
        
        # 生成章节标题
        title = self._generate_title(content, chapter_num)
        
        # 创建章节对象
        chapter = Chapter(
            number=chapter_num,
            title=title,
            content=content,
            status=ChapterStatus.DRAFT,
            summary=self._generate_summary(content),
            word_count=len(content),
        )
        
        # 更新状态
        state.chapters.append(chapter)
        state.current_chapter = chapter_num
        state.total_words += chapter.word_count
        
        self._log(f"第{chapter_num}章撰写完成: {title} ({chapter.word_count}字)")
        
        return {"state": state, "chapter": chapter}
    
    def _get_rag_context(self, state: NovelState, chapter_num: int) -> str:
        """RAG 检索增强：正则+关键字混合检索本地数据（角色/事件/钩子/章节）

        - 规则切分关键词 → 正则匹配本地语料（离线可用）
        - 零命中或多命中时 LLM 提取关键词补搜（并集）
        - ChromaDB 不可用时静默降级（返回空串）
        """
        try:
            from src.core.vector_store import get_rag_system
            chapter_info = {"outline": ""}
            # 当前章细纲作为检索 query
            if state.story_bible and chapter_num in state.story_bible.chapter_outlines:
                chapter_info["outline"] = state.story_bible.chapter_outlines[chapter_num]
            # 最近章节摘要作为补充 query
            if not chapter_info["outline"] and state.chapters:
                chapter_info["outline"] = state.chapters[-1].summary[:100]
            return get_rag_system().generate_writing_context(chapter_info)
        except Exception:
            return ""

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位专业的网文作者，擅长：
1. 生动的场景描写
2. 流畅的对话设计
3. 紧凑的剧情节奏
4. 细腻的情感刻画

写作要求：
- 严格按照细纲写作
- 保持人物性格一致
- 每章2000字左右
- 章末留有悬念或钩子
- 避免大段心理描写
- 多用动作和对话推进剧情

风格要求：
- 简洁明快
- 画面感强
- 节奏紧凑
- 爽点明确"""
    
    def _build_writing_prompt(self, context: str, outline: str, chapter_num: int) -> str:
        """构建写作Prompt"""
        return f"""
{context}

【章节细纲】
{outline if outline else "无细纲，请根据上下文自行发挥"}

请撰写第{chapter_num}章的内容，要求：
1. 字数：2000字左右
2. 风格：简洁明快，画面感强
3. 结构：开头承接上章，中间推进剧情，结尾留悬念
4. 注意：保持人物性格一致，符合世界观设定

请直接输出章节内容，不要包含标题。
"""
    
    def _generate_title(self, content: str, chapter_num: int) -> str:
        """生成章节标题"""
        # 简化处理，从内容中提取或生成默认标题
        first_line = content.split("\n")[0][:20] if content else ""
        if first_line:
            return f"第{chapter_num}章 {first_line}"
        return f"第{chapter_num}章"
    
    def _generate_summary(self, content: str) -> str:
        """生成章节摘要"""
        # 取前200字作为摘要
        return content[:200] + "..." if len(content) > 200 else content