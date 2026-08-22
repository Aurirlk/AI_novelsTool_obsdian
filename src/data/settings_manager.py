"""
设置管理器
管理应用程序设置、LLM配置等
"""

import os
from typing import Optional, List, Dict, Any
from .database_manager import get_database_manager


class SettingsManager:
    """设置管理器"""
    
    # 支持的LLM提供商
    SUPPORTED_PROVIDERS = {
        "zhipuai": {
            "name": "智谱AI",
            "description": "智谱GLM系列模型，国内免费",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": [
                {"id": "glm-4-flash", "name": "GLM-4 Flash", "description": "快速响应"},
                {"id": "glm-4", "name": "GLM-4", "description": "标准模型"},
                {"id": "glm-4v", "name": "GLM-4V", "description": "多模态模型"},
                {"id": "glm-3-turbo", "name": "GLM-3 Turbo", "description": "经济型"},
            ],
            "requires_key": True,
            "key_name": "ZHIPUAI_API_KEY",
        },
        "deepseek": {
            "name": "DeepSeek",
            "description": "DeepSeek系列模型，性价比高",
            "base_url": "https://api.deepseek.com/v1",
            "models": [
                {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "description": "快速经济"},
                {"id": "deepseek-chat", "name": "DeepSeek Chat", "description": "通用对话"},
                {"id": "deepseek-coder", "name": "DeepSeek Coder", "description": "代码专用"},
                {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "description": "推理专用"},
            ],
            "requires_key": True,
            "key_name": "DEEPSEEK_API_KEY",
        },
        "openai": {
            "name": "OpenAI",
            "description": "GPT系列模型",
            "base_url": "https://api.openai.com/v1",
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o", "description": "最新旗舰"},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "经济型"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "高性能"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "快速"},
            ],
            "requires_key": True,
            "key_name": "OPENAI_API_KEY",
        },
        "anthropic": {
            "name": "Anthropic",
            "description": "Claude系列模型",
            "base_url": "https://api.anthropic.com/v1",
            "models": [
                {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "最新旗舰"},
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "最强能力"},
                {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "description": "平衡型"},
                {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "description": "快速"},
            ],
            "requires_key": True,
            "key_name": "ANTHROPIC_API_KEY",
        },
        "qwen": {
            "name": "通义千问",
            "description": "阿里云通义千问系列模型",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": [
                {"id": "qwen-turbo", "name": "Qwen Turbo", "description": "快速"},
                {"id": "qwen-plus", "name": "Qwen Plus", "description": "增强版"},
                {"id": "qwen-max", "name": "Qwen Max", "description": "最强"},
                {"id": "qwen-long", "name": "Qwen Long", "description": "长文本"},
            ],
            "requires_key": True,
            "key_name": "DASHSCOPE_API_KEY",
        },
        "moonshot": {
            "name": "月之暗面",
            "description": "Kimi系列模型，长文本能力强",
            "base_url": "https://api.moonshot.cn/v1",
            "models": [
                {"id": "moonshot-v1-8k", "name": "Moonshot V1 8K", "description": "8K上下文"},
                {"id": "moonshot-v1-32k", "name": "Moonshot V1 32K", "description": "32K上下文"},
                {"id": "moonshot-v1-128k", "name": "Moonshot V1 128K", "description": "128K上下文"},
            ],
            "requires_key": True,
            "key_name": "MOONSHOT_API_KEY",
        },
        "baichuan": {
            "name": "百川智能",
            "description": "百川系列模型",
            "base_url": "https://api.baichuan-ai.com/v1",
            "models": [
                {"id": "Baichuan2-Turbo", "name": "Baichuan2 Turbo", "description": "快速"},
                {"id": "Baichuan2-Turbo-192k", "name": "Baichuan2 Turbo 192K", "description": "长文本"},
            ],
            "requires_key": True,
            "key_name": "BAICHUAN_API_KEY",
        },
        "spark": {
            "name": "讯飞星火",
            "description": "讯飞星火系列模型",
            "base_url": "https://spark-api-open.xf-yun.com/v1",
            "models": [
                {"id": "generalv3.5", "name": "星火 V3.5", "description": "标准版"},
                {"id": "generalv3", "name": "星火 V3", "description": "经济版"},
                {"id": "pro-128k", "name": "星火 Pro 128K", "description": "长文本"},
            ],
            "requires_key": True,
            "key_name": "SPARK_API_KEY",
        },
        "glm": {
            "name": "智谱GLM",
            "description": "本地GLM模型（需要部署）",
            "base_url": "http://localhost:8000/v1",
            "models": [
                {"id": "glm-4-9b-chat", "name": "GLM-4 9B Chat", "description": "本地9B模型"},
            ],
            "requires_key": False,
            "key_name": None,
        },
        "ollama": {
            "name": "Ollama",
            "description": "本地Ollama模型",
            "base_url": "http://localhost:11434/v1",
            "models": [
                {"id": "llama3", "name": "Llama 3", "description": "Meta Llama 3"},
                {"id": "qwen2", "name": "Qwen 2", "description": "通义千问2"},
                {"id": "glm4", "name": "GLM 4", "description": "智谱GLM4"},
                {"id": "deepseek-v2", "name": "DeepSeek V2", "description": "DeepSeek V2"},
                {"id": "mistral", "name": "Mistral", "description": "Mistral"},
                {"id": "phi3", "name": "Phi-3", "description": "微软Phi-3"},
            ],
            "requires_key": False,
            "key_name": None,
        },
    }
    
    def __init__(self):
        """初始化设置管理器"""
        self.db = get_database_manager()
    
    # ==================== LLM提供商管理 ====================
    
    def get_provider_info(self, provider: str) -> Optional[Dict]:
        """
        获取提供商信息
        
        Args:
            provider: 提供商名称
        
        Returns:
            提供商信息
        """
        return self.SUPPORTED_PROVIDERS.get(provider)
    
    def list_providers(self) -> List[Dict]:
        """
        列出所有提供商
        
        Returns:
            提供商列表
        """
        providers = []
        for provider_id, provider_info in self.SUPPORTED_PROVIDERS.items():
            providers.append({
                "id": provider_id,
                "name": provider_info["name"],
                "description": provider_info["description"],
                "requires_key": provider_info["requires_key"],
                "models": provider_info["models"],
            })
        return providers
    
    def get_provider_models(self, provider: str) -> List[Dict]:
        """
        获取提供商的模型列表
        
        Args:
            provider: 提供商名称
        
        Returns:
            模型列表
        """
        provider_info = self.SUPPORTED_PROVIDERS.get(provider)
        if provider_info:
            return provider_info["models"]
        return []
    
    def get_provider_base_url(self, provider: str) -> Optional[str]:
        """
        获取提供商的基础URL
        
        Args:
            provider: 提供商名称
        
        Returns:
            基础URL
        """
        provider_info = self.SUPPORTED_PROVIDERS.get(provider)
        if provider_info:
            return provider_info["base_url"]
        return None
    
    # ==================== API密钥管理 ====================
    
    def set_api_key(self, provider: str, api_key: str, key_name: Optional[str] = None,
                    base_url: Optional[str] = None, model: Optional[str] = None,
                    is_default: bool = True):
        """
        设置API密钥
        
        Args:
            provider: 提供商名称
            api_key: API密钥
            key_name: 密钥名称
            base_url: 基础URL
            model: 默认模型
            is_default: 是否默认
        """
        if key_name is None:
            key_name = f"{provider}_default"
        
        self.db.add_api_key(provider, key_name, api_key, base_url, model, is_default)
    
    def get_api_key(self, provider: str, key_name: Optional[str] = None) -> Optional[str]:
        """
        获取API密钥
        
        Args:
            provider: 提供商名称
            key_name: 密钥名称
        
        Returns:
            API密钥
        """
        key_info = self.db.get_api_key(provider, key_name)
        if key_info:
            return key_info["api_key"]
        return None
    
    def get_llm_config(self, provider: Optional[str] = None, model: Optional[str] = None) -> Dict:
        """
        获取LLM配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
        
        Returns:
            LLM配置
        """
        if provider is None:
            provider = self.get_setting("generation", "default_provider", "deepseek")

        if model is None:
            model = self.get_setting("generation", "default_model", "deepseek-v4-flash")
        
        # 获取API密钥
        api_key = self.get_api_key(provider)
        
        # 获取基础URL
        base_url = self.get_provider_base_url(provider)
        
        # 检查是否有自定义URL
        custom_url = self.get_setting("llm", f"{provider}_base_url")
        if custom_url:
            base_url = custom_url
        
        return {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "temperature": float(self.get_setting("generation", "temperature", "0.7")),
            "max_tokens": int(self.get_setting("generation", "max_tokens", "2000")),
        }
    
    # ==================== 设置管理 ====================
    
    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """
        获取设置
        
        Args:
            category: 分类
            key: 键名
            default: 默认值
        
        Returns:
            设置值
        """
        return self.db.get_setting(category, key, default)
    
    def set_setting(self, category: str, key: str, value: Any, description: Optional[str] = None):
        """
        设置设置
        
        Args:
            category: 分类
            key: 键名
            value: 值
            description: 描述
        """
        self.db.set_setting(category, key, value, description)
    
    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """
        获取分类下的所有设置
        
        Args:
            category: 分类
        
        Returns:
            设置字典
        """
        return self.db.get_settings_by_category(category)
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有设置
        
        Returns:
            设置字典
        """
        return self.db.get_all_settings()
    
    # ==================== 快捷键管理 ====================
    
    def get_shortcut(self, action: str) -> Optional[str]:
        """
        获取快捷键
        
        Args:
            action: 动作
        
        Returns:
            快捷键序列
        """
        return self.db.get_shortcut(action)
    
    def set_shortcut(self, action: str, key_sequence: str, description: Optional[str] = None):
        """
        设置快捷键
        
        Args:
            action: 动作
            key_sequence: 快捷键序列
            description: 描述
        """
        self.db.set_shortcut(action, key_sequence, description)
    
    def list_shortcuts(self) -> List[Dict]:
        """
        列出所有快捷键
        
        Returns:
            快捷键列表
        """
        return self.db.list_shortcuts()
    
    def reset_shortcuts(self):
        """重置快捷键为默认值"""
        self.db.reset_shortcuts()
    
    # ==================== 项目管理 ====================
    
    def add_recent_project(self, name: str, path: str, description: Optional[str] = None,
                           genre: Optional[str] = None):
        """
        添加最近项目
        
        Args:
            name: 项目名称
            path: 项目路径
            description: 描述
            genre: 类型
        """
        self.db.add_project(name, path, description, genre)
    
    def get_recent_projects(self, limit: int = 10) -> List[Dict]:
        """
        获取最近项目
        
        Args:
            limit: 返回数量限制
        
        Returns:
            项目列表
        """
        return self.db.list_projects(limit)
    
    def update_project_last_opened(self, path: str):
        """
        更新项目最后打开时间
        
        Args:
            path: 项目路径
        """
        self.db.update_project_last_opened(path)


# 全局实例
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """获取设置管理器单例"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
