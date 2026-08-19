"""
项目数据工具层（本地 function calling）
把写作空间/大纲库/角色/钩子/时间线/邮箱投递 暴露成 LLM 可调用的工具。
LLM 通过 chat_with_tools 自主决定何时调用（识别用户需要读写本地数据时）。
"""

import json
import os
import time
from typing import Callable, Dict, List

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DELIVERIES_FILE = os.path.join(_PROJECT_ROOT, "data", "deliveries.json")


# ==================== 读取工具 ====================

def _read_books() -> list:
    """列出写作空间的所有书"""
    from src.data.writing_space import get_writing_space
    tree = get_writing_space().list_tree()
    books = []
    for node in tree:
        if node.get("type") == "book":
            books.append({"name": node["name"], "path": node["path"]})
    return books


def _read_book(book_name: str) -> dict:
    """读取一本书的章节列表（每章前800字预览）"""
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    tree = ws.list_tree()
    for node in tree:
        if node.get("type") != "book" or node["name"] != book_name:
            continue
        chapters = []
        for child in node.get("children", []):
            if child.get("type") == "chapter":
                content = ws.read(child["path"])
                chapters.append({
                    "title": child["name"],
                    "path": child["path"],
                    "preview": content[:800],
                })
            elif child.get("type") == "folder":
                for sub in child.get("children", []):
                    if sub.get("type") == "chapter":
                        content = ws.read(sub["path"])
                        chapters.append({
                            "title": sub["name"],
                            "path": sub["path"],
                            "preview": content[:800],
                        })
        return {"name": book_name, "chapters": chapters}
    return {"error": f"未找到书籍「{book_name}」，可先列出所有书籍确认书名"}


def _read_chapter(book_name: str, chapter_title: str) -> dict:
    """读取指定书的指定章节全文"""
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    tree = ws.list_tree()
    for node in tree:
        if node.get("type") != "book" or node["name"] != book_name:
            continue
        for child in node.get("children", []):
            if child.get("type") == "chapter" and child["name"] == chapter_title:
                return {"book": book_name, "chapter": chapter_title, "content": ws.read(child["path"])}
            if child.get("type") == "folder":
                for sub in child.get("children", []):
                    if sub.get("type") == "chapter" and sub["name"] == chapter_title:
                        return {"book": book_name, "chapter": chapter_title, "content": ws.read(sub["path"])}
    return {"error": f"未找到 {book_name} 的章节「{chapter_title}」"}


def _list_outlines(category: str = "") -> list:
    """列出大纲库作品"""
    from src.data.outline_library import get_outline_library
    works = get_outline_library().list_works(category or None)
    return [{"title": w.title, "category": w.category} for w in works]


def _read_outline(title: str) -> dict:
    """读取大纲库中指定作品的大纲内容"""
    from src.data.outline_library import get_outline_library
    lib = get_outline_library()
    for w in lib.list_works():
        if w.title == title:
            return {"title": w.title, "category": w.category, "outline": lib.read_work(w, "outline")}
    return {"error": f"大纲库未找到作品「{title}」"}


def _list_characters() -> list:
    """列出所有角色（名称+类型）（统一存储：写作空间书目录）"""
    from src.data.character_store import load_all_books_characters
    chars = load_all_books_characters()
    return [{"name": c.get("name"), "role_type": c.get("role_type")} for c in chars]


def _read_character(name: str) -> dict:
    """读取角色详情"""
    from src.data.character_store import load_all_books_characters
    for c in load_all_books_characters():
        if c.get("name") == name:
            return {k: c.get(k) for k in
                    ("name", "role_type", "personality", "background", "status", "location", "appearance", "abilities", "items", "relationships")}
    return {"error": f"未找到角色「{name}」"}


def _list_hooks() -> list:
    """列出所有悬念（内容前30字+状态）"""
    from src.data.hook_store import load_all_books_hooks
    hooks = load_all_books_hooks()
    return [{"content": h.get("content", "")[:30], "type": h.get("type"), "status": h.get("status")} for h in hooks]


def _list_events() -> list:
    """列出时间线事件（时间+章节+概要）"""
    from src.data.timeline_store import load_all_books_events
    events = load_all_books_events()
    return [{"chapter": e.get("chapter"), "title": e.get("title", "")[:40], "content": e.get("content", "")[:80]}
            for e in events[-30:]]


# ==================== 写入工具 ====================

