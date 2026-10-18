"""
作品状态快照（阶段 1）
把一本书的 元数据/大纲/正文进度/角色/悬念/时间线 聚合为一段 Markdown，
供 AI 助手每次发送消息前注入 system prompt，让模型掌握"这本书现在写到哪了"。

参考 goink 的 State 注入设计：只读聚合、体积上限、按优先级裁剪。
每个小节独立 try/except：任一数据源损坏都不阻塞对话。
"""

from typing import List, Optional

DEFAULT_MAX_CHARS = 6000


def build_state_snapshot(book_name: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """构建书籍状态快照；书籍名为空、书籍目录不存在或没有任何内容时返回空串"""
    book_name = (book_name or "").strip()
    if not book_name:
        return ""
    # 前置校验：书籍目录必须存在。各数据源构造器可能自动建目录，
    # 提前返回可避免为不存在的书产生空目录副作用。
    try:
        from src.data.writing_space import WORKSPACE_DIR
        import os
        if not os.path.isdir(os.path.join(WORKSPACE_DIR, book_name)):
            return ""
    except Exception:
        return ""

    sections: List[str] = [
        _book_meta_section(book_name),
        _outline_section(book_name),
        _progress_section(book_name),
        _characters_section(book_name),
        _hooks_section(book_name),
        _timeline_section(book_name),
    ]
    sections = [s.strip("\n") for s in sections if s and s.strip("\n")]
    if not sections:
        return ""

    parts: List[str] = []
    used = 0
    for s in sections:  # 按优先级从前到后填充，超出预算截断
        if used + len(s) > max_chars:
            if not parts:
                parts.append(s[:max_chars])
            break
        parts.append(s)
        used += len(s)
    return "\n\n".join(parts)


def _book_meta_section(book_name: str) -> str:
    """书籍元数据：频道/题材/简介（书籍目录不存在则返回空）"""
    try:
        from src.data.writing_space import WORKSPACE_DIR
        import os
        if not os.path.isdir(os.path.join(WORKSPACE_DIR, book_name)):
            return ""
        from src.data.book_meta import get_meta
        meta = get_meta(book_name)
    except Exception:
        return ""
    lines = [f"## 书籍信息：《{book_name}》"]
    if meta.get("channel"):
        lines.append(f"- 频道：{meta['channel']}")
    if meta.get("genre"):
        lines.append(f"- 题材：{meta['genre']}")
    desc = (meta.get("description") or "").strip()
    if desc:
        lines.append(f"- 简介：{desc[:200]}")
    return "\n".join(lines)


def _is_outline_doc(name: str) -> bool:
    """大纲/细纲文档不是正文章节"""
    return "大纲" in name or "细纲" in name


def _outline_section(book_name: str) -> str:
    """大纲/细纲摘要（故事走向锚点）"""
    try:
        from src.data.outline_library import get_outline_library
        library = get_outline_library()
        library.refresh()
        work = next((w for w in library.list_works() if w.title == book_name), None)
        if work is None:
            return ""
        outline = library.read_work(work, "outline")
        if not outline or outline.startswith("("):
            return ""
        return f"## 大纲摘要\n{outline[:1500]}"
    except Exception:
        return ""


def _progress_section(book_name: str) -> str:
    """正文进度：章节数 + 最近章节预览"""
    try:
        from src.data.writing_space import get_writing_space
        ws = get_writing_space()
        tree = ws.list_tree()
    except Exception:
        return ""
    for node in tree:
        if node.get("type") != "book" or node.get("name") != book_name:
            continue
        chapters: List[dict] = []
        for child in node.get("children", []):
            if child.get("type") == "chapter":
                if _is_outline_doc(child["name"]):
                    continue
                chapters.append(child)
            elif child.get("type") == "folder":
                chapters.extend(sub for sub in child.get("children", [])
                                if sub.get("type") == "chapter" and not _is_outline_doc(sub["name"]))
        if not chapters:
            return ""
        lines = [f"## 正文进度（共 {len(chapters)} 章）"]
        recent = chapters[-3:]
        lines.append("最近章节：" + "、".join(c["name"] for c in recent))
        last = recent[-1]
        try:
            content = ws.read(last["path"]) or ""
        except Exception:
            content = ""
        if content.strip():
            lines.append(f"最近一章《{last['name']}》开头：{content.strip()[:200]}")
        return "\n".join(lines)
    return ""


def _characters_section(book_name: str) -> str:
    """角色状态（前 10 个）"""
    try:
        from src.data.character_store import CharacterStore
        chars = CharacterStore(book=book_name).load_all()
    except Exception:
        return ""
    chars = [c for c in chars if c.get("name")]
    if not chars:
        return ""
    lines = ["## 角色"]
    for c in chars[:10]:
        name = c.get("name", "?")
        role = c.get("role_type", "") or c.get("role", "")
        personality = (c.get("personality", "") or "")[:24]
        extra = c.get("status", "")
        tags = " / ".join(x for x in (role, personality, extra) if x)
        lines.append(f"- {name}" + (f"（{tags}）" if tags else ""))
    return "\n".join(lines)


def _hooks_section(book_name: str) -> str:
    """悬念/伏笔：未回收钩子 + 超期标记"""
    try:
        from src.data.hook_store import HookStore
        hooks = HookStore(book=book_name).load_all()
    except Exception:
        return ""
    hooks = [h for h in hooks if h.get("content") and h.get("status") != "已回收"]
    if not hooks:
        return ""
    max_actual = max((int(h.get("actual_chapter", 0) or 0) for h in hooks), default=0)
    lines = ["## 未回收悬念"]
    for h in hooks[:12]:
        content = h.get("content", "")[:40]
        status = h.get("status", "已埋下")
        expected = int(h.get("expected_chapter", 0) or 0)
        flag = " ⚠️超期" if max_actual > 0 and 0 < expected < max_actual else ""
        lines.append(f"- {content}（{status}，预期回收第{expected}章）{flag}".rstrip())
    return "\n".join(lines)


def _timeline_section(book_name: str) -> str:
    """时间线大事记（最近 5 条）"""
    try:
        from src.data.timeline_store import TimelineStore
        events = TimelineStore(book=book_name).load_events()
    except Exception:
        return ""
    events = [e for e in events if e.get("content") or e.get("event_type")]
    if not events:
        return ""
    lines = ["## 近期大事记"]
    for e in events[-5:]:
        chapter = e.get("chapter") or e.get("chapter_num") or ""
        etype = e.get("type") or e.get("event_type") or ""
        content = (e.get("content", "") or "")[:60]
        prefix = " ".join(x for x in (f"第{chapter}章" if chapter else "", etype) if x)
        lines.append(f"- {content}" + (f"（{prefix}）" if prefix else ""))
    return "\n".join(lines)
