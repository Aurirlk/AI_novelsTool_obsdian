"""
意图识别器
识别用户的意图，决定智能体应该执行什么任务
"""

from enum import Enum
from typing import Optional, List, Dict, Tuple
import re


class Intent(Enum):
    """意图类型"""
    # 生成模式
    GENERATE_OUTLINE = "generate_outline"      # 生成大纲
    GENERATE_CHAPTER = "generate_chapter"      # 生成章节
    GENERATE_CHARACTER = "generate_character"  # 生成角色
    
    # 批评模式
    CRITIQUE_OUTLINE = "critique_outline"      # 批评大纲
    CRITIQUE_CHAPTER = "critique_chapter"      # 批评章节
    CRITIQUE_CHARACTER = "critique_character"  # 批评角色
    
    # 素材模式
    PROVIDE_MATERIAL = "provide_material"      # 提供素材
    PROVIDE_INSPIRATION = "provide_inspiration"  # 提供灵感
    PROVIDE_REFERENCE = "provide_reference"    # 提供参考
    
    # 陪练模式
    FIND_BLIND_SPOTS = "find_blind_spots"      # 发现盲点
    FIND_LIMITATIONS = "find_limitations"      # 发现局限
    SUGGEST_IMPROVEMENTS = "suggest_improvements"  # 建议改进
    
    # 知识库模式
    CHECK_KNOWLEDGE = "check_knowledge"        # 检查知识
    QUERY_KNOWLEDGE = "query_knowledge"        # 查询知识
    
    # 未知
    UNKNOWN = "unknown"


