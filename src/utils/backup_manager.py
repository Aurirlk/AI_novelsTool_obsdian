"""
全量备份管理
打包 写作空间/ + data/ + 小说大纲/ 为带时间戳的 zip，支持覆盖式恢复

设计决策（grill-me 评审）：
- 全量 zip + 覆盖恢复：单文件语义简单
- 纯手动触发：不干扰写作流程
"""

import os
import shutil
import tempfile
import zipfile

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 参与全量备份的顶层目录（顺序即 zip 内顺序）
BACKUP_DIRS = ["写作空间", "data", "小说大纲"]


def backup_dirs() -> list:
    """返回实际存在的备份目录列表"""
    return [d for d in BACKUP_DIRS if os.path.isdir(os.path.join(_ROOT, d))]


def create_full_backup(dest_zip: str) -> str:
    """把全部用户数据打包为 zip，返回 zip 路径

    Args:
        dest_zip: 目标 zip 文件路径（不含 .zip 时自动补）

    Returns:
        zip 文件路径
    """
    if not dest_zip.endswith(".zip"):
        dest_zip += ".zip"
    os.makedirs(os.path.dirname(dest_zip), exist_ok=True) if os.path.dirname(dest_zip) else None

    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in backup_dirs():
            src = os.path.join(_ROOT, d)
            for root, _dirs, files in os.walk(src):
                # 跳过回收站（临时删除内容不进备份）
                if os.path.basename(root) == "trash" and "trash" in os.path.relpath(root, _ROOT):
                    continue
                for f in files:
                    full = os.path.join(root, f)
                    arc = os.path.relpath(full, _ROOT)
                    zf.write(full, arc)
    return dest_zip


def restore_full_backup(zip_path: str) -> str:
    """从全量 zip 覆盖式恢复数据

    Args:
        zip_path: 备份 zip 路径

    Returns:
        恢复说明（列出覆盖的目录）
    """
    restored = []
    tmp_dir = tempfile.mkdtemp(prefix="full_restore_")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        for d in BACKUP_DIRS:
            src = os.path.join(tmp_dir, d)
            dst = os.path.join(_ROOT, d)
            if not os.path.isdir(src):
                continue
            # 保护当前回收站：恢复 data/ 前暂存 trash，恢复后放回
            trash_stash = None
            if d == "data":
                trash_src = os.path.join(dst, "trash")
                if os.path.isdir(trash_src):
                    trash_stash = os.path.join(tmp_dir, "_trash_stash")
                    shutil.move(trash_src, trash_stash)
            try:
                if os.path.isdir(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            finally:
                if trash_stash and os.path.isdir(trash_stash):
                    os.makedirs(dst, exist_ok=True)
                    shutil.move(trash_stash, os.path.join(dst, "trash"))
            restored.append(d)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if not restored:
        raise ValueError("备份文件中未找到可恢复的数据目录")
    return "已恢复：" + "、".join(restored)


if __name__ == "__main__":
    import tempfile as _tf

    dest = os.path.join(_tf.gettempdir(), "test_full_backup.zip")
    create_full_backup(dest)
    print("backup created:", dest, os.path.getsize(dest), "bytes")
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    print("entries:", len(names))
    print("sample:", names[:5])
