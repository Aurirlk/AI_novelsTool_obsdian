"""
AI网文写作智能体 - 配置文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 日志目录
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# LLM配置
LLM_CONFIG = {
    # 智谱GLM（主力，永久免费）
    "zhipuai": {
        "api_key": os.getenv("ZHIPUAI_API_KEY"),
        "model": "glm-4-flash",  # 永久免费
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    # DeepSeek（备用，极便宜）
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com/v1",
    },
    # OpenAI（可选）
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    },
}

# 默认LLM提供商
DEFAULT_LLM_PROVIDER = "deepseek"

# 向量数据库配置
CHROMA_CONFIG = {
    "persist_directory": os.getenv("CHROMA_PERSIST_DIRECTORY", str(DATA_DIR / "chromadb")),
    "collection_name": os.getenv("CHROMA_COLLECTION_NAME", "novel_knowledge"),
}

# SQLite数据库配置
SQLITE_CONFIG = {
    "database_path": os.getenv("SQLITE_DATABASE_PATH", str(DATA_DIR / "novel.db")),
}

# 日志配置
LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "file": os.getenv("LOG_FILE", str(LOG_DIR / "app.log")),
}

# 小说生成配置
NOVEL_CONFIG = {
    "max_chapters": 20,  # 最大章节数
    "words_per_chapter": 2000,  # 每章字数
    "max_retries": 3,  # 最大重试次数
}

print(f"配置加载完成")
print(f"  - 默认LLM: {DEFAULT_LLM_PROVIDER}")
print(f"  - 数据目录: {DATA_DIR}")
print(f"  - 日志目录: {LOG_DIR}")