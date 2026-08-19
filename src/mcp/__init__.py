"""
MCP（Model Context Protocol）支持
stdio 方式连接 MCP 服务器，工具发现与调用
"""

from .config import MCPServerConfig, load_mcp_config, save_mcp_config
from .manager import MCPManager, get_mcp_manager

__all__ = [
    'MCPServerConfig',
    'load_mcp_config',
    'save_mcp_config',
    'MCPManager',
    'get_mcp_manager',
]
