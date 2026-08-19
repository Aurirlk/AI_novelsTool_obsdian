"""
向量存储模块
使用ChromaDB实现语义检索
"""

import os
import json
import re
from typing import Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[警告] ChromaDB未安装，向量检索功能不可用")


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, persist_dir: str = "data/vector_db"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        self.client = None
        self.collections = {}
        
        if CHROMADB_AVAILABLE:
            self._init_chromadb()
    
    def _init_chromadb(self):
        """初始化ChromaDB"""
        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            print(f"[向量存储] ChromaDB初始化成功: {self.persist_dir}")
        except Exception as e:
            print(f"[向量存储] ChromaDB初始化失败: {e}")
            self.client = None
    
    def get_collection(self, name: str):
        """获取或创建集合"""
        if not self.client:
            return None
        
        if name not in self.collections:
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"[向量存储] 获取集合失败: {e}")
                return None
        
        return self.collections[name]
    
    def add_documents(self, collection_name: str, documents: list[dict]):
        """
        添加文档到向量库
        
        Args:
            collection_name: 集合名称
            documents: 文档列表 [{"id": "...", "text": "...", "metadata": {...}}]
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return False
        
        try:
            ids = [doc["id"] for doc in documents]
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"[向量存储] 添加 {len(documents)} 个文档到 {collection_name}")
            return True
        except Exception as e:
            print(f"[向量存储] 添加文档失败: {e}")
            return False
    
    def search(self, collection_name: str, query: str, 
               n_results: int = 5, where: dict = None) -> list[dict]:
        """
        语义搜索
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
        
        Returns:
            搜索结果列表
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return []
        
        try:
            kwargs = {
                "query_texts": [query],
                "n_results": n_results,
            }
            
            if where:
                kwargs["where"] = where
            
            results = collection.query(**kwargs)
            
            # 格式化结果
            formatted_results = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    result = {
                        "id": results["ids"][0][i] if results["ids"] else "",
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    }
                    formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            print(f"[向量存储] 搜索失败: {e}")
            return []
    
    def delete_collection(self, name: str):
        """删除集合"""
        if self.client:
            try:
                self.client.delete_collection(name)
                if name in self.collections:
                    del self.collections[name]
                print(f"[向量存储] 删除集合: {name}")
            except Exception as e:
                print(f"[向量存储] 删除集合失败: {e}")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self.client:
            return {"status": "不可用", "collections": 0}
        
        try:
            collections = self.client.list_collections()
            return {
                "status": "可用",
                "collections": len(collections),
                "names": [c.name for c in collections],
            }
        except Exception as e:
            return {"status": f"错误: {e}", "collections": 0}


class RAGSystem:
    """RAG检索增强系统"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def index_characters(self, characters: dict):
        """索引角色信息"""
        if not self.vector_store:
            return
        documents = []
        
        for char_id, char in characters.items():
            text = f"""
角色名: {char.get('name', '')}
类型: {char.get('role', '')}
性格: {char.get('personality', '')}
背景: {char.get('background', '')}
当前位置: {char.get('current_location', '')}
状态: {char.get('status', 'alive')}
"""
            documents.append({
                "id": f"char_{char_id}",
                "text": text.strip(),
                "metadata": {
                    "type": "character",
                    "char_id": char_id,
                    "name": char.get('name', ''),
                }
            })
        
        if documents:
            self.vector_store.add_documents("characters", documents)
    
    def index_events(self, events: list):
        """索引事件"""
        if not self.vector_store:
            return
        documents = []
        
        for event in events:
            text = f"""
章节: 第{event.get('chapter_num', 0)}章
类型: {event.get('event_type', '')}
内容: {event.get('content', '')}
重要程度: {event.get('importance', 5)}
"""
            documents.append({
                "id": event.get('id', ''),
                "text": text.strip(),
                "metadata": {
                    "type": "event",
                    "chapter": event.get('chapter_num', 0),
                    "importance": event.get('importance', 5),
                }
            })
        
        if documents:
            self.vector_store.add_documents("events", documents)
    
    def index_hooks(self, hooks: dict):
        """索引钩子"""
        if not self.vector_store:
            return
        documents = []
        
        for hook_id, hook in hooks.items():
            text = f"""
