"""
MCP 多服务器管理器
负责连接管理、工具聚合、OpenAI tools 格式转换
"""

import json
import threading
from typing import Dict, List, Optional

from .client import MCPClient, MCPClientError
from .config import MCPServerConfig, load_mcp_config, save_mcp_config


class MCPManager:
    """MCP管理器（单例）"""

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, dict] = {}  # full_name -> {server, name, description, schema}
        self._lock = threading.Lock()
        self._connect_errors: Dict[str, str] = {}

    # ==================== 配置 ====================

    def list_server_configs(self) -> List[MCPServerConfig]:
        return load_mcp_config()

    def add_server(self, config: MCPServerConfig):
        servers = [s for s in load_mcp_config() if s.name != config.name]
        servers.append(config)
        save_mcp_config(servers)

    def remove_server(self, name: str):
        self.disconnect(name)
        servers = [s for s in load_mcp_config() if s.name != name]
        save_mcp_config(servers)

    def set_enabled(self, name: str, enabled: bool):
        servers = load_mcp_config()
        for s in servers:
            if s.name == name:
                s.enabled = enabled
        save_mcp_config(servers)
        if not enabled:
            self.disconnect(name)

    # ==================== 连接管理 ====================

    def connect(self, name: str, timeout: float = 45.0) -> int:
        """连接指定服务器并抓取工具列表，返回工具数"""
        configs = {s.name: s for s in load_mcp_config()}
        config = configs.get(name)
        if config is None:
            raise MCPClientError(f"服务器不存在：{name}")

        self.disconnect(name)

        client = MCPClient(config)
        try:
            client.connect(timeout=timeout)
            tools = client.list_tools(timeout=30)
        except Exception as e:
            with self._lock:
                self._connect_errors[name] = str(e)
            raise

        with self._lock:
            self._clients[name] = client
            self._connect_errors.pop(name, None)
            # 清理该服务器旧工具，登记新工具
            self._tools = {k: v for k, v in self._tools.items() if v["server"] != name}
            for tool in tools:
                full_name = f"{name}__{tool['name']}"
                self._tools[full_name] = {
                    "server": name,
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "schema": tool.get("inputSchema", {"type": "object", "properties": {}}),
                }
            return len(tools)

    def connect_all_enabled(self, timeout: float = 45.0) -> Dict[str, str]:
        """连接所有已启用的服务器，返回 {服务器名: 状态说明}"""
        results = {}
        for config in load_mcp_config():
            if not config.enabled:
                continue
            try:
                count = self.connect(config.name, timeout=timeout)
                results[config.name] = f"已连接，{count} 个工具"
            except Exception as e:
                results[config.name] = f"连接失败：{e}"
        return results

    def disconnect(self, name: str):
        with self._lock:
            client = self._clients.pop(name, None)
            self._tools = {k: v for k, v in self._tools.items() if v["server"] != name}
        if client is not None:
            client.close()

    def disconnect_all(self):
        for name in list(self._clients):
            self.disconnect(name)

    def server_status(self) -> Dict[str, str]:
        """各服务器状态"""
        status = {}
        for config in load_mcp_config():
            if not config.enabled:
                status[config.name] = "已禁用"
            elif config.name in self._clients and self._clients[config.name].is_alive:
                count = sum(1 for t in self._tools.values() if t["server"] == config.name)
                status[config.name] = f"已连接（{count} 个工具）"
            elif config.name in self._connect_errors:
                status[config.name] = f"连接失败：{self._connect_errors[config.name]}"
            else:
                status[config.name] = "未连接"
        return status

    # ==================== 工具 ====================

    def list_tools(self) -> List[dict]:
        """所有已连接服务器的工具"""
        with self._lock:
            return [{"full_name": k, **v} for k, v in self._tools.items()]

    def tool_count(self) -> int:
        with self._lock:
            return len(self._tools)

    def to_openai_tools(self) -> List[dict]:
        """转换为 OpenAI tools 参数格式"""
        openai_tools = []
        for tool in self.list_tools():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["full_name"],
                    "description": f"[{tool['server']}] {tool['description']}",
                    "parameters": tool["schema"],
                },
            })
        return openai_tools

    def call_tool(self, full_name: str, arguments: dict) -> str:
        """按全名（server__tool）调用工具"""
        with self._lock:
            tool = self._tools.get(full_name)
        if tool is None:
            raise MCPClientError(f"工具不存在或未连接：full_name")

        client = self._clients.get(tool["server"])
        if client is None or not client.is_alive:
            raise MCPClientError(f"服务器 {tool['server']} 未连接")

        return client.call_tool(tool["name"], arguments)

    def tool_handler(self):
        """返回可供 LLMClient.chat_with_tools 使用的处理函数"""
        def handle(name: str, arguments_json: str) -> str:
            try:
                args = json.loads(arguments_json) if arguments_json else {}
            except json.JSONDecodeError:
                args = {}
            try:
                return self.call_tool(name, args)
            except Exception as e:
                return f"工具调用失败：{e}"
        return handle


_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """获取MCP管理器单例"""
    global _manager
    if _manager is None:
        _manager = MCPManager()
    return _manager