def _save_outline(title: str, content: str, category: str = "玄幻") -> dict:
    """保存/更新大纲（统一存储：写作空间/{书}/{书}_大纲.md，不存在则新建书）"""
    from src.data.outline_library import get_outline_library
    lib = get_outline_library()

    # 查找已有作品
    for w in lib.list_works():
        if w.title == title:
            if w.outline_file:
                with open(w.outline_file, "w", encoding="utf-8") as f:
                    f.write(content)
            return {"ok": True, "message": f"大纲《{title}》已更新", "path": w.outline_file}

    # 不存在则新建（写作空间建书目录）
    ok, msg = lib.create_work(category, title)
    if not ok:
        return {"ok": False, "message": str(msg)}
    lib.refresh()
    for w in lib.list_works():
        if w.title == title:
            with open(w.outline_file, "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True, "message": f"大纲《{title}》已新建（分类「{category}」）", "path": w.outline_file}
    return {"ok": False, "message": "保存失败：未找到新建作品"}


def _save_character(name: str, role_type: str = "配角", personality: str = "",
                    background: str = "", status: str = "存活",
                    location: str = "", appearance: str = "", abilities: list = None,
                    book: str = "") -> dict:
    """保存角色（不存在则新建，存在则更新）。book 为空时写入写作空间唯一书籍；多本书时需指定 book"""
    from src.data.character_store import CharacterStore
    book = _resolve_book(book)
    if not book:
        return {"ok": False, "message": "无法确定书籍：请指定 book 参数（写作空间有多本书）"}
    store = CharacterStore(book=book)
    for c in store.load_all():
        if c.get("name") == name:
            store.update(c["id"], {
                "name": name, "role_type": role_type, "personality": personality,
                "background": background, "status": status, "location": location,
                "appearance": appearance, "abilities": abilities or [], "book": book,
            })
            return {"ok": True, "message": f"角色「{name}」已更新（书：{book}）"}
    store.add({
        "name": name, "role_type": role_type, "personality": personality,
        "background": background, "status": status, "location": location,
        "appearance": appearance, "abilities": abilities or [], "book": book,
    })
    return {"ok": True, "message": f"角色「{name}」已新建（书：{book}）"}


def _save_hook(content: str, type_: str = "主线", status: str = "已埋下",
               planted_chapter: int = 1, expected_chapter: int = 10,
               actual_chapter: int = 0, notes: str = "", book: str = "") -> dict:
    """保存悬念（不存在则新建，存在则更新）"""
    from src.data.hook_store import HookStore
    book = _resolve_book(book)
    if not book:
        return {"ok": False, "message": "无法确定书籍：请指定 book 参数（写作空间有多本书）"}
    store = HookStore(book=book)
    for h in store.load_all():
        if h.get("content") == content:
            store.update(h["id"], {
                "content": content, "type": type_, "status": status,
                "planted_chapter": planted_chapter, "expected_chapter": expected_chapter,
                "actual_chapter": actual_chapter, "notes": notes, "book": book,
            })
            return {"ok": True, "message": "悬念已更新"}
    store.add({
        "content": content, "type": type_, "status": status,
        "planted_chapter": planted_chapter, "expected_chapter": expected_chapter,
        "actual_chapter": actual_chapter, "characters": [], "notes": notes, "book": book,
    })
    return {"ok": True, "message": "悬念已新建"}


def _save_event(title: str, content: str, chapter: int = 1, branch: str = "主线",
                book: str = "") -> dict:
    """保存时间线事件"""
    from src.data.timeline_store import TimelineStore
    book = _resolve_book(book)
    if not book:
        return {"ok": False, "message": "无法确定书籍：请指定 book 参数（写作空间有多本书）"}
    event = TimelineStore(book=book).add_event(
        {"title": title, "content": content, "chapter": chapter, "branch": branch, "book": book})
    return {"ok": True, "message": f"事件「{title}」已记录到时间线（书：{book}）", "id": event.get("id")}


def _resolve_book(book: str = "") -> str:
    """解析书籍名：显式指定则用之；为空时若写作空间只有一本书则返回该书，否则返回空"""
    if book:
        return book
    try:
        from src.data.writing_space import get_writing_space
        books = [n["name"] for n in get_writing_space().list_tree() if n.get("type") == "book"]
        if len(books) == 1:
            return books[0]
    except Exception:
        pass
    return ""


def _write_chapter(book_name: str, chapter_title: str, content: str) -> dict:
    """写入章节到写作空间（书不存在则自动创建）"""
    import shutil
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    tree = ws.list_tree()
    book_exists = any(n.get("type") == "book" and n["name"] == book_name for n in tree)
    if not book_exists:
        ok, msg = ws.create_book(book_name)
        if not ok:
            return {"ok": False, "message": str(msg)}
    # save 使用相对当前目录的路径，必须拼上写作空间根目录
    safe_title = "".join(c for c in chapter_title if c not in r'\/:*?"<>|') or "未命名章节"
    path = os.path.join(ws.root, book_name, f"{safe_title}.md")
    try:
        ws.save(path, content)
        return {"ok": True, "message": f"章节已保存到写作空间：{book_name}/{safe_title}.md", "path": path}
    except Exception as e:
        return {"ok": False, "message": f"保存失败：{e}"}


# ==================== 投递工具 ====================

def _send_to_editor(book_name: str, chapter_title: str = "", content: str = "",
                    editor_email: str = "", attach_chapters: bool = False) -> dict:
    """一键投递章节到编辑邮箱，并记录投递历史"""
    from src.utils.email_sender import send_chapter_to_editor, get_email_config

    cfg = get_email_config()
    target = editor_email or cfg.get("editor_email", "")
    if not target:
        return {"ok": False, "message": "未配置编辑邮箱，请到 系统设置→邮箱投递 配置，或提供 editor_email 参数"}

    attachments = []
    if attach_chapters and book_name:
        try:
            from src.utils.exporter import NovelExporter
            import tempfile
            tmp = tempfile.mkdtemp(prefix="novel_deliver_")
            from src.data.writing_space import get_writing_space
            ws = get_writing_space()
            tree = ws.list_tree()
            chapters = []
            for node in tree:
                if node.get("type") == "book" and node["name"] == book_name:
                    for child in node.get("children", []):
                        if child.get("type") == "chapter":
                            chapters.append({
                                "number": len(chapters) + 1,
                                "title": child["name"],
                                "content": ws.read(child["path"]),
                                "summary": "",
                            })
            if chapters:
                filepath = NovelExporter(output_dir=tmp).export_txt(book_name, chapters, filename=f"{book_name}_投稿.txt")
                attachments = [filepath]
        except Exception:
            attachments = []

    ok, msg = send_chapter_to_editor(
        book_title=book_name or "未命名",
        chapter_title=chapter_title or "章节",
        content=content,
        editor_email=target,
        attachments=attachments,
    )

    # 记录投递历史
    if ok:
        _record_delivery(book_name, chapter_title, target, "成功")
    else:
        _record_delivery(book_name, chapter_title, target, f"失败：{msg[:100]}")

    return {"ok": ok, "message": msg}


def _get_delivery_history() -> list:
    """查询邮箱投递历史记录"""
    if not os.path.isfile(DELIVERIES_FILE):
        return []
    try:
        with open(DELIVERIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data[-20:]
    except (OSError, json.JSONDecodeError):
        return []


def _record_delivery(book_name: str, chapter_title: str, target: str, result: str):
    """写入一条投递记录"""
    try:
        data = []
        if os.path.isfile(DELIVERIES_FILE):
            with open(DELIVERIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "book": book_name,
            "chapter": chapter_title,
            "to": target,
            "result": result,
        })
        os.makedirs(os.path.dirname(DELIVERIES_FILE), exist_ok=True)
        with open(DELIVERIES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ==================== 工具注册表 ====================

# 工具分组：项目数据（写作空间/角色/钩子/事件/邮箱）vs 大纲库
_TOOL_GROUPS = {
    "project": {"list_books", "read_book", "read_chapter", "list_characters",
                "read_character", "list_hooks", "list_events", "save_character",
                "save_hook", "save_event", "write_chapter",
                "send_to_editor", "get_delivery_history"},
    "outline": {"list_outlines", "read_outline", "save_outline"},
}


def get_project_tools(groups: list = None) -> list:
    """
    OpenAI 格式的工具定义列表。

    Args:
        groups: 启用的工具组列表，如 ["project"] 或 ["outline"] 或 ["project", "outline"]
                None 表示全部启用
    """
    all_tools = _all_tools()
    if groups is None:
        return all_tools
    enabled_names = set()
    for g in groups:
        enabled_names.update(_TOOL_GROUPS.get(g, set()))
    return [t for t in all_tools if t["function"]["name"] in enabled_names]


def get_project_tool_handler(groups: list = None) -> Callable[[str, str], str]:
    """返回工具执行函数 (name, arguments_json) -> str"""
    all_tools = {t["function"]["name"]: t for t in _all_tools()}
    registry = _tool_registry()
    enabled_names = None
    if groups is not None:
        enabled_names = set()
        for g in groups:
            enabled_names.update(_TOOL_GROUPS.get(g, set()))

    def handler(name: str, arguments_json: str) -> str:
        if enabled_names is not None and name not in enabled_names:
            return f"工具 {name} 未启用（当前工具组不含此功能）"
        fn = registry.get(name)
        if fn is None:
            return f"未知工具：{name}"
        try:
            args = json.loads(arguments_json or "{}")
            if not isinstance(args, dict):
                args = {}
        except json.JSONDecodeError:
            args = {}
        try:
            return fn(args)
        except Exception as e:
            return f"工具执行失败：{e}"

    return handler


def _all_tools() -> list:
    """全部工具定义（内部）"""
    return [
        {
            "type": "function",
            "function": {
                "name": "list_books",
                "description": "列出写作空间中的所有书籍（书名）。用户问'我的书''我写了什么'时调用",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_book",
                "description": "读取一本书的章节列表及每章开头预览。用户要求总结某本书、讨论剧情时先调用此工具",
                "parameters": {
                    "type": "object",
                    "properties": {"book_name": {"type": "string", "description": "书名"}},
                    "required": ["book_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_chapter",
                "description": "读取指定书籍的指定章节全文。用户要求总结/修改/讨论某个具体章节时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "book_name": {"type": "string", "description": "书名"},
                        "chapter_title": {"type": "string", "description": "章节标题（不含.md后缀）"},
                    },
                    "required": ["book_name", "chapter_title"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_outlines",
                "description": "列出大纲库中的所有作品（标题+分类）。用户问'我的大纲''有哪些作品'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {"category": {"type": "string", "description": "分类过滤（可选）"}},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_outline",
                "description": "读取大纲库中指定作品的大纲内容。用户要求总结/讨论/修改某部作品大纲时调用",
                "parameters": {
                    "type": "object",
                    "properties": {"title": {"type": "string", "description": "作品标题"}},
                    "required": ["title"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_characters",
                "description": "列出所有角色（名称+类型）。用户问'有哪些人物''我的角色'时调用",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_character",
                "description": "读取角色详情（性格/背景/状态/能力）。用户讨论具体人物时调用",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "角色名"}},
                    "required": ["name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_hooks",
                "description": "列出所有悬念/伏笔（内容+类型+状态）。用户问'有哪些悬念''伏笔'时调用",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_events",
                "description": "列出时间线事件（最近30条）。用户问'故事线''大事记'时调用",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "save_outline",
                "description": "把大纲内容保存/更新到大纲库（作品不存在则自动新建）。用户要求'把大纲存下来''保存到大纲区'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "作品标题"},
                        "content": {"type": "string", "description": "完整大纲内容（Markdown）"},
                        "category": {"type": "string", "description": "题材分类，如玄幻/都市/科幻（可选，默认玄幻）"},
                    },
                    "required": ["title", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "save_character",
                "description": "保存角色到当前书籍的角色库（不存在则新建，存在则更新）。用户要求'记录这个人物''保存角色设定'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "角色名"},
                        "role_type": {"type": "string", "description": "主角/配角/反派/龙套"},
                        "personality": {"type": "string", "description": "性格特点"},
                        "background": {"type": "string", "description": "背景故事"},
                        "status": {"type": "string", "description": "存活/死亡/失踪/受伤"},
                        "location": {"type": "string", "description": "当前位置"},
                        "appearance": {"type": "string", "description": "外貌描述"},
                        "abilities": {"type": "array", "items": {"type": "string"}, "description": "能力列表"},
                        "book": {"type": "string", "description": "书籍名（可选，默认当前唯一书籍）"},
                    },
                    "required": ["name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "save_hook",
                "description": "保存悬念/伏笔到当前书籍的钩子库。用户要求'记一下这个伏笔''保存悬念'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "悬念内容"},
                        "type_": {"type": "string", "description": "主线/支线/物品/人物秘密"},
                        "status": {"type": "string", "description": "已埋下/发展中/即将回收/已回收/已遗忘"},
                        "planted_chapter": {"type": "integer", "description": "埋下章节"},
                        "expected_chapter": {"type": "integer", "description": "预期回收章节"},
                        "notes": {"type": "string", "description": "备注"},
                        "book": {"type": "string", "description": "书籍名（可选，默认当前唯一书籍）"},
                    },
                    "required": ["content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "save_event",
                "description": "记录时间线事件到当前书籍的故事线（大事记）。用户要求'记一下剧情进展''记录事件'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "事件标题"},
                        "content": {"type": "string", "description": "事件描述"},
                        "chapter": {"type": "integer", "description": "章节号（可选）"},
                        "book": {"type": "string", "description": "书籍名（可选，默认当前唯一书籍）"},
                    },
                    "required": ["title", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_chapter",
                "description": "把完整章节内容写入写作空间（书不存在自动创建）。用户要求'把这章保存到我的书'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "book_name": {"type": "string", "description": "书名"},
                        "chapter_title": {"type": "string", "description": "章节标题"},
                        "content": {"type": "string", "description": "完整章节正文"},
                    },
                    "required": ["book_name", "chapter_title", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "send_to_editor",
                "description": "一键把章节投递到编辑邮箱（使用设置页配置的SMTP），并记录投递历史。用户要求'投递到邮箱''发给编辑'时调用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "book_name": {"type": "string", "description": "书名"},
                        "chapter_title": {"type": "string", "description": "章节标题（可选）"},
                        "content": {"type": "string", "description": "正文内容（可选）"},
                        "editor_email": {"type": "string", "description": "编辑邮箱（可选，默认用设置里的）"},
                        "attach_chapters": {"type": "boolean", "description": "是否附带全书章节文件作为附件（可选）"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_delivery_history",
                "description": "查询邮箱投递历史记录。用户问'投递记录''发过哪些邮件'时调用",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]


def _tool_registry() -> Dict[str, Callable]:
    """工具名 -> 执行函数 映射"""
    return {
        "list_books": lambda args: json.dumps(_read_books(), ensure_ascii=False),
        "read_book": lambda args: json.dumps(_read_book(args.get("book_name", "")), ensure_ascii=False),
        "read_chapter": lambda args: json.dumps(
            _read_chapter(args.get("book_name", ""), args.get("chapter_title", "")), ensure_ascii=False),
        "list_outlines": lambda args: json.dumps(_list_outlines(args.get("category", "")), ensure_ascii=False),
        "read_outline": lambda args: json.dumps(_read_outline(args.get("title", "")), ensure_ascii=False),
        "list_characters": lambda args: json.dumps(_list_characters(), ensure_ascii=False),
        "read_character": lambda args: json.dumps(_read_character(args.get("name", "")), ensure_ascii=False),
        "list_hooks": lambda args: json.dumps(_list_hooks(), ensure_ascii=False),
        "list_events": lambda args: json.dumps(_list_events(), ensure_ascii=False),
        "save_outline": lambda args: json.dumps(
            _save_outline(args.get("title", ""), args.get("content", ""), args.get("category", "玄幻")),
            ensure_ascii=False),
        "save_character": lambda args: json.dumps(
            _save_character(args.get("name", ""), args.get("role_type", "配角"),
                            args.get("personality", ""), args.get("background", ""),
                            args.get("status", "存活"), args.get("location", ""),
                            args.get("appearance", ""), args.get("abilities")),
            ensure_ascii=False),
        "save_hook": lambda args: json.dumps(
            _save_hook(args.get("content", ""), args.get("type_", "主线"),
                       args.get("status", "已埋下"), args.get("planted_chapter", 1),
                       args.get("expected_chapter", 10), args.get("actual_chapter", 0),
                       args.get("notes", "")),
            ensure_ascii=False),
        "save_event": lambda args: json.dumps(
            _save_event(args.get("title", ""), args.get("content", ""), args.get("chapter", 1)),
            ensure_ascii=False),
        "write_chapter": lambda args: json.dumps(
            _write_chapter(args.get("book_name", ""), args.get("chapter_title", ""), args.get("content", "")),
            ensure_ascii=False),
        "send_to_editor": lambda args: json.dumps(
            _send_to_editor(args.get("book_name", ""), args.get("chapter_title", ""),
                            args.get("content", ""), args.get("editor_email", ""),
                            bool(args.get("attach_chapters", False))),
            ensure_ascii=False),
        "get_delivery_history": lambda args: json.dumps(_get_delivery_history(), ensure_ascii=False),
    }
