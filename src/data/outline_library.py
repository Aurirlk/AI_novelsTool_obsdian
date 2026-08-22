"""
大纲库（统一存储版）
以 写作空间/{书}/ 为数据根：
    写作空间/{书}/{书}_大纲.md + {书}_细纲.md，分类记录在 meta.json 的 genre 字段

接口保持与旧版一致：refresh / list_categories / list_works / count /
read_work / create_work / rename_work / delete_work / library_dir / read_content
"""

import os
import re
import shutil
from dataclasses import dataclass
from typing import List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 统一数据根 = 写作空间（兼容旧属性名 library_dir）
DEFAULT_LIBRARY_DIR = os.path.join(_PROJECT_ROOT, "写作空间")


@dataclass
class OutlineWork:
    """一部作品（= 写作空间里的一本书）"""
    title: str
    category: str
    path: str
    outline_file: Optional[str] = None   # {书}_大纲.md
    detail_file: Optional[str] = None    # {书}_细纲.md


def _book_data_dir() -> str:
    """书数据根目录"""
    return DEFAULT_LIBRARY_DIR


def _category_of(book_dir: str) -> str:
    """从 meta.json 读分类（默认「未分类」）"""
    try:
        import json
        with open(os.path.join(book_dir, "meta.json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
        return str(meta.get("genre", "") or "未分类")
    except Exception:
        return "未分类"


class OutlineLibrary:
    """大纲库：扫描写作空间书目录，把每本书的 大纲/细纲 md 接入大纲页"""

    def __init__(self, library_dir: Optional[str] = None):
        self.library_dir = library_dir or DEFAULT_LIBRARY_DIR
        self._works: List[OutlineWork] = []
        self.refresh()

    def refresh(self):
        """重新扫描写作空间书目录"""
        self._works = []
        if not os.path.isdir(self.library_dir):
            return

        for entry in sorted(os.listdir(self.library_dir)):
            book_dir = os.path.join(self.library_dir, entry)
            if not os.path.isdir(book_dir) or entry.startswith("."):
                continue

            outline_file, detail_file = None, None
            for fname in os.listdir(book_dir):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(book_dir, fname)
                if "细纲" in fname:
                    detail_file = fpath
                elif "大纲" in fname:
                    outline_file = fpath

            if outline_file or detail_file:
                self._works.append(OutlineWork(
                    title=entry,
                    category=_category_of(book_dir),
                    path=book_dir,
                    outline_file=outline_file,
                    detail_file=detail_file,
                ))

    def list_categories(self) -> List[str]:
        """所有题材分类（来自 meta.json genre）"""
        return sorted({w.category for w in self._works})

    def list_works(self, category: Optional[str] = None) -> List[OutlineWork]:
        """作品列表，可按分类过滤"""
        if category and category != "全部分类":
            return [w for w in self._works if w.category == category]
        return list(self._works)

    def count(self) -> int:
        return len(self._works)

    # ==================== 分类管理（统一存储：分类 = meta.json 的 genre） ====================

    def create_category(self, name: str) -> tuple[bool, str]:
        """新建题材分类（兼容旧接口：统一存储下分类由各书 meta.json 的 genre 决定，
        此处仅校验分类名合法性，不创建实际目录）"""
        name = self._safe_name(name)
        if not name:
            return False, "分类名不能为空"
        if name in self.list_categories():
            return False, f"分类「{name}」已存在"
        # 统一存储下不创建独立分类目录；分类随作品创建时写入 meta.json
        self.refresh()
        return True, name

    def delete_category(self, name: str) -> tuple[bool, str]:
        """删除分类（兼容旧接口）：将属于该分类的作品 genre 改为「未分类」"""
        works = self.list_works(name)
        if not works:
            return False, f"分类「{name}」不存在或没有作品"
        import json
        for w in works:
            meta_path = os.path.join(w.path, "meta.json")
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["genre"] = "未分类"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            except Exception:
                continue
        self.refresh()
        return True, name

    # ==================== 作品管理 ====================

    @staticmethod
    def _safe_name(name: str) -> str:
        """清理文件系统非法字符"""
        return "".join(c for c in name.strip() if c not in r'\/:*?"<>|')

    def create_work(self, category: str, title: str) -> tuple[bool, object]:
        """新建作品（= 写作空间里新建书目录 + 大纲/细纲模板）"""
        title = self._safe_name(title)
        if not title:
            return False, "作品名不能为空"

        book_dir = os.path.join(self.library_dir, title)
        if os.path.exists(book_dir):
            return False, "同名作品（书）已存在"

        os.makedirs(book_dir)
        with open(os.path.join(book_dir, f"{title}_大纲.md"), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n## 基本信息\n\n- **题材**：{category}\n- **核心卖点**：\n\n## 故事梗概\n\n\n## 主要角色\n\n")
        with open(os.path.join(book_dir, f"{title}_细纲.md"), "w", encoding="utf-8") as f:
            f.write(f"# {title} 细纲\n\n## 第一卷\n\n### 第1章\n\n- 核心事件：\n- 出场人物：\n- 章末钩子：\n")
        import json
        with open(os.path.join(book_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({"channel": "男频", "genre": category if category and category != "全部分类" else "未分类",
                       "description": "", "cover": ""}, f, ensure_ascii=False, indent=2)

        self.refresh()
        work = next((w for w in self._works if w.title == title), None)
        return True, work

    def delete_work(self, work: OutlineWork) -> tuple[bool, str]:
        """删除作品（= 删除书目录）"""
        if not os.path.isdir(work.path):
            return False, "作品目录不存在"
        if os.path.commonpath([os.path.abspath(work.path),
                               os.path.abspath(self.library_dir)]) != os.path.abspath(self.library_dir):
            return False, "非法路径"
        shutil.rmtree(work.path)
        self.refresh()
        return True, work.title

    def rename_work(self, work: OutlineWork, new_title: str) -> tuple[bool, object]:
        """重命名作品（书目录 + 内部文件一并改名）"""
        new_title = self._safe_name(new_title)
        if not new_title:
            return False, "作品名不能为空"

        parent = os.path.dirname(work.path)
        new_dir = os.path.join(parent, new_title)
        if os.path.exists(new_dir):
            return False, "同名作品已存在"

        os.rename(work.path, new_dir)
        # 内部文件改名
        for fname in os.listdir(new_dir):
            if work.title in fname and fname.endswith(".md"):
                os.rename(os.path.join(new_dir, fname),
                          os.path.join(new_dir, fname.replace(work.title, new_title)))
        self.refresh()
        renamed = next((w for w in self._works if w.title == new_title), None)
        return True, renamed

    @staticmethod
    def read_content(file_path: str) -> str:
        """读取大纲文件内容（自动适配 UTF-8/GBK 编码）"""
        for encoding in ("utf-8", "gbk", "utf-16"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except OSError as e:
                return f"(读取失败：{e})"
        return "(读取失败：无法识别的文件编码)"

    def read_work(self, work: OutlineWork, kind: str = "outline") -> str:
        """读取作品的大纲或细纲内容"""
        file_path = work.outline_file if kind == "outline" else work.detail_file
        if not file_path:
            return "(该作品没有此文件)"
        return self.read_content(file_path)

    def save_work(self, work: OutlineWork, kind: str, content: str) -> bool:
        """保存作品的大纲/细纲内容"""
        file_path = work.outline_file if kind == "outline" else work.detail_file
        if not file_path:
            return False
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except OSError:
            return False


_library: Optional[OutlineLibrary] = None


def get_outline_library() -> OutlineLibrary:
    """获取大纲库单例"""
    global _library
    if _library is None:
        _library = OutlineLibrary()
    return _library
