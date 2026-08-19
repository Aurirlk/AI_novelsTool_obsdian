"""
拆书/仿写模块
分析网文结构、情绪、人物，提取写作模式
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class ChapterAnalysis:
    """章节分析"""
    chapter_num: int
    word_count: int = 0
    
    # 结构分析
    structure: dict = field(default_factory=lambda: {
        "opening_hook": "",  # 开头钩子
        "conflict_point": 0,  # 冲突点位置（段落数）
        "climax_point": 0,   # 高潮点位置
        "ending_hook": "",   # 结尾钩子
    })
    
    # 情绪分析
    emotions: list = field(default_factory=list)  # ["憋屈", "爽", "紧张"]
    emotion_flow: list = field(default_factory=list)  # 情绪变化曲线
    
    # 人物分析
    characters_appeared: list = field(default_factory=list)
    character_actions: dict = field(default_factory=dict)  # {角色: [行为]}
    
    # 技法分析
    techniques: list = field(default_factory=list)  # ["打脸", "扮猪吃虎", "逆袭"]
    
    # 爽点分析
    satisfaction_points: list = field(default_factory=list)
    satisfaction_level: int = 5  # 1-10


@dataclass
class BookAnalysis:
    """书籍分析结果"""
    title: str
    author: str = ""
    genre: str = ""
    
    # 基础统计
    total_chapters: int = 0
    total_words: int = 0
    avg_words_per_chapter: int = 0
    
    # 结构模式
    structure_pattern: str = ""  # 黄金三章、起承转合等
    pacing: dict = field(default_factory=dict)  # 节奏分布
    
    # 人物模式
    character_archetypes: list = field(default_factory=list)  # 角色原型
    character_relations: list = field(default_factory=list)
    
    # 爽点模式
    satisfaction_patterns: list = field(default_factory=list)
    hook_patterns: list = field(default_factory=list)
    
    # 写作风格
    writing_style: dict = field(default_factory=dict)
    
    # 章节分析
    chapter_analyses: list = field(default_factory=list)
    
    # 总结
    key_takeaways: list = field(default_factory=list)
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class BookAnalyzer:
    """拆书分析器"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    def analyze_book(self, title: str, chapters: list[dict], 
                     author: str = "", genre: str = "") -> BookAnalysis:
        """
        分析整本书
        
        Args:
            title: 书名
            chapters: 章节内容列表 [{"number": 1, "content": "..."}]
            author: 作者
            genre: 题材
        
        Returns:
            分析结果
        """
        print(f"[拆书] 开始分析: {title}")
        
        analysis = BookAnalysis(
            title=title,
            author=author,
            genre=genre,
            total_chapters=len(chapters),
        )
        
        # 统计字数
        total_words = sum(len(c.get("content", "")) for c in chapters)
        analysis.total_words = total_words
        analysis.avg_words_per_chapter = total_words // len(chapters) if chapters else 0
        
        # 逐章分析
        for chapter in chapters:
            chapter_analysis = self._analyze_chapter(chapter)
            analysis.chapter_analyses.append(chapter_analysis)
        
        # 分析结构模式
        analysis.structure_pattern = self._analyze_structure_pattern(analysis)
        
        # 分析人物原型
        analysis.character_archetypes = self._analyze_character_archetypes(analysis)
        
        # 分析爽点模式
        analysis.satisfaction_patterns = self._analyze_satisfaction_patterns(analysis)
        
        # 分析钩子模式
        analysis.hook_patterns = self._analyze_hook_patterns(analysis)
        
        # 分析写作风格
        analysis.writing_style = self._analyze_writing_style(chapters)
        
        # 生成关键要点
        analysis.key_takeaways = self._generate_key_takeaways(analysis)
        
        print(f"[拆书] 分析完成: {title}")
        return analysis
    
    def _analyze_chapter(self, chapter: dict) -> ChapterAnalysis:
        """分析单个章节"""
        content = chapter.get("content", "")
        chapter_num = chapter.get("number", 0)
        
        analysis = ChapterAnalysis(
            chapter_num=chapter_num,
            word_count=len(content),
        )
        
        if not content:
            return analysis
        
        # 基础分析（不调用LLM）
        paragraphs = content.split("\n")
        non_empty = [p for p in paragraphs if p.strip()]
        
        # 分析开头和结尾
        if non_empty:
            analysis.structure["opening_hook"] = non_empty[0][:100]
            analysis.structure["ending_hook"] = non_empty[-1][:100]
        
        # 估算冲突点（段落中间位置）
        analysis.structure["conflict_point"] = len(non_empty) // 2
        
        # 检测常见爽点关键词
        satisfaction_keywords = ["打脸", "逆袭", "碾压", "震惊", "不敢相信", "跪下", "求饶"]
        for keyword in satisfaction_keywords:
            if keyword in content:
                analysis.satisfaction_points.append(keyword)
        
        if analysis.satisfaction_points:
            analysis.satisfaction_level = min(10, 5 + len(analysis.satisfaction_points))
        
        # 检测情绪关键词
        emotion_keywords = {
            "紧张": ["紧张", "危险", "生死", "千钧一发"],
            "爽": ["爽", "痛快", "解气", "大快人心"],
            "憋屈": ["憋屈", "愤怒", "不甘", "忍耐"],
            "感动": ["感动", "泪目", "温暖", "友情"],
        }
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    analysis.emotions.append(emotion)
                    break
        
        return analysis
    
    def _analyze_structure_pattern(self, analysis: BookAnalysis) -> str:
        """分析结构模式"""
        if analysis.total_chapters >= 3:
            # 检查黄金三章
            first_three = analysis.chapter_analyses[:3]
            if all(a.satisfaction_level >= 5 for a in first_three):
                return "黄金三章（前三章爽点密集）"
        
        if analysis.total_chapters >= 4:
            # 检查起承转合
            return "起承转合结构"
        
        return "标准网文结构"
    
    def _analyze_character_archetypes(self, analysis: BookAnalysis) -> list:
        """分析人物原型"""
        archetypes = []
        
        # 统计所有出场角色
        all_characters = []
        for chapter in analysis.chapter_analyses:
            all_characters.extend(chapter.characters_appeared)
        
        # 简单的原型识别
        if any("主角" in c or "少年" in c for c in all_characters):
            archetypes.append("成长型主角")
        
        if any("反派" in c or "BOSS" in c for c in all_characters):
            archetypes.append("阶段性反派")
        
        return archetypes if archetypes else ["标准网文人物配置"]
    
    def _analyze_satisfaction_patterns(self, analysis: BookAnalysis) -> list:
        """分析爽点模式"""
        patterns = []
        
        # 统计所有爽点
        all_points = []
        for chapter in analysis.chapter_analyses:
            all_points.extend(chapter.satisfaction_points)
        
        # 识别模式
        if "打脸" in all_points:
            patterns.append("打脸模式（先被轻视后逆袭）")
        if "逆袭" in all_points:
            patterns.append("逆袭模式（弱者变强）")
        if "碾压" in all_points:
            patterns.append("碾压模式（实力碾压对手）")
        
        return patterns if patterns else ["标准爽点模式"]
    
    def _analyze_hook_patterns(self, analysis: BookAnalysis) -> list:
        """分析钩子模式"""
        patterns = []
        
        for chapter in analysis.chapter_analyses:
            if chapter.structure.get("ending_hook"):
                patterns.append(f"第{chapter.chapter_num}章结尾钩子")
        
        return patterns[:5] if patterns else ["章末悬念"]
    
    def _analyze_writing_style(self, chapters: list[dict]) -> dict:
        """分析写作风格"""
        if not chapters:
            return {}
        
        all_content = " ".join(c.get("content", "") for c in chapters[:5])  # 取前5章
        
        style = {
            "avg_sentence_length": 0,
            "dialogue_ratio": 0,
            "description_density": "中等",
            "pacing": "中等",
        }
        
        # 计算平均句长
        sentences = all_content.split("。")
        if sentences:
            style["avg_sentence_length"] = sum(len(s) for s in sentences) // len(sentences)
        
        # 计算对话比例
        dialogue_count = all_content.count('"') + all_content.count('"')
        total_chars = len(all_content) if all_content else 1
        style["dialogue_ratio"] = dialogue_count / total_chars * 100
        
        return style
    
    def _generate_key_takeaways(self, analysis: BookAnalysis) -> list:
        """生成关键要点"""
        takeaways = []
        
        takeaways.append(f"全书{analysis.total_chapters}章，共{analysis.total_words}字")
        takeaways.append(f"平均每章{analysis.avg_words_per_chapter}字")
        
        if analysis.structure_pattern:
            takeaways.append(f"结构模式：{analysis.structure_pattern}")
        
        if analysis.satisfaction_patterns:
            takeaways.append(f"主要爽点：{analysis.satisfaction_patterns[0]}")
        
        return takeaways
    
    def generate_imitation_prompt(self, analysis: BookAnalysis) -> str:
        """生成仿写Prompt"""
        prompt = f"""请模仿以下风格写作：

【书籍信息】
书名：{analysis.title}
题材：{analysis.genre}
结构：{analysis.structure_pattern}

【写作风格要求】
- 平均句长：约{analysis.writing_style.get('avg_sentence_length', 30)}字
- 对话比例：{analysis.writing_style.get('dialogue_ratio', 20):.1f}%
- 节奏：{analysis.writing_style.get('pacing', '中等')}

【爽点模式】
"""
        for pattern in analysis.satisfaction_patterns:
            prompt += f"- {pattern}\n"
        
        prompt += """
【人物设定】
"""
        for archetype in analysis.character_archetypes:
            prompt += f"- {archetype}\n"
        
        return prompt
    
    def save_analysis(self, analysis: BookAnalysis, filepath: str):
        """保存分析结果"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(analysis), f, ensure_ascii=False, indent=2)
        
        print(f"[拆书] 分析结果已保存: {filepath}")
    
    def load_analysis(self, filepath: str) -> Optional[BookAnalysis]:
        """加载分析结果"""
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return BookAnalysis(**data)


# ==================== 网文模式库 ====================

class NovelPatterns:
    """网文常见模式库"""
    
    STRUCTURE_PATTERNS = {
        "黄金三章": {
            "description": "前三章必须抓人，每章一个爽点",
            "chapters": 3,
            "requirements": ["引入主角", "展示金手指", "第一个冲突", "第一次爽点"],
        },
        "起承转合": {
            "description": "经典四段式结构",
            "phases": ["起（引入）", "承（发展）", "转（高潮）", "合（结局）"],
        },
        "副本循环": {
            "description": "进入副本→获得机缘→打败BOSS→离开副本",
            "cycle_length": 20,  # 约20章一个副本
        },
    }
    
    SATISFACTION_PATTERNS = {
        "打脸": {
            "description": "被轻视→展示实力→震惊众人",
            "keywords": ["嘲笑", "不屑", "震惊", "不敢相信"],
        },
        "逆袭": {
            "description": "弱者→获得机缘→变强→复仇",
            "keywords": ["废物", "觉醒", "突破", "复仇"],
        },
        "碾压": {
            "description": "实力远超对手，轻松获胜",
            "keywords": ["秒杀", "一招", "碾压", "不配"],
        },
        "扮猪吃虎": {
            "description": "隐藏实力→被小看→暴露实力→震惊",
            "keywords": ["隐藏", "伪装", "真面目", "竟然"],
        },
    }
    
    CHARACTER_ARCHETYPES = {
        "主角": ["废柴逆袭", "天才成长", "重生复仇", "穿越者"],
        "女主": ["青梅竹马", "冰山美人", "活泼少女", "御姐"],
        "反派": ["纨绔子弟", "阴险小人", "强大BOSS", "宿敌"],
        "配角": ["忠诚兄弟", "智慧导师", "搞笑担当", "忠犬"],
    }
    
    HOOK_PATTERNS = {
        "悬念钩子": "本章结尾留下未解之谜",
        "危机钩子": "本章结尾主角陷入危险",
        "期待钩子": "本章结尾预告下章精彩内容",
        "反转钩子": "本章结尾出现意想不到的反转",
    }