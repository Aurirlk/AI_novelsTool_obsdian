"""
复盘智能体与读者模拟器
定期总结故事，模拟读者反馈
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ReviewReport:
    """复盘报告"""
    review_type: str  # periodic/milestone/manual
    chapter_range: tuple = (0, 0)
    
    # 故事进展
    plot_progress: str = ""
    character_development: str = ""
    
    # 健康度评估
    hook_health: dict = field(default_factory=dict)  # 钩子健康度
    pacing_score: int = 5  # 节奏评分 1-10
    satisfaction_score: int = 5  # 爽点评分 1-10
    
    # 问题清单
    issues: list = field(default_factory=list)
    
    # 建议
    suggestions: list = field(default_factory=list)
    
    # 后续规划
    next_arc_plan: str = ""
    character_plans: dict = field(default_factory=dict)
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReaderFeedback:
    """读者反馈"""
    chapter_num: int
    
    # 整体评价
    overall_rating: int = 5  # 1-10
    would_continue: bool = True
    
    # 情感反应
    emotions_felt: list = field(default_factory=list)  # ["紧张", "爽", "无聊"]
    
    # 具体反馈
    likes: list = field(default_factory=list)
    dislikes: list = field(default_factory=list)
    
    # 改进建议
    suggestions: list = field(default_factory=list)
    
    # 人物评价
    character_feedback: dict = field(default_factory=dict)  # {角色: 评价}
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ReviewAgent:
    """复盘智能体"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.review_history: list[ReviewReport] = []
    
    def periodic_review(self, chapters: list[dict], 
                        characters: dict, hooks: dict,
                        events: list) -> ReviewReport:
        """定期复盘"""
        print("[复盘智能体] 开始定期复盘...")
        
        report = ReviewReport(
            review_type="periodic",
            chapter_range=(chapters[0]["number"] if chapters else 0,
                          chapters[-1]["number"] if chapters else 0),
        )
        
        # 分析故事进展
        report.plot_progress = self._analyze_plot_progress(chapters)
        report.character_development = self._analyze_character_development(characters, chapters)
        
        # 评估健康度
        report.hook_health = self._evaluate_hook_health(hooks, chapters[-1]["number"] if chapters else 0)
        report.pacing_score = self._evaluate_pacing(chapters)
        report.satisfaction_score = self._evaluate_satisfaction(chapters)
        
        # 识别问题
        report.issues = self._identify_issues(chapters, characters, hooks)
        
        # 生成建议
        report.suggestions = self._generate_suggestions(report)
        
        self.review_history.append(report)
        print(f"[复盘智能体] 复盘完成，评分: 节奏={report.pacing_score}, 爽点={report.satisfaction_score}")
        
        return report
    
    def _analyze_plot_progress(self, chapters: list[dict]) -> str:
        """分析剧情进展"""
        if not chapters:
            return "暂无内容"
        
        total_words = sum(len(c.get("content", "")) for c in chapters)
        return f"已完成{len(chapters)}章，共{total_words}字"
    
    def _analyze_character_development(self, characters: dict, chapters: list[dict]) -> str:
        """分析人物发展"""
        active_chars = []
        for char_id, char in characters.items():
            if char.get("last_active_chapter", 0) >= len(chapters) - 5:
                active_chars.append(char.get("name", char_id))
        
        return f"活跃角色：{', '.join(active_chars) if active_chars else '无'}"
    
    def _evaluate_hook_health(self, hooks: dict, current_chapter: int) -> dict:
        """评估钩子健康度"""
        active_hooks = [h for h in hooks.values() 
                       if h.get("status") not in ["resolved", "forgotten"]]
        
        overdue = [h for h in active_hooks 
                  if h.get("expected_resolve_chapter", 0) < current_chapter - 10]
        
        return {
            "total_active": len(active_hooks),
            "overdue": len(overdue),
            "health_score": max(0, 100 - len(overdue) * 10),
        }
    
    def _evaluate_pacing(self, chapters: list[dict]) -> int:
        """评估节奏"""
        if not chapters:
            return 5
        
        # 简单评估：字数波动
        word_counts = [len(c.get("content", "")) for c in chapters]
        if not word_counts:
            return 5
        
        avg = sum(word_counts) / len(word_counts)
        variance = sum((w - avg) ** 2 for w in word_counts) / len(word_counts)
        
        # 方差越小，节奏越稳定
        if variance < 10000:
            return 8
        elif variance < 50000:
            return 6
        else:
            return 4
    
    def _evaluate_satisfaction(self, chapters: list[dict]) -> int:
        """评估爽点"""
        if not chapters:
            return 5
        
        # 检查爽点关键词
        satisfaction_keywords = ["震惊", "不敢相信", "逆袭", "打脸", "碾压", "爽"]
        count = 0
        for chapter in chapters:
            content = chapter.get("content", "")
            if any(kw in content for kw in satisfaction_keywords):
                count += 1
        
        # 爽点比例
        ratio = count / len(chapters) if chapters else 0
        return min(10, int(5 + ratio * 5))
    
    def _identify_issues(self, chapters: list[dict], characters: dict, hooks: dict) -> list:
        """识别问题"""
        issues = []
        
        # 检查灌水
        for chapter in chapters[-5:]:
            if len(chapter.get("content", "")) < 1000:
                issues.append(f"第{chapter.get('number', 0)}章内容过少，可能灌水")
        
        return issues
    
    def _generate_suggestions(self, report: ReviewReport) -> list:
        """生成建议"""
        suggestions = []
        
        if report.pacing_score < 6:
            suggestions.append("节奏偏慢，建议加快剧情推进")
        
        if report.satisfaction_score < 6:
            suggestions.append("爽点不足，建议增加冲突或反转")
        
        if report.hook_health.get("overdue", 0) > 0:
            suggestions.append(f"有{report.hook_health['overdue']}个钩子逾期，建议尽快回收")
        
        return suggestions


