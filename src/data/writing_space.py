"""
写作空间（Obsidian式文件管理）
结构：写作空间/书名/分卷/章节.md，根目录放散文件
删除操作进入回收站（data/trash），支持恢复/清空/30天自动清理
"""

import os
import re
import shutil
import time
from typing import List, Optional, Tuple

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKSPACE_DIR = os.path.join(_PROJECT_ROOT, "写作空间")
TRASH_DIR = os.path.join(_PROJECT_ROOT, "data", "trash")
TRASH_KEEP_DAYS = 30  # 回收站保留天数


def _safe_name(name: str) -> str:
    return "".join(c for c in name.strip() if c not in r'\/:*?"<>|')


class WritingSpace:
    """写作空间文件管理"""

    def __init__(self, root: Optional[str] = None):
        self.root = root or WORKSPACE_DIR
        os.makedirs(self.root, exist_ok=True)

    # ---------- 树结构 ----------

    def list_tree(self) -> List[dict]:
        """列出目录树：[{name, path, type: book/folder, children: [{name, path, type: chapter/folder}]}]"""
        tree = []
        if not os.path.isdir(self.root):
            return tree

        for book in sorted(os.listdir(self.root)):
            book_path = os.path.join(self.root, book)
            if os.path.isfile(book_path):
                if book.endswith(".md"):
                    tree.append({"name": book, "path": book_path, "type": "chapter", "children": []})
                continue
            book_node = {"name": book, "path": book_path, "type": "book", "children": []}
            for entry in sorted(os.listdir(book_path)):
                entry_path = os.path.join(book_path, entry)
                if os.path.isdir(entry_path):
                    folder_node = {"name": entry, "path": entry_path, "type": "folder", "children": []}
                    for fname in sorted(os.listdir(entry_path)):
                        if fname.endswith(".md"):
                            folder_node["children"].append({
                                "name": fname[:-3], "path": os.path.join(entry_path, fname),
                                "type": "chapter", "children": []})
                    book_node["children"].append(folder_node)
                elif entry.endswith(".md"):
                    book_node["children"].append({
                        "name": entry[:-3], "path": entry_path,
                        "type": "chapter", "children": []})
            tree.append(book_node)
        return tree

    # ---------- 创建 ----------

    def create_book(self, name: str) -> Tuple[bool, str]:
        name = _safe_name(name)
        if not name:
            return False, "书名不能为空"
        path = os.path.join(self.root, name)
        if os.path.exists(path):
            return False, "已存在同名书"
        os.makedirs(path)
        return True, path

    def create_folder(self, book_path: str, name: str) -> Tuple[bool, str]:
        name = _safe_name(name)
        if not name:
            return False, "名称不能为空"
        path = os.path.join(book_path, name)
        if os.path.exists(path):
            return False, "已存在同名目录"
        os.makedirs(path)
        return True, path

    def create_chapter(self, parent_path: str, title: str) -> Tuple[bool, str]:
        title = _safe_name(title)
        if not title:
            return False, "章节名不能为空"
        path = os.path.join(parent_path, f"{title}.md")
        if os.path.exists(path):
            return False, "已存在同名章节"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
        return True, path

    # ---------- 重命名/删除 ----------

    def rename(self, path: str, new_name: str) -> Tuple[bool, str]:
        new_name = _safe_name(new_name)
        if not new_name:
            return False, "名称不能为空"
        parent = os.path.dirname(path)
        if path.endswith(".md"):
            new_name += ".md"
        new_path = os.path.join(parent, new_name)
        if os.path.exists(new_path):
            return False, "已存在同名项"
        os.rename(path, new_path)
        return True, new_path

    def delete(self, path: str) -> Tuple[bool, str]:
        """删除：移入回收站（data/trash），可恢复"""
        if os.path.commonpath([os.path.abspath(path),
                               os.path.abspath(self.root)]) != os.path.abspath(self.root):
            return False, "非法路径"
        if not os.path.exists(path):
            return False, "路径不存在"

        # 移入回收站：trash/时间戳_原名/（统一目录结构，含 _origin.txt）
        ts = time.strftime("%Y%m%d_%H%M%S")
        entry_name = f"{ts}_{os.path.basename(path)}"
        entry_dir = os.path.join(TRASH_DIR, entry_name)
        os.makedirs(entry_dir, exist_ok=True)

        dst = os.path.join(entry_dir, os.path.basename(path))
        try:
            shutil.move(path, dst)
            with open(os.path.join(entry_dir, "_origin.txt"), "w", encoding="utf-8") as f:
                f.write(os.path.abspath(path))
        except Exception as e:
            shutil.rmtree(entry_dir, ignore_errors=True)
            return False, f"移入回收站失败：{e}"
        return True, entry_dir

    # ---------- 回收站 ----------

    def list_trash(self) -> List[dict]:
        """列出回收站内容：[{entry, name, origin, deleted_at}]"""
        items = []
        if not os.path.isdir(TRASH_DIR):
            return items
        for entry in sorted(os.listdir(TRASH_DIR), reverse=True):
            entry_dir = os.path.join(TRASH_DIR, entry)
            if not os.path.isdir(entry_dir):
                continue
            origin = ""
            origin_file = os.path.join(entry_dir, "_origin.txt")
            if os.path.isfile(origin_file):
                try:
                    with open(origin_file, "r", encoding="utf-8") as f:
                        origin = f.read().strip()
                except OSError:
                    pass
            items.append({
                "entry": entry,
                "name": entry.split("_", 2)[-1] if "_" in entry else entry,
                "origin": origin,
                "deleted_at": entry.split("_", 1)[0] if "_" in entry else "",
            })
        return items

    def restore(self, entry: str, overwrite: bool = False) -> Tuple[bool, str]:
        """从回收站恢复指定条目

        Args:
            entry: 回收站条目名（list_trash 返回的 entry）
            overwrite: 目标已存在同名节点时是否覆盖（False 且冲突时返回 False,"conflict"）

        Returns:
            (是否成功, 新路径或错误信息)
        """
        entry_dir = os.path.join(TRASH_DIR, entry)
        if not os.path.isdir(entry_dir):
            return False, "回收站条目不存在"

        origin = ""
        origin_file = os.path.join(entry_dir, "_origin.txt")
        if os.path.isfile(origin_file):
            try:
                with open(origin_file, "r", encoding="utf-8") as f:
                    origin = f.read().strip()
            except OSError:
                pass

        if not origin:
            return False, "回收站条目缺少原始路径信息，无法恢复"

        # 目标位置必须仍在写作空间内
        try:
            inside = os.path.commonpath([os.path.abspath(origin),
                                         os.path.abspath(self.root)]) == os.path.abspath(self.root)
        except ValueError:
            inside = False
        if not inside:
            return False, "原始路径不在写作空间内，无法恢复"

        if os.path.exists(origin):
            if not overwrite:
                return False, "conflict"
            if os.path.isdir(origin):
                shutil.rmtree(origin, ignore_errors=True)
            else:
                os.remove(origin)

        os.makedirs(os.path.dirname(origin), exist_ok=True)
        src = os.path.join(entry_dir, os.path.basename(origin))
        if not os.path.exists(src):
            # 兼容：源文件名可能与 origin 名不一致（重命名后删除）
            leftovers = [n for n in os.listdir(entry_dir) if n != "_origin.txt"]
            if leftovers:
                src = os.path.join(entry_dir, leftovers[0])
            else:
                return False, "回收站条目内容缺失"
        shutil.move(src, origin)
        os.remove(origin_file)
        # 条目目录已空则清理
        try:
            os.rmdir(entry_dir)
        except OSError:
            pass
        return True, origin

    def empty_trash(self) -> int:
        """清空回收站，返回清除的条目数"""
        count = 0
        if os.path.isdir(TRASH_DIR):
            for entry in os.listdir(TRASH_DIR):
                entry_dir = os.path.join(TRASH_DIR, entry)
                if os.path.isdir(entry_dir):
                    shutil.rmtree(entry_dir, ignore_errors=True)
                    count += 1
        return count

    def cleanup_trash(self, days: int = TRASH_KEEP_DAYS) -> int:
        """清理超过保留天数的回收站条目，返回清理数量"""
        cutoff = time.time() - days * 86400
        count = 0
        if not os.path.isdir(TRASH_DIR):
            return 0
        for entry in os.listdir(TRASH_DIR):
            entry_dir = os.path.join(TRASH_DIR, entry)
            if not os.path.isdir(entry_dir):
                continue
            ts_part = entry.split("_", 1)[0]
            try:
                ts = time.mktime(time.strptime(ts_part, "%Y%m%d"))
            except (ValueError, OSError):
                continue
            if ts < cutoff:
                shutil.rmtree(entry_dir, ignore_errors=True)
                count += 1
        return count

    # ---------- 读写 ----------

    @staticmethod
    def read(path: str) -> str:
        for encoding in ("utf-8", "gbk"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, OSError):
                continue
        return ""

    @staticmethod
    def save(path: str, content: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


_space: Optional[WritingSpace] = None


def get_writing_space() -> WritingSpace:
    global _space
    if _space is None:
        _space = WritingSpace()
    return _space
