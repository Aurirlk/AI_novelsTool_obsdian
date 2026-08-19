"""
缓存管理模块
提供多级缓存，加速上下文加载
"""

import os
import json
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from collections import OrderedDict


class MemoryCache:
    """内存缓存（LRU）"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[any]:
        """获取缓存"""
        if key in self.cache:
            # 检查是否过期
            if self._is_expired(key):
                self._remove(key)
                return None
            
            # 移到最前面（LRU）
            self.cache.move_to_end(key)
            return self.cache[key]
        
        return None
    
    def set(self, key: str, value: any):
        """设置缓存"""
        # 如果已存在，更新
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = value
            self.timestamps[key] = datetime.now()
            return
        
        # 如果满了，删除最旧的
        if len(self.cache) >= self.max_size:
            self._remove_oldest()
        
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
    
    def remove(self, key: str):
        """删除缓存"""
        self._remove(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
    
    def _is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self.timestamps:
            return True
        
        elapsed = (datetime.now() - self.timestamps[key]).total_seconds()
        return elapsed > self.ttl_seconds
    
    def _remove(self, key: str):
        """删除单个缓存"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def _remove_oldest(self):
        """删除最旧的缓存"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": 0,  # 需要额外统计
        }


class ChapterCache:
    """章节缓存"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 内存缓存（最近章节）
        self.memory_cache = MemoryCache(max_size=20, ttl_seconds=7200)
    
    def get_chapter(self, chapter_num: int) -> Optional[dict]:
        """获取章节内容"""
        cache_key = f"chapter_{chapter_num}"
        
        # 先查内存缓存
        cached = self.memory_cache.get(cache_key)
        if cached:
            return cached
        
        # 再查文件缓存
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 加入内存缓存
                    self.memory_cache.set(cache_key, data)
                    return data
            except Exception:
                pass
        
        return None
    
    def save_chapter(self, chapter_num: int, content: dict):
        """保存章节内容"""
        cache_key = f"chapter_{chapter_num}"
        
        # 保存到内存缓存
        self.memory_cache.set(cache_key, content)
        
        # 保存到文件缓存
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[缓存] 保存章节失败: {e}")
    
    def get_recent_chapters(self, count: int = 5) -> list[dict]:
        """获取最近几章"""
        chapters = []
        
        # 从文件缓存中查找
        try:
            files = os.listdir(self.cache_dir)
            chapter_files = [f for f in files if f.startswith("chapter_") and f.endswith(".json")]
            chapter_files.sort(key=lambda x: int(x.replace("chapter_", "").replace(".json", "")))
            
            # 取最后几章
            for filename in chapter_files[-count:]:
                filepath = os.path.join(self.cache_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    chapters.append(json.load(f))
        except Exception:
            pass
        
        return chapters


class ContextCache:
    """上下文缓存"""
    
    def __init__(self):
        self.cache = MemoryCache(max_size=50, ttl_seconds=1800)
    
    def get_context(self, key: str) -> Optional[str]:
        """获取上下文"""
        return self.cache.get(key)
    
    def set_context(self, key: str, context: str):
        """设置上下文"""
        self.cache.set(key, context)
    
    def generate_context_key(self, chapter_num: int, characters: list) -> str:
        """生成上下文键"""
        chars_str = "_".join(sorted(characters))
        return f"ctx_{chapter_num}_{hashlib.md5(chars_str.encode()).hexdigest()[:8]}"


# 全局缓存实例
_chapter_cache: Optional[ChapterCache] = None
_context_cache: Optional[ContextCache] = None


def get_chapter_cache() -> ChapterCache:
    """获取章节缓存单例"""
    global _chapter_cache
    if _chapter_cache is None:
        _chapter_cache = ChapterCache()
    return _chapter_cache


def get_context_cache() -> ContextCache:
    """获取上下文缓存单例"""
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache