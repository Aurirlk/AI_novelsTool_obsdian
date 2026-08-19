"""
页面模块
包含所有页面的定义
"""

from .home_page import HomePage
from .chat_page import ChatPage
from .extensions_page import ExtensionsPage
from .book_library_page import BookLibraryPage
from .writer_page import WriterPage
from .outline_page import OutlinePage
from .character_page import CharacterPage
from .hook_page import HookPage
from .event_page import EventPage
from .critic_page import CriticPage
from .book_page import BookPage
from .export_page import ExportPage
from .history_page import HistoryPage
from .shared_memory_page import SharedMemoryPage
from .settings_page import SettingsPage

__all__ = [
    'HomePage',
    'ChatPage',
    'ExtensionsPage',
    'BookLibraryPage',
    'WriterPage',
    'OutlinePage',
    'CharacterPage',
    'HookPage',
    'EventPage',
    'CriticPage',
    'BookPage',
    'ExportPage',
    'HistoryPage',
    'SharedMemoryPage',
    'SettingsPage',
]
