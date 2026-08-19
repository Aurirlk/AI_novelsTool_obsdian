# 接口文档

## 核心模块API

### 1. 向量存储 API

#### VectorStore

```python
class VectorStore:
    def add_documents(collection_name: str, documents: list[dict]) -> bool
    def search(collection_name: str, query: str, n_results: int = 5) -> list[dict]
    def delete_collection(name: str) -> None
    def get_stats() -> dict
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| collection_name | str | 集合名称（characters/events/hooks/chapters） |
| documents | list[dict] | 文档列表，格式：[{"id": "", "text": "", "metadata": {}}] |
| query | str | 搜索查询文本 |
| n_results | int | 返回结果数量 |

**返回值：**

```python
# search返回格式
[{
    "id": "char_001",
    "text": "角色描述文本",
    "metadata": {"type": "character", "name": "林云"},
    "distance": 0.15  # 相似度距离
}]
```

#### RAGSystem

```python
class RAGSystem:
    def index_characters(characters: dict) -> None
    def index_events(events: list) -> None
    def index_hooks(hooks: dict) -> None
    def index_chapters(chapters: list) -> None
    def search_relevant_context(query: str, context_type: str = "all") -> dict
    def generate_writing_context(chapter_info: dict, involved_characters: list = None) -> str
```

### 2. 缓存 API

#### ChapterCache

```python
class ChapterCache:
    def get_chapter(chapter_num: int) -> Optional[dict]
    def save_chapter(chapter_num: int, content: dict) -> None
    def get_recent_chapters(count: int = 5) -> list[dict]
```

#### ContextCache

```python
class ContextCache:
    def get_context(key: str) -> Optional[str]
    def set_context(key: str, context: str) -> None
    def generate_context_key(chapter_num: int, characters: list) -> str
```

### 3. 流式输出 API

#### StreamHandler

```python
class StreamHandler:
    def start() -> None
    def add_chunk(content: str, chunk_type: str = "text") -> None
    def complete() -> None
    def error(error_msg: str) -> None
    def register_callback(callback: Callable) -> None
    def get_progress() -> dict
```

**回调函数签名：**

```python
def on_stream_event(event: str, data: dict):
    """
    event: "start" | "chunk" | "complete" | "error"
    data: {"content": "", "full_content": "", ...}
    """
```

#### StreamingWriter

```python
class StreamingWriter:
    def write_stream(prompt: str, system_prompt: str = "", on_chunk: Callable = None) -> str
```

### 4. 工作流引擎 API

#### WorkflowEngine

```python
class WorkflowEngine:
    def register_agent(name: str, agent_func: Callable) -> None
    def add_node(node: WorkflowNode) -> None
    def connect(from_id: str, to_id: str, condition: str = None) -> None
    def create_novel_workflow() -> None
    def start(initial_data: dict = None) -> None
    def get_status() -> dict
```

**状态返回格式：**

```python
{
    "workflow_id": "wf_xxx",
    "status": "running" | "completed" | "failed",
    "current_node": "chapter_write",
    "progress": 0.5,
    "history_count": 5
}
```

### 5. 智能体 API

#### OutlineAgent

```python
class OutlineAgent:
    def execute(state: NovelState, idea: str = "") -> dict
    def generate_chapter_outline(state: NovelState, chapter_num: int) -> dict
```

#### WriterAgent

```python
class WriterAgent:
    def execute(state: NovelState, chapter_num: int = 0) -> dict
```

#### ReviewerAgent

```python
class ReviewerAgent:
    def execute(state: NovelState, chapter_num: int = 0) -> dict
