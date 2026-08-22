"""
素材转化器模块
包含爬虫、内容提取、分类、Deep Research等功能
"""

import os
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
from enum import Enum


class MaterialCategory(Enum):
    """素材一级分类"""
    OUTLINE = "outline"      # 大纲素材
    DESCRIPTION = "description"  # 描写素材
    BACKGROUND = "background"  # 背景素材
    GENRE = "genre"          # 题材素材


class MaterialQuality(Enum):
    """素材质量"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"


@dataclass
class Material:
    """素材条目"""
    id: str
    title: str
    content: str
    source: str = ""
    source_url: str = ""
    
    # 分类
    primary_category: str = ""  # 一级分类
    secondary_category: str = ""  # 二级分类
    tags: list = field(default_factory=list)
    
    # 质量
    quality: str = MaterialQuality.MEDIUM.value
    usefulness_score: float = 0.5  # 有用性评分 0-1
    
    # 元数据
    word_count: int = 0
    raw_type: str = ""  # 网页/视频/博客/文章
    author: str = ""
    publish_date: str = ""
    
    # 状态
    is_verified: bool = False
    is_duplicate: bool = False
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CrawlTask:
    """爬取任务"""
    id: str
    query: str
    target_categories: list = field(default_factory=list)
    
    # 状态
    status: str = "pending"  # pending/running/completed/failed
    progress: float = 0.0
    
    # 结果
    materials_found: int = 0
    materials_collected: int = 0
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MaterialCollector:
    """素材收集器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, "materials")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 素材存储
        self.materials: dict[str, Material] = {}
        self.tasks: dict[str, CrawlTask] = []
        
        # 分类规则
        self.category_rules = self._init_category_rules()
        
        self._load_all()
    
    def _init_category_rules(self) -> dict:
        """初始化分类规则"""
        return {
            "outline": {
                "keywords": ["大纲", "结构", "开头", "结尾", "高潮", "转折", "节奏"],
                "subcategories": ["长篇", "短篇", "开头", "结尾", "高潮设计", "转折技巧"],
            },
            "description": {
                "keywords": ["描写", "场景", "人物", "动作", "心理", "对话", "环境"],
                "subcategories": ["人物描写", "场景描写", "动作描写", "心理描写", "对话技巧"],
            },
            "background": {
                "keywords": ["设定", "世界观", "力量体系", "社会", "历史", "规则"],
                "subcategories": ["世界观设定", "力量体系", "社会结构", "历史背景"],
            },
            "genre": {
                "keywords": ["修仙", "武侠", "灵异", "都市", "科幻", "奇幻", "玄幻"],
                "subcategories": ["修仙", "武侠", "灵异", "都市", "科幻", "奇幻", "玄幻"],
            },
        }
    
    # ==================== 素材管理 ====================
    
    def add_material(self, material: Material) -> str:
        """添加素材"""
        # 生成ID
        if not material.id:
            material.id = hashlib.md5(material.content[:100].encode()).hexdigest()[:12]
        
        # 自动分类
        if not material.primary_category:
            material.primary_category, material.secondary_category = self._auto_classify(material.content)
        
        # 计算字数
        material.word_count = len(material.content)
        
        self.materials[material.id] = material
        self._save_materials()
        
        return material.id
    
    def get_material(self, material_id: str) -> Optional[Material]:
        """获取素材"""
        return self.materials.get(material_id)
    
    def search_materials(self, query: str = "", category: str = "", 
                         tags: list = None, limit: int = 10) -> list[Material]:
        """搜索素材"""
        results = list(self.materials.values())
        
        # 按关键词过滤
        if query:
            query_lower = query.lower()
            results = [m for m in results 
                      if query_lower in m.title.lower() or query_lower in m.content.lower()]
        
        # 按分类过滤
        if category:
            results = [m for m in results if m.primary_category == category]
        
        # 按标签过滤
        if tags:
            results = [m for m in results if any(tag in m.tags for tag in tags)]
        
        # 按有用性排序
        results.sort(key=lambda x: x.usefulness_score, reverse=True)
        
        return results[:limit]
    
    def update_usefulness(self, material_id: str, score: float):
        """更新素材有用性评分"""
        if material_id in self.materials:
            self.materials[material_id].usefulness_score = max(0, min(1, score))
            self.materials[material_id].updated_at = datetime.now().isoformat()
            self._save_materials()
    
    # ==================== 分类系统 ====================
    
    def _auto_classify(self, content: str) -> tuple[str, str]:
        """自动分类"""
        content_lower = content.lower()
        
        best_category = "outline"
        best_score = 0
        
        for category, rules in self.category_rules.items():
            score = sum(1 for kw in rules["keywords"] if kw in content_lower)
            if score > best_score:
                best_score = score
                best_category = category
        
        # 二级分类（简化）
        secondary = "其他"
        if best_category in self.category_rules:
            subcats = self.category_rules[best_category]["subcategories"]
            for subcat in subcats:
                if subcat in content_lower:
                    secondary = subcat
                    break
        
        return best_category, secondary
    
    def get_category_stats(self) -> dict:
        """获取分类统计"""
        stats = {}
        for material in self.materials.values():
            cat = material.primary_category or "未分类"
            stats[cat] = stats.get(cat, 0) + 1
        return stats
    
    # ==================== 去重与质量控制 ====================
    
    def check_duplicate(self, content: str) -> Optional[str]:
        """检查重复"""
        content_hash = hashlib.md5(content[:200].encode()).hexdigest()
        
        for material in self.materials.values():
            existing_hash = hashlib.md5(material.content[:200].encode()).hexdigest()
            if content_hash == existing_hash:
                return material.id
        
        return None
    
    def filter_low_quality(self, min_words: int = 50) -> list[str]:
        """过滤低质量素材"""
        removed = []
        
        for material_id, material in list(self.materials.items()):
            if material.word_count < min_words:
                material.quality = MaterialQuality.LOW.value
                removed.append(material_id)
        
        self._save_materials()
        return removed
    
    # ==================== 素材导出 ====================
    
    def export_for_learning(self, category: str = "", limit: int = 100) -> list[dict]:
        """导出素材供学习系统使用"""
        materials = self.search_materials(category=category, limit=limit)
        
        return [{
            "id": m.id,
            "title": m.title,
            "content": m.content,
            "category": m.primary_category,
            "subcategory": m.secondary_category,
            "tags": m.tags,
        } for m in materials]
    
    # ==================== 统计 ====================
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total": len(self.materials),
            "categories": self.get_category_stats(),
            "avg_usefulness": sum(m.usefulness_score for m in self.materials.values()) / len(self.materials) if self.materials else 0,
        }
    
    # ==================== 持久化 ====================
    
    def _load_all(self):
        self._load_materials()
        self._load_tasks()
    
    def _load_materials(self):
        filepath = os.path.join(self.data_dir, "materials.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for mat_id, mat_data in data.items():
                    self.materials[mat_id] = Material(**mat_data)
    
    def _load_tasks(self):
        filepath = os.path.join(self.data_dir, "tasks.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.tasks = [CrawlTask(**t) for t in data]
    
    def _save_materials(self):
        filepath = os.path.join(self.data_dir, "materials.json")
        data = {mat_id: asdict(mat) for mat_id, mat in self.materials.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_tasks(self):
        filepath = os.path.join(self.data_dir, "tasks.json")
        data = [asdict(t) for t in self.tasks]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_all(self):
        self._save_materials()
        self._save_tasks()


class DeepResearchAgent:
    """Deep Research 深度研究智能体"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    def plan_research(self, query: str, existing_knowledge: list = None) -> dict:
        """规划研究任务"""
        print(f"[研究规划] 分析需求: {query}")
        
        # 分解为子任务
        subtasks = self._decompose_query(query)
        
        plan = {
            "original_query": query,
            "subtasks": subtasks,
            "search_strategy": "广度优先 + 深度挖掘",
            "expected_sources": ["博客", "教程", "网文", "论坛"],
        }
        
        return plan
    
    def _decompose_query(self, query: str) -> list[dict]:
        """分解查询为子任务"""
        subtasks = []
        
        # 基于关键词分解
        keywords = ["开头", "结尾", "人物", "设定", "爽点", "节奏"]
        
        for keyword in keywords:
            if keyword in query:
                subtasks.append({
                    "query": f"{query} {keyword}技巧",
                    "depth": "deep",
                    "priority": "high",
                })
        
        # 默认子任务
        if not subtasks:
            subtasks = [
                {"query": f"{query} 写法", "depth": "medium", "priority": "high"},
                {"query": f"{query} 案例", "depth": "shallow", "priority": "medium"},
                {"query": f"{query} 常见问题", "depth": "medium", "priority": "low"},
            ]
        
        return subtasks
    
    def search(self, subtask: dict) -> list[dict]:
        """执行搜索（模拟）"""
        print(f"[深度搜索] 搜索: {subtask['query']}")
        
        # 模拟搜索结果
        results = [
            {
                "title": f"{subtask['query']}的技巧",
                "url": "https://example.com/article1",
                "snippet": f"关于{subtask['query']}的详细讲解...",
                "score": 0.85,
            },
            {
                "title": f"{subtask['query']}实战案例",
                "url": "https://example.com/article2",
                "snippet": f"多个{subtask['query']}的成功案例分析...",
                "score": 0.78,
            },
        ]
        
        return results
    
    def synthesize(self, search_results: list[list[dict]]) -> list[Material]:
        """合成知识"""
        print("[知识合成] 整合搜索结果...")
        
        materials = []
        
        for results in search_results:
            for result in results:
                material = Material(
                    id="",
                    title=result.get("title", ""),
                    content=result.get("snippet", ""),
                    source_url=result.get("url", ""),
                    source="deep_research",
                    raw_type="网页",
                )
                materials.append(material)
        
        return materials