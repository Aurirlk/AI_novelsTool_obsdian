"""
心理维度表与情感案例库
管理人物性格多维数值和情感表达模式
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class PsychologicalProfile:
    """心理档案"""
    character_id: str
    
    # 心理维度（0-10）
    hostility: float = 5.0      # 对主角的敌意
    conviction: float = 5.0     # 对自身信念的坚守
    empathy: float = 5.0        # 对他人痛苦的共情
    rationality: float = 5.0    # 理智程度
    inner_conflict: float = 5.0 # 内心矛盾感
    
    # 核心气质（相对固定）
    temperament: str = "中性"    # 阴险/豪爽/冷静/热血等
    expression_style: str = "正常"  # 内敛/张扬/沉默等
    
    # 转变阶段
    current_stage: str = "初始"  # 初始/动摇/挣扎/接纳/完成
    target_stage: str = ""       # 目标阶段
    
    # 变化限制
    max_change_per_event: float = 2.0  # 单次事件最大变化
    
    # 历史记录
    change_history: list = field(default_factory=list)
    
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EmotionCase:
    """情感案例"""
    id: str
    emotion_type: str  # 悲伤/愤怒/喜悦/恐惧/感动等
    intensity: int     # 强度 1-10
    
    # 场景描述
    situation: str
    trigger: str
    
    # 表达方式
    physical_reaction: str = ""  # 身体反应
    verbal_expression: str = ""  # 语言表达
    inner_thought: str = ""      # 内心活动
    
    # 适用角色类型
    suitable_characters: list = field(default_factory=list)
    
    # 来源
    source: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PsychologyManager:
    """心理与情感管理器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, "psychology")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.profiles: dict[str, PsychologicalProfile] = {}
        self.emotion_cases: dict[str, EmotionCase] = {}
        
        self._load_all()
    
    # ==================== 心理档案管理 ====================
    
    def add_profile(self, profile: PsychologicalProfile):
        """添加心理档案"""
        self.profiles[profile.character_id] = profile
        self._save_profiles()
    
    def update_dimension(self, character_id: str, dimension: str, 
                         change: float, reason: str = "") -> tuple[bool, str]:
        """更新心理维度"""
        profile = self.profiles.get(character_id)
        if not profile:
            return False, "角色心理档案不存在"
        
        # 检查变化幅度
        if abs(change) > profile.max_change_per_event:
            return False, f"变化幅度 {abs(change)} 超过限制 {profile.max_change_per_event}"
        
        # 获取当前值
        current_value = getattr(profile, dimension, None)
        if current_value is None:
            return False, f"维度 {dimension} 不存在"
        
        # 计算新值（限制在0-10范围内）
        new_value = max(0, min(10, current_value + change))
        
        # 记录变化
        change_record = {
            "dimension": dimension,
            "old_value": current_value,
            "new_value": new_value,
            "change": change,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }
        profile.change_history.append(change_record)
        
        # 更新值
        setattr(profile, dimension, new_value)
        profile.updated_at = datetime.now().isoformat()
        
        self._save_profiles()
        return True, f"{dimension}: {current_value} -> {new_value}"
    
    def advance_stage(self, character_id: str, new_stage: str) -> tuple[bool, str]:
        """推进转变阶段"""
        profile = self.profiles.get(character_id)
        if not profile:
            return False, "角色心理档案不存在"
        
        old_stage = profile.current_stage
        profile.current_stage = new_stage
        profile.updated_at = datetime.now().isoformat()
        
        self._save_profiles()
        return True, f"阶段: {old_stage} -> {new_stage}"
    
    def get_character_state(self, character_id: str) -> dict:
        """获取角色心理状态"""
        profile = self.profiles.get(character_id)
        if not profile:
            return {}
        
        return {
            "hostility": profile.hostility,
            "conviction": profile.conviction,
            "empathy": profile.empathy,
            "rationality": profile.rationality,
            "inner_conflict": profile.inner_conflict,
            "stage": profile.current_stage,
            "temperament": profile.temperament,
        }
    
    # ==================== 情感案例管理 ====================
    
    def add_emotion_case(self, case: EmotionCase):
        """添加情感案例"""
        self.emotion_cases[case.id] = case
        self._save_emotion_cases()
    
    def get_cases_by_emotion(self, emotion_type: str) -> list[EmotionCase]:
        """按情感类型获取案例"""
        return [c for c in self.emotion_cases.values() if c.emotion_type == emotion_type]
    
    def get_suitable_cases(self, character_type: str, emotion_type: str) -> list[EmotionCase]:
        """获取适合某类角色的情感案例"""
        return [c for c in self.emotion_cases.values()
                if c.emotion_type == emotion_type
                and (not c.suitable_characters or character_type in c.suitable_characters)]
    
    # ==================== 上下文生成 ====================
    
    def generate_psychology_context(self, character_id: str) -> str:
        """生成心理上下文"""
        profile = self.profiles.get(character_id)
        if not profile:
            return ""
        
        parts = []
        parts.append(f"【心理状态】阶段={profile.current_stage}, 气质={profile.temperament}")
        parts.append(f"- 敌意: {profile.hostility}/10")
        parts.append(f"- 信念: {profile.conviction}/10")
        parts.append(f"- 共情: {profile.empathy}/10")
        parts.append(f"- 理智: {profile.rationality}/10")
        parts.append(f"- 矛盾: {profile.inner_conflict}/10")
        
        return "\n".join(parts)
    
    def generate_emotion_guidance(self, character_id: str, emotion_type: str) -> str:
        """生成情感表达指导"""
        profile = self.profiles.get(character_id)
        cases = self.get_suitable_cases(profile.temperament if profile else "", emotion_type)
        
        if not cases:
            return f"请自然地表达{emotion_type}的情感"
        
        case = cases[0]
        guidance = f"【{emotion_type}表达参考】"
        guidance += f"\n场景：{case.situation}"
        guidance += f"\n触发：{case.trigger}"
        if case.physical_reaction:
            guidance += f"\n身体反应：{case.physical_reaction}"
        if case.verbal_expression:
            guidance += f"\n语言表达：{case.verbal_expression}"
        if case.inner_thought:
            guidance += f"\n内心活动：{case.inner_thought}"
        
        return guidance
    
    # ==================== 持久化 ====================
    
    def _load_all(self):
        self._load_profiles()
        self._load_emotion_cases()
    
    def _load_profiles(self):
        filepath = os.path.join(self.data_dir, "profiles.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for char_id, profile_data in data.items():
                    self.profiles[char_id] = PsychologicalProfile(**profile_data)
    
    def _load_emotion_cases(self):
        filepath = os.path.join(self.data_dir, "emotion_cases.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for case_id, case_data in data.items():
                    self.emotion_cases[case_id] = EmotionCase(**case_data)
    
    def _save_profiles(self):
        filepath = os.path.join(self.data_dir, "profiles.json")
        data = {char_id: asdict(profile) for char_id, profile in self.profiles.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_emotion_cases(self):
        filepath = os.path.join(self.data_dir, "emotion_cases.json")
        data = {case_id: asdict(case) for case_id, case in self.emotion_cases.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_all(self):
        self._save_profiles()
        self._save_emotion_cases()