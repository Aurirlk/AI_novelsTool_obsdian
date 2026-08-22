"""
书籍元数据管理
每本书的封面/频道/类型/简介，存储在 写作空间/{书名}/meta.json
"""

import json
import os
import shutil
from typing import List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_COVER = "assets/icons/book-open.png"

BOOK_META_FILE = "meta.json"
COVER_FILENAME = "cover.png"


def _book_meta_path(book_dir: str) -> str:
    return os.path.join(book_dir, BOOK_META_FILE)


def list_books() -> List[dict]:
    """
    列出所有书籍及其元数据
    返回: [{name, path, cover, channel, genre, description, chapter_count}]
    """
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    tree = ws.list_tree()
    books = []
    for node in tree:
        if node.get("type") != "book":
            continue
        meta = get_meta(node["name"])
        chapter_count = _count_chapters(node)
        books.append({
            "name": node["name"],
            "path": node["path"],
            "cover": meta.get("cover", ""),
            "channel": meta.get("channel", "男频"),
            "genre": meta.get("genre", ""),
            "description": meta.get("description", ""),
            "chapter_count": chapter_count,
        })
    return books


def _count_chapters(book_node: dict) -> int:
    count = 0
    for child in book_node.get("children", []):
        if child.get("type") == "chapter":
            count += 1
        elif child.get("type") == "folder":
            count += sum(1 for sub in child.get("children", []) if sub.get("type") == "chapter")
    return count


def get_meta(book_name: str) -> dict:
    """读取一本书的元数据（无则默认）"""
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    book_dir = os.path.join(ws.root, book_name)
    meta_path = _book_meta_path(book_dir)
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {"channel": "男频", "genre": "", "description": "", "cover": ""}


def save_meta(book_name: str, channel: str = "男频", genre: str = "",
              description: str = "", cover: str = "") -> dict:
    """保存书籍元数据"""
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    book_dir = os.path.join(ws.root, book_name)
    os.makedirs(book_dir, exist_ok=True)
    meta = get_meta(book_name)
    meta.update({
        "channel": channel,
        "genre": genre,
        "description": description,
        "cover": cover or meta.get("cover", ""),
    })
    with open(_book_meta_path(book_dir), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta


def set_cover(book_name: str, image_path: str) -> str:
    """
    设置书籍封面：把图片复制到 写作空间/{书}/cover.png

    Returns:
        封面相对路径（相对项目根），失败返回空串
    """
    from src.data.writing_space import get_writing_space
    ws = get_writing_space()
    book_dir = os.path.join(ws.root, book_name)
    os.makedirs(book_dir, exist_ok=True)

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        ext = ".png"
    dst = os.path.join(book_dir, f"cover{ext}")
    try:
        shutil.copy2(image_path, dst)
    except OSError:
        return ""
    # 相对项目根路径，便于跨机器
    try:
        rel = os.path.relpath(dst, _PROJECT_ROOT)
    except ValueError:
        rel = dst
    meta = get_meta(book_name)
    meta["cover"] = rel
    save_meta(book_name, channel=meta.get("channel", "男频"), genre=meta.get("genre", ""),
              description=meta.get("description", ""), cover=rel)
    return rel


def get_cover_path(book_name: str) -> Optional[str]:
    """获取封面绝对路径（无封面返回 None）"""
    meta = get_meta(book_name)
    cover = meta.get("cover", "")
    if not cover:
        return None
    abs_path = cover if os.path.isabs(cover) else os.path.join(_PROJECT_ROOT, cover)
    if os.path.isfile(abs_path):
        return abs_path
    return None
