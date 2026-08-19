"""
记忆管理系统
管理人物状态、钩子追踪、大事记、人物关系
"""

import os
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class HookStatus(Enum):
    """钩子状态"""
    PLANTED = "planted"          # 已埋下
    DEVELOPING = "developing"    # 发展中
    ABOUT_TO_RESOLVE = "about_to_resolve"  # 即将回收
    RESOLVED = "resolved"        # 已回收
    FORGOTTEN = "forgotten"      # 已遗忘


class CharacterStatus(Enum):
    """角色状态"""
    ALIVE = "alive"
    DEAD = "dead"
    MISSING = "missing"
    INJURED = "injured"


class CharacterLayer(Enum):
    """角色层级"""
    CORE = "core"           # 核心主角团
    ACTIVE = "active"       # 当前活跃
    ARCHIVED = "archived"   # 已归档


@dataclass
class CharacterState:
    """角色状态"""
    id: str
    name: str
    role: str  # 主角/配角/反派/龙套
    layer: str = CharacterLayer.ACTIVE.value
    
    # 基础信息
    personality: str = ""
    background: str = ""
    appearance: str = ""
    
    # 动态状态
    current_location: str = "未知"
    status: str = CharacterStatus.ALIVE.value
    last_active_chapter: int = 0
    
    # 能力相关
    abilities: list = field(default_factory=list)
    items: list = field(default_factory=list)
    
    # 人际关系
    relationships: dict = field(default_factory=dict)  # {character_id: "关系描述"}
    
    # 时间线
    first_appearance: int = 0
    death_chapter: Optional[int] = None
    
    # 更新时间
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Hook:
    """钩子/悬念"""
    id: str
    content: str
    hook_type: str  # 主线/支线/物品/人物秘密
    status: str = HookStatus.PLANTED.value
    
    # 章节信息
    planted_chapter: int = 0
    expected_resolve_chapter: int = 0
    actual_resolve_chapter: Optional[int] = None
    
    # 相关信息
    related_characters: list = field(default_factory=list)
    related_items: list = field(default_factory=list)
    notes: str = ""
    
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Event:
    """大事记"""
    id: str
    chapter_num: int
    event_type: str  # 战斗/突破/情感/剧情转折
    content: str
    
    related_characters: list = field(default_factory=list)
    related_locations: list = field(default_factory=list)
    
    importance: int = 5  # 1-10，重要程度
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.memory_dir = os.path.join(project_dir, "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 加载数据
        self.characters: dict[str, CharacterState] = {}
        self.hooks: dict[str, Hook] = {}
        self.events: list[Event] = []
        
        self._load_all()
    
    # ==================== 人物管理 ====================
    
    def add_character(self, character: CharacterState):
        """添加角色"""
        self.characters[character.id] = character
        self._save_characters()
    
    def update_character(self, char_id: str, **kwargs):
        """更新角色状态"""
        if char_id in self.characters:
            for key, value in kwargs.items():
                if hasattr(self.characters[char_id], key):
                    setattr(self.characters[char_id], key, value)
            self.characters[char_id].updated_at = datetime.now().isoformat()
            self._save_characters()
    
    def move_character(self, char_id: str, location: str, chapter_num: int):
        """移动角色位置"""
        self.update_character(char_id, current_location=location, last_active_chapter=chapter_num)
        
        # 记录事件
        char = self.characters.get(char_id)
        if char:
            self.add_event(
                chapter_num=chapter_num,
                event_type="移动",
                content=f"{char.name}移动到{location}",
                related_characters=[char_id],
                related_locations=[location],
            )
    
    def kill_character(self, char_id: str, chapter_num: int, death_method: str = ""):
        """标记角色死亡"""
        char = self.characters.get(char_id)
        if char:
            death_info = f"死亡于第{chapter_num}章"
            if death_method:
                death_info += f"，方式：{death_method}"
            
            self.update_character(
                char_id,
                status=CharacterStatus.DEAD.value,
                death_chapter=chapter_num,
                notes=death_info,
            )
            
            self.add_event(
                chapter_num=chapter_num,
                event_type="角色死亡",
                content=f"{char.name}{death_info}",
                related_characters=[char_id],
                importance=8,
            )
    
    def get_characters_at_location(self, location: str) -> list[CharacterState]:
        """获取某位置的所有角色"""
        return [c for c in self.characters.values() 
                if c.current_location == location and c.status == CharacterStatus.ALIVE.value]
    
    def get_active_characters(self, current_chapter: int, recent_chapters: int = 10) -> list[CharacterState]:
        """获取活跃角色"""
        return [c for c in self.characters.values()
                if c.status == CharacterStatus.ALIVE.value
                and c.last_active_chapter >= current_chapter - recent_chapters]
    
    def get_core_characters(self) -> list[CharacterState]:
        """获取核心角色"""
        return [c for c in self.characters.values() if c.layer == CharacterLayer.CORE.value]
    
    def check_character_consistency(self, char_id: str, location: str) -> tuple[bool, str]:
        """检查角色一致性"""
        char = self.characters.get(char_id)
        if not char:
            return True, "角色不存在"
        
        # 检查生死
        if char.status == CharacterStatus.DEAD.value:
            return False, f"{char.name}已死亡（第{char.death_chapter}章），不应出现"
        
        # 检查位置
        if char.current_location != location and char.current_location != "未知":
            return False, f"{char.name}当前在{char.current_location}，不应出现在{location}"
        
        return True, "通过"
    
    # ==================== 钩子管理 ====================
    
    def add_hook(self, hook: Hook):
        """添加钩子"""
        self.hooks[hook.id] = hook
        self._save_hooks()
    
    def update_hook(self, hook_id: str, **kwargs):
        """更新钩子状态"""
        if hook_id in self.hooks:
            for key, value in kwargs.items():
                if hasattr(self.hooks[hook_id], key):
                    setattr(self.hooks[hook_id], key, value)
            self.hooks[hook_id].updated_at = datetime.now().isoformat()
            self._save_hooks()
    
    def resolve_hook(self, hook_id: str, chapter_num: int):
        """回收钩子"""
        self.update_hook(
            hook_id,
            status=HookStatus.RESOLVED.value,
            actual_resolve_chapter=chapter_num,
        )
    
    def get_active_hooks(self) -> list[Hook]:
        """获取活跃钩子"""
        return [h for h in self.hooks.values() 
                if h.status not in [HookStatus.RESOLVED.value, HookStatus.FORGOTTEN.value]]
    
    def get_hooks_by_type(self, hook_type: str) -> list[Hook]:
        """按类型获取钩子"""
        return [h for h in self.hooks.values() if h.hook_type == hook_type]
    
    def get_overdue_hooks(self, current_chapter: int) -> list[Hook]:
        """获取逾期钩子"""
        return [h for h in self.hooks.values()
                if h.status not in [HookStatus.RESOLVED.value]
                and h.expected_resolve_chapter > 0
                and h.expected_resolve_chapter < current_chapter - 10]  # 逾期10章
    
    def check_hook_health(self, current_chapter: int) -> dict:
        """检查钩子健康度"""
        active = self.get_active_hooks()
        overdue = self.get_overdue_hooks(current_chapter)
        
        return {
            "total_active": len(active),
            "overdue": len(overdue),
            "health_score": max(0, 100 - len(overdue) * 10),
            "overdue_hooks": [{"id": h.id, "content": h.content[:50]} for h in overdue[:5]],
        }
    
    # ==================== 大事记管理 ====================
    
    def add_event(self, chapter_num: int, event_type: str, content: str,
                  related_characters: list = None, related_locations: list = None,
                  importance: int = 5):
        """添加事件"""
        event = Event(
            id=f"event_{len(self.events) + 1:04d}",
            chapter_num=chapter_num,
            event_type=event_type,
            content=content,
            related_characters=related_characters or [],
            related_locations=related_locations or [],
            importance=importance,
        )
        self.events.append(event)
        self.events.sort(key=lambda e: e.chapter_num)
        self._save_events()
    
    def get_events_by_chapter(self, chapter_num: int) -> list[Event]:
        """获取某章节的事件"""
        return [e for e in self.events if e.chapter_num == chapter_num]
    
    def get_events_by_character(self, char_id: str) -> list[Event]:
        """获取角色相关事件"""
        return [e for e in self.events if char_id in e.related_characters]
    
    def get_recent_events(self, count: int = 10) -> list[Event]:
        """获取最近事件"""
        return self.events[-count:] if self.events else []
    
    def get_important_events(self, min_importance: int = 7) -> list[Event]:
        """获取重要事件"""
        return [e for e in self.events if e.importance >= min_importance]
    
    # ==================== 上下文生成 ====================
    
    def generate_writing_context(self, chapter_num: int, involved_characters: list[str] = None) -> str:
        """生成写作上下文"""
        parts = []
        
        # 活跃角色状态
        if involved_characters:
            parts.append("【角色状态】")
            for char_id in involved_characters:
                char = self.characters.get(char_id)
                if char:
                    parts.append(f"- {char.name}：位置={char.current_location}, 状态={char.status}")
                    if char.abilities:
                        parts.append(f"  能力：{', '.join(char.abilities)}")
                    if char.items:
                        parts.append(f"  物品：{', '.join(char.items)}")
        
        # 活跃钩子
        active_hooks = self.get_active_hooks()
        if active_hooks:
            parts.append("\n【活跃悬念】")
            for hook in active_hooks[:5]:
                parts.append(f"- {hook.content}（状态：{hook.status}）")
        
        # 最近重要事件
        recent_events = self.get_recent_events(5)
        if recent_events:
            parts.append("\n【最近事件】")
            for event in recent_events:
                parts.append(f"- 第{event.chapter_num}章：{event.content[:50]}")
        
        # 位置一致性提醒
        if involved_characters:
            parts.append("\n【位置检查】")
            for char_id in involved_characters:
                char = self.characters.get(char_id)
                if char:
                    consistent, msg = self.check_character_consistency(char_id, "当前位置")
                    if not consistent:
                        parts.append(f"注意:{msg}")
        
        return "\n".join(parts)
    
    def generate_summary(self) -> str:
        """生成记忆摘要"""
        parts = []
        
        # 角色统计
        alive_chars = [c for c in self.characters.values() if c.status == CharacterStatus.ALIVE.value]
        dead_chars = [c for c in self.characters.values() if c.status == CharacterStatus.DEAD.value]
        parts.append(f"角色：{len(alive_chars)}存活，{len(dead_chars)}死亡")
        
        # 钩子统计
        active_hooks = self.get_active_hooks()
        parts.append(f"悬念：{len(active_hooks)}个活跃")
        
        # 事件统计
        parts.append(f"事件：{len(self.events)}条记录")
        
        return " | ".join(parts)
    
    # ==================== 持久化 ====================
    
    def _load_all(self):
        """加载所有数据"""
        self._load_characters()
        self._load_hooks()
        self._load_events()
    
    def _load_characters(self):
        filepath = os.path.join(self.memory_dir, "characters.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for char_id, char_data in data.items():
                    self.characters[char_id] = CharacterState(**char_data)
    
    def _load_hooks(self):
        filepath = os.path.join(self.memory_dir, "hooks.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for hook_id, hook_data in data.items():
                    self.hooks[hook_id] = Hook(**hook_data)
    
    def _load_events(self):
        filepath = os.path.join(self.memory_dir, "events.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.events = [Event(**e) for e in data]
    
    def _save_characters(self):
        filepath = os.path.join(self.memory_dir, "characters.json")
        data = {char_id: asdict(char) for char_id, char in self.characters.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_hooks(self):
        filepath = os.path.join(self.memory_dir, "hooks.json")
        data = {hook_id: asdict(hook) for hook_id, hook in self.hooks.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_events(self):
        filepath = os.path.join(self.memory_dir, "events.json")
        data = [asdict(e) for e in self.events]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_all(self):
        """保存所有数据"""
        self._save_characters()
        self._save_hooks()
        self._save_events()