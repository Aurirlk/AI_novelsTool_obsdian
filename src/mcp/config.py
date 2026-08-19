"""
MCP 服务器配置
配置文件格式与 Claude Code 的 mcp.json 约定一致
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "mcp_servers.json")


@dataclass
class MCPServerConfig:
    """单个MCP服务器配置"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""


_DEFAULT_TEMPLATE = {
    "servers": {
        "novel-workflow": {
            "command": "npx",
            "args": ["-y", "@ttaqt/novel-workflow-mcp"],
            "env": {},
            "enabled": False,
            "description": "中文网文工作流：故事概念→大纲→场景→正文（需要Node.js）"
        }
    }
}


def load_mcp_config(path: Optional[str] = None) -> List[MCPServerConfig]:
    """加载MCP服务器配置，文件不存在时创建模板"""
    path = path or DEFAULT_CONFIG_PATH

    if not os.path.isfile(path):
        save_mcp_config([MCPServerConfig(
            name="novel-workflow",
            command="npx",
            args=["-y", "@ttaqt/novel-workflow-mcp"],
            enabled=False,
            description="中文网文工作流：故事概念→大纲→场景→正文（需要Node.js）",
        )], path)
        return load_mcp_config(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    servers = []
    for name, cfg in data.get("servers", {}).items():
        servers.append(MCPServerConfig(
            name=name,
            command=cfg.get("command", ""),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
            enabled=cfg.get("enabled", True),
            description=cfg.get("description", ""),
        ))
    return servers


def save_mcp_config(servers: List[MCPServerConfig], path: Optional[str] = None):
    """保存MCP服务器配置"""
    path = path or DEFAULT_CONFIG_PATH
    data = {
        "servers": {
            s.name: {
                "command": s.command,
                "args": s.args,
                "env": s.env,
                "enabled": s.enabled,
                "description": s.description,
            }
            for s in servers
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
