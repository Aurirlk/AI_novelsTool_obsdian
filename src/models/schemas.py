"""
数据模型定义
定义小说生成过程中使用的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class CharacterRole(Enum):
    """角色类型"""
    PROTAGONIST = "protagonist"  # 主角
    ANTAGONIST = "antagonist"    # 反派
    SUPPORTING = "supporting"    # 配角
    MINOR = "minor"              # 龙套


class HookStatus(Enum):
    """钩子状态"""
    PLANTED = "planted"          # 已埋下
    DEVELOPING = "developing"    # 发展中
    ABOUT_TO_RESOLVE = "about_to_resolve"  # 即将回收
    RESOLVED = "resolved"        # 已回收
    FORGOTTEN = "forgotten"      # 已遗忘（需要提醒）


class ChapterStatus(Enum):
    """章节状态"""
    DRAFT = "draft"              # 草稿
    REVIEWING = "reviewing"      # 审核中
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已拒绝
    POLISHED = "polished"        # 已修正（错别字）


@dataclass
class Character:
    """角色定义"""
    id: str
    name: str
    role: CharacterRole
    personality: str  # 性格描述
    background: str   # 背景故事
    current_location: str = "未知"
    is_alive: bool = True
    first_appearance: int = 0  # 首次出现章节
    last_appearance: int = 0   # 最后出现章节
    relationships: dict = field(default_factory=dict)  # 与其他角色的关系
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "personality": self.personality,
            "background": self.background,
            "current_location": self.current_location,
            "is_alive": self.is_alive,
            "first_appearance": self.first_appearance,
            "last_appearance": self.last_appearance,
            "relationships": self.relationships,
        }


@dataclass
class Hook:
    """钩子（悬念/伏笔）"""
    id: str
    content: str              # 钩子内容
    status: HookStatus
    planted_chapter: int      # 埋下章节
    expected_resolve: int     # 预期回收章节
    actual_resolve: Optional[int] = None  # 实际回收章节
    related_characters: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value,
            "planted_chapter": self.planted_chapter,
            "expected_resolve": self.expected_resolve,
            "actual_resolve": self.actual_resolve,
            "related_characters": self.related_characters,
        }


@dataclass
class Chapter:
    """章节"""
    number: int
    title: str
    content: str
    status: ChapterStatus = ChapterStatus.DRAFT
    summary: str = ""  # 章节摘要
    word_count: int = 0
    hooks_planted: list = field(default_factory=list)  # 本章埋下的钩子
    hooks_resolved: list = field(default_factory=list)  # 本章回收的钩子
    characters_appeared: list = field(default_factory=list)  # 出现的角色
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "status": self.status.value,
            "summary": self.summary,
            "word_count": self.word_count,
            "hooks_planted": self.hooks_planted,
            "hooks_resolved": self.hooks_resolved,
            "characters_appeared": self.characters_appeared,
            "created_at": self.created_at,
        }


@dataclass
class StoryBible:
    """故事圣经（核心设定）"""
    title: str
    genre: str           # 题材类型
    theme: str           # 主题
    worldview: str       # 世界观设定
    power_system: str    # 力量体系
    main_characters: list = field(default_factory=list)  # 主要角色ID
    plot_outline: str = ""  # 主线大纲
    chapter_outlines: dict = field(default_factory=dict)  # 章节细纲
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "genre": self.genre,
            "theme": self.theme,
            "worldview": self.worldview,
            "power_system": self.power_system,
            "main_characters": self.main_characters,
            "plot_outline": self.plot_outline,
            "chapter_outlines": self.chapter_outlines,
            "created_at": self.created_at,
        }


@dataclass
class NovelState:
    """小说状态（用于工作流）"""
    story_bible: Optional[StoryBible] = None
    characters: dict = field(default_factory=dict)  # id -> Character
    chapters: list = field(default_factory=list)     # Chapter列表
    hooks: dict = field(default_factory=dict)        # id -> Hook
    current_chapter: int = 0
    total_words: int = 0
    
    def get_character(self, name: str) -> Optional[Character]:
        """根据名字查找角色"""
        for char in self.characters.values():
            if char.name == name:
                return char
        return None
    
    def get_active_hooks(self) -> list[Hook]:
        """获取未回收的钩子"""
        return [h for h in self.hooks.values() 
                if h.status != HookStatus.RESOLVED]
    
    def get_characters_in_chapter(self, chapter_num: int) -> list[Character]:
        """获取某章节出现的角色"""
        if chapter_num <= len(self.chapters):
            chapter = self.chapters[chapter_num - 1]
            return [self.characters[cid] for cid in chapter.characters_appeared 
                    if cid in self.characters]
        return []
    
    def to_dict(self) -> dict:
        return {
            "story_bible": self.story_bible.to_dict() if self.story_bible else None,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "chapters": [c.to_dict() for c in self.chapters],
            "hooks": {k: v.to_dict() for k, v in self.hooks.items()},
            "current_chapter": self.current_chapter,
            "total_words": self.total_words,
        }