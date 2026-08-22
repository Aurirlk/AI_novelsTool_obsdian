"""
数据管理模块
"""

from .history_manager import HistoryManager, HistoryRecord, get_history_manager
from .material_collector import MaterialCollector
from .database_manager import DatabaseManager, get_database_manager
from .settings_manager import SettingsManager, get_settings_manager

__all__ = [
    'HistoryManager',
    'HistoryRecord',
    'get_history_manager',
    'MaterialCollector',
    'DatabaseManager',
    'get_database_manager',
    'SettingsManager',
    'get_settings_manager',
]
