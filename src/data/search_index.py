"""
全局搜索模块
跨写作空间/大纲库/角色库/钩子库/时间线全文搜索（Obsidian 式）
章节内容按 (path, mtime) 缓存，文件未变不重复读盘
"""

import os
import re
from functools import lru_cache
from typing import List, Dict

_CHAPTER_CACHE_MAX = 512


@lru_cache(maxsize=_CHAPTER_CACHE_MAX)
def _read_chapter_cached(path: str, mtime: float) -> str:
    """按 (path, mtime) 缓存章节内容"""
    from src.data.writing_space import WritingSpace
    return WritingSpace.read(path)


def chapter_content(path: str) -> str:
    """读取章节内容（带缓存：文件未修改则复用内存，避免每次击键全盘扫描）"""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return ""
    return _read_chapter_cached(path, mtime)


def _iter_chapters():
    """遍历写作空间所有章节（懒加载，供 search_all/find_backlinks 复用）"""
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    tree = ws.list_tree()

    def walk_book(node, book_name=""):
        for child in node.get("children", []):
            if child.get("type") == "chapter":
                yield {"path": child["path"], "name": child["name"], "book": book_name}
            elif child.get("type") == "folder":
                yield from walk_book(child, book_name)

    for node in tree:
        if node.get("type") == "book":
            yield from walk_book(node, node["name"])


def search_all(keyword: str, limit: int = 50) -> List[Dict]:
    """
    全局搜索，返回结果列表：
    [{type, title, path, preview, score}]
    type: chapter/outline/character/hook/event
    """
    keyword = keyword.strip()
    if not keyword:
        return []
    results = []
    kw = keyword.lower()

    # ===== 1. 写作空间章节 =====
    try:
        for ch in _iter_chapters():
            content = chapter_content(ch["path"])
            if kw in content.lower():
                results.append({
                    "type": "chapter",
                    "title": f"{ch['book']} / {ch['name']}",
                    "path": ch["path"],
                    "preview": _snippet(content, keyword),
                    "score": content.lower().count(kw),
                })
    except Exception:
        pass

    # ===== 2. 大纲库（写作空间书目录） =====
    try:
        from src.data.outline_library import get_outline_library
        lib = get_outline_library()
        for w in lib.list_works():
            content = lib.read_work(w, "outline")
            if kw in content.lower():
                results.append({
                    "type": "outline",
                    "title": f"大纲库 / {w.title}",
                    "path": w.outline_file or "",
                    "preview": _snippet(content, keyword),
                    "score": content.lower().count(kw),
                })
            detail = lib.read_work(w, "detail")
            if detail != "(该作品没有此文件)" and kw in detail.lower():
                results.append({
                    "type": "outline",
                    "title": f"细纲库 / {w.title}",
                    "path": w.detail_file or "",
                    "preview": _snippet(detail, keyword),
                    "score": detail.lower().count(kw),
                })
    except Exception:
        pass

    # ===== 3. 角色库（写作空间书目录） =====
    try:
        from src.data.character_store import load_all_books_characters
        for c in load_all_books_characters():
            haystack = " ".join(str(c.get(k, "")) for k in ("name", "personality", "background", "location", "appearance"))
            if kw in haystack.lower():
                results.append({
                    "type": "character",
                    "title": f"角色 / {c.get('name')}",
                    "path": "",
                    "preview": _snippet(haystack, keyword),
                    "score": haystack.lower().count(kw),
                })
    except Exception:
        pass

    # ===== 4. 钩子库（写作空间书目录） =====
    try:
        from src.data.hook_store import load_all_books_hooks
        for h in load_all_books_hooks():
            content = h.get("content", "")
            if kw in content.lower():
                results.append({
                    "type": "hook",
                    "title": f"悬念 / {content[:20]}",
                    "path": "",
                    "preview": _snippet(content, keyword),
                    "score": content.lower().count(kw),
                })
    except Exception:
        pass

    # ===== 5. 时间线（写作空间书目录） =====
    try:
        from src.data.timeline_store import load_all_books_events
        for e in load_all_books_events():
            content = f"{e.get('title', '')} {e.get('content', '')}"
            if kw in content.lower():
                results.append({
                    "type": "event",
                    "title": f"事件 / {e.get('title', '')[:30]}",
                    "path": "",
                    "preview": _snippet(content, keyword),
                    "score": content.lower().count(kw),
                })
    except Exception:
        pass

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def find_backlinks(name: str) -> List[Dict]:
    """
    反向链接：查找写作空间中所有提到指定名字的章节（Obsidian 式反向链接）

    Args:
        name: 角色名/关键词

    Returns:
        [{chapter, book, path, preview}]
    """
    name = name.strip()
    if not name:
        return []
    results = []
    kw = name.lower()

    try:
        for ch in _iter_chapters():
            content = chapter_content(ch["path"])
            if kw in content.lower():
                results.append({
                    "chapter": ch["name"],
                    "book": ch["book"],
                    "path": ch["path"],
                    "preview": _snippet(content, name),
                })
    except Exception:
        pass

    return results


def _snippet(text: str, keyword: str, radius: int = 40) -> str:
    """提取关键字附近的上下文片段"""
    idx = text.lower().find(keyword.lower())
    if idx < 0:
        return text[:80]
    start = max(0, idx - radius)
    end = min(len(text), idx + len(keyword) + radius)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return prefix + text[start:end].replace("\n", " ") + suffix
