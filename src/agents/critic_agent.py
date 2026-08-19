"""
评论家智能体
负责批判反思，修改Prompt实现自进化
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CritiqueResult:
    """批评结果"""
    chapter_num: int
    
    # 整体评价
    overall_score: int = 5  # 1-10
    overall_comment: str = ""
    rule_score: int = -1  # 规则兜底分（0-100），-1 表示未计算
    
    # 具体问题
    issues: list = field(default_factory=list)  # [{"type": "节奏", "description": "...", "severity": "high"}]
    
    # 改进建议
    suggestions: list = field(default_factory=list)
    
    # Prompt修改建议
    prompt_modifications: list = field(default_factory=list)
    
    # 与爆款对比
    comparison_with_best: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PromptEvolution:
    """Prompt进化记录"""
    target_agent: str  # 被修改的智能体
    original_prompt: str
    modified_prompt: str
    reason: str
    improvement_expected: str
    
    chapter_num: int = 0
    applied: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CriticAgent:
    """评论家智能体"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.critique_history: list[CritiqueResult] = []
        self.prompt_evolutions: list[PromptEvolution] = []
    
    def _get_llm(self):
        """懒加载LLM客户端（用户配置API）"""
        if self.llm is None:
            from src.utils.llm import get_llm_client
            self.llm = get_llm_client()
        return self.llm
    
    def critique_chapter(self, chapter_content: str, chapter_num: int,
                         story_bible: dict = None, 
                         previous_chapters_summary: str = "",
                         target_metrics: dict = None) -> CritiqueResult:
        """
        批评一个章节
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            story_bible: 故事圣经
            previous_chapters_summary: 前文摘要
            target_metrics: 目标指标
        
        Returns:
            批评结果
        """
        print(f"[评论家] 正在批评第{chapter_num}章...")
        
        result = CritiqueResult(chapter_num=chapter_num)
        
        # 规则分析（兜底）：百分制评分 + 文本肌理问题
        rule_score = self._evaluate_overall_100(chapter_content)
        result.rule_score = rule_score
        rule_issues = self._identify_issues(chapter_content, story_bible)
        rule_issues.extend(self._texture_issues(chapter_content))
        result.suggestions = self._generate_suggestions(chapter_content, rule_issues)
        
        # LLM深度批评（真实调用，规则结果合并）
        try:
            llm_result = self._critique_with_llm(
                chapter_content, chapter_num, story_bible, previous_chapters_summary, target_metrics
            )
            result.overall_score = llm_result.get("score", result.overall_score)
            result.overall_comment = llm_result.get("comment", "")
            result.comparison_with_best = llm_result.get("comparison", "")
            llm_issues = llm_result.get("issues", [])
            result.issues = llm_issues + rule_issues if llm_issues else rule_issues
            if llm_result.get("suggestions"):
                result.suggestions = llm_result["suggestions"]
        except Exception as e:
            print(f"[评论家] LLM批评失败: {e}")
            result.issues = rule_issues
        
        # 规则兜底否决：LLM高分但规则分不达标（<60）→ 强制降级并附加规则问题
        if rule_score < 60:
            result.overall_score = min(result.overall_score, 4)
            result.overall_comment = (result.overall_comment or "").strip()
            veto_note = f"⚠️ 规则兜底否决：文本肌理得分 {rule_score}/100（低于60分及格线）"
            if result.overall_comment:
                result.overall_comment = f"{veto_note}。{result.overall_comment}"
            else:
                result.overall_comment = veto_note
        
        result.prompt_modifications = self._suggest_prompt_modifications(result)
        
        # 保存历史
        self.critique_history.append(result)
        
        print(f"[评论家] 第{chapter_num}章评分: {result.overall_score}/10 (规则分 {rule_score}/100)")
        return result
    
    def _critique_with_llm(self, chapter_content: str, chapter_num: int,
                           story_bible: dict = None,
                           previous_chapters_summary: str = "",
                           target_metrics: dict = None) -> dict:
        """使用LLM进行深度批评，返回 {score, comment, issues, suggestions, comparison}"""
        bible_text = ""
        if story_bible:
            bible_text = str(story_bible)[:800]
        
        prompt = f"""
【故事设定（如有）】
{bible_text or "无"}

【前文摘要（如有）】
{previous_chapters_summary or "无"}

【待批评章节】
第{chapter_num}章
{chapter_content[:2500]}...

请作为毒舌网文评论家，从六维打分（各10分）：题材定位、开篇留存、节奏、人物、文笔、爽点密度。
输出严格JSON格式：
{{"score": 总体分(1-10), "comment": "总体评价", "issues": [{{"type": "分类", "description": "问题", "severity": "high/medium/low"}}], "suggestions": ["建议1"], "comparison": "与爆款对比"}}
"""
        try:
            client = self._get_llm()
            response = client.chat(prompt, system_prompt=self._get_critic_prompt())
            return self._parse_llm_json(response)
        except Exception as e:
            print(f"[评论家] LLM调用异常: {e}")
            return {}
    
    def _get_critic_prompt(self) -> str:
        """批评系统提示词"""
        return """你是要求严格的网文评论家，毒舌但专业。从题材定位、开篇留存、节奏、人物、文笔、爽点密度六维评价。
必须输出严格JSON，不要输出任何JSON以外的内容。问题要具体，引用原文，不说空话套话。"""
    
    def _parse_llm_json(self, response: str) -> dict:
        """解析LLM返回的JSON"""
        import json
        import re
        try:
            match = re.search(r"\{.*\}", response, re.S)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {}
    
    def _evaluate_overall(self, content: str) -> int:
        """整体评分（保留10分制，供兼容）"""
        score = 5  # 基础分
        
        # 检查字数
        word_count = len(content)
        if 1500 <= word_count <= 2500:
            score += 1
        elif word_count < 1000:
            score -= 2
        elif word_count > 3000:
            score -= 1
        
        # 检查爽点
        satisfaction_keywords = ["震惊", "不敢相信", "逆袭", "打脸", "碾压"]
        if any(kw in content for kw in satisfaction_keywords):
            score += 1
        
        # 检查对话
        dialogue_count = content.count('"') + content.count('"')
        if dialogue_count > 10:
            score += 1
        
        # 检查节奏（段落数）
        paragraphs = [p for p in content.split("\n") if p.strip()]
        if 5 <= len(paragraphs) <= 20:
            score += 1
        
        return max(1, min(10, score))
    
    # ==================== 百分制规则评分（InkWeave 式文本肌理质检） ====================

    # AI水文词：空洞、套路化表达
    _WATER_WORDS = [
        "仿佛", "似乎", "宛如", "犹如", "如同", "瞬间", "顿时", "猛然", "忽然",
        "不禁", "不由", "深深", "静静", "缓缓", "轻轻", "默默", "微微",
        "一丝", "一抹", "一缕", "一股", "一阵", "一道", "一层", "一片",
        "嘴角勾起", "眼中闪过一丝", "心中一动", "若有所思", "喃喃自语",
    ]

    # 套路反应词（读者已免疫）：权重低，检测到扣分
    _CLICHE_REACTIONS = [
        "瞳孔一缩", "倒吸一口凉气", "倒吸一口冷气", "浑身一震", "虎躯一震",
        "冷笑一声", "冷哼一声", "眉头一皱", "眼睛一亮", "嘴角上扬",
    ]

    # 重复动作点名
    _REPEATED_ACTIONS = ["点了点头", "摇了摇头", "点了点头"]

    def _evaluate_overall_100(self, content: str) -> int:
        """百分制规则评分：基础80分，按文本肌理问题扣分"""
        if not content:
            return 0
        score = 80

        # 字数
        word_count = len(content)
        if word_count < 1000:
            score -= 10
        elif word_count > 3500:
            score -= 5

        # AI水文词密度（每3个扣1分，上限15）
        water_hits = sum(content.count(w) for w in self._WATER_WORDS)
        score -= min(15, water_hits // 3)

        # 套路反应词（每个扣2分，上限10）
        cliche_hits = sum(content.count(w) for w in self._CLICHE_REACTIONS)
        score -= min(10, cliche_hits * 2)

        # 重复动作点名（同一动作出现≥3次扣5分）
        for act in self._REPEATED_ACTIONS:
            if content.count(act) >= 3:
                score -= 5

        # 感叹号配额：每段超过3个感叹号扣分（上限10）
        for para in content.split("\n"):
            ex_count = para.count("！") + para.count("!")
            if ex_count > 3:
                score -= min(10, (ex_count - 3) * 2)

        # 逗号链：单句超过8个逗号扣分（上限8）
        import re
        for sentence in re.split(r"[。！？!?；\n]", content):
            if sentence.count("，") + sentence.count(",") > 8:
                score -= 2
        score = max(0, score)

        # 句群波形：连续10句长度近似（同长段扣4分，简化检测）
        sentences = [s for s in re.split(r"[。！？!?；\n]", content) if len(s.strip()) > 4]
        if len(sentences) >= 10:
            similar = 0
            for i in range(1, len(sentences)):
                if abs(len(sentences[i]) - len(sentences[i - 1])) <= 3:
                    similar += 1
            if similar >= len(sentences) - 2:
                score -= 4

        return max(0, min(100, score))

    def _texture_issues(self, content: str) -> list:
        """文本肌理专项检测（对齐 InkWeave 9项检测中的核心项）"""
        import re
        issues = []

        # 1. 套路反应词
        cliche_hits = [w for w in self._CLICHE_REACTIONS if w in content]
        if cliche_hits:
            issues.append({
                "type": "文笔",
                "description": f"套路化反应词：{'、'.join(cliche_hits[:4])}（读者已免疫，建议换高质量生理锚点）",
                "severity": "medium",
            })

        # 2. AI水文词密度
        water_hits = sum(content.count(w) for w in self._WATER_WORDS)
        if water_hits >= 10:
            issues.append({
                "type": "文笔",
                "description": f"AI水文词出现{water_hits}次（仿佛/似乎/宛如/瞬间等），空洞表达过多",
                "severity": "medium",
            })

        # 3. 动作点名册：同一动作≥3次
        for act in self._REPEATED_ACTIONS:
            n = content.count(act)
            if n >= 3:
                issues.append({
                    "type": "文笔",
                    "description": f"动作重复{n}次：「{act}」反复出现，建议多样化",
                    "severity": "low",
                })

        # 4. 感叹号配额：一段>3个
        for para in content.split("\n"):
            ex_count = para.count("！") + para.count("!")
            if ex_count > 3:
                issues.append({
                    "type": "文笔",
                    "description": f"某段感叹号达{ex_count}个，情绪表达廉价化",
                    "severity": "low",
                })

        # 5. 逗号链：单句>8逗号
        for sentence in re.split(r"[。！？!?；\n]", content):
            if sentence.count("，") + sentence.count(",") > 8:
                issues.append({
                    "type": "节奏",
                    "description": "存在单句超过8个逗号的长句，建议断句",
                    "severity": "low",
                })

        # 6. 句群波形：连续10句长度近似
        sentences = [s for s in re.split(r"[。！？!?；\n]", content) if len(s.strip()) > 4]
        if len(sentences) >= 10:
            similar = 0
            for i in range(1, len(sentences)):
                if abs(len(sentences[i]) - len(sentences[i - 1])) <= 3:
                    similar += 1
            if similar >= len(sentences) - 2:
                issues.append({
                    "type": "节奏",
                    "description": "句群长度高度雷同（连续10句近乎等长），缺乏长短句交替",
                    "severity": "medium",
                })

        # 7. 数据锚点：虚数夸张
        vague_numbers = ["数万人", "无数人", "不计其数", "漫山遍野", "铺天盖地", "一眼望不到头"]
        vague_hits = [w for w in vague_numbers if w in content]
        if vague_hits:
            issues.append({
                "type": "文笔",
                "description": f"数据锚点模糊：{'、'.join(vague_hits[:3])}，建议给具体数字增强真实感",
                "severity": "low",
            })

        return issues
    
    def _identify_issues(self, content: str, story_bible: dict = None) -> list:
        """识别问题"""
        issues = []
        
        # 节奏问题
        paragraphs = [p for p in content.split("\n") if p.strip()]
        if len(paragraphs) > 30:
            issues.append({
                "type": "节奏",
                "description": "段落过多，节奏可能拖沓",
                "severity": "medium",
            })
        
        # 对话比例
        dialogue_count = content.count('"') + content.count('"')
        total_chars = len(content) if content else 1
        dialogue_ratio = dialogue_count / total_chars
        
        if dialogue_ratio < 0.1:
            issues.append({
                "type": "对话",
                "description": "对话过少，可能缺乏互动",
                "severity": "low",
            })
        elif dialogue_ratio > 0.5:
            issues.append({
                "type": "对话",
                "description": "对话过多，可能缺乏描写",
                "severity": "low",
            })
        
        # 爽点不足
        satisfaction_keywords = ["震惊", "不敢相信", "逆袭", "打脸", "碾压", "爽"]
        if not any(kw in content for kw in satisfaction_keywords):
            issues.append({
                "type": "爽点",
                "description": "本章缺乏明显爽点",
                "severity": "medium",
            })
        
        # 检查常见错误
        error_patterns = ["突然", "莫名其妙", "不合逻辑"]
        for pattern in error_patterns:
            if pattern in content:
                issues.append({
                    "type": "逻辑",
                    "description": f"检测到'{pattern}'，可能存在逻辑问题",
                    "severity": "low",
                })
        
        return issues
    
    def _generate_suggestions(self, content: str, issues: list) -> list:
        """生成改进建议"""
        suggestions = []
        
        for issue in issues:
            if issue["type"] == "节奏":
                suggestions.append("减少不必要的描写，加快节奏")
            elif issue["type"] == "对话":
                suggestions.append("增加角色互动对话")
            elif issue["type"] == "爽点":
                suggestions.append("在关键节点设置爽点或冲突")
            elif issue["type"] == "逻辑":
                suggestions.append("检查情节逻辑，确保合理")
        
        # 通用建议
        if len(content) < 1500:
            suggestions.append("内容偏少，可以增加细节描写")
        
        return suggestions
    
    def _suggest_prompt_modifications(self, result: CritiqueResult) -> list:
        """建议Prompt修改"""
        modifications = []
        
        for issue in result.issues:
            if issue["type"] == "节奏" and issue["severity"] == "medium":
                modifications.append({
                    "target": "writer",
                    "modification": "注意控制节奏，避免过多心理描写，多用动作和对话推进剧情",
                    "reason": "节奏拖沓",
                })
            
            elif issue["type"] == "爽点":
                modifications.append({
                    "target": "writer",
                    "modification": "每章必须包含至少一个爽点或冲突，放在章节中后段",
                    "reason": "爽点不足",
                })
            
            elif issue["type"] == "对话":
                modifications.append({
                    "target": "writer",
                    "modification": "增加角色对话比例，对话要简洁有力，体现人物性格",
                    "reason": "对话不足",
                })
        
        return modifications
    
    def apply_prompt_evolution(self, evolution: PromptEvolution) -> str:
        """应用Prompt进化"""
        print(f"[评论家] 应用Prompt修改: {evolution.target_agent}")
        
        evolution.applied = True
        self.prompt_evolutions.append(evolution)
        
        return evolution.modified_prompt
    
    def get_evolution_summary(self) -> dict:
        """获取进化摘要"""
        return {
            "total_critiques": len(self.critique_history),
            "avg_score": sum(c.overall_score for c in self.critique_history) / len(self.critique_history) if self.critique_history else 0,
            "total_modifications": len(self.prompt_evolutions),
            "applied_modifications": len([e for e in self.prompt_evolutions if e.applied]),
        }
    
    def generate_critique_report(self) -> str:
        """生成批评报告"""
        if not self.critique_history:
            return "暂无批评记录"
        
        report_parts = []
        report_parts.append("=" * 50)
        report_parts.append("批评报告")
        report_parts.append("=" * 50)
        
        # 整体统计
        avg_score = sum(c.overall_score for c in self.critique_history) / len(self.critique_history)
        report_parts.append(f"\n平均评分: {avg_score:.1f}/10")
        report_parts.append(f"总章节数: {len(self.critique_history)}")
        
        # 问题统计
        all_issues = []
        for critique in self.critique_history:
            all_issues.extend(critique.issues)
        
        if all_issues:
            report_parts.append("\n常见问题:")
            issue_types = {}
            for issue in all_issues:
                issue_type = issue["type"]
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
                report_parts.append(f"  - {issue_type}: {count}次")
        
        # Prompt进化记录
        if self.prompt_evolutions:
            report_parts.append("\nPrompt进化记录:")
            for evo in self.prompt_evolutions[-5:]:  # 最近5条
                status = "已应用" if evo.applied else "待应用"
                report_parts.append(f"  - {evo.target_agent}: {evo.reason} [{status}]")
        
        return "\n".join(report_parts)