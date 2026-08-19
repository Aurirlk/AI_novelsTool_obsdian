"""
LLM工具模块
提供统一的LLM调用接口，优先使用GUI设置中的用户API密钥，支持流式输出
包含指数退避重试（仅幂等接口，限流/超时/连接类异常）
"""

import os
import time
from typing import Optional, Iterator
from dotenv import load_dotenv

load_dotenv()

# 重试策略：额外重试次数 + 每次等待秒数（指数退避）
RETRY_ATTEMPTS = 2
RETRY_BACKOFF = [0.5, 1.5]
REQUEST_TIMEOUT = 60  # 秒

_DEFAULT_BASE_URLS = {
    "zhipuai": "https://open.bigmodel.cn/api/paas/v4",
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "baichuan": "https://api.baichuan-ai.com/v1",
    "spark": "https://spark-api-open.xf-yun.com/v1",
    "glm": "http://localhost:8000/v1",
    "ollama": "http://localhost:11434/v1",
}

_ENV_KEY_NAMES = {
    "zhipuai": "ZHIPUAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "baichuan": "BAICHUAN_API_KEY",
    "spark": "SPARK_API_KEY",
}

_DEFAULT_MODELS = {
    "zhipuai": "glm-4-flash",
    "deepseek": "deepseek-v4-flash",
    "openai": "gpt-4o-mini",
    "qwen": "qwen-plus",
    "moonshot": "moonshot-v1-8k",
    "baichuan": "Baichuan2-Turbo",
    "spark": "generalv3.5",
    "glm": "glm-4-9b-chat",
    "ollama": "llama3",
}

_NO_KEY_PROVIDERS = {"ollama", "glm"}