```

**返回格式：**

```python
{
    "state": NovelState,
    "chapter": Chapter,
    "result": {
        "passed": True,
        "issues": [],
        "suggestions": []
    }
}
```

### 6. 记忆系统 API

#### MemoryManager

```python
class MemoryManager:
    def add_character(character: CharacterState) -> None
    def update_character(char_id: str, **kwargs) -> None
    def move_character(char_id: str, location: str, chapter_num: int) -> None
    def kill_character(char_id: str, chapter_num: int, death_method: str = "") -> None
    def add_hook(hook: Hook) -> None
    def resolve_hook(hook_id: str, chapter_num: int) -> None
    def add_event(chapter_num: int, event_type: str, content: str, ...) -> None
    def generate_writing_context(chapter_num: int, involved_characters: list = None) -> str
    def generate_summary() -> str
```

#### EntityDictionary

```python
class EntityDictionary:
    def add_item(item: Item) -> None
    def add_location(location: Location) -> None
    def add_skill(skill: Skill) -> None
    def use_skill(skill_id: str, chapter_num: int) -> tuple[bool, str]
    def check_item_consistency(item_id: str, claimed_owner: str) -> tuple[bool, str]
    def generate_entity_context(chapter_num: int, involved_entities: list = None) -> str
```

#### WorldRulesManager

```python
class WorldRulesManager:
    def add_rule(rule: WorldRule) -> None
    def add_time_point(chapter_num: int, story_time: str, ...) -> None
    def check_rule_compliance(action: str, location: str = "", character: str = "") -> list[dict]
    def generate_rules_context(location: str = "") -> str
```

#### PsychologyManager

```python
class PsychologyManager:
    def add_profile(profile: PsychologicalProfile) -> None
    def update_dimension(character_id: str, dimension: str, change: float, reason: str = "") -> tuple[bool, str]
    def advance_stage(character_id: str, new_stage: str) -> tuple[bool, str]
    def generate_psychology_context(character_id: str) -> str
```

### 7. 数据管理 API

#### ProjectManager

```python
class ProjectManager:
    def create_project(name: str, genre: str, description: str = "") -> str
    def load_project(project_id: str) -> Optional[ProjectData]
    def save_project(project_id: str, project_data: ProjectData) -> None
    def delete_project(project_id: str) -> bool
    def list_projects() -> list[dict]
```

#### MaterialCollector

```python
class MaterialCollector:
    def add_material(material: Material) -> str
    def search_materials(query: str = "", category: str = "", limit: int = 10) -> list[Material]
    def update_usefulness(material_id: str, score: float) -> None
    def export_for_learning(category: str = "", limit: int = 100) -> list[dict]
    def get_stats() -> dict
```

### 8. 导出 API

#### NovelExporter

```python
class NovelExporter:
    def export_txt(title: str, chapters: list[dict], filename: Optional[str] = None) -> str
    def export_markdown(title: str, chapters: list[dict], metadata: dict = None, filename: Optional[str] = None) -> str
    def export_word(title: str, chapters: list[dict], metadata: dict = None, filename: Optional[str] = None) -> str
```

## 数据结构

### NovelState

```python
@dataclass
class NovelState:
    story_bible: Optional[StoryBible]
    characters: dict[str, Character]
    chapters: list[Chapter]
    hooks: dict[str, Hook]
    current_chapter: int
    total_words: int
```

### CharacterState

```python
@dataclass
class CharacterState:
    id: str
    name: str
    role: str  # 主角/配角/反派/龙套
    layer: str  # core/active/archived
    personality: str
    background: str
    current_location: str
    status: str  # alive/dead/missing/injured
    abilities: list[str]
    items: list[str]
    relationships: dict[str, str]
```

### Hook

```python
@dataclass
class Hook:
    id: str
    content: str
    hook_type: str  # 主线/支线/物品/人物秘密
    status: str  # planted/developing/about_to_resolve/resolved/forgotten
    planted_chapter: int
    expected_resolve_chapter: int
    actual_resolve_chapter: Optional[int]
    related_characters: list[str]
```

### Chapter

```python
@dataclass
class Chapter:
    number: int
    title: str
    content: str
    status: str  # draft/reviewing/approved/rejected/polished
    summary: str
    word_count: int
    hooks_planted: list[str]
    hooks_resolved: list[str]
    characters_appeared: list[str]
```