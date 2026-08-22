"""
时间线存储与分支回退
事件持久化 + 分支快照（类似git的checkpoint/rollback）
统一存储：指定 book 时读写 写作空间/{书}/events.json + branches.json；不指定时兼容旧路径 data/timeline
"""

import json
import os
import time
import uuid
from typing import List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIMELINE_DIR = os.path.join(_PROJECT_ROOT, "data", "timeline")


def _book_data_dir(book: str) -> str:
    from src.data.writing_space import WORKSPACE_DIR
    return os.path.join(WORKSPACE_DIR, book)


class TimelineStore:
    """时间线存储"""

    def __init__(self, base_dir: Optional[str] = None, book: Optional[str] = None):
        if base_dir is not None:
            self.base_dir = base_dir
        elif book:
            self.base_dir = _book_data_dir(book)
        else:
            self.base_dir = TIMELINE_DIR
        os.makedirs(self.base_dir, exist_ok=True)
        self.events_file = os.path.join(self.base_dir, "events.json")
        self.branches_file = os.path.join(self.base_dir, "branches.json")

    # ==================== 事件 CRUD ====================

    def load_events(self) -> List[dict]:
        if not os.path.isfile(self.events_file):
            return []
        try:
            with open(self.events_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def save_events(self, events: List[dict]):
        with open(self.events_file, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)

    def add_event(self, event: dict) -> dict:
        events = self.load_events()
        event = dict(event)
        event["id"] = uuid.uuid4().hex[:10]
        event["created_at"] = time.time()
        events.append(event)
        events.sort(key=lambda e: (e.get("chapter", 0), e.get("created_at", 0)))
        self.save_events(events)
        return event

    def update_event(self, event_id: str, updates: dict) -> bool:
        events = self.load_events()
        for i, e in enumerate(events):
            if e.get("id") == event_id:
                events[i] = {**e, **updates, "id": event_id}
                self.save_events(events)
                return True
        return False

    def delete_event(self, event_id: str) -> bool:
        events = self.load_events()
        new_events = [e for e in events if e.get("id") != event_id]
        if len(new_events) == len(events):
            return False
        self.save_events(new_events)
        return True

    # ==================== 分支（快照/回退） ====================

    def list_branches(self) -> List[dict]:
        if not os.path.isfile(self.branches_file):
            return []
        try:
            with open(self.branches_file, "r", encoding="utf-8") as f:
                branches = json.load(f)
            branches.sort(key=lambda b: b.get("created_at", 0), reverse=True)
            return branches
        except (OSError, json.JSONDecodeError):
            return []

    def _save_branches(self, branches: List[dict]):
        with open(self.branches_file, "w", encoding="utf-8") as f:
            json.dump(branches, f, ensure_ascii=False, indent=2)

    def create_branch(self, name: str) -> dict:
        """创建分支点（当前时间线的完整快照）"""
        events = self.load_events()
        branch = {
            "id": uuid.uuid4().hex[:10],
            "name": name,
            "created_at": time.time(),
            "event_count": len(events),
            "events": events,
        }
        branches = self.list_branches()
        branches.append(branch)
        self._save_branches(branches)
        return branch

    def restore_branch(self, branch_id: str, auto_backup: bool = True) -> tuple[bool, str]:
        """回退到分支点。回退前自动备份当前状态"""
        branches = self.list_branches()
        branch = next((b for b in branches if b["id"] == branch_id), None)
        if branch is None:
            return False, "分支不存在"

        if auto_backup:
            self.create_branch(f"回退前自动备份 {time.strftime('%m-%d %H:%M')}")

        self.save_events(branch["events"])
        return True, branch["name"]

    def delete_branch(self, branch_id: str) -> bool:
        branches = self.list_branches()
        new_branches = [b for b in branches if b["id"] != branch_id]
        if len(new_branches) == len(branches):
            return False
        self._save_branches(new_branches)
        return True


_store: Optional[TimelineStore] = None


def load_all_books_events() -> List[dict]:
    """遍历写作空间所有书目录，合并全部事件（用于「全部书籍」视图）"""
    from src.data.writing_space import get_writing_space
    result = []
    try:
        for node in get_writing_space().list_tree():
            if node.get("type") != "book":
                continue
            result.extend(TimelineStore(book=node["name"]).load_events())
    except Exception:
        pass
    return result


def get_timeline_store() -> TimelineStore:
    global _store
    if _store is None:
        _store = TimelineStore()
    return _store
