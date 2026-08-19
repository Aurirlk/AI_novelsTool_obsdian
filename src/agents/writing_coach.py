"""
写作陪练智能体
帮助作者发现自己的写作盲点和局限
"""

import uuid
from typing import Optional, List, Dict
from src.agents.base import BaseAgent
from src.models.schemas import NovelState
from src.data.history_manager import get_history_manager, HistoryRecord


class WritingCoach(BaseAgent):
    """写作陪练智能体 - 帮助作者发现自己的局限"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("写作陪练", llm_provider)
        self.history_manager = get_history_manager()
    
    def execute(self, state: NovelState, text: str = "", 
                mode: str = "find_blind_spots", 
                project_name: str = "未命名项目", **kwargs) -> dict:
        """
        执行写作陪练
        
        Args:
            state: 小说状态
            text: 待分析文本
            mode: 模式（find_blind_spots/find_limitations/suggest_improvements）
            project_name: 项目名称
        
        Returns:
            分析结果
        """
        self._log(f"开始写作陪练分析 (模式: {mode})...")
        
        if not text:
            return {
                "error": "未提供文本",
                "issues": [],
                "report": "无法进行分析：未提供文本"
            }
        
        # 根据模式执行不同的分析
        if mode == "find_blind_spots":
            result = self._find_blind_spots(text)
        elif mode == "find_limitations":
            result = self._find_limitations(text)
        elif mode == "suggest_improvements":
            result = self._suggest_improvements(text)
        else:
            result = self._find_blind_spots(text)
        
        # 保存历史记录
        record_id = str(uuid.uuid4())[:8]
        history_record = HistoryRecord(
            id=record_id,
            function_type="writing_coach",
            project_name=project_name,
            title=f"写作陪练 - {mode}",
            content=text[:2000],
            result=result["report"],
            metadata={
                "mode": mode,
                "issue_count": len(result["issues"]),
            }
        )
        self.history_manager.save_record(history_record)
        
        self._log(f"写作陪练分析完成: 发现 {len(result['issues'])} 个问题")
        
        return {
            **result,
            "history_record_id": record_id,
        }
    
    def _find_blind_spots(self, text: str) -> dict:
        """发现写作盲点"""
        self._log("分析写作盲点...")
        
        prompt = f"""
请分析以下文本，帮助作者发现写作盲点：

{text[:2000]}

请从以下角度分析：
1. 情节设计盲点：是否有遗漏的情节线
2. 人物塑造盲点：是否有扁平化的角色
3. 场景描写盲点：是否有缺乏细节的场景
4. 情感表达盲点：是否有情感缺失的地方
5. 节奏控制盲点：是否有节奏问题

请用刁钻但有建设性的语气指出问题。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_coach_prompt())
            issues = self._parse_issues(response, "blind_spot")
            report = self._generate_report(issues, "写作盲点分析")
            
            return {
                "issues": issues,
                "report": report,
                "mode": "find_blind_spots",
            }
        except Exception as e:
            self._log(f"分析失败: {e}")
            return {
                "issues": [],
                "report": f"分析失败: {e}",
                "mode": "find_blind_spots",
            }
    
    def _find_limitations(self, text: str) -> dict:
        """发现写作局限"""
        self._log("分析写作局限...")
        
        prompt = f"""
请分析以下文本，帮助作者发现自己的写作局限：

{text[:2000]}

请从以下角度分析：
1. 叙事能力局限：是否只能用单一视角
2. 描写能力局限：是否只能写表面
3. 对话能力局限：对话是否生硬
4. 想象力局限：是否缺乏创意
5. 知识储备局限：是否有知识盲区

请直接指出作者的局限，不要客气。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_coach_prompt())
            issues = self._parse_issues(response, "limitation")
            report = self._generate_report(issues, "写作局限分析")
            
            return {
                "issues": issues,
                "report": report,
                "mode": "find_limitations",
            }
        except Exception as e:
            self._log(f"分析失败: {e}")
            return {
                "issues": [],
                "report": f"分析失败: {e}",
                "mode": "find_limitations",
            }
    
    def _suggest_improvements(self, text: str) -> dict:
        """建议改进方向"""
        self._log("分析改进方向...")
        
        prompt = f"""
请分析以下文本，为作者提供改进建议：

{text[:2000]}

请从以下角度提供建议：
1. 情节设计改进：如何让情节更吸引人
2. 人物塑造改进：如何让人物更立体
3. 场景描写改进：如何让场景更生动
4. 情感表达改进：如何让情感更打动人
5. 节奏控制改进：如何让节奏更舒服

请提供具体、可操作的建议。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_coach_prompt())
            issues = self._parse_issues(response, "improvement")
            report = self._generate_report(issues, "改进建议")
            
            return {
                "issues": issues,
                "report": report,
                "mode": "suggest_improvements",
            }
        except Exception as e:
            self._log(f"分析失败: {e}")
            return {
                "issues": [],
                "report": f"分析失败: {e}",
                "mode": "suggest_improvements",
            }
    
    def _get_coach_prompt(self) -> str:
        """获取陪练系统提示词"""
        return """你是一位资深的写作教练，专门帮助作者发现自己的写作盲点和局限。

你的特点：
1. 直言不讳：直接指出问题，不拐弯抹角
2. 有建设性：不仅指出问题，还提供改进方向
3. 有深度：看到表面问题背后的深层原因
4. 有同理心：理解作者的困难，给予鼓励

你的目标：
- 帮助作者发现"自己写不了什么"
- 帮助作者突破自己的局限
- 帮助作者提升写作水平

请用专业、直接、有建设性的语气进行分析。"""
    
    def _parse_issues(self, response: str, issue_type: str) -> List[Dict]:
        """解析问题"""
        issues = []
        
        paragraphs = response.split("\n")
        
        current_issue = None
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 检测问题
            if any(keyword in paragraph for keyword in ["盲点", "局限", "改进", "问题", "建议"]):
                if current_issue:
                    issues.append(current_issue)
                
                current_issue = {
                    "type": issue_type,
                    "description": paragraph,
                    "suggestion": "",
                }
            elif current_issue and ("建议" in paragraph or "可以" in paragraph):
                current_issue["suggestion"] = paragraph
        
        if current_issue:
            issues.append(current_issue)
        
        # 如果没有解析出问题，创建一个通用问题
        if not issues and response:
            issues.append({
                "type": issue_type,
                "description": response[:500] if len(response) > 500 else response,
                "suggestion": "请根据分析结果进行改进",
            })
        
        return issues
    
    def _generate_report(self, issues: List[Dict], title: str) -> str:
        """生成报告"""
        if not issues:
            return f"## {title}\n\n未发现明显问题。"
        
        report_parts = [
            f"## {title}",
            "",
            f"共发现 {len(issues)} 个问题：",
            "",
        ]
        
        for i, issue in enumerate(issues, 1):
            report_parts.append(f"### {i}. {issue['description']}")
            if issue.get('suggestion'):
                report_parts.append(f"**建议**: {issue['suggestion']}")
            report_parts.append("")
        
        return "\n".join(report_parts)


def create_writing_coach(llm_provider: Optional[str] = None) -> WritingCoach:
    """创建写作陪练实例"""
    return WritingCoach(llm_provider)
