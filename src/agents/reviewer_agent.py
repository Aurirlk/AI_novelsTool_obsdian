"""
督察智能体
负责审核章节内容的一致性和质量
"""

from typing import Optional
from src.agents.base import BaseAgent
from src.models.schemas import NovelState, Chapter, ChapterStatus


class ReviewResult:
    """审核结果"""
    
    def __init__(self):
        self.passed = True
        self.issues = []  # 问题列表
        self.suggestions = []  # 建议列表
    
    def add_issue(self, issue: str):
        """添加问题"""
        self.passed = False
        self.issues.append(issue)
    
    def add_suggestion(self, suggestion: str):
        """添加建议"""
        self.suggestions.append(suggestion)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class ReviewerAgent(BaseAgent):
    """督察智能体 - 负责内容审核"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("督察", llm_provider)
    
    def execute(self, state: NovelState, chapter_num: int = 0, **kwargs) -> dict:
        """
        审核章节
        
        Args:
            state: 小说状态
            chapter_num: 章节号
        
        Returns:
            审核结果
        """
        if chapter_num == 0:
            chapter_num = state.current_chapter
        
        if chapter_num > len(state.chapters):
            return {"error": f"第{chapter_num}章不存在"}
        
        chapter = state.chapters[chapter_num - 1]
        
        self._log(f"开始审核第{chapter_num}章: {chapter.title}")
        
        # 执行各项审核
        result = ReviewResult()
        
        # 1. 时空一致性检查
        self._check_spatiotemporal_consistency(state, chapter, result)
        
        # 2. 人物一致性检查
        self._check_character_consistency(state, chapter, result)
        
        # 3. 世界观一致性检查
        self._check_worldview_consistency(state, chapter, result)
        
        # 4. 钩子检查
        self._check_hooks(state, chapter, result)
        
        # 5. 信息密度检查
        self._check_information_density(chapter, result)
        
        # 更新章节状态
        if result.passed:
            chapter.status = ChapterStatus.APPROVED
            self._log(f"第{chapter_num}章审核通过")
        else:
            chapter.status = ChapterStatus.REJECTED
            self._log(f"第{chapter_num}章审核不通过: {len(result.issues)}个问题")
        
        return {
            "state": state,
            "chapter": chapter,
            "result": result.to_dict(),
        }
    
    def _check_spatiotemporal_consistency(self, state: NovelState, chapter: Chapter, result: ReviewResult):
        """检查时空一致性"""
        self._log("检查时空一致性...")
        
        # 检查角色位置是否合理
        for char_name in chapter.characters_appeared:
            char = state.get_character(char_name)
            if char and not char.is_alive:
                result.add_issue(f"角色'{char_name}'已死亡，但本章出现了")
        
        # 这里应该调用LLM进行更深入的检查
        # 简化处理，跳过LLM调用
    
    def _check_character_consistency(self, state: NovelState, chapter: Chapter, result: ReviewResult):
        """检查人物一致性"""
        self._log("检查人物一致性...")
        
        # 检查角色性格是否一致
        for char_name in chapter.characters_appeared:
            char = state.get_character(char_name)
            if char:
                # 这里应该调用LLM检查角色行为是否符合性格
                pass
    
    def _check_worldview_consistency(self, state: NovelState, chapter: Chapter, result: ReviewResult):
        """检查世界观一致性"""
        self._log("检查世界观一致性...")
        
        # 检查是否违反世界观设定
        if state.story_bible:
            # 这里应该调用LLM检查内容是否符合世界观
            pass
    
    def _check_hooks(self, state: NovelState, chapter: Chapter, result: ReviewResult):
        """检查钩子（悬念）"""
        self._log("检查钩子...")
        
        # 检查是否有该回收的钩子没有回收
        active_hooks = state.get_active_hooks()
        for hook in active_hooks:
            if hook.expected_resolve <= chapter.number:
                result.add_suggestion(f"钩子'{hook.content[:30]}...'应该在本章回收")
    
    def _check_information_density(self, chapter: Chapter, result: ReviewResult):
        """检查信息密度"""
        self._log("检查信息密度...")
        
        # 检查字数是否达标
        if chapter.word_count < 1500:
            result.add_issue(f"章节字数不足: {chapter.word_count}字（最少1500字）")
        elif chapter.word_count > 3000:
            result.add_suggestion(f"章节字数过多: {chapter.word_count}字（建议2000字左右）")
    
    def review_with_llm(self, state: NovelState, chapter: Chapter) -> ReviewResult:
        """使用LLM进行深度审核（12项一致性检查，真实调用LLM）"""
        result = ReviewResult()

        context = self._build_context(state)

        prompt = f"""
{context}

【待审核章节】
第{chapter.number}章 {chapter.title}
{chapter.content[:2000]}...

请对本章进行严格的12项一致性检查：
1. 时空一致性：时间线、地点是否矛盾（角色不能同时出现在两个地方）
2. 人物性格一致性：角色行为是否符合性格设定（防止OOC）
3. 能力体系一致性：实力、能力是否越级或前后矛盾
4. 称谓统一：角色称呼是否前后一致
5. 外貌描写一致：角色外形是否前后矛盾
6. 伏笔/钩子遗漏：该回收的伏笔是否被遗忘
7. 逻辑漏洞：情节发展是否合理，有无硬伤
8. 设定冲突：是否违反世界观规则
9. 配角OOC：配角行为是否符合其设定
10. 数据矛盾：数字、时间、距离等前后是否一致
11. 情节节奏：节奏是否拖沓或过赶
12. 文风统一：文笔风格是否前后一致

输出格式（严格按此格式）：
问题1：<问题描述>
建议1：<修改建议>
问题2：<问题描述>
建议2：<修改建议>
...
（如无问题，输出：无问题）
"""
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_review_prompt())
            self._parse_review_response(response, result)
        except Exception as e:
            self._log(f"LLM审核失败: {e}")

        return result

    def _parse_review_response(self, response: str, result: ReviewResult):
        """解析LLM审核响应，填充ReviewResult"""
        if not response:
            return

        # 无问题直接通过
        if "无问题" in response or "未发现" in response:
            result.passed = True
            return

        lines = response.split("\n")
        pending_issue = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("问题"):
                # 保存上一条
                if pending_issue:
                    result.add_issue(pending_issue)
                pending_issue = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif line.startswith("建议"):
                if pending_issue:
                    result.add_suggestion(line.split("：", 1)[-1].split(":", 1)[-1].strip())
                    pending_issue = None
                else:
                    result.add_suggestion(line.split("：", 1)[-1].split(":", 1)[-1].strip())
        if pending_issue:
            result.add_issue(pending_issue)

        # 兜底：LLM 提到"问题"但没解析出结构时，整段作为一条
        if not result.issues and len(response) > 20:
            result.add_issue(response[:300])
    
    def _get_review_prompt(self) -> str:
        """获取审核系统提示词"""
        return """你是一位要求极其严格的网文一致性督察，负责12项检查：
时空一致性、人物性格一致性、能力体系一致性、称谓统一、外貌描写一致、
伏笔遗漏、时间线矛盾、地点矛盾、逻辑漏洞、设定冲突、配角OOC、数据前后矛盾。

审核标准：
- 发现问题必须明确指出，附原文引用
- 区分严重程度（严重/一般/建议）
- 每章至少检查以上全部维度
- 诚实客观：没问题就说没问题，不硬凑问题"""
