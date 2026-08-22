"""
章节记忆提取器
章节保存后自动提取：角色状态变化 / 新钩子 / 钩子回收 / 大事记
输出结构化变更清单，供自动写入或人工确认
"""

import json
import re
import uuid
from datetime import datetime
from typing import List, Optional

_EXAMPLE_OUTPUT = """{
  "characters": [
    {"name": "林动", "action": "new", "role_type": "主角",
     "personality": "隐忍坚韧，重情重义", "background": "落魄家族子弟",
     "appearance": "身形单薄，眼神坚毅", "location": "青云宗",
     "status": "存活",
     "abilities": [{"name": "淬体九重", "description": "肉体强度达到九重境界，可徒手碎岩"}],
     "items": [{"name": "淬体丹", "description": "加速淬体修炼的丹药"}],
     "relationships": [{"name": "王炎", "relation": "仇敌，被其当众羞辱"}]
    }
  ],
  "new_hooks": [
    {"content": "无名老人留下的玉简", "type": "物品", "expected_resolve_chapter": 30}
  ],
  "resolved_hooks": [
    {"content": "第一章的黑衣人身份", "resolved_chapter": 12}
  ],
  "events": [
    {"content": "林动击败王炎，获得淬体丹", "event_type": "战斗", "importance": 7}
  ]
}"""


def _parse_json_response(response: str) -> dict:
    """从LLM响应中解析JSON（容错：截取首个{...}块）"""
    if not response:
        return {}
    try:
        match = re.search(r"\{.*\}", response, re.S)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


def extract_memory_changes(chapter_text: str, book_name: str = "",
                           chapter_num: int = 0) -> dict:
    """
    用LLM提取章节中的记忆变更

    Returns:
        {"characters": [...], "new_hooks": [...], "resolved_hooks": [...], "events": [...],
         "ok": bool, "error": str}
    """
    empty = {
        "characters": [], "new_hooks": [], "resolved_hooks": [], "events": [],
        "ok": False, "error": "",
    }
    if not chapter_text or not chapter_text.strip():
        empty["error"] = "章节内容为空"
        return empty

    text = chapter_text[:4000]  # 截断控制token

    prompt = f"""你是小说的记忆管理员。阅读下面的章节，提取对全书记忆有影响的变更。
只提取【确定发生】的信息，不要臆测。

输出要求（严格JSON，不要输出JSON以外的任何内容）：
{_EXAMPLE_OUTPUT}

字段说明：
- characters.action: "update"（已有角色状态变化）或 "new"（新登场重要角色，仅限有姓名且影响剧情的）
- characters: 只输出【状态变化】的角色；new 角色必须尽力填写全部字段（personality/background/appearance 不能留空，要按原文推断）
- characters.personality: 性格特点（2-10字概括）
- characters.background: 背景身世
- characters.appearance: 外貌特征
- characters.abilities: 能力数组，每项 {"name": 能力名, "description": 能力效果/限制说明}——不要只给名字，必须给出该能力的作用描述
- characters.items: 物品数组，每项 {"name": 物品名, "description": 物品用途/来历说明}
- characters.relationships: 关系数组，每项 {"name": 关系对象, "relation": 关系描述（敌友/恩怨/亲属等）}
- new_hooks: 本章新埋下的钩子/悬念（未解决的疑问、伏笔）
- resolved_hooks: 本章回收的旧钩子（需与原文明确对应）
- events: 本章重要事件（战斗/突破/转折等），importance 1-10
- 没有对应变更时输出空数组 []

【书籍】{book_name}
【章节】第{chapter_num}章
【正文】
{text}
"""
    try:
        from src.utils.llm import get_llm_client
        client = get_llm_client()
        response = client.chat(prompt, system_prompt="你是严格的小说记忆管理员，只输出JSON，不输出任何其他内容。")
        data = _parse_json_response(response)
        result = {
            "characters": data.get("characters") or [],
            "new_hooks": data.get("new_hooks") or [],
            "resolved_hooks": data.get("resolved_hooks") or [],
            "events": data.get("events") or [],
        }
        # 校验字段类型，防止脏数据写入
        for key in result:
            if not isinstance(result[key], list):
                result[key] = []
        result["ok"] = True
        return result
    except Exception as e:
        empty["error"] = str(e)
        return empty


# ==================== 写入现有 Store（去重合并） ====================

def _normalize_ability_items(items) -> list:
    """
    规范化能力/物品列表：兼容两种输入
    - 旧数据/简单输入：["淬体九重"] → [{"name": "淬体九重", "description": ""}]
    - 新结构：{"name": "淬体九重", "description": "..."} 或 dict 列表
    """
    result = []
    if not items:
        return result
    for it in items:
        if isinstance(it, dict):
            result.append({
                "name": str(it.get("name", "")).strip(),
                "description": str(it.get("description", "")).strip(),
            })
        else:
            result.append({"name": str(it).strip(), "description": ""})
    return [r for r in result if r["name"]]


def _normalize_relationships(rels) -> list:
    """规范化人物关系：兼容 dict 或 "对象-关系" 字符串"""
    result = []
    if not rels:
        return result
    for r in rels:
        if isinstance(r, dict):
            result.append({
                "name": str(r.get("name", "")).strip(),
                "relation": str(r.get("relation", "")).strip(),
            })
        else:
            text = str(r).strip()
            if "-" in text:
                n, _, rel = text.partition("-")
                result.append({"name": n.strip(), "relation": rel.strip()})
            else:
                result.append({"name": text, "relation": ""})
    return [r for r in result if r["name"]]


