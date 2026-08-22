"""
悬念/钩子存储
悬念 CRUD + JSON 持久化
统一存储：指定 book 时读写 写作空间/{书}/hooks.json；不指定时兼容旧路径 data/hooks
"""

import json
import os
import time
import uuid
from typing import List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK_DIR = os.path.join(_PROJECT_ROOT, "data", "hooks")


def _book_data_path(book: str, filename: str) -> str:
    from src.data.writing_space import WORKSPACE_DIR
    return os.path.join(WORKSPACE_DIR, book, filename)


class HookStore:
    """悬念/钩子存储（JSON 文件持久化）"""

    def __init__(self, base_dir: Optional[str] = None, book: Optional[str] = None):
        if base_dir is not None:
            self.file = os.path.join(base_dir, "hooks.json")
        elif book:
            self.file = _book_data_path(book, "hooks.json")
        else:
            self.file = os.path.join(HOOK_DIR, "hooks.json")
        os.makedirs(os.path.dirname(self.file), exist_ok=True)

    def load_all(self) -> List[dict]:
        if not os.path.isfile(self.file):
            return []
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, items: List[dict]):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def add(self, item: dict) -> dict:
        items = self.load_all()
        item = dict(item)
        item["id"] = uuid.uuid4().hex[:10]
        item["created_at"] = time.time()
        items.append(item)
        self._save(items)
        return item

    def update(self, item_id: str, updates: dict) -> bool:
        items = self.load_all()
        for i, it in enumerate(items):
            if it.get("id") == item_id:
                items[i] = {**it, **updates, "id": item_id}
                self._save(items)
                return True
        return False

    def delete(self, item_id: str) -> bool:
        items = self.load_all()
        new_items = [it for it in items if it.get("id") != item_id]
        if len(new_items) == len(items):
            return False
        self._save(new_items)
        return True

    def get(self, item_id: str) -> Optional[dict]:
        for it in self.load_all():
            if it.get("id") == item_id:
                return it
        return None

    def get_overdue(self, current_chapter: int, book: str = "") -> List[dict]:
        """
        查询超期未回收的钩子：未回收（status != 已回收）且预期回收章节 < 当前章节
        Args:
            current_chapter: 当前写到第几章
            book: 书籍名，为空则查全部
        Returns:
            超期钩子列表（按预期回收章节升序）
        """
        overdue = []
        for it in self.load_all():
            if it.get("status") == "已回收":
                continue
            expected = int(it.get("expected_chapter", 0) or 0)
            if expected <= 0:
                continue
            if expected < current_chapter:
                if book and it.get("book", "") != book:
                    continue
                overdue.append(it)
        overdue.sort(key=lambda x: int(x.get("expected_chapter", 0) or 0))
        return overdue


def load_all_books_hooks() -> List[dict]:
    """遍历写作空间所有书目录，合并全部钩子（用于「全部书籍」视图）"""
    from src.data.writing_space import get_writing_space
    result = []
    try:
        for node in get_writing_space().list_tree():
            if node.get("type") != "book":
                continue
            result.extend(HookStore(book=node["name"]).load_all())
    except Exception:
        pass
    return result
