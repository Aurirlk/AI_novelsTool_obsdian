"""
大纲批评师智能体
负责对抗式审视人类大纲，找逻辑漏洞、设定漏洞、情节硬伤、常识错误
"""

import uuid
from typing import Optional, List, Dict
from src.agents.base import BaseAgent
from src.models.schemas import NovelState
from src.prompts.critic_prompts import OUTLINE_CRITIC_PROMPT, format_criticism_report
from src.knowledge.loader import load_knowledge
from src.data.history_manager import get_history_manager, HistoryRecord
from src.memory.shared_memory import get_shared_memory, MemoryEntry
from src.memory.agent_caller import get_agent_caller


class OutlineCritic(BaseAgent):
    """大纲批评师智能体 - 对抗式审核人类大纲"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("大纲批评师", llm_provider)
        self.knowledge_base = None
        self.history_manager = get_history_manager()
        self.shared_memory = get_shared_memory()
        self.agent_caller = get_agent_caller()
        
        # 注册到共享记忆
        self.shared_memory.register_agent("outline_critic", "outline_critic")
        
        # 注册到调用器
        self.agent_caller.register_agent(
            agent_id="outline_critic",
            agent_instance=self,
            agent_role="outline_critic",
            description="大纲批评师 - 对抗式审核人类大纲",
            methods=[
                {"name": "execute", "description": "执行大纲批评", "params": ["state", "outline_text", "project_name"]},
                {"name": "critique_outline", "description": "批评大纲", "params": ["outline_text"]},
            ],
            dependencies=["knowledge_checker"]  # 依赖知识库检查器
        )
    
    def execute(self, state: NovelState, outline_text: str = "", 
                project_name: str = "未命名项目", **kwargs) -> dict:
        """
        执行大纲批评
        
        Args:
            state: 小说状态
            outline_text: 人类作者的大纲文本
            project_name: 项目名称
        
        Returns:
            批评结果
        """
        self._log("开始对抗式审核大纲...")
        
        # 如果没有提供大纲文本，从state中获取
        if not outline_text and state.story_bible:
            outline_text = self._extract_outline_from_state(state)
        
        if not outline_text:
            return {
                "error": "未提供大纲文本",
                "issues": [],
                "report": "无法进行批评：未提供大纲文本"
            }
        
        # 调用知识库检查器进行常识检查
        knowledge_issues = self._call_knowledge_checker(outline_text)
        
        # 使用LLM进行对抗式批评
        llm_issues = self._critique_with_llm(outline_text)
        
        # 合并问题
        issues = llm_issues + knowledge_issues
        
        # 生成批评报告
        report = format_criticism_report(issues)
        
        # 保存到历史记录
        record_id = str(uuid.uuid4())[:8]
        history_record = HistoryRecord(
            id=record_id,
            function_type="outline_critic",
            project_name=project_name,
            title=f"大纲批评 - {project_name}",
            content=outline_text[:2000],
            result=report,
            metadata={
                "issue_count": len(issues),
                "high_severity_count": sum(1 for i in issues if i.get("severity") == "高"),
            }
        )
        self.history_manager.save_record(history_record)
        
        # 保存到共享记忆
        memory_id = str(uuid.uuid4())[:8]
        memory = MemoryEntry(
            id=memory_id,
            source_agent="outline_critic",
            memory_type="opinion",
            content=f"大纲批评结果: 发现{len(issues)}个问题",
            related_agents=["writer", "outline"],
            metadata={
                "project_name": project_name,
                "issue_count": len(issues),
                "high_severity_count": sum(1 for i in issues if i.get("severity") == "高"),
            },
            importance=7
        )
        self.shared_memory.add_memory(memory)
        
        # 更新智能体状态
        self.shared_memory.update_agent_state(
            "outline_critic",
            status="completed",
            total_tasks=self.shared_memory.get_agent_state("outline_critic").total_tasks + 1,
            completed_tasks=self.shared_memory.get_agent_state("outline_critic").completed_tasks + 1,
            last_task=f"大纲批评 - {project_name}"
        )
        
        self._log(f"批评完成: 发现 {len(issues)} 个问题")
        
        return {
            "issues": issues,
            "report": report,
            "issue_count": len(issues),
            "high_severity_count": sum(1 for i in issues if i.get("severity") == "高"),
            "history_record_id": record_id,
            "memory_id": memory_id,
        }
    
    def _call_knowledge_checker(self, text: str) -> List[Dict]:
        """调用知识库检查器"""
        self._log("调用知识库检查器...")
        
        try:
            # 使用调用器调用知识库检查器
            call_result = self.agent_caller.call_agent(
                caller_id="outline_critic",
                callee_id="knowledge_checker",
                method="check_knowledge",
                params={"text": text}
            )
            
            if call_result.status == "completed" and call_result.result:
                return call_result.result.get("issues", [])
            else:
                self._log(f"知识库检查器调用失败: {call_result.error}")
                return []
        
        except Exception as e:
            self._log(f"调用知识库检查器失败: {e}")
            return []
    
    def critique_outline(self, outline_text: str) -> Dict:
        """
        批评大纲（供其他智能体调用）
        
        Args:
            outline_text: 大纲文本
        
        Returns:
            批评结果
        """
        issues = self._critique_with_llm(outline_text)
        report = format_criticism_report(issues)
        
        return {
            "issues": issues,
            "report": report,
            "issue_count": len(issues),
        }
    
    def _extract_outline_from_state(self, state: NovelState) -> str:
        """从state中提取大纲文本"""
        if not state.story_bible:
            return ""
        
        parts = []
        if state.story_bible.title:
            parts.append(f"标题: {state.story_bible.title}")
        if state.story_bible.genre:
            parts.append(f"题材: {state.story_bible.genre}")
        if state.story_bible.theme:
            parts.append(f"主题: {state.story_bible.theme}")
        if state.story_bible.worldview:
            parts.append(f"世界观: {state.story_bible.worldview}")
        if state.story_bible.power_system:
            parts.append(f"力量体系: {state.story_bible.power_system}")
        if state.story_bible.plot_outline:
            parts.append(f"主线大纲: {state.story_bible.plot_outline}")
        
        return "\n".join(parts)
    
    def _critique_with_llm(self, outline_text: str) -> List[Dict]:
        """使用LLM进行对抗式批评"""
        self._log("调用LLM进行对抗式批评...")
        
        prompt = f"""
请对以下大纲进行刁钻刻薄的批评：

{outline_text}

请严格按照系统提示词的要求，找出所有问题。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=OUTLINE_CRITIC_PROMPT)
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
            if any(keyword in paragraph for keyword in ["逻辑", "设定", "情节", "常识", "人物"]):
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
        categories = ["逻辑", "设定", "情节", "常识", "人物"]
        for category in categories:
            if category in text:
                return category
        return "其他"
    
    def _check_knowledge(self, outline_text: str) -> List[Dict]:
        """使用知识库检查常识错误"""
        self._log("使用知识库检查常识错误...")
        
        if self.knowledge_base is None:
            self.knowledge_base = load_knowledge()
        
        # 检查常识错误
        knowledge_errors = self.knowledge_base.check_fact(outline_text)
        
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


def create_outline_critic(llm_provider: Optional[str] = None) -> OutlineCritic:
    """创建大纲批评师实例"""
    return OutlineCritic(llm_provider)
