"""
知识库检查器智能体
负责检查文本中的常识性错误
"""

import uuid
from typing import Optional, List, Dict
from src.agents.base import BaseAgent
from src.models.schemas import NovelState
from src.prompts.critic_prompts import KNOWLEDGE_CHECK_PROMPT
from src.knowledge.loader import load_knowledge
from src.data.history_manager import get_history_manager, HistoryRecord
from src.memory.shared_memory import get_shared_memory, MemoryEntry
from src.memory.agent_caller import get_agent_caller


class KnowledgeChecker(BaseAgent):
    """知识库检查器智能体 - 检查常识性错误"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("知识库检查器", llm_provider)
        self.knowledge_base = None
        self.history_manager = get_history_manager()
        self.shared_memory = get_shared_memory()
        self.agent_caller = get_agent_caller()
        
        # 注册到共享记忆
        self.shared_memory.register_agent("knowledge_checker", "knowledge_checker")
        
        # 注册到调用器
        self.agent_caller.register_agent(
            agent_id="knowledge_checker",
            agent_instance=self,
            agent_role="knowledge_checker",
            description="知识库检查器 - 检查常识性错误",
            methods=[
                {"name": "execute", "description": "执行知识库检查", "params": ["state", "text", "category", "project_name"]},
                {"name": "check_knowledge", "description": "检查知识", "params": ["text", "category"]},
            ],
            dependencies=[]
        )
    
    def execute(self, state: NovelState, text: str = "", 
                category: Optional[str] = None, 
                project_name: str = "未命名项目", **kwargs) -> dict:
        """
        执行知识库检查
        
        Args:
            state: 小说状态
            text: 待检查文本
            category: 知识类别过滤（历史、地理、科学）
            project_name: 项目名称
        
        Returns:
            检查结果
        """
        self._log("开始检查常识性错误...")
        
        if not text:
            return {
                "error": "未提供文本",
                "issues": [],
                "report": "无法进行检查：未提供文本"
            }
        
        # 使用知识库检查
        knowledge_issues = self._check_knowledge(text, category)
        
        # 使用LLM进行深度检查
        llm_issues = self._check_with_llm(text, category)
        
        # 合并问题
        all_issues = knowledge_issues + llm_issues
        
        # 去重
        unique_issues = self._deduplicate_issues(all_issues)
        
        # 生成报告
        report = self._generate_report(unique_issues)
        
        # 保存历史记录
        record_id = str(uuid.uuid4())[:8]
        history_record = HistoryRecord(
            id=record_id,
            function_type="knowledge_check",
            project_name=project_name,
            title=f"知识库检查 - {project_name}",
            content=text[:2000],
            result=report,
            metadata={
                "category": category,
                "issue_count": len(unique_issues),
            }
        )
        self.history_manager.save_record(history_record)
        
        # 保存到共享记忆
        memory_id = str(uuid.uuid4())[:8]
        memory = MemoryEntry(
            id=memory_id,
            source_agent="knowledge_checker",
            memory_type="knowledge",
            content=f"知识库检查结果: 发现{len(unique_issues)}个常识错误",
            related_agents=["outline_critic", "chapter_critic", "writer"],
            metadata={
                "project_name": project_name,
                "category": category,
                "issue_count": len(unique_issues),
            },
            importance=6
        )
        self.shared_memory.add_memory(memory)
        
        # 更新智能体状态
        self.shared_memory.update_agent_state(
            "knowledge_checker",
            status="completed",
            total_tasks=self.shared_memory.get_agent_state("knowledge_checker").total_tasks + 1,
            completed_tasks=self.shared_memory.get_agent_state("knowledge_checker").completed_tasks + 1,
            last_task=f"知识库检查 - {project_name}"
        )
        
        self._log(f"检查完成: 发现 {len(unique_issues)} 个常识错误")
        
        return {
            "issues": unique_issues,
            "report": report,
            "issue_count": len(unique_issues),
            "history_record_id": record_id,
            "memory_id": memory_id,
        }
    
    def check_knowledge(self, text: str, category: Optional[str] = None) -> Dict:
        """
        检查知识（供其他智能体调用）
        
        Args:
            text: 待检查文本
            category: 知识类别过滤
        
        Returns:
            检查结果
        """
        knowledge_issues = self._check_knowledge(text, category)
        llm_issues = self._check_with_llm(text, category)
        
        all_issues = knowledge_issues + llm_issues
        unique_issues = self._deduplicate_issues(all_issues)
        
        return {
            "issues": unique_issues,
            "issue_count": len(unique_issues),
        }
    
    def _check_knowledge(self, text: str, category: Optional[str] = None) -> List[Dict]:
        """使用知识库检查常识错误"""
        self._log("使用知识库检查常识错误...")
        
        if self.knowledge_base is None:
            self.knowledge_base = load_knowledge()
        
        # 检查常识错误
        knowledge_errors = self.knowledge_base.check_fact(text, category)
        
        # 转换为标准格式
        issues = []
        for error in knowledge_errors:
            issues.append({
                "category": error.get("type", "常识"),
                "severity": error.get("severity", "中"),
                "description": error.get("description", ""),
                "suggestion": error.get("suggestion", ""),
                "source": "knowledge_base"
            })
        
        return issues
    
    def _check_with_llm(self, text: str, category: Optional[str] = None) -> List[Dict]:
        """使用LLM进行深度检查"""
        self._log("调用LLM进行深度检查...")
        
        # 截取前2000字进行检查（避免token限制）
        text_to_check = text[:2000] if len(text) > 2000 else text
        
        category_filter = ""
        if category:
            category_filter = f"请重点检查{category}相关的错误。"
        
        prompt = f"""
