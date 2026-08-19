"""
实体词典
管理物品、地点、招式的统一名称和描述
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Entity:
    """实体基类"""
    id: str
    name: str
    entity_type: str  # item/location/skill/faction
    description: str = ""
    
    # 属性
    attributes: dict = field(default_factory=dict)
    
    # 关联
    related_entities: list = field(default_factory=list)
    
    # 状态
    is_active: bool = True
    first_appearance: int = 0
    last_appearance: int = 0
    
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Item(Entity):
    """物品"""
    item_type: str = ""  # 武器/防具/丹药/法宝
    quality: str = ""    # 凡品/灵品/仙品
    owner: str = ""      # 当前持有者
    location: str = ""   # 当前位置
    
    # 属性
    attack_power: int = 0
    defense: int = 0
    special_effect: str = ""


@dataclass
class Location(Entity):
    """地点"""
    location_type: str = ""  # 城市/秘境/宗门
    level: int = 0           # 等级要求
    danger_level: int = 1    # 危险等级 1-10
    
    # 连接
    connected_locations: list = field(default_factory=list)
    
    # 特殊规则
    rules: list = field(default_factory=list)  # 如 ["禁魔", "时间流速x2"]


@dataclass
class Skill(Entity):
    """技能/招式"""
    skill_type: str = ""     # 攻击/防御/辅助
    power_level: int = 1     # 威力等级
    
    # 使用限制
    cooldown: int = 0        # 冷却回合数
    mana_cost: int = 0       # 灵力消耗
    max_uses: int = -1       # 最大使用次数（-1为无限）
    
    # 当前状态
    current_cooldown: int = 0
    remaining_uses: int = -1


class EntityDictionary:
    """实体词典管理器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, "entities")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 按类型存储
        self.items: dict[str, Item] = {}
        self.locations: dict[str, Location] = {}
        self.skills: dict[str, Skill] = {}
        
        self._load_all()
    
    # ==================== 物品管理 ====================
    
    def add_item(self, item: Item):
        """添加物品"""
        self.items[item.id] = item
        self._save_items()
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """获取物品"""
        return self.items.get(item_id)
    
    def update_item(self, item_id: str, **kwargs):
        """更新物品"""
        if item_id in self.items:
            for key, value in kwargs.items():
                if hasattr(self.items[item_id], key):
                    setattr(self.items[item_id], key, value)
            self.items[item_id].updated_at = datetime.now().isoformat()
            self._save_items()
    
    def transfer_item(self, item_id: str, new_owner: str, chapter_num: int):
        """转移物品所有权"""
        item = self.items.get(item_id)
        if item:
            old_owner = item.owner
            item.owner = new_owner
            item.last_appearance = chapter_num
            item.updated_at = datetime.now().isoformat()
            self._save_items()
            return f"{item.name} 从 {old_owner} 转移到 {new_owner}"
        return None
    
    def check_item_consistency(self, item_id: str, claimed_owner: str) -> tuple[bool, str]:
        """检查物品一致性"""
        item = self.items.get(item_id)
        if not item:
            return True, "物品不存在"
        
        if item.owner and item.owner != claimed_owner:
            return False, f"{item.name} 当前属于 {item.owner}，不是 {claimed_owner}"
        
        return True, "通过"
    
    # ==================== 地点管理 ====================
    
    def add_location(self, location: Location):
        """添加地点"""
        self.locations[location.id] = location
        self._save_locations()
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """获取地点"""
        return self.locations.get(location_id)
    
    def check_location_rules(self, location_id: str, action: str) -> tuple[bool, str]:
        """检查地点规则"""
        location = self.locations.get(location_id)
        if not location:
            return True, "地点不存在"
        
        for rule in location.rules:
            if action in rule.lower():
                return False, f"在 {location.name} 中 {rule}"
        
        return True, "通过"
    
    # ==================== 技能管理 ====================
    
    def add_skill(self, skill: Skill):
        """添加技能"""
        self.skills[skill.id] = skill
        self._save_skills()
    
    def use_skill(self, skill_id: str, chapter_num: int) -> tuple[bool, str]:
        """使用技能"""
        skill = self.skills.get(skill_id)
        if not skill:
            return False, "技能不存在"
        
        # 检查冷却
        if skill.current_cooldown > 0:
            return False, f"{skill.name} 冷却中，还需 {skill.current_cooldown} 回合"
        
        # 检查使用次数
        if skill.remaining_uses == 0:
            return False, f"{skill.name} 使用次数已耗尽"
        
        # 执行使用
        skill.current_cooldown = skill.cooldown
        if skill.remaining_uses > 0:
            skill.remaining_uses -= 1
        
        self._save_skills()
        return True, f"{skill.name} 使用成功"
    
    def reduce_cooldowns(self, chapters: int = 1):
        """减少冷却时间"""
        for skill in self.skills.values():
            if skill.current_cooldown > 0:
                skill.current_cooldown = max(0, skill.current_cooldown - chapters)
        self._save_skills()
    
    # ==================== 一致性检查 ====================
    
    def check_all_consistency(self, chapter_entities: list[dict]) -> list[dict]:
        """检查所有实体一致性"""
        issues = []
        
        for entity in chapter_entities:
            entity_id = entity.get("id")
            entity_type = entity.get("type")
            claimed_owner = entity.get("owner")
            location = entity.get("location")
            
            if entity_type == "item" and claimed_owner:
                consistent, msg = self.check_item_consistency(entity_id, claimed_owner)
                if not consistent:
                    issues.append({"type": "物品一致性", "entity": entity_id, "issue": msg})
            
            if entity_type == "location":
                consistent, msg = self.check_location_rules(entity_id, entity.get("action", ""))
                if not consistent:
                    issues.append({"type": "地点规则", "entity": entity_id, "issue": msg})
        
        return issues
    
    # ==================== 上下文生成 ====================
    
    def generate_entity_context(self, chapter_num: int, involved_entities: list[str] = None) -> str:
        """生成实体上下文"""
        parts = []
        
        # 活跃物品
        active_items = [i for i in self.items.values() if i.is_active and i.owner]
        if active_items:
            parts.append("【重要物品】")
            for item in active_items[:5]:
                parts.append(f"- {item.name}：持有者={item.owner}, 品质={item.quality}")
        
        # 当前地点
        if involved_entities:
            locations = [self.locations[eid] for eid in involved_entities if eid in self.locations]
            if locations:
                parts.append("\n【地点信息】")
                for loc in locations:
                    rules = f", 规则: {', '.join(loc.rules)}" if loc.rules else ""
                    parts.append(f"- {loc.name}：等级={loc.level}, 危险={loc.danger_level}{rules}")
        
        # 可用技能
        available_skills = [s for s in self.skills.values() if s.current_cooldown == 0]
        if available_skills:
            parts.append("\n【可用技能】")
            for skill in available_skills[:3]:
                parts.append(f"- {skill.name}：威力={skill.power_level}")
        
        return "\n".join(parts)
    
    # ==================== 持久化 ====================
    
    def _load_all(self):
        self._load_items()
        self._load_locations()
        self._load_skills()
    
    def _load_items(self):
        filepath = os.path.join(self.data_dir, "items.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item_id, item_data in data.items():
                    self.items[item_id] = Item(**item_data)
    
    def _load_locations(self):
        filepath = os.path.join(self.data_dir, "locations.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for loc_id, loc_data in data.items():
                    self.locations[loc_id] = Location(**loc_data)
    
    def _load_skills(self):
        filepath = os.path.join(self.data_dir, "skills.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for skill_id, skill_data in data.items():
                    self.skills[skill_id] = Skill(**skill_data)
    
    def _save_items(self):
        filepath = os.path.join(self.data_dir, "items.json")
        data = {item_id: asdict(item) for item_id, item in self.items.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_locations(self):
        filepath = os.path.join(self.data_dir, "locations.json")
        data = {loc_id: asdict(loc) for loc_id, loc in self.locations.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_skills(self):
        filepath = os.path.join(self.data_dir, "skills.json")
        data = {skill_id: asdict(skill) for skill_id, skill in self.skills.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_all(self):
        self._save_items()
        self._save_locations()
        self._save_skills()