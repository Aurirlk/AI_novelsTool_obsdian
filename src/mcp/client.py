"""
MCP stdio 客户端
JSON-RPC 2.0 over stdio（换行分隔的JSON消息）
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from typing import Optional

from .config import MCPServerConfig

PROTOCOL_VERSION = "2024-11-05"
CLIENT_INFO = {"name": "ai-novel-editor", "version": "2.0.0"}
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_path(value: str) -> str:
    """相对路径解析为基于项目根的绝对路径（仅当该路径真实存在）"""
    if not value or "://" in value or os.path.isabs(value):
        return value
    if "/" in value or "\\" in value:
        candidate = os.path.normpath(os.path.join(PROJECT_ROOT, value))
        if os.path.exists(candidate):
            return candidate
    return value


class MCPClientError(Exception):
    pass


class MCPClient:
    """单个MCP服务器的stdio连接"""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.name = config.name
        self._proc: Optional[subprocess.Popen] = None
        self._reader: Optional[threading.Thread] = None
        self._pending = {}
        self._pending_lock = threading.Lock()
        self._id_counter = 0
        self._id_lock = threading.Lock()
        self._stderr_lines = []
        self._closed = False

    # ==================== 生命周期 ====================

    def connect(self, timeout: float = 30.0):
        """启动进程并完成 initialize 握手"""
        if self._proc is not None:
            return

        cmd = self._resolve_command()
        env = os.environ.copy()
        for key, value in self.config.env.items():
            env[key] = _resolve_path(value)

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=PROJECT_ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except FileNotFoundError as e:
            raise MCPClientError(f"命令不存在：{self.config.command}（{e}）")

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        threading.Thread(target=self._stderr_loop, daemon=True).start()

        try:
            self._request("initialize", {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            }, timeout=timeout)
            self._notify("notifications/initialized", {})
        except Exception:
            self.close()
            raise

    def _resolve_command(self) -> list:
        """解析命令路径，Windows下npx等需要cmd包装"""
        command = self.config.command
        resolved = shutil.which(command)
        args = [_resolve_path(a) for a in self.config.args]
        if resolved:
            return [resolved] + args
        if os.path.isfile(command):
            return [command] + args
        if sys.platform == "win32":
            return ["cmd", "/c", command] + args
        raise MCPClientError(f"找不到命令：{command}")

    def close(self):
        """关闭连接"""
        self._closed = True
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    @property
    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # ==================== IO 线程 ====================

    def _read_loop(self):
        """读取stdout的JSON-RPC消息"""
        assert self._proc and self._proc.stdout
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg_id = msg.get("id")
            if msg_id is not None:
                with self._pending_lock:
                    entry = self._pending.get(msg_id)
                if entry is not None:
                    entry["result"] = msg
                    entry["event"].set()

        self._closed = True
        with self._pending_lock:
            pending = list(self._pending.values())
        for entry in pending:
            entry["result"] = {"error": {"message": "服务器进程已退出"}}
            entry["event"].set()

    def _stderr_loop(self):
        """收集stderr便于诊断"""
        assert self._proc and self._proc.stderr
        try:
            for line in self._proc.stderr:
                self._stderr_lines.append(line.rstrip())
                if len(self._stderr_lines) > 50:
                    self._stderr_lines.pop(0)
        except Exception:
            pass

    # ==================== JSON-RPC ====================

    def _next_id(self) -> int:
        with self._id_lock:
            self._id_counter += 1
            return self._id_counter

    def _send(self, payload: dict):
        if not self.is_alive:
            raise MCPClientError("服务器进程未运行")
        assert self._proc and self._proc.stdin
        try:
            self._proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise MCPClientError(f"写入服务器失败：{e}")

    def _request(self, method: str, params: dict, timeout: float = 60.0) -> dict:
        msg_id = self._next_id()
        event = threading.Event()
        entry = {"event": event, "result": None}
        with self._pending_lock:
            self._pending[msg_id] = entry

        try:
            self._send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})
        except Exception:
            with self._pending_lock:
                self._pending.pop(msg_id, None)
            raise

        if not event.wait(timeout):
            with self._pending_lock:
                self._pending.pop(msg_id, None)
            hint = f"；stderr: {self._stderr_lines[-1]}" if self._stderr_lines else ""
            raise MCPClientError(f"请求 {method} 超时（{timeout}s）{hint}")

        msg = entry["result"]
        if "error" in msg:
            raise MCPClientError(f"{method} 错误：{msg['error'].get('message', msg['error'])}")
        return msg.get("result", {})

    def _notify(self, method: str, params: dict):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    # ==================== MCP 能力 ====================

    def list_tools(self, timeout: float = 30.0) -> list:
        """获取服务器工具列表"""
        result = self._request("tools/list", {}, timeout=timeout)
        return result.get("tools", [])

    def call_tool(self, tool_name: str, arguments: dict, timeout: float = 120.0) -> str:
        """调用工具，返回文本结果"""
        result = self._request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {},
        }, timeout=timeout)

        if result.get("isError"):
            contents = result.get("content", [])
            text = "\n".join(c.get("text", "") for c in contents if c.get("type") == "text")
            raise MCPClientError(f"工具 {tool_name} 执行失败：{text or '未知错误'}")

        contents = result.get("content", [])
        texts = []
        for c in contents:
            if c.get("type") == "text":
                texts.append(c.get("text", ""))
            else:
                texts.append(json.dumps(c, ensure_ascii=False))
        return "\n".join(texts) if texts else "(工具无文本输出)"

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