class LLMClient:
    """LLM客户端，支持所有OpenAI兼容协议的提供商"""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        config = self._load_config(provider, model)
        self.provider = config["provider"]
        self.model = config["model"]
        self.api_key = config["api_key"]
        self.base_url = config["base_url"]
        self.temperature = config["temperature"]
        self.max_tokens = config["max_tokens"]
        self._client = None
        self._init_client()

    def _load_config(self, provider: Optional[str], model: Optional[str]) -> dict:
        config = None
        try:
            from src.data.settings_manager import get_settings_manager
            config = get_settings_manager().get_llm_config(provider, model)
        except Exception:
            pass

        if not config:
            config = {
                "provider": provider or os.getenv("DEFAULT_LLM_PROVIDER", "deepseek"),
                "model": model,
                "api_key": None,
                "base_url": None,
                "temperature": 0.7,
                "max_tokens": 2000,
            }

        provider = config["provider"]

        if not config.get("api_key"):
            env_name = _ENV_KEY_NAMES.get(provider)
            if env_name:
                config["api_key"] = os.getenv(env_name)

        if not config.get("base_url"):
            config["base_url"] = _DEFAULT_BASE_URLS.get(provider)

        if not config.get("model"):
            config["model"] = _DEFAULT_MODELS.get(provider, "gpt-4o-mini")

        return config

    def _init_client(self):
        if self.provider == "anthropic":
            raise ValueError("Anthropic 暂未直接支持，请选用其他提供商，或在其自定义接口地址中填入 OpenAI 兼容代理地址")
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装openai: pip install openai")

        api_key = self.api_key
        if not api_key:
            if self.provider in _NO_KEY_PROVIDERS:
                api_key = "not-required"
            else:
                raise ValueError(f"未配置 {self.provider} 的API密钥，请在 设置 → LLM 中添加")

        kwargs = {"api_key": api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        kwargs["timeout"] = REQUEST_TIMEOUT
        self._client = OpenAI(**kwargs)

    # ---------- 重试机制 ----------

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """是否可重试：限流/超时/连接类异常（认证、参数错误等直接抛出）"""
        from openai import (
            RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)
        if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError,
                            InternalServerError)):
            return True
        # 兜底：网络层异常（无 openai 类型包装时）
        import socket
        if isinstance(exc, (socket.timeout, ConnectionError, TimeoutError)):
            return True
        return False

    def _call_with_retry(self, fn):
        """指数退避重试调用：仅重试可重试异常，其余直接抛出"""
        last_exc = None
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                return fn()
            except Exception as e:
                last_exc = e
                if attempt < RETRY_ATTEMPTS and self._is_retryable(e):
                    time.sleep(RETRY_BACKOFF[attempt])
                    continue
                raise
        raise last_exc  # pragma: no cover

    def _build_messages(self, message: str, system_prompt: Optional[str], history: Optional[list]) -> list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})
        return messages

    def chat(self, message: str, system_prompt: Optional[str] = None,
             history: Optional[list] = None) -> str:
        messages = self._build_messages(message, system_prompt, history)
        response = self._call_with_retry(lambda: self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ))
        return response.choices[0].message.content

    def chat_stream(self, message: str, system_prompt: Optional[str] = None,
                    history: Optional[list] = None) -> Iterator[str]:
        """流式聊天，逐块产出回复文本"""
        messages = self._build_messages(message, system_prompt, history)
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    def chat_with_context(self, message: str, context: list[dict]) -> str:
        return self.chat(message, history=context)

    def chat_with_tools(self, messages: list, tools: list, tool_handler,
                        max_rounds: int = 8, on_tool_event=None) -> str:
        """
        带工具调用的对话循环（MCP/函数调用）

        Args:
            messages: 消息列表（含system/user/history）
            tools: OpenAI tools 格式的工具定义
            tool_handler: 工具执行函数 (name, arguments_json) -> str
            max_rounds: 最大工具调用轮数
            on_tool_event: 工具事件回调 (event_text)

        Returns:
            最终文本回复
        """
        messages = list(messages)

        for _ in range(max_rounds):
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            if tools:
                kwargs["tools"] = tools

            response = self._call_with_retry(
                lambda: self._client.chat.completions.create(**kwargs))
            msg = response.choices[0].message

            if not getattr(msg, "tool_calls", None):
                return msg.content or ""

            # 序列化 assistant 消息（含 tool_calls）
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                if on_tool_event:
                    on_tool_event(f"调用工具 {tc.function.name}")
                try:
                    result = tool_handler(tc.function.name, tc.function.arguments or "{}")
                except Exception as e:
                    result = f"工具调用失败：{e}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result)[:8000],
                })

        # 达到最大轮数后，不带工具要一个最终回答
        response = self._call_with_retry(lambda: self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ))
        return response.choices[0].message.content or ""

    def chat_with_tools_stream(self, messages: list, tools: list, tool_handler,
                               max_rounds: int = 8, on_tool_event=None) -> Iterator[str]:
        """
        带工具调用的流式对话循环（MCP/函数调用）

        工具调用轮完整接收后执行工具，最终生成轮逐块流式产出

        Args:
            messages: 消息列表（含system/user/history）
            tools: OpenAI tools 格式的工具定义
            tool_handler: 工具执行函数 (name, arguments_json) -> str
            max_rounds: 最大工具调用轮数
            on_tool_event: 工具事件回调 (event_text)

        Yields:
            最终文本回复的流式片段
        """
        messages = list(messages)

        for _ in range(max_rounds):
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools

            stream = self._client.chat.completions.create(**kwargs)

            content_parts = []
            tool_calls: dict = {}  # index -> {"id","name","arguments"}
            is_tool_round = False

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                if getattr(delta, "tool_calls", None):
                    is_tool_round = True
                    for tc in delta.tool_calls:
                        entry = tool_calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                        if tc.id:
                            entry["id"] = tc.id
                        if tc.function and tc.function.name:
                            entry["name"] += tc.function.name
                        if tc.function and tc.function.arguments:
                            entry["arguments"] += tc.function.arguments
                elif delta.content:
                    content_parts.append(delta.content)
                    yield delta.content

            if is_tool_round:
                # 执行工具调用
                serialized = [
                    {
                        "id": e["id"],
                        "type": "function",
                        "function": {"name": e["name"], "arguments": e["arguments"]},
                    }
                    for e in tool_calls.values()
                ]
                messages.append({
                    "role": "assistant",
                    "content": "".join(content_parts) or "",
                    "tool_calls": serialized,
                })
                for tc in serialized:
                    if on_tool_event:
                        on_tool_event(f"调用工具 {tc['function']['name']}")
                    try:
                        result = tool_handler(tc["function"]["name"], tc["function"]["arguments"] or "{}")
                    except Exception as e:
                        result = f"工具调用失败：{e}"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result)[:8000],
                    })
                continue

            # 无工具调用，生成完成
            return

        # 达到最大轮数后，不带工具流式输出最终回答
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    def test_connection(self) -> tuple[bool, str]:
        """测试连接，返回 (是否成功, 说明)"""
        try:
            self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            return True, f"连接成功：{self.provider} / {self.model}"
        except Exception as e:
            return False, f"连接失败：{e}"


_llm_client: Optional[LLMClient] = None


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    global _llm_client
    if _llm_client is None or (provider and _llm_client.provider != provider) \
            or (model and _llm_client.model != model):
        _llm_client = LLMClient(provider, model)
    return _llm_client


def reset_llm_client():
    """设置变更后调用，使新配置立即生效"""
    global _llm_client
    _llm_client = None


def has_api_key(provider: Optional[str] = None) -> bool:
    """检查指定提供商（或默认提供商）是否已配置密钥"""
    try:
        if provider:
            config = LLMClient.__new__(LLMClient)._load_config(provider, None)
        else:
            try:
                from src.data.settings_manager import get_settings_manager
                provider = get_settings_manager().get_setting("generation", "default_provider", "deepseek")
            except Exception:
                provider = "deepseek"
            config = LLMClient.__new__(LLMClient)._load_config(provider, None)
        if config["provider"] in _NO_KEY_PROVIDERS:
            return True
        return bool(config.get("api_key"))
    except Exception:
        return False


def chat(message: str, system_prompt: Optional[str] = None, provider: Optional[str] = None) -> str:
    client = get_llm_client(provider)
    return client.chat(message, system_prompt)


if __name__ == "__main__":
    print("=" * 50)
    print("测试LLM调用")
    print("=" * 50)
    try:
        response = chat("你好，请简单介绍一下自己。")
        print(f"回复: {response}")
    except Exception as e:
        print(f"测试失败: {e}")
        print("\n请确保已配置API密钥（设置页或 .env）")
