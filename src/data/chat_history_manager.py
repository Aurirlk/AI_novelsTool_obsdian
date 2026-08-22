"""
AI 助手对话历史管理器

独立于 HistoryManager(后者服务于大纲/章节等生成功能)。
专门管理 chat_page 的多轮对话:

- 每次对话一个 JSON 文件
- 自动保存(AI 回复完成后触发)
- 支持列表/加载/删除/搜索
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ChatSession:
    """一次完整的 AI 助手对话"""

    id: str
    title: str                                    # 首条用户消息截取
    provider: str = ""
    model: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        return cls(**data)


class ChatHistoryManager:
    """AI 助手对话历史管理器"""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            base_dir = os.path.join(project_root, "data", "chat_history")
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    # ---------- 基础 CRUD ----------

    def _filepath(self, session_id: str) -> str:
        safe = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return os.path.join(self.base_dir, f"{safe}.json")

    def create_session(self, provider: str = "", model: str = "") -> ChatSession:
        """开始一次新对话"""
        return ChatSession(
            id=uuid.uuid4().hex[:12],
            title="新对话",
            provider=provider,
            model=model,
        )

    def save_session(self, session: ChatSession) -> str:
        """保存(或更新)对话"""
        session.updated_at = datetime.now().isoformat()
        # 用首条用户消息生成标题
        if session.title in ("", "新对话"):
            for msg in session.messages:
                if msg.get("role") == "user":
                    text = msg.get("content", "").strip().replace("\n", " ")
                    # 去掉附件块,只留用户输入
                    if "【用户消息】" in text:
                        text = text.split("【用户消息】", 1)[1].strip()
                    session.title = (text[:24] + "…") if len(text) > 24 else (text or "未命名")
                    break
        with open(self._filepath(session.id), "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        return self._filepath(session.id)

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        path = self._filepath(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return ChatSession.from_dict(json.load(f))
        except (json.JSONDecodeError, OSError, TypeError):
            return None

    def delete_session(self, session_id: str) -> bool:
        path = self._filepath(session_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False

    # ---------- 列表与搜索 ----------

    def list_sessions(self, limit: int = 100) -> List[ChatSession]:
        """按更新时间倒序返回最近 N 条"""
        sessions: List[ChatSession] = []
        if not os.path.isdir(self.base_dir):
            return sessions
        for filename in os.listdir(self.base_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.base_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sessions.append(ChatSession.from_dict(json.load(f)))
            except (json.JSONDecodeError, OSError, TypeError):
                continue
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]

    def search(self, keyword: str, limit: int = 50) -> List[ChatSession]:
        keyword = keyword.strip().lower()
        if not keyword:
            return self.list_sessions(limit)
        matched = []
        for s in self.list_sessions(limit=500):
            if keyword in s.title.lower():
                matched.append(s)
                continue
            for msg in s.messages:
                if keyword in msg.get("content", "").lower():
                    matched.append(s)
                    break
        return matched[:limit]


# 全局单例
_chat_history_manager: Optional[ChatHistoryManager] = None


def get_chat_history_manager() -> ChatHistoryManager:
    global _chat_history_manager
    if _chat_history_manager is None:
        _chat_history_manager = ChatHistoryManager()
    return _chat_history_manager
