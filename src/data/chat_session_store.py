"""
聊天会话存储
AI助手的历史对话保存/加载/删除
"""

import json
import os
import time
import uuid
from typing import List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SESSIONS_DIR = os.path.join(_PROJECT_ROOT, "data", "chat_sessions")


class ChatSessionStore:
    """聊天会话存储"""

    def __init__(self, sessions_dir: Optional[str] = None):
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        os.makedirs(self.sessions_dir, exist_ok=True)

    def save_session(self, messages: List[dict], provider: str = "", model: str = "",
                     session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """保存（新建或更新）会话，返回会话ID"""
        if not messages:
            return session_id or ""

        if session_id is None:
            session_id = uuid.uuid4().hex[:12]

        if title is None:
            first_user = next((m["content"] for m in messages if m.get("role") == "user"), "")
            title = first_user.replace("\n", " ")[:24] or "未命名对话"

        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        created_at = time.time()
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    created_at = json.load(f).get("created_at", created_at)
            except (OSError, json.JSONDecodeError):
                pass

        data = {
            "id": session_id,
            "title": title,
            "provider": provider,
            "model": model,
            "created_at": created_at,
            "updated_at": time.time(),
            "messages": messages,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return session_id

    def list_sessions(self) -> List[dict]:
        """列出会话（最新在前，不含messages正文）"""
        sessions = []
        if not os.path.isdir(self.sessions_dir):
            return sessions
        for fname in os.listdir(self.sessions_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self.sessions_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "id": data.get("id", fname[:-5]),
                    "title": data.get("title", "未命名对话"),
                    "model": data.get("model", ""),
                    "updated_at": data.get("updated_at", 0),
                    "message_count": len(data.get("messages", [])),
                })
            except (OSError, json.JSONDecodeError):
                continue
        sessions.sort(key=lambda s: s["updated_at"], reverse=True)
        return sessions

    def load_session(self, session_id: str) -> Optional[dict]:
        """加载完整会话"""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False


_store: Optional[ChatSessionStore] = None


def get_chat_session_store() -> ChatSessionStore:
    global _store
    if _store is None:
        _store = ChatSessionStore()
    return _store