class ReaderSimulator:
    """读者模拟器"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.feedback_history: list[ReaderFeedback] = []
    
    def simulate_feedback(self, chapter_content: str, chapter_num: int,
                          story_context: str = "") -> ReaderFeedback:
        """模拟读者反馈"""
        print(f"[读者模拟器] 评估第{chapter_num}章...")
        
        feedback = ReaderFeedback(chapter_num=chapter_num)
        
        # 分析情感反应
        feedback.emotions_felt = self._analyze_emotions(chapter_content)
        
        # 评估质量
        feedback.overall_rating = self._rate_quality(chapter_content)
        feedback.would_continue = feedback.overall_rating >= 5
        
        # 生成喜好评价
        feedback.likes = self._identify_likes(chapter_content)
        feedback.dislikes = self._identify_dislikes(chapter_content)
        
        # 生成建议
        feedback.suggestions = self._generate_suggestions(feedback)
        
        self.feedback_history.append(feedback)
        print(f"[读者模拟器] 评分: {feedback.overall_rating}/10, 继续阅读: {feedback.would_continue}")
        
        return feedback
    
    def _analyze_emotions(self, content: str) -> list:
        """分析情感反应"""
        emotions = []
        
        emotion_keywords = {
            "紧张": ["危险", "千钧一发", "生死", "紧张"],
            "爽": ["爽", "痛快", "打脸", "逆袭", "碾压"],
            "无聊": ["平淡", "无趣", "拖沓"],
            "感动": ["感动", "泪目", "温暖"],
            "愤怒": ["愤怒", "不甘", "憋屈"],
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(kw in content for kw in keywords):
                emotions.append(emotion)
        
        return emotions if emotions else ["平淡"]
    
    def _rate_quality(self, content: str) -> int:
        """评估质量"""
        score = 5
        
        # 字数
        if len(content) > 2000:
            score += 1
        elif len(content) < 1000:
            score -= 1
        
        # 爽点
        satisfaction_keywords = ["震惊", "不敢相信", "逆袭", "打脸"]
        if any(kw in content for kw in satisfaction_keywords):
            score += 1
        
        # 对话
        dialogue_count = content.count('"') + content.count('"')
        if dialogue_count > 10:
            score += 1
        
        return max(1, min(10, score))
    
    def _identify_likes(self, content: str) -> list:
        """识别喜欢的点"""
        likes = []
        
        if "爽" in content or "痛快" in content:
            likes.append("爽点设计")
        if content.count('"') > 10:
            likes.append("对话精彩")
        if len(content) > 2000:
            likes.append("内容充实")
        
        return likes
    
    def _identify_dislikes(self, content: str) -> list:
        """识别不喜欢的点"""
        dislikes = []
        
        if len(content) < 1000:
            dislikes.append("内容过少")
        if "拖沓" in content or "无聊" in content:
            dislikes.append("节奏拖沓")
        
        return dislikes
    
    def _generate_suggestions(self, feedback: ReaderFeedback) -> list:
        """生成建议"""
        suggestions = []
        
        if feedback.overall_rating < 5:
            suggestions.append("整体质量需要提升")
        
        if "无聊" in feedback.emotions_felt:
            suggestions.append("增加冲突或悬念")
        
        if feedback.dislikes:
            for dislike in feedback.dislikes:
                if "过少" in dislike:
                    suggestions.append("增加内容深度")
                elif "拖沓" in dislike:
                    suggestions.append("加快节奏")
        
        return suggestions
    
    def get_reader_summary(self) -> dict:
        """获取读者反馈摘要"""
        if not self.feedback_history:
            return {}
        
        ratings = [f.overall_rating for f in self.feedback_history]
        
        return {
            "total_reviews": len(self.feedback_history),
            "avg_rating": sum(ratings) / len(ratings),
            "continue_rate": sum(1 for f in self.feedback_history if f.would_continue) / len(self.feedback_history),
        }