钩子内容: {hook.get('content', '')}
类型: {hook.get('hook_type', '')}
状态: {hook.get('status', '')}
埋下章节: 第{hook.get('planted_chapter', 0)}章
预期回收: 第{hook.get('expected_resolve_chapter', 0)}章
"""
            documents.append({
                "id": f"hook_{hook_id}",
                "text": text.strip(),
                "metadata": {
                    "type": "hook",
                    "hook_id": hook_id,
                    "status": hook.get('status', ''),
                }
            })
        
        if documents:
            self.vector_store.add_documents("hooks", documents)
    
    def index_chapters(self, chapters: list):
        """索引章节"""
        if not self.vector_store:
            return
        documents = []
        
        for chapter in chapters:
            # 只索引摘要，不索引全文
            text = f"""
章节: 第{chapter.get('number', 0)}章
标题: {chapter.get('title', '')}
摘要: {chapter.get('summary', '')[:200]}
"""
            documents.append({
                "id": f"chapter_{chapter.get('number', 0)}",
                "text": text.strip(),
                "metadata": {
                    "type": "chapter",
                    "chapter_num": chapter.get('number', 0),
                }
            })
        
        if documents:
            self.vector_store.add_documents("chapters", documents)

    # ==================== 正则+关键字混合检索 ====================

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def _load_corpus(self) -> dict:
        """实时读取本地数据作为检索语料：{角色/事件/钩子/章节（全文）}（统一存储：写作空间书目录）"""
        corpus = {"characters": [], "events": [], "hooks": [], "chapters": []}
        try:
            from src.data.character_store import load_all_books_characters
            for c in load_all_books_characters():
                corpus["characters"].append({
                    "id": c.get("id", ""),
                    "text": " ".join(str(c.get(k, "")) for k in
                                     ("name", "role", "personality", "background", "location")),
                })
        except Exception:
            pass
        try:
            from src.data.timeline_store import load_all_books_events
            for e in load_all_books_events():
                corpus["events"].append({
                    "id": e.get("id", ""),
                    "text": f"第{e.get('chapter', 0)}章 {e.get('title', '')} {e.get('content', '')}",
                })
        except Exception:
            pass
        try:
            from src.data.hook_store import load_all_books_hooks
            for h in load_all_books_hooks():
                corpus["hooks"].append({
                    "id": h.get("id", ""),
                    "text": f"{h.get('content', '')} {h.get('hook_type', '')}",
                })
        except Exception:
            pass
        try:
            from src.data.search_index import _iter_chapters, chapter_content
            for ch in _iter_chapters():
                # 章节索引全文（不截断，避免中后段关键词漏检）
                corpus["chapters"].append({
                    "id": ch["path"],
                    "text": f"{ch['book']} {ch['name']} {chapter_content(ch['path'])}",
                })
        except Exception:
            pass
        return corpus

    @staticmethod
    def _split_keywords(query: str) -> list:
        """规则切分候选关键词（不调 LLM）：
        1. 《》/引号内容 2. 已知角色名子串 3. 标点切分的 2-6 字片段
        """
        kws = set()
        for m in re.finditer(r"[《「『\"']([^》」』\"']{2,12})", query):
            kws.add(m.group(1).strip())
        # 已知角色名子串
        try:
            from src.data.character_store import load_all_books_characters
            for c in load_all_books_characters():
                name = (c.get("name") or "").strip()
                if name and len(name) >= 2 and name in query:
                    kws.add(name)
        except Exception:
            pass
        # 事件标题/钩子内容的 2-6 字片段子串
        try:
            from src.data.timeline_store import load_all_books_events
            for e in load_all_books_events():
                for frag in re.split(r"[,，。.!！?？;；\s]+", e.get("title", "")):
                    frag = frag.strip()
                    if 2 <= len(frag) <= 6 and frag in query:
                        kws.add(frag)
        except Exception:
            pass
        try:
            from src.data.hook_store import load_all_books_hooks
            for h in load_all_books_hooks():
                for frag in re.split(r"[,，。.!！?？;；\s]+", h.get("content", "")):
                    frag = frag.strip()
                    if 2 <= len(frag) <= 6 and frag in query:
                        kws.add(frag)
        except Exception:
            pass
        for part in re.split(r"[,，。.!！?？;；\s]+", query):
            part = part.strip()
            if 2 <= len(part) <= 6:
                kws.add(part)
        return [k for k in kws if k][:10]

    def _regex_search(self, corpus: dict, keywords: list, limit: int = 8) -> list:
        """多关键词正则匹配（并集），返回命中列表 [{type, id, text}]"""
        hits = []
        seen = set()
        for kw in keywords:
            if not kw:
                continue
            try:
                rx = re.compile(re.escape(kw), re.IGNORECASE)
            except re.error:
                continue
            for ctype, items in corpus.items():
                for it in items:
                    key = (ctype, it["id"])
                    if key in seen:
                        continue
                    if rx.search(it["text"]):
                        seen.add(key)
                        hits.append({"type": ctype, "id": it["id"], "text": it["text"]})
        return hits[:limit]

    def _extract_keywords_llm(self, query: str) -> list:
        """LLM 提取关键词；无密钥/失败时返回空列表（由规则结果兜底）"""
        try:
            from src.utils.llm import LLMClient
            client = LLMClient()
            resp = client.chat(
                f"从以下写作场景中提取3-5个用于检索的关键词（人物名、地点、事件、术语均可），"
                f"用逗号分隔，只输出关键词，不要解释。\n场景：{query}",
                system_prompt="你是检索关键词提取器。")
            kws = [k.strip() for k in resp.replace("\n", ",").split(",") if k.strip()][:6]
            return kws
        except Exception:
            return []

    def generate_writing_context(self, chapter_info: dict,
                                 involved_characters: list = None) -> str:
        """
        生成写作上下文（正则+关键字混合检索，LLM 增强）

        策略（grill-me 第四轮决策 + 修正版）：
        1. 规则切分关键词（书名号/实体/片段），正则匹配本地语料（章节全文）
        2. 零命中或多命中(≥8) 时 LLM 提取关键词补搜，结果与正则结果**并集**
        3. 无 ChromaDB 依赖、无 key 也可用（规则层不调 LLM）
        """
        query = chapter_info.get("outline", "") or " ".join(involved_characters or [])
        if not query:
            return ""

        corpus = self._load_corpus()
        hits = self._regex_search(corpus, self._split_keywords(query), limit=8)

        # 零命中或多命中 → LLM 关键词补搜（并集，不覆盖已有结果）
        if not hits or len(hits) >= 8:
            llm_kws = self._extract_keywords_llm(query)
            if llm_kws:
                existing = {(h["type"], h["id"]) for h in hits}
                for h in self._regex_search(corpus, llm_kws, limit=8):
                    if (h["type"], h["id"]) not in existing:
                        hits.append(h)
                hits = hits[:8]

        if not hits:
            return ""

        parts = []
        for h in hits[:8]:
            label = {"characters": "角色", "events": "事件", "hooks": "悬念",
                     "chapters": "章节"}.get(h["type"], h["type"])
            parts.append(f"【{label}】{h['text'][:150]}")
        return "\n".join(parts)

    def search_relevant_context(self, query: str, context_type: str = "all",
                                 n_results: int = 5) -> dict:
        """
        搜索相关上下文
        
        Args:
            query: 查询内容
            context_type: 上下文类型 (character/event/hook/chapter/all)
            n_results: 每种类型返回的结果数量
        
        Returns:
            相关上下文
        """
        if not self.vector_store:
            return {}
        results = {}
        
        collections_to_search = []
        if context_type == "all":
            collections_to_search = ["characters", "events", "hooks", "chapters"]
        else:
            collections_to_search = [context_type]
        
        for collection_name in collections_to_search:
            search_results = self.vector_store.search(
                collection_name=collection_name,
                query=query,
                n_results=n_results
            )
            
            if search_results:
                results[collection_name] = search_results
        
        return results


# 全局实例
_vector_store: Optional[VectorStore] = None
_rag_system: Optional[RAGSystem] = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def get_rag_system() -> RAGSystem:
    """获取RAG系统单例（混合检索模式：不初始化 ChromaDB，避免 embedding 模型下载卡顿）

    正则+关键字混合检索直接读取本地 JSON/章节数据，离线可用。
    vector_store 置空：ChromaDB 向量接口仅在有明确调用时按需创建。
    """
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem(None)
    return _rag_system