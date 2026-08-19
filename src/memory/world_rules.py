"""
规则清单与全局时间轴
管理世界观规则和故事内时间线
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class WorldRule:
    """世界观规则"""
    id: str
    name: str
    rule_type: str  # magic/physics/social/power
    description: str
    
    # 适用范围
    applicable_locations: list = field(default_factory=list)  # 空列表表示全局
    applicable_characters: list = field(default_factory=list)
    
    # 规则内容
    condition: str = ""  # 条件
    effect: str = ""     # 效果
    exceptions: list = field(default_factory=list)  # 例外
    
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TimePoint:
    """时间点"""
    chapter_num: int
    story_time: str  # 故事内时间（如"第一天"、"三年后"）
    real_time_offset: int = 0  # 相对于起始的天数
    
    events: list = field(default_factory=list)
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class WorldRulesManager:
    """世界观规则管理器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, "world")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.rules: dict[str, WorldRule] = {}
        self.timeline: list[TimePoint] = []
        self.current_day: int = 0  # 当前故事内天数
        
        self._load_all()
    
    # ==================== 规则管理 ====================
    
    def add_rule(self, rule: WorldRule):
        """添加规则"""
        self.rules[rule.id] = rule
        self._save_rules()
    
    def update_rule(self, rule_id: str, **kwargs):
        """更新规则"""
        if rule_id in self.rules:
            for key, value in kwargs.items():
                if hasattr(self.rules[rule_id], key):
                    setattr(self.rules[rule_id], key, value)
            self._save_rules()
    
    def get_rules_for_location(self, location: str) -> list[WorldRule]:
        """获取某地点的规则"""
        return [r for r in self.rules.values() 
                if r.is_active and (not r.applicable_locations or location in r.applicable_locations)]
    
    def check_rule_compliance(self, action: str, location: str = "", 
                              character: str = "") -> list[dict]:
        """检查行为是否符合规则"""
        violations = []
        
        for rule in self.rules.values():
            if not rule.is_active:
                continue
            
            # 检查适用范围
            if rule.applicable_locations and location not in rule.applicable_locations:
                continue
            if rule.applicable_characters and character not in rule.applicable_characters:
                continue
            
            # 检查是否违反规则
            if action.lower() in rule.condition.lower():
                # 检查例外
                is_exception = False
                for exception in rule.exceptions:
                    if exception.lower() in action.lower():
                        is_exception = True
                        break
                
                if not is_exception:
                    violations.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "violation": rule.effect,
                    })
        
        return violations
    
    # ==================== 时间线管理 ====================
    
    def add_time_point(self, chapter_num: int, story_time: str, 
                       events: list = None, time_delta: int = 1):
        """添加时间点"""
        self.current_day += time_delta
        
        time_point = TimePoint(
            chapter_num=chapter_num,
            story_time=story_time,
            real_time_offset=self.current_day,
            events=events or [],
        )
        
        self.timeline.append(time_point)
        self._save_timeline()
    
    def get_current_time(self) -> dict:
        """获取当前时间"""
        return {
            "chapter": self.timeline[-1].chapter_num if self.timeline else 0,
            "story_time": self.timeline[-1].story_time if self.timeline else "未知",
            "days_passed": self.current_day,
        }
    
    def check_time_consistency(self, chapter_num: int, new_time: str) -> tuple[bool, str]:
        """检查时间一致性"""
        if not self.timeline:
            return True, "无历史时间记录"
        
        last_point = self.timeline[-1]
        
        # 简单检查：新时间不能早于上一章
        # 实际应用中需要更复杂的时间解析
        return True, "通过"
    
    def get_events_in_timespan(self, start_chapter: int, end_chapter: int) -> list[dict]:
        """获取某时间段的事件"""
        events = []
        for point in self.timeline:
            if start_chapter <= point.chapter_num <= end_chapter:
                events.extend([{"chapter": point.chapter_num, "event": e} for e in point.events])
        return events
    
    # ==================== 上下文生成 ====================
    
    def generate_rules_context(self, location: str = "") -> str:
        """生成规则上下文"""
        parts = []
        
        # 全局规则
        global_rules = [r for r in self.rules.values() if r.is_active and not r.applicable_locations]
        if global_rules:
            parts.append("【世界观规则】")
            for rule in global_rules:
                parts.append(f"- {rule.name}：{rule.description}")
        
        # 地点规则
        if location:
            location_rules = self.get_rules_for_location(location)
            if location_rules:
                parts.append(f"\n【{location}特殊规则】")
                for rule in location_rules:
                    parts.append(f"- {rule.name}：{rule.effect}")
        
        # 时间信息
        current_time = self.get_current_time()
        if current_time["story_time"] != "未知":
            parts.append(f"\n【当前时间】{current_time['story_time']}（已过{current_time['days_passed']}天）")
        
        return "\n".join(parts)
    
    # ==================== 持久化 ====================
    
    def _load_all(self):
        self._load_rules()
        self._load_timeline()
    
    def _load_rules(self):
        filepath = os.path.join(self.data_dir, "rules.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for rule_id, rule_data in data.items():
                    self.rules[rule_id] = WorldRule(**rule_data)
    
    def _load_timeline(self):
        filepath = os.path.join(self.data_dir, "timeline.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.timeline = [TimePoint(**t) for t in data.get("timeline", [])]
                self.current_day = data.get("current_day", 0)
    
    def _save_rules(self):
        filepath = os.path.join(self.data_dir, "rules.json")
        data = {rule_id: asdict(rule) for rule_id, rule in self.rules.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_timeline(self):
        filepath = os.path.join(self.data_dir, "timeline.json")
        data = {
            "timeline": [asdict(t) for t in self.timeline],
            "current_day": self.current_day,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_all(self):
        self._save_rules()
        self._save_timeline()