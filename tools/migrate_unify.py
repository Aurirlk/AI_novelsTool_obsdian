# -*- coding: utf-8 -*-
"""
统一存储迁移脚本
目标结构：写作空间/{书}/ 为唯一数据根
  写作空间/{书}/meta.json、{书}_大纲.md、{书}_细纲.md、characters.json、hooks.json、events.json、branches.json

迁移内容：
1. 小说大纲/{分类}/{编号_作品}/ → 写作空间/{作品}/（大纲/细纲 md + meta.json 记录分类）
2. data/characters/characters.json → 按 book 分组写入 写作空间/{book}/characters.json
3. data/hooks/hooks.json → 按 book 分组写入 写作空间/{book}/hooks.json
4. data/timeline/events.json + branches.json → 按 book 分组写入书目录
5. data/memory/*.json（MemoryManager 旧数据）→ 转换格式合并进书目录

安全：迁移完成后旧数据移动到 data/_legacy_统一存储迁移_YYYYMMDD/ 备份（不删除）
幂等：书目录已有对应文件且内容非空时跳过（重复执行安全）
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(ROOT, "写作空间")
OUTLINE_LIB = os.path.join(ROOT, "小说大纲")
DATA = os.path.join(ROOT, "data")

STATS = {"outline_works": 0, "characters": 0, "hooks": 0, "events": 0, "branches": 0, "memory_merged": 0}
LEGACY = os.path.join(DATA, f"_legacy_统一存储迁移_{datetime.now().strftime('%Y%m%d_%H%M%S')}")


def log(msg):
    print(msg)


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def book_dir(book: str) -> str:
    return os.path.join(WORKSPACE, book)


def ensure_book(book: str) -> str:
    d = book_dir(book)
    os.makedirs(d, exist_ok=True)
    return d


def merge_json_list(target_path, new_items, key="id"):
    """合并列表（按 key 去重），已存在非空则跳过"""
    if not new_items:
        return
    existing = read_json(target_path)
    if existing is None:
        write_json(target_path, new_items)
        return
    seen = {it.get(key) for it in existing if isinstance(it, dict) and it.get(key)}
    merged = list(existing)
    for it in new_items:
        if not isinstance(it, dict):
            continue
        if it.get(key) and it.get(key) in seen:
            continue
        merged.append(it)
        if it.get(key):
            seen.add(it.get(key))
    write_json(target_path, merged)


# ==================== 1. 大纲库 → 书目录 ====================

def migrate_outline_library():
    if not os.path.isdir(OUTLINE_LIB):
        log("[跳过] 小说大纲目录不存在")
        return
    for category in sorted(os.listdir(OUTLINE_LIB)):
        cat_dir = os.path.join(OUTLINE_LIB, category)
        if not os.path.isdir(cat_dir) or category.startswith("."):
            continue
        for entry in sorted(os.listdir(cat_dir)):
            work_dir = os.path.join(cat_dir, entry)
            if not os.path.isdir(work_dir):
                continue
            # 作品名 = 去掉编号前缀
            title = re.sub(r"^\d+_", "", entry)
            # 找到 大纲.md / 细纲.md
            outline_file = detail_file = None
            for fname in os.listdir(work_dir):
                if not fname.endswith(".md"):
                    continue
                if "细纲" in fname:
                    detail_file = os.path.join(work_dir, fname)
                elif "大纲" in fname:
                    outline_file = os.path.join(work_dir, fname)
            if not outline_file and not detail_file:
                continue
            # 建书目录（若已存在则合并文件）
            bd = ensure_book(title)
            copied = False
            for src, dst_name in ((outline_file, f"{title}_大纲.md"), (detail_file, f"{title}_细纲.md")):
                if src and os.path.isfile(src):
                    dst = os.path.join(bd, dst_name)
                    if not os.path.isfile(dst):
                        shutil.copy2(src, dst)
                        copied = True
            # meta.json：记录分类（不覆盖已有）
            meta_path = os.path.join(bd, "meta.json")
            meta = read_json(meta_path) or {}
            if not meta.get("genre"):
                meta["genre"] = category
            write_json(meta_path, meta)
            STATS["outline_works"] += 1
            log(f"[大纲库] {category} / {title} -> 写作空间/{title}/")


# ==================== 2. 角色 ====================

def migrate_characters():
    src = os.path.join(DATA, "characters", "characters.json")
    data = read_json(src)
    if not isinstance(data, list):
        log("[跳过] characters.json 非列表或不存在")
        return
    by_book = {}
    for c in data:
        by_book.setdefault(c.get("book", ""), []).append(c)
    for book, items in by_book.items():
        if not book:
            continue
        ensure_book(book)
        merge_json_list(os.path.join(book_dir(book), "characters.json"), items)
        STATS["characters"] += len(items)
        log(f"[角色] {book}: {len(items)}个 -> 书目录")
    if by_book.get("") and len(by_book) == 1:
        # 全部无 book 的角色：挂到唯一书籍（若有）
        books = [n["name"] for n in _ws_books()]
        if len(books) == 1:
            ensure_book(books[0])
            merge_json_list(os.path.join(book_dir(books[0]), "characters.json"), by_book[""])
            STATS["characters"] += len(by_book[""])
            log(f"[角色] 无book角色({len(by_book[''])}个) -> 挂到 {books[0]}")


def _ws_books():
    result = []
    if os.path.isdir(WORKSPACE):
        for n in sorted(os.listdir(WORKSPACE)):
            if os.path.isdir(os.path.join(WORKSPACE, n)) and not n.startswith("."):
                result.append({"name": n})
    return result


# ==================== 3. 钩子 ====================

def migrate_hooks():
    src = os.path.join(DATA, "hooks", "hooks.json")
    data = read_json(src)
    if not isinstance(data, list):
        log("[跳过] hooks.json 非列表或不存在")
        return
    by_book = {}
    for h in data:
        by_book.setdefault(h.get("book", ""), []).append(h)
    for book, items in by_book.items():
        if not book:
            continue
        ensure_book(book)
        merge_json_list(os.path.join(book_dir(book), "hooks.json"), items)
        STATS["hooks"] += len(items)
        log(f"[钩子] {book}: {len(items)}个 -> 书目录")
    if by_book.get(""):
        books = [n["name"] for n in _ws_books()]
        if len(books) == 1:
            ensure_book(books[0])
            merge_json_list(os.path.join(book_dir(books[0]), "hooks.json"), by_book[""])
            STATS["hooks"] += len(by_book[""])


# ==================== 4. 事件 + 分支 ====================

def migrate_timeline():
    ev_src = os.path.join(DATA, "timeline", "events.json")
    br_src = os.path.join(DATA, "timeline", "branches.json")
    events = read_json(ev_src)
    branches = read_json(br_src) or []

    if isinstance(events, list):
        by_book = {}
        for e in events:
            by_book.setdefault(e.get("book", ""), []).append(e)
        for book, items in by_book.items():
            if not book:
                continue
            ensure_book(book)
            merge_json_list(os.path.join(book_dir(book), "events.json"), items)
            STATS["events"] += len(items)
            log(f"[事件] {book}: {len(items)}个 -> 书目录")

    # 分支：整体复制到涉及的书（分支快照含全部事件，属全局；保留到事件所在书目录）
    if branches:
        books_with_events = set()
        if isinstance(events, list):
            books_with_events = {e.get("book") for e in events if e.get("book")}
        target_books = [b for b in books_with_events if b]
        if not target_books:
            target_books = [n["name"] for n in _ws_books()]
        for book in target_books:
            ensure_book(book)
            dst = os.path.join(book_dir(book), "branches.json")
            if not os.path.isfile(dst):
                write_json(dst, branches)
                STATS["branches"] += len(branches)
                log(f"[分支] {len(branches)}个 -> {book}/branches.json")


# ==================== 5. data/memory 旧数据合并 ====================

def migrate_memory():
    mem_chars = os.path.join(DATA, "memory", "characters.json")
    data = read_json(mem_chars)
    if not isinstance(data, dict):
        log("[跳过] memory/characters.json 非 dict 或不存在")
        return
    # MemoryManager 格式：{id: {id,name,role,personality,background,current_location,is_alive,...}}
    # 转换为 CharacterStore 格式
    books = [n["name"] for n in _ws_books()]
    for char_id, c in data.items():
        if not isinstance(c, dict) or not c.get("name"):
            continue
        role_map = {"protagonist": "主角", "supporting": "配角", "antagonist": "反派", "villain": "反派"}
        converted = {
            "name": c.get("name", ""),
            "role_type": role_map.get(c.get("role", ""), "配角"),
            "personality": c.get("personality", ""),
            "background": c.get("background", ""),
            "status": "存活" if c.get("is_alive", True) else "死亡",
            "location": c.get("current_location", ""),
            "appearance": "",
            "abilities": [],
            "items": [],
            "relationships": [{"name": k, "relation": v} for k, v in (c.get("relationships") or {}).items()],
        }
        # 挂到所有书（或唯一书）
        for book in books:
            ensure_book(book)
            merge_json_list(os.path.join(book_dir(book), "characters.json"), [converted], key="name")
        STATS["memory_merged"] += 1
    if books:
        log(f"[记忆合并] {STATS['memory_merged']}个角色（MemoryManager旧数据）-> 书目录")


# ==================== 6. 备份旧数据 ====================

def backup_legacy():
    moved = []
    for rel in ("characters", "hooks", "timeline"):
        src = os.path.join(DATA, rel)
        if os.path.isdir(src):
            dst = os.path.join(LEGACY, rel)
            os.makedirs(dst, exist_ok=True)
            for fname in os.listdir(src):
                fpath = os.path.join(src, fname)
                if os.path.isfile(fpath):
                    shutil.move(fpath, os.path.join(dst, fname))
                    moved.append(f"{rel}/{fname}")
    if moved:
        log(f"[备份] 旧数据已移动到 {LEGACY}:")
        for m in moved:
            log(f"       {m}")


def main():
    log("=" * 50)
    log("统一存储迁移开始")
    log("=" * 50)
    migrate_outline_library()
    migrate_characters()
    migrate_hooks()
    migrate_timeline()
    migrate_memory()
    log("-" * 50)
    log(f"迁移统计: 大纲作品{STATS['outline_works']} 角色{STATS['characters']} 钩子{STATS['hooks']} 事件{STATS['events']} 分支{STATS['branches']} 记忆合并{STATS['memory_merged']}")
    # 备份旧数据（迁移成功后）
    if any(STATS.values()):
        backup_legacy()
    else:
        log("[提示] 无迁移数据，跳过备份（旧数据保持原位）")
    log("迁移完成。可删除 data/_legacy_* 目录以彻底清理。")


if __name__ == "__main__":
    main()
