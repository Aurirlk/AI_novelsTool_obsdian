"""
Git 自动提交工具（goink turn_commits 模式）

设计约束：
- 正文/大纲等用户内容已被 .gitignore 排除（写作空间/、小说大纲/、data/），不进仓库；
- 因此每轮 AI / 用户变更落地时，把"变更事件"追加到 docs/turn_commits.json，
  并对该日志文件执行 git commit，把 commit hash 写回记录 —— 达成
  「每轮自动 git commit + turn_commits 存档」且保持仓库纯净。
- git 不可用 / 非仓库环境时优雅降级：记录保留，hash 为空。
"""

import json
import os
import subprocess
import threading
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TURN_COMMITS_FILE = os.path.join(_PROJECT_ROOT, "docs", "turn_commits.json")

# 多个写入口（AI 审批 / 用户保存 / 工具直写）可能并发调用，锁保证日志追加与 git 提交串行
_lock = threading.Lock()


def _run_git(args: list) -> subprocess.CompletedProcess:
    """运行 git 命令，任何异常均返回失败对象（不抛出）"""
    try:
        return subprocess.run(
            ["git", "-C", _PROJECT_ROOT] + args,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        return subprocess.CompletedProcess(args, 1, "", str(e))


def load_turn_commits() -> list:
    """读取变更记录（最新在前）"""
    if not os.path.isfile(TURN_COMMITS_FILE):
        return []
    try:
        with open(TURN_COMMITS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return list(data) if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_turn_commits(records: list):
    os.makedirs(os.path.dirname(TURN_COMMITS_FILE), exist_ok=True)
    with open(TURN_COMMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def record_and_commit(kind: str, message: str) -> dict:
    """
    记录一条变更事件并自动 git commit（goink turn_commits 模式）。

    Args:
        kind: "ai"（AI 工具写入）或 "user"（用户手动保存）
        message: 提交信息（含书名/章节等信息）

    Returns:
        dict: {"time", "kind", "message", "hash"}，hash 为空表示 commit 未成功（非仓库环境）
    """
    with _lock:
        records = load_turn_commits()
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kind": kind,
            "message": message,
            "hash": "",
        }
        records.append(entry)
        # 只保留最近 200 条，防止日志无限膨胀
        records = records[-200:]
        _save_turn_commits(records)

        # 提交日志文件本身（正文/大纲已被 gitignore，不会进仓库）
        _run_git(["add", "docs/turn_commits.json"])
        commit = _run_git(["commit", "-m", message])
        if commit.returncode == 0:
            rev = _run_git(["rev-parse", "--short", "HEAD"])
            if rev.returncode == 0:
                entry["hash"] = rev.stdout.strip()
                _save_turn_commits(records)
        return entry


def is_git_repo() -> bool:
    """当前项目是否为 git 仓库"""
    return _run_git(["rev-parse", "--is-inside-work-tree"]).returncode == 0
