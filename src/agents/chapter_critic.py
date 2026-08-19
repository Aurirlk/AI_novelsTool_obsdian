"""
章节批评师智能体
负责对抗式审视人类章节，找逻辑漏洞、情节硬伤、常识错误
"""

import uuid
from typing import Optional, List, Dict
from src.agents.base import BaseAgent
from src.models.schemas import NovelState, Chapter
from src.prompts.critic_prompts import CHAPTER_CRITIC_PROMPT, format_criticism_report
from src.knowledge.loader import load_knowledge
from src.data.history_manager import get_history_manager, HistoryRecord


class ChapterCritic(BaseAgent):
    """章节批评师智能体 - 对抗式审核人类章节"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("章节批评师", llm_provider)
        self.knowledge_base = None
        self.history_manager = get_history_manager()
    
    def execute(self, state: NovelState, chapter_text: str = "", 
                chapter_num: int = 0, project_name: str = "未命名项目", **kwargs) -> dict:
        """
        执行章节批评
        
        Args:
            state: 小说状态
            chapter_text: 人类作者的章节文本
            chapter_num: 章节号
            project_name: 项目名称
        
        Returns:
            批评结果
        """
        self._log(f"开始对抗式审核第{chapter_num}章...")
        
        # 如果没有提供章节文本，从state中获取
        if not chapter_text and chapter_num > 0 and chapter_num <= len(state.chapters):
            chapter = state.chapters[chapter_num - 1]
            chapter_text = chapter.content
        
        if not chapter_text:
            return {
                "error": "未提供章节文本",
                "issues": [],
                "report": "无法进行批评：未提供章节文本"
            }
        
        # 使用LLM进行对抗式批评
        issues = self._critique_with_llm(chapter_text, chapter_num)
        
        # 使用知识库检查常识错误
        knowledge_issues = self._check_knowledge(chapter_text)
        issues.extend(knowledge_issues)
        
        # 生成批评报告
        report = format_criticism_report(issues)
        
        # 保存历史记录
        record_id = str(uuid.uuid4())[:8]
        history_record = HistoryRecord(
            id=record_id,
            function_type="chapter_critic",
            project_name=project_name,
            title=f"第{chapter_num}章批评 - {project_name}",
            content=chapter_text[:2000],  # 限制长度
            result=report,
            metadata={
                "chapter_num": chapter_num,
                "issue_count": len(issues),
                "high_severity_count": sum(1 for i in issues if i.get("severity") == "高"),
            }
        )
        self.history_manager.save_record(history_record)
        
        self._log(f"批评完成: 发现 {len(issues)} 个问题")
        
        return {
            "issues": issues,
            "report": report,
            "issue_count": len(issues),
            "high_severity_count": sum(1 for i in issues if i.get("severity") == "高"),
            "history_record_id": record_id,
        }
    
    def _critique_with_llm(self, chapter_text: str, chapter_num: int) -> List[Dict]:
        """使用LLM进行对抗式批评"""
        self._log("调用LLM进行对抗式批评...")
        
        # 截取前2000字进行批评（避免token限制）
        text_to_critique = chapter_text[:2000] if len(chapter_text) > 2000 else chapter_text
        
        prompt = f"""
请对第{chapter_num}章进行刁钻刻薄的批评：

{text_to_critique}

请严格按照系统提示词的要求，找出所有问题。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=CHAPTER_CRITIC_PROMPT)
            issues = self._parse_llm_response(response)
            return issues
        except Exception as e:
            self._log(f"LLM批评失败: {e}")
            return []
    
    def _parse_llm_response(self, response: str) -> List[Dict]:
        """解析LLM响应，提取问题"""
        issues = []
        
        # 简单解析：按段落分割，识别问题
        paragraphs = response.split("\n")
        
        current_issue = None
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 检测问题分类
            if any(keyword in paragraph for keyword in ["逻辑", "情节", "常识", "人物", "文字", "节奏"]):
                if current_issue:
                    issues.append(current_issue)
                
                # 提取严重程度
                severity = "中"
                if "高" in paragraph:
                    severity = "高"
                elif "低" in paragraph:
                    severity = "低"
                
                current_issue = {
                    "category": self._extract_category(paragraph),
                    "severity": severity,
                    "description": paragraph,
                    "suggestion": ""
                }
            elif current_issue and ("建议" in paragraph or "修改" in paragraph):
                current_issue["suggestion"] = paragraph
        
        if current_issue:
            issues.append(current_issue)
        
        # 如果没有解析出问题，创建一个通用问题
        if not issues and response:
            issues.append({
                "category": "其他",
                "severity": "中",
                "description": response[:500] if len(response) > 500 else response,
                "suggestion": "请根据批评意见进行修改"
            })
        
        return issues
    
    def _extract_category(self, text: str) -> str:
        """提取问题分类"""
        categories = ["逻辑", "情节", "常识", "人物", "文字", "节奏"]
        for category in categories:
            if category in text:
                return category
        return "其他"
    
    def _check_knowledge(self, chapter_text: str) -> List[Dict]:
        """使用知识库检查常识错误"""
        self._log("使用知识库检查常识错误...")
        
        if self.knowledge_base is None:
            self.knowledge_base = load_knowledge()
        
        # 检查常识错误
        knowledge_errors = self.knowledge_base.check_fact(chapter_text)
        
        # 转换为标准格式
        issues = []
        for error in knowledge_errors:
            issues.append({
                "category": error.get("type", "常识"),
                "severity": error.get("severity", "中"),
                "description": error.get("description", ""),
                "suggestion": error.get("suggestion", "")
            })
        
        return issues


def create_chapter_critic(llm_provider: Optional[str] = None) -> ChapterCritic:
    """创建章节批评师实例"""
    return ChapterCritic(llm_provider)
