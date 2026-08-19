"""
垃圾清理工具
扫描日志、临时文件、过期备份，移入回收站（而非直接删除）
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path

# 项目根目录
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _try_send2trash(path: str) -> bool:
    """尝试用 send2trash 移入回收站，失败则返回 False"""
    try:
        from send2trash import send2trash
        send2trash(path)
        return True
    except ImportError:
        pass
    except Exception:
        pass
    return False


def _safe_delete(path: str) -> bool:
    """安全删除：优先回收站，回退到直接删除"""
    if _try_send2trash(path):
        return True
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True
    except Exception:
        return False


def scan_cleanable(max_log_days: int = 7, max_backup_count: int = 5) -> dict:
    """
    扫描可清理的文件，返回分类统计。
    不删除任何文件，只报告。
    """
    result = {
        "logs": [],         # 过期日志文件
        "temp": [],         # 临时文件
        "backups": [],      # 多余备份
        "legacy": [],       # 迁移遗留数据
        "total_size": 0,
    }

    now = time.time()
    cutoff = now - max_log_days * 86400

    # 1. 日志文件（超过 max_log_days 天）
    log_dir = os.path.join(_ROOT, "logs")
    if os.path.isdir(log_dir):
        for f in os.listdir(log_dir):
            fp = os.path.join(log_dir, f)
            if os.path.isfile(fp):
                mtime = os.path.getmtime(fp)
                size = os.path.getsize(fp)
                if mtime < cutoff:
                    result["logs"].append({"path": fp, "size": size, "mtime": mtime})
                    result["total_size"] += size

    # 2. 临时文件（__pycache__、.pyc、.pyo）
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        # 跳过 .git、node_modules、写作空间
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__", "写作空间", "小说大纲")]
        for d in dirnames:
            if d == "__pycache__":
                dp = os.path.join(dirpath, d)
                size = _dir_size(dp)
                result["temp"].append({"path": dp, "size": size})
                result["total_size"] += size
        for f in filenames:
            if f.endswith((".pyc", ".pyo")):
                fp = os.path.join(dirpath, f)
                size = os.path.getsize(fp)
                result["temp"].append({"path": fp, "size": size})
                result["total_size"] += size

    # 3. 多余备份（data/_pre_migrate_backup* 保留最新 max_backup_count 个）
    data_dir = os.path.join(_ROOT, "data")
    if os.path.isdir(data_dir):
        backups = []
        for f in os.listdir(data_dir):
            if f.startswith("_pre_migrate_backup"):
                fp = os.path.join(data_dir, f)
                if os.path.isdir(fp):
                    mtime = os.path.getmtime(fp)
                    size = _dir_size(fp)
                    backups.append({"path": fp, "size": size, "mtime": mtime})
        backups.sort(key=lambda x: x["mtime"], reverse=True)
        for b in backups[max_backup_count:]:
            result["backups"].append(b)
            result["total_size"] += b["size"]

    # 4. 迁移遗留（data/_legacy_*）
    if os.path.isdir(data_dir):
        for f in os.listdir(data_dir):
            if f.startswith("_legacy_"):
                fp = os.path.join(data_dir, f)
                if os.path.isdir(fp):
                    size = _dir_size(fp)
                    result["legacy"].append({"path": fp, "size": size})
                    result["total_size"] += size

    return result


def execute_cleanup(scan_result: dict) -> dict:
    """
    执行清理：将扫描结果中的文件移入回收站。
    返回清理统计。
    """
    cleaned = {"count": 0, "size": 0, "failed": 0}
    all_items = (
        scan_result.get("logs", [])
        + scan_result.get("temp", [])
        + scan_result.get("backups", [])
        + scan_result.get("legacy", [])
    )
    for item in all_items:
        if _safe_delete(item["path"]):
            cleaned["count"] += 1
            cleaned["size"] += item["size"]
        else:
            cleaned["failed"] += 1
    return cleaned


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _dir_size(path: str) -> int:
    """计算目录总大小"""
    total = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except OSError:
        pass
    return total
