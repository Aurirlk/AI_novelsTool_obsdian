# 技术文档

## 系统架构概述

AI写作助手采用多智能体协作架构，包含以下核心模块：

1. **核心基础设施层** - 向量存储、缓存、流式输出、工作流引擎
2. **智能体层** - 11个专业智能体协同工作
3. **记忆系统层** - 7个记忆模块管理长期记忆
4. **数据管理层** - 项目管理、素材收集、导出
5. **UI层** - PyQt6桌面应用

## 核心模块详解

### 1. 向量存储系统 (`src/core/vector_store.py`)

基于ChromaDB的向量数据库，支持语义检索。

```python
from src.core.vector_store import get_vector_store, get_rag_system

# 获取向量存储实例
vector_store = get_vector_store()

# 添加文档
vector_store.add_documents("characters", [
    {"id": "char_001", "text": "林云：修仙少年", "metadata": {"role": "主角"}}
])

# 语义搜索
results = vector_store.search("characters", "修仙", n_results=5)

# RAG系统
rag = get_rag_system()
context = rag.generate_writing_context(chapter_info, involved_characters)
```

### 2. 缓存系统 (`src/core/cache_manager.py`)

多级缓存架构，加速上下文加载。

```python
from src.core.cache_manager import get_chapter_cache, get_context_cache

# 章节缓存
cache = get_chapter_cache()
cache.save_chapter(1, chapter_data)
chapter = cache.get_chapter(1)

# 上下文缓存
ctx_cache = get_context_cache()
ctx_cache.set_context("ctx_001", context_text)
```

### 3. 流式输出 (`src/core/stream_handler.py`)

支持LLM流式响应和实时UI更新。

```python
from src.core.stream_handler import StreamingWriter

writer = StreamingWriter(llm_client)
writer.write_stream(
    prompt="写一个修仙小说开头",
    on_chunk=lambda event, data: print(data["content"])
)
```

### 4. 工作流引擎 (`src/core/workflow_engine.py`)

状态机管理多智能体协作。

```python
from src.core.workflow_engine import get_workflow_engine

engine = get_workflow_engine()
engine.create_novel_workflow()
engine.start({"idea": "废柴逆袭修仙"})

# 查看状态
status = engine.get_status()
```

## 智能体系统

### 智能体列表

| 智能体 | 文件 | 职责 |
|--------|------|------|
| 大纲师 | outline_agent.py | 生成故事大纲和章节细纲 |
| 码字工 | writer_agent.py | 撰写章节内容 |
| 督察 | reviewer_agent.py | 审核内容一致性 |
| 运营 | polisher_agent.py | 润色和生成标题 |
| 评论家 | critic_agent.py | 批评评分、Prompt自进化 |
| 复盘智能体 | review_agent.py | 定期总结、调整规划 |
| 读者模拟器 | review_agent.py | 模拟读者反馈 |

### 智能体协作流程

```
用户输入创意
    ↓
大纲师 → 生成故事Bible
    ↓
码字工 → 撰写章节初稿
    ↓
督察 → 审核（12项检查）
    ↓ (不通过则返回码字工)
运营 → 润色优化
    ↓
数据持久化
    ↓
复盘智能体 → 定期总结
    ↓
评论家 → Prompt自进化
```

## 记忆系统

### 记忆模块列表

| 模块 | 文件 | 功能 |
|------|------|------|
| 记忆管理器 | memory_manager.py | 人物状态、钩子追踪、大事记 |
| 实体词典 | entity_dictionary.py | 物品/地点/技能管理 |
| 世界观规则 | world_rules.py | 规则清单、全局时间轴 |
| 心理维度 | psychology.py | 心理档案、情感案例 |
| 风格指南 | style_guide.py | 文风统一要求 |

### 分层记忆架构

| 层级 | 内容 | 存储方式 | 更新频率 |
|------|------|----------|----------|
| 层级0 | 故事Bible | JSON | 极少修改 |
| 层级1 | 人物档案 | 向量+结构化 | 每章更新 |
| 层级2 | 大事记 | 列表+摘要 | 每章追加 |
| 层级3 | 最近N章 | 缓存 | 滚动更新 |
| 层级4 | 钩子清单 | 结构化 | 每章更新 |

## 审核系统

### 12项审核检查

1. 人物时空一致性
2. 人物性格一致性
3. 能力体系一致性
4. 时间线一致性
5. 世界观规则遵守
6. 钩子一致性
7. 前文连续性
8. 实体名称一致性
9. 信息密度
10. 智商合理性
11. 情感铺垫
12. 爽点重复度

## 数据存储

### 存储结构

```
data/
├── projects/           # 项目数据
│   └── proj_xxx/
│       ├── config.json
│       ├── story_bible.json
│       ├── characters.json
│       ├── chapters.json
│       ├── hooks.json
│       ├── events.json
│       └── memory/
├── chromadb/           # 向量数据库
├── cache/              # 缓存
├── materials/          # 素材库
└── exports/            # 导出文件
```

## LLM集成

### 支持的LLM提供商

| 提供商 | 模型 | 成本 |
|--------|------|------|
| 智谱GLM | glm-4-flash | 免费 |
| DeepSeek | deepseek-v4-flash | ¥1-2/百万token |
| OpenAI | gpt-4o-mini | $0.15/百万token |

### LLM调用示例

```python
from src.utils.llm import get_llm_client

client = get_llm_client("zhipuai")
response = client.chat("写一个修仙小说开头", system_prompt="你是一位网文作者")
```

## 性能优化

### 缓存策略
- 内存LRU缓存：最近访问的章节和上下文
- 文件缓存：持久化存储

### 向量检索优化
- 使用ChromaDB本地部署，避免网络延迟
- 批量索引，减少索引次数

### 流式输出
- 实时返回生成内容，提升用户体验
- 进度追踪，显示生成状态