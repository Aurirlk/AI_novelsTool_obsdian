"""
记忆管理模块
管理角色档案、大事记、钩子等长期记忆
"""

import json
import os
from typing import Optional
from datetime import datetime
from src.models.schemas import Character, Hook, HookStatus, NovelState


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, persist_dir: str = "data/memory"):
        """
        初始化记忆管理器
        
        Args:
            persist_dir: 持久化目录
        """
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # 内存中的数据
        self.characters: dict[str, Character] = {}
        self.hooks: dict[str, Hook] = {}
        self.events: list[dict] = []  # 大事记
    
    def add_character(self, character: Character):
        """添加角色"""
        self.characters[character.id] = character
        self._save_characters()
    
    def get_character(self, name: str) -> Optional[Character]:
        """根据名字查找角色"""
        for char in self.characters.values():
            if char.name == name:
                return char
        return None
    
    def update_character_location(self, char_id: str, location: str, chapter_num: int):
        """更新角色位置"""
        if char_id in self.characters:
            self.characters[char_id].current_location = location
            self.characters[char_id].last_appearance = chapter_num
            self._save_characters()
    
    def mark_character_dead(self, char_id: str, chapter_num: int):
        """标记角色死亡"""
        if char_id in self.characters:
            self.characters[char_id].is_alive = False
            self.add_event(
                chapter_num=chapter_num,
                event_type="character_death",
                content=f"{self.characters[char_id].name}死亡",
                related_characters=[char_id],
            )
            self._save_characters()
    
    def add_hook(self, hook: Hook):
        """添加钩子"""
        self.hooks[hook.id] = hook
        self._save_hooks()
    
    def resolve_hook(self, hook_id: str, chapter_num: int):
        """回收钩子"""
        if hook_id in self.hooks:
            self.hooks[hook_id].status = HookStatus.RESOLVED
            self.hooks[hook_id].actual_resolve = chapter_num
            self._save_hooks()
    
    def get_active_hooks(self) -> list[Hook]:
        """获取未回收的钩子"""
        return [h for h in self.hooks.values() 
                if h.status != HookStatus.RESOLVED]
    
    def get_overdue_hooks(self, current_chapter: int) -> list[Hook]:
        """获取逾期未回收的钩子"""
        return [h for h in self.hooks.values() 
                if h.status != HookStatus.RESOLVED and h.expected_resolve < current_chapter]
    
    def add_event(self, chapter_num: int, event_type: str, content: str, 
                  related_characters: list[str] = None):
        """添加大事记"""
        event = {
            "chapter_num": chapter_num,
            "event_type": event_type,
            "content": content,
            "related_characters": related_characters or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.events.append(event)
        self._save_events()
    
    def get_recent_events(self, count: int = 10) -> list[dict]:
        """获取最近的大事记"""
        return self.events[-count:]
    
    def get_character_events(self, char_id: str) -> list[dict]:
        """获取角色相关的大事记"""
        return [e for e in self.events if char_id in e.get("related_characters", [])]
    
    # 持久化方法
    def _save_characters(self):
        """保存角色数据"""
        filepath = os.path.join(self.persist_dir, "characters.json")
        data = {k: v.to_dict() for k, v in self.characters.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_hooks(self):
        """保存钩子数据"""
        filepath = os.path.join(self.persist_dir, "hooks.json")
        data = {k: v.to_dict() for k, v in self.hooks.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_events(self):
        """保存大事记"""
        filepath = os.path.join(self.persist_dir, "events.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载数据"""
        self._load_characters()
        self._load_hooks()
        self._load_events()
    
    def _load_characters(self):
        """加载角色数据"""
        filepath = os.path.join(self.persist_dir, "characters.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 简化处理，实际应该反序列化为Character对象
    
    def _load_hooks(self):
        """加载钩子数据"""
        filepath = os.path.join(self.persist_dir, "hooks.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 简化处理
    
    def _load_events(self):
        """加载大事记"""
        filepath = os.path.join(self.persist_dir, "events.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                self.events = json.load(f)
    
    def get_memory_context(self, current_chapter: int) -> str:
        """获取记忆上下文（用于LLM）"""
        parts = []
        
        # 角色信息
        if self.characters:
            parts.append("【角色档案】")
            for char in list(self.characters.values())[:5]:
                status = "存活" if char.is_alive else "已死亡"
                parts.append(f"- {char.name}({char.role.value}): {char.personality}, 当前位置:{char.current_location}, 状态:{status}")
        
        # 活跃钩子
        active_hooks = self.get_active_hooks()
        if active_hooks:
            parts.append("\n【未回收悬念】")
            for hook in active_hooks[:5]:
                parts.append(f"- {hook.content} (第{hook.planted_chapter}章埋下)")
        
        # 最近事件
        recent_events = self.get_recent_events(5)
        if recent_events:
            parts.append("\n【最近事件】")
            for event in recent_events:
                parts.append(f"- 第{event['chapter_num']}章: {event['content']}")
        
        return "\n".join(parts)


# 全局记忆管理器实例
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取记忆管理器单例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager