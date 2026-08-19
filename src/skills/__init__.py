"""
技能系统模块
OpenCode/Claude Code 风格的 SKILL.md 技能加载与管理
"""

from .skill_loader import Skill, load_skill, scan_skills
from .skill_manager import SkillManager, get_skill_manager

__all__ = [
    'Skill',
    'load_skill',
    'scan_skills',
    'SkillManager',
    'get_skill_manager',
]
