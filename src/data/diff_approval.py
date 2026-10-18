"""
AI 变更暂存与 Diff 审批（goink diff-approval 模式）

核心规则：
- AI 通过工具写入正文（>500 字）时**不直接落盘**，先暂存为 pending 变更；
- 前端 Diff 审批面板由用户批准/拒绝；
- 批准后落盘 + 自动 git commit（turn_commits 存档）；
- pending 内容含正文，存放在 gitignored 的 data/ 下，不进仓库。
"""

import json
import os
import threading
import time
import uuid

from typing import Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PENDING_FILE = os.path.join(_PROJECT_ROOT, "data", "pending_changes.json")

# worker 线程（write_chapter 暂存）与 UI 线程（approve/reject）并发读改写同一文件，
# 模块级锁保证 read-modify-write 原子性
_lock = threading.Lock()


def _load() -> list:
    if not os.path.isfile(PENDING_FILE):
        return []
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return list(data) if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save(changes: list):
    os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
    # 保留全部 pending + 最近 50 条已决记录，防止含全文的旧记录无限膨胀
    kept = [c for c in changes if c.get("status") == "pending"]
    decided = [c for c in changes if c.get("status") != "pending"][-50:]
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(kept + decided, f, ensure_ascii=False, indent=2)


def stage_change(book_name: str, chapter_title: str, path: str, new_content: str) -> dict:
    """
    暂存一次 AI 正文写入（不落盘）。

    同一章节已有 pending 变更时直接覆盖（AI 后续修改替换旧暂存）。
    """
    with _lock:
        changes = _load()
        for c in changes:
            if c.get("path") == path and c.get("status") == "pending":
                c["new_content"] = new_content
                c["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                _save(changes)
                return c
        change = {
            "id": uuid.uuid4().hex[:12],
            "book_name": book_name,
            "chapter_title": chapter_title,
            "path": path,
            "old_content": _read_file(path),
            "new_content": new_content,
            "status": "pending",  # pending / approved / rejected
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commit_hash": "",
        }
        changes.append(change)
        _save(changes)
        return change


def _read_file(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    for encoding in ("utf-8", "gbk"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, OSError):
            continue
    return ""


def list_pending() -> list:
    """未审批的变更列表（按时间顺序）"""
    return [c for c in _load() if c.get("status") == "pending"]


def count_pending() -> int:
    return len(list_pending())


def get_change(change_id: str) -> Optional[dict]:
    for c in _load():
        if c.get("id") == change_id:
            return c
    return None


def approve(change_id: str) -> Optional[dict]:
    """
    批准变更：落盘 + 自动 git commit（AI 变更，turn_commits 存档）。
    返回更新后的变更；找不到或状态非 pending 返回 None。
    """
    with _lock:
        changes = _load()
        for c in changes:
            if c.get("id") == change_id and c.get("status") == "pending":
                try:
                    from src.data.writing_space import get_writing_space
                    get_writing_space().save(c["path"], c["new_content"])
                except Exception as e:
                    return {"error": f"落盘失败：{e}"}
                from src.utils.git_commits import record_and_commit
                entry = record_and_commit(
                    "ai", f"AI 写入：{c['book_name']}/{c['chapter_title']}（Diff 审批通过）")
                c["status"] = "approved"
                c["commit_hash"] = entry.get("hash", "")
                c["approved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                _save(changes)
                return c
    return None


def reject(change_id: str) -> Optional[dict]:
    """拒绝变更：丢弃暂存内容，不落盘"""
    with _lock:
        changes = _load()
        for c in changes:
            if c.get("id") == change_id and c.get("status") == "pending":
                c["status"] = "rejected"
                _save(changes)
                return c
    return None


def approve_all() -> tuple[int, list]:
    """批量批准全部 pending 变更。返回 (成功数量, 失败原因列表)"""
    ok_count = 0
    errors = []
    for c in list_pending():
        result = approve(c["id"])
        if result is None:
            continue
        if "error" in result:
            errors.append(f"{c['book_name']}/{c['chapter_title']}: {result['error']}")
        else:
            ok_count += 1
    return ok_count, errors


def reject_all() -> int:
    """批量拒绝全部 pending 变更"""
    count = 0
    for c in list_pending():
        if reject(c["id"]):
            count += 1
    return count