def apply_to_stores(changes: dict, book_name: str = "", chapter_num: int = 0) -> dict:
    """
    将提取结果写入 CharacterStore / HookStore / TimelineStore（幂等：按名称/内容去重）
    Returns: 实际写入统计 {"characters": n, "new_hooks": n, "resolved_hooks": n, "events": n}
    """
    stats = {"characters": 0, "new_hooks": 0, "resolved_hooks": 0, "events": 0}
    if not changes or not changes.get("ok"):
        return stats

    from src.data.character_store import CharacterStore
    from src.data.hook_store import HookStore
    from src.data.timeline_store import TimelineStore

    # ---------- 角色 ----------
    store = CharacterStore(book=book_name or None)
    existing = store.load_all()
    for ch in changes.get("characters", []):
        name = str(ch.get("name", "")).strip()
        if not name:
            continue
        # 同书同名 → 更新
        target = None
        for e in existing:
            if e.get("name") == name and (book_name == "" or e.get("book", "") == book_name):
                target = e
                break
        if target:
            updates = {}
            for field in ("role_type", "personality", "background", "status", "location", "appearance"):
                if ch.get(field):
                    updates[field] = str(ch[field])
            if ch.get("abilities"):
                updates["abilities"] = _normalize_ability_items(ch["abilities"])
            if ch.get("items"):
                updates["items"] = _normalize_ability_items(ch["items"])
            if ch.get("relationships"):
                updates["relationships"] = _normalize_relationships(ch["relationships"])
            if updates:
                store.update(target["id"], updates)
                stats["characters"] += 1
        else:
            store.add({
                "name": name,
                "book": book_name,
                "role_type": str(ch.get("role_type", "龙套")),
                "personality": str(ch.get("personality", "")),
                "background": str(ch.get("background", "")),
                "status": str(ch.get("status", "存活")),
                "location": str(ch.get("location", "")),
                "appearance": str(ch.get("appearance", "")),
                "abilities": _normalize_ability_items(ch.get("abilities", [])),
                "items": _normalize_ability_items(ch.get("items", [])),
                "relationships": _normalize_relationships(ch.get("relationships", [])),
            })
            stats["characters"] += 1

    # ---------- 钩子 ----------
    hstore = HookStore(book=book_name or None)
    hooks = hstore.load_all()
    for h in changes.get("new_hooks", []):
        content = str(h.get("content", "")).strip()
        if not content:
            continue
        # 同书同内容 → 跳过（已存在）
        if any(he.get("content", "").strip() == content
               and (book_name == "" or he.get("book", "") == book_name) for he in hooks):
            continue
        hstore.add({
            "content": content,
            "type": str(h.get("type", "主线")),
            "status": "已埋下",
            "planted_chapter": chapter_num or int(h.get("planted_chapter", 0) or 0),
            "expected_chapter": int(h.get("expected_resolve_chapter", 0) or 0),
            "actual_chapter": 0,
            "characters": [str(c) for c in h.get("characters", []) if isinstance(c, str)],
            "notes": "",
            "book": book_name,
        })
        stats["new_hooks"] += 1

    # 回收旧钩子
    for h in changes.get("resolved_hooks", []):
        content = str(h.get("content", "")).strip()
        if not content:
            continue
        for he in hooks:
            if (he.get("content", "").strip() == content or content in he.get("content", "")
                    or he.get("content", "").strip() in content) \
                    and he.get("status") != "已回收":
                hstore.update(he["id"], {
                    "status": "已回收",
                    "actual_chapter": int(h.get("resolved_chapter", chapter_num or 0) or 0),
                })
                stats["resolved_hooks"] += 1
                break

    # ---------- 事件 ----------
    tstore = TimelineStore(book=book_name or None)
    for ev in changes.get("events", []):
        content = str(ev.get("content", "")).strip()
        if not content:
            continue
        tstore.add_event({
            "title": content[:50],
            "content": content,
            "chapter": chapter_num,
            "branch": "main",
            "book": book_name,
            "event_type": str(ev.get("event_type", "剧情转折")),
            "importance": int(ev.get("importance", 5) or 5),
            "related_characters": [str(c) for c in ev.get("characters", []) if isinstance(c, str)],
        })
        stats["events"] += 1

    return stats


def summarize_changes(changes: dict) -> str:
    """生成变更摘要（用于确认对话框展示）"""
    if not changes or not changes.get("ok"):
        return "本次未提取到记忆变更。"
    lines = []
    for ch in changes.get("characters", []):
        name = ch.get("name", "")
        action = "新增角色" if ch.get("action") == "new" else "角色更新"
        parts = [f"{action}：{name}"]
        if ch.get("location"):
            parts.append(f"位置={ch['location']}")
        if ch.get("status"):
            parts.append(f"状态={ch['status']}")
        lines.append(" · ".join(parts))
    for h in changes.get("new_hooks", []):
        lines.append(f"新钩子：{h.get('content', '')[:40]}")
    for h in changes.get("resolved_hooks", []):
        lines.append(f"钩子回收：{h.get('content', '')[:40]}")
    for ev in changes.get("events", []):
        lines.append(f"事件：{ev.get('content', '')[:40]}")
    if not lines:
        return "本次未提取到记忆变更。"
    return "\n".join(lines)