class IntentRecognizer:
    """意图识别器"""
    
    # 批评模式关键词
    CRITIQUE_KEYWORDS = [
        "看看", "检查", "批评", "审核", "找问题", "找漏洞", "诊断",
        "分析", "评价", "评估", "审查", "挑错", "找错", "发现",
        "有没有问题", "是否合理", "是否正确", "是否合适",
    ]
    
    # 生成模式关键词
    GENERATE_KEYWORDS = [
        "写", "生成", "创作", "帮我写", "帮我生成", "帮我创作",
        "写一个", "生成一个", "创作一个", "写一篇", "生成一篇",
        "写一章", "生成一章", "写大纲", "生成大纲",
    ]
    
    # 素材模式关键词
    MATERIAL_KEYWORDS = [
        "素材", "参考", "灵感", "建议", "提供", "给我",
        "推荐", "举例", "示例", "例子", "模板",
    ]
    
    # 陪练模式关键词
    COACH_KEYWORDS = [
        "陪练", "指导", "辅导", "提升", "改进", "提高",
        "怎么写", "如何写", "写作技巧", "写作方法",
        "我的不足", "我的问题", "我的局限",
    ]
    
    # 知识库关键词
    KNOWLEDGE_KEYWORDS = [
        "知识", "常识", "历史", "地理", "科学", "查询",
        "是否正确", "是否准确", "是否真实",
    ]
    
    # 大纲相关关键词
    OUTLINE_KEYWORDS = [
        "大纲", "细纲", "故事线", "剧情", "主线", "支线",
    ]
    
    # 章节相关关键词
    CHAPTER_KEYWORDS = [
        "章节", "一章", "这一章", "那章", "第几章",
    ]
    
    # 角色相关关键词
    CHARACTER_KEYWORDS = [
        "角色", "人物", "主角", "配角", "反派", "龙套",
    ]
    
    def recognize(self, user_input: str, context: Optional[Dict] = None) -> Tuple[Intent, Dict]:
        """
        识别用户意图
        
        Args:
            user_input: 用户输入
            context: 上下文信息
        
        Returns:
            (意图, 参数)
        """
        text = user_input.lower().strip()
        
        # 识别动作类型
        action_type = self._recognize_action_type(text)
        
        # 识别对象类型
        object_type = self._recognize_object_type(text)
        
        # 组合意图
        intent = self._combine_intent(action_type, object_type)
        
        # 提取参数
        params = self._extract_params(text, context)
        
        return intent, params
    
    def _recognize_action_type(self, text: str) -> str:
        """识别动作类型"""
        # 批评模式
        for keyword in self.CRITIQUE_KEYWORDS:
            if keyword in text:
                return "critique"
        
        # 生成模式
        for keyword in self.GENERATE_KEYWORDS:
            if keyword in text:
                return "generate"
        
        # 素材模式
        for keyword in self.MATERIAL_KEYWORDS:
            if keyword in text:
                return "material"
        
        # 陪练模式
        for keyword in self.COACH_KEYWORDS:
            if keyword in text:
                return "coach"
        
        # 知识库模式
        for keyword in self.KNOWLEDGE_KEYWORDS:
            if keyword in text:
                return "knowledge"
        
        # 默认为生成模式
        return "generate"
    
    def _recognize_object_type(self, text: str) -> str:
        """识别对象类型"""
        # 大纲相关
        for keyword in self.OUTLINE_KEYWORDS:
            if keyword in text:
                return "outline"
        
        # 章节相关
        for keyword in self.CHAPTER_KEYWORDS:
            if keyword in text:
                return "chapter"
        
        # 角色相关
        for keyword in self.CHARACTER_KEYWORDS:
            if keyword in text:
                return "character"
        
        # 默认为大纲
        return "outline"
    
    def _combine_intent(self, action_type: str, object_type: str) -> Intent:
        """组合意图"""
        intent_map = {
            # 生成模式
            ("generate", "outline"): Intent.GENERATE_OUTLINE,
            ("generate", "chapter"): Intent.GENERATE_CHAPTER,
            ("generate", "character"): Intent.GENERATE_CHARACTER,
            
            # 批评模式
            ("critique", "outline"): Intent.CRITIQUE_OUTLINE,
            ("critique", "chapter"): Intent.CRITIQUE_CHAPTER,
            ("critique", "character"): Intent.CRITIQUE_CHARACTER,
            
            # 素材模式
            ("material", "outline"): Intent.PROVIDE_MATERIAL,
            ("material", "chapter"): Intent.PROVIDE_MATERIAL,
            ("material", "character"): Intent.PROVIDE_MATERIAL,
            
            # 陪练模式
            ("coach", "outline"): Intent.FIND_BLIND_SPOTS,
            ("coach", "chapter"): Intent.SUGGEST_IMPROVEMENTS,
            ("coach", "character"): Intent.FIND_LIMITATIONS,
            
            # 知识库模式
            ("knowledge", "outline"): Intent.CHECK_KNOWLEDGE,
            ("knowledge", "chapter"): Intent.CHECK_KNOWLEDGE,
            ("knowledge", "character"): Intent.QUERY_KNOWLEDGE,
        }
        
        return intent_map.get((action_type, object_type), Intent.UNKNOWN)
    
    def _extract_params(self, text: str, context: Optional[Dict] = None) -> Dict:
        """提取参数"""
        params = {}
        
        # 提取章节号
        chapter_match = re.search(r'第(\d+)章', text)
        if chapter_match:
            params['chapter_num'] = int(chapter_match.group(1))
        
        # 提取项目名称
        if context:
            params['project_name'] = context.get('project_name', '未命名项目')
        
        return params
    
    def get_smart_agent(self, intent: Intent) -> str:
        """根据意图选择智能体"""
        agent_map = {
            # 生成模式 → 大纲师/码字工
            Intent.GENERATE_OUTLINE: "outline_agent",
            Intent.GENERATE_CHAPTER: "writer_agent",
            Intent.GENERATE_CHARACTER: "writer_agent",
            
            # 批评模式 → 批评师
            Intent.CRITIQUE_OUTLINE: "outline_critic",
            Intent.CRITIQUE_CHAPTER: "chapter_critic",
            Intent.CRITIQUE_CHARACTER: "chapter_critic",
            
            # 素材模式 → 素材供应商
            Intent.PROVIDE_MATERIAL: "material_supplier",
            Intent.PROVIDE_INSPIRATION: "material_supplier",
            Intent.PROVIDE_REFERENCE: "material_supplier",
            
            # 陪练模式 → 写作陪练
            Intent.FIND_BLIND_SPOTS: "writing_coach",
            Intent.FIND_LIMITATIONS: "writing_coach",
            Intent.SUGGEST_IMPROVEMENTS: "writing_coach",
            
            # 知识库模式 → 知识库检查器
            Intent.CHECK_KNOWLEDGE: "knowledge_checker",
            Intent.QUERY_KNOWLEDGE: "knowledge_checker",
        }
        
        return agent_map.get(intent, "unknown")
    
    def get_response_template(self, intent: Intent) -> str:
        """获取响应模板"""
        templates = {
            Intent.GENERATE_OUTLINE: "正在为您生成大纲...",
            Intent.GENERATE_CHAPTER: "正在为您生成章节...",
            Intent.GENERATE_CHARACTER: "正在为您生成角色...",
            
            Intent.CRITIQUE_OUTLINE: "正在为您批评大纲...",
            Intent.CRITIQUE_CHAPTER: "正在为您批评章节...",
            Intent.CRITIQUE_CHARACTER: "正在为您批评角色...",
            
            Intent.PROVIDE_MATERIAL: "正在为您搜索素材...",
            Intent.PROVIDE_INSPIRATION: "正在为您寻找灵感...",
            Intent.PROVIDE_REFERENCE: "正在为您查找参考...",
            
            Intent.FIND_BLIND_SPOTS: "正在分析您的写作盲点...",
            Intent.FIND_LIMITATIONS: "正在发现您的写作局限...",
            Intent.SUGGEST_IMPROVEMENTS: "正在为您建议改进方向...",
            
            Intent.CHECK_KNOWLEDGE: "正在检查知识准确性...",
            Intent.QUERY_KNOWLEDGE: "正在查询相关知识...",
        }
        
        return templates.get(intent, "正在处理您的请求...")


# 全局实例
_intent_recognizer: Optional[IntentRecognizer] = None


def get_intent_recognizer() -> IntentRecognizer:
    """获取意图识别器单例"""
    global _intent_recognizer
    if _intent_recognizer is None:
        _intent_recognizer = IntentRecognizer()
    return _intent_recognizer