请检查以下文本中的常识性错误：

{text_to_check}

{category_filter}

请严格按照系统提示词的要求，找出所有常识性错误。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=KNOWLEDGE_CHECK_PROMPT)
            issues = self._parse_llm_response(response)
            return issues
        except Exception as e:
            self._log(f"LLM检查失败: {e}")
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
            if any(keyword in paragraph for keyword in ["历史", "地理", "科学", "常识"]):
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
                    "suggestion": "",
                    "source": "llm"
                }
            elif current_issue and ("正确" in paragraph or "应该是" in paragraph):
                current_issue["suggestion"] = paragraph
        
        if current_issue:
            issues.append(current_issue)
        
        return issues
    
    def _extract_category(self, text: str) -> str:
        """提取问题分类"""
        categories = ["历史", "地理", "科学", "常识"]
        for category in categories:
            if category in text:
                return category
        return "常识"
    
    def _deduplicate_issues(self, issues: List[Dict]) -> List[Dict]:
        """去重"""
        unique_issues = []
        seen_descriptions = set()
        
        for issue in issues:
            description = issue.get("description", "")
            if description not in seen_descriptions:
                seen_descriptions.add(description)
                unique_issues.append(issue)
        
        return unique_issues
    
    def _generate_report(self, issues: List[Dict]) -> str:
        """生成报告"""
        if not issues:
            return "未发现常识性错误。"
        
        # 统计问题数量
        high_count = sum(1 for issue in issues if issue.get("severity") == "高")
        medium_count = sum(1 for issue in issues if issue.get("severity") == "中")
        low_count = sum(1 for issue in issues if issue.get("severity") == "低")
        
        # 按分类统计
        category_counts = {}
        for issue in issues:
            category = issue.get("category", "常识")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        report_parts = [
            "## 常识性错误检查报告",
            "",
            "### 问题统计",
            f"- 高严重度问题：{high_count}个",
            f"- 中严重度问题：{medium_count}个",
            f"- 低严重度问题：{low_count}个",
            "",
            "### 分类统计",
        ]
        
        for category, count in category_counts.items():
            report_parts.append(f"- {category}：{count}个")
        
        report_parts.append("")
        report_parts.append("### 问题详情")
        
        for i, issue in enumerate(issues, 1):
            report_parts.append(f"{i}. [{issue.get('severity', '中')}] {issue.get('category', '常识')}")
            report_parts.append(f"   问题：{issue.get('description', '')}")
            if issue.get('suggestion'):
                report_parts.append(f"   建议：{issue.get('suggestion', '')}")
            report_parts.append("")
        
        return "\n".join(report_parts)


def create_knowledge_checker(llm_provider: Optional[str] = None) -> KnowledgeChecker:
    """创建知识库检查器实例"""
    return KnowledgeChecker(llm_provider)
