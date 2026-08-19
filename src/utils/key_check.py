"""
测试密钥检测
扫描 .env 文件 + SQLite 已保存的 API 密钥，发现已知测试密钥时提示（用于上线前清理）

设计决策（grill-me 评审）：
- 检测范围：.env + SQLite 双源全扫
- 警告形态：非阻塞警告条（设置页顶部），不打断启动
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(_ROOT, ".env")

# 已知测试密钥前缀（开源版不含任何真实密钥）
# 匹配完整 key 或此前缀，避免误伤真实密钥
TEST_KEY_PREFIXES = (
    "sk-test-placeholder",
)

# .env 中可能存放密钥的环境变量名（对应各提供商）
_ENV_VAR_NAMES = (
    "DEEPSEEK_API_KEY", "ZHIPUAI_API_KEY", "OPENAI_API_KEY",
    "DASHSCOPE_API_KEY", "MOONSHOT_API_KEY", "BAICHUAN_API_KEY", "SPARK_API_KEY",
)


def _is_test_key(key: str) -> bool:
    key = (key or "").strip()
    if not key:
        return False
    return any(key == prefix or key.startswith(prefix) for prefix in TEST_KEY_PREFIXES)


def find_test_keys() -> list:
    """扫描 .env + SQLite，返回命中列表：[{source, provider, key_name}]"""
    hits = []

    # 1. .env 文件
    if os.path.isfile(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    var, _, value = line.partition("=")
                    var = var.strip()
                    value = value.strip().strip('"').strip("'")
                    if var in _ENV_VAR_NAMES and _is_test_key(value):
                        hits.append({"source": ".env", "provider": var, "key_name": var})
        except OSError:
            pass

    # 2. SQLite 已保存密钥
    try:
        from src.data.database_manager import get_database_manager
        keys = get_database_manager().list_api_keys()
        for k in keys or []:
            if _is_test_key(k.get("api_key")):
                hits.append({
                    "source": "SQLite",
                    "provider": k.get("provider", ""),
                    "key_name": k.get("key_name", ""),
                })
    except Exception:
        pass

    return hits


if __name__ == "__main__":
    hits = find_test_keys()
    if hits:
        print("检测到测试密钥：")
        for h in hits:
            print(f"  [{h['source']}] {h['provider']} / {h['key_name']}")
    else:
        print("未检测到测试密钥")
