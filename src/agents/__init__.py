"""
智能体模块
包含所有智能体的定义和工厂函数
"""

from .base import BaseAgent
from .outline_agent import OutlineAgent
from .writer_agent import WriterAgent
from .reviewer_agent import ReviewerAgent
from .polisher_agent import PolisherAgent
from .critic_agent import CriticAgent
from .outline_critic import OutlineCritic, create_outline_critic
from .chapter_critic import ChapterCritic, create_chapter_critic
from .knowledge_checker import KnowledgeChecker, create_knowledge_checker
from .writing_coach import WritingCoach, create_writing_coach
from .material_supplier import MaterialSupplier, create_material_supplier
from .intent_recognizer import IntentRecognizer, Intent, get_intent_recognizer

__all__ = [
    'BaseAgent',
    'OutlineAgent',
    'WriterAgent',
    'ReviewerAgent',
    'PolisherAgent',
    'CriticAgent',
    'OutlineCritic',
    'create_outline_critic',
    'ChapterCritic',
    'create_chapter_critic',
    'KnowledgeChecker',
    'create_knowledge_checker',
    'WritingCoach',
    'create_writing_coach',
    'MaterialSupplier',
    'create_material_supplier',
    'IntentRecognizer',
    'Intent',
    'get_intent_recognizer',
]
