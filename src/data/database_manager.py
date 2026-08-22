"""
SQLite数据库管理器
管理API密钥、设置、项目配置等
"""

import os
import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "settings.db")
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建API密钥表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    key_name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    base_url TEXT,
                    model TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(provider, key_name)
                )
            """)
            
            # 创建设置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            """)
            
            # 创建项目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    description TEXT,
                    genre TEXT,
                    last_opened TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(path)
                )
            """)
            
            # 创建快捷键表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shortcuts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL UNIQUE,
                    key_sequence TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 插入默认设置
            self._insert_default_settings(cursor)
            self._insert_default_shortcuts(cursor)
    
    def _insert_default_settings(self, cursor):
        """插入默认设置"""
        default_settings = [
            # 通用设置
            ("general", "language", "zh_CN", "界面语言"),
            ("general", "theme", "dark", "主题"),
            ("general", "font_size", "14", "字体大小"),
            ("general", "auto_save", "true", "自动保存"),
            ("general", "auto_save_interval", "300", "自动保存间隔（秒）"),
            ("general", "recent_projects_limit", "10", "最近项目数量限制"),
            
            # 编辑器设置
            ("editor", "tab_size", "4", "Tab大小"),
            ("editor", "word_wrap", "true", "自动换行"),
            ("editor", "line_numbers", "true", "显示行号"),
            ("editor", "highlight_current_line", "true", "高亮当前行"),
            ("editor", "auto_indent", "true", "自动缩进"),
            
            # 生成设置
            ("generation", "default_provider", "deepseek", "默认LLM提供商"),
            ("generation", "default_model", "glm-4-flash", "默认模型"),
            ("generation", "temperature", "0.7", "温度"),
            ("generation", "max_tokens", "2000", "最大token数"),
            ("generation", "max_retries", "3", "最大重试次数"),
            ("generation", "words_per_chapter", "2000", "每章字数"),
            
            # 存储设置
            ("storage", "data_dir", "./data", "数据目录"),
            ("storage", "backup_enabled", "true", "启用备份"),
            ("storage", "backup_count", "5", "备份数量"),
            ("storage", "chroma_persist_dir", "./data/chromadb", "ChromaDB目录"),
        ]
        
        for category, key, value, description in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO settings (category, key, value, description)
                VALUES (?, ?, ?, ?)
            """, (category, key, value, description))
    
    def _insert_default_shortcuts(self, cursor):
        """插入默认快捷键"""
        default_shortcuts = [
            ("new_project", "Ctrl+N", "新建项目"),
            ("open_project", "Ctrl+O", "打开项目"),
            ("save", "Ctrl+S", "保存"),
            ("save_as", "Ctrl+Shift+S", "另存为"),
            ("undo", "Ctrl+Z", "撤销"),
            ("redo", "Ctrl+Y", "重做"),
            ("cut", "Ctrl+X", "剪切"),
            ("copy", "Ctrl+C", "复制"),
            ("paste", "Ctrl+V", "粘贴"),
            ("find", "Ctrl+F", "查找"),
            ("replace", "Ctrl+H", "替换"),
            ("generate", "Ctrl+G", "生成"),
            ("critique", "Ctrl+Shift+C", "批评"),
            ("export", "Ctrl+E", "导出"),
            ("settings", "Ctrl+,", "设置"),
            ("quit", "Ctrl+Q", "退出"),
        ]
        
        for action, key_sequence, description in default_shortcuts:
            cursor.execute("""
                INSERT OR IGNORE INTO shortcuts (action, key_sequence, description)
                VALUES (?, ?, ?)
            """, (action, key_sequence, description))
    
    # ==================== API密钥管理 ====================
    
    def add_api_key(self, provider: str, key_name: str, api_key: str,
                    base_url: Optional[str] = None, model: Optional[str] = None,
                    is_default: bool = False) -> int:
        """
        添加API密钥
        
        Args:
            provider: 提供商名称
            key_name: 密钥名称
            api_key: API密钥
            base_url: 基础URL
            model: 默认模型
            is_default: 是否默认
        
        Returns:
            插入的ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 如果设置为默认，先取消其他默认
            if is_default:
                cursor.execute("""
                    UPDATE api_keys SET is_default = 0 WHERE provider = ?
                """, (provider,))
            
            cursor.execute("""
                INSERT OR REPLACE INTO api_keys (provider, key_name, api_key, base_url, model, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (provider, key_name, api_key, base_url, model, is_default))
            
            return cursor.lastrowid
    
    def get_api_key(self, provider: str, key_name: Optional[str] = None) -> Optional[Dict]:
        """
        获取API密钥
        
        Args:
            provider: 提供商名称
            key_name: 密钥名称（可选）
        
        Returns:
            API密钥信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if key_name:
                cursor.execute("""
                    SELECT * FROM api_keys WHERE provider = ? AND key_name = ?
                """, (provider, key_name))
            else:
                cursor.execute("""
                    SELECT * FROM api_keys WHERE provider = ? AND is_default = 1
                """, (provider,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_api_keys(self, provider: Optional[str] = None) -> List[Dict]:
        """
        列出API密钥
        
        Args:
            provider: 提供商名称过滤
        
        Returns:
            API密钥列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if provider:
                cursor.execute("""
                    SELECT * FROM api_keys WHERE provider = ? ORDER BY is_default DESC, key_name
                """, (provider,))
            else:
                cursor.execute("""
                    SELECT * FROM api_keys ORDER BY provider, is_default DESC, key_name
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_api_key(self, provider: str, key_name: str) -> bool:
        """
        删除API密钥
        
        Args:
            provider: 提供商名称
            key_name: 密钥名称
        
        Returns:
            是否删除成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM api_keys WHERE provider = ? AND key_name = ?
            """, (provider, key_name))
            
            return cursor.rowcount > 0
    
    def set_default_api_key(self, provider: str, key_name: str) -> bool:
        """
        设置默认API密钥
        
        Args:
            provider: 提供商名称
            key_name: 密钥名称
        
        Returns:
            是否设置成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 取消该提供商的其他默认
            cursor.execute("""
                UPDATE api_keys SET is_default = 0 WHERE provider = ?
            """, (provider,))
            
            # 设置新的默认
            cursor.execute("""
                UPDATE api_keys SET is_default = 1 WHERE provider = ? AND key_name = ?
            """, (provider, key_name))
            
            return cursor.rowcount > 0
    
    # ==================== 设置管理 ====================
    
    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """
        获取设置
        
        Args:
            category: 分类
            key: 键名
            default: 默认值
        
        Returns:
            设置值
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM settings WHERE category = ? AND key = ?
            """, (category, key))
            
            row = cursor.fetchone()
            if row:
                value = row['value']
                # 尝试解析JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            
            return default
    
    def set_setting(self, category: str, key: str, value: Any, description: Optional[str] = None):
        """
        设置设置
        
        Args:
            category: 分类
            key: 键名
            value: 值
            description: 描述
        """
        # 转换为JSON字符串
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (category, key, value, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (category, key, value_str, description))
    
    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """
        获取分类下的所有设置
        
        Args:
            category: 分类
        
        Returns:
            设置字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key, value FROM settings WHERE category = ?
            """, (category,))
            
            settings = {}
            for row in cursor.fetchall():
                value = row['value']
                try:
                    settings[row['key']] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    settings[row['key']] = value
            
            return settings
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有设置
        
        Returns:
            设置字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, key, value FROM settings ORDER BY category, key
            """)
            
            settings = {}
            for row in cursor.fetchall():
                category = row['category']
                if category not in settings:
                    settings[category] = {}
                
                value = row['value']
                try:
                    settings[category][row['key']] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    settings[category][row['key']] = value
            
            return settings
    
    # ==================== 项目管理 ====================
    
    def add_project(self, name: str, path: str, description: Optional[str] = None,
                    genre: Optional[str] = None) -> int:
        """
        添加项目
        
        Args:
            name: 项目名称
            path: 项目路径
            description: 描述
            genre: 类型
        
        Returns:
            插入的ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO projects (name, path, description, genre, last_opened)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, path, description, genre))
            
            return cursor.lastrowid
    
    def get_project(self, path: str) -> Optional[Dict]:
        """
        获取项目
        
        Args:
            path: 项目路径
        
        Returns:
            项目信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects WHERE path = ?
            """, (path,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_projects(self, limit: int = 20) -> List[Dict]:
        """
        列出项目
        
        Args:
            limit: 返回数量限制
        
        Returns:
            项目列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects ORDER BY last_opened DESC LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_project_last_opened(self, path: str):
        """
        更新项目最后打开时间
        
        Args:
            path: 项目路径
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects SET last_opened = CURRENT_TIMESTAMP WHERE path = ?
            """, (path,))
    
    def delete_project(self, path: str) -> bool:
        """
        删除项目
        
        Args:
            path: 项目路径
        
        Returns:
            是否删除成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM projects WHERE path = ?
            """, (path,))
            
            return cursor.rowcount > 0
    
    # ==================== 快捷键管理 ====================
    
    def get_shortcut(self, action: str) -> Optional[str]:
        """
        获取快捷键
        
        Args:
            action: 动作
        
        Returns:
            快捷键序列
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key_sequence FROM shortcuts WHERE action = ?
            """, (action,))
            
            row = cursor.fetchone()
            return row['key_sequence'] if row else None
    
    def set_shortcut(self, action: str, key_sequence: str, description: Optional[str] = None):
        """
        设置快捷键
        
        Args:
            action: 动作
            key_sequence: 快捷键序列
            description: 描述
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO shortcuts (action, key_sequence, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (action, key_sequence, description))
    
    def list_shortcuts(self) -> List[Dict]:
        """
        列出所有快捷键
        
        Returns:
            快捷键列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM shortcuts ORDER BY action
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def reset_shortcuts(self):
        """重置快捷键为默认值"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shortcuts")
            self._insert_default_shortcuts(cursor)


# 全局实例
_database_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器单例"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager
