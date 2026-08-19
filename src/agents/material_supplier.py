"""
素材供应商智能体
为作者提供写作素材、参考和灵感
"""

import uuid
from typing import Optional, List, Dict
from src.agents.base import BaseAgent
from src.models.schemas import NovelState
from src.data.history_manager import get_history_manager, HistoryRecord
from src.knowledge.loader import load_knowledge


class MaterialSupplier(BaseAgent):
    """素材供应商智能体 - 提供写作素材"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__("素材供应商", llm_provider)
        self.history_manager = get_history_manager()
        self.knowledge_base = None
    
    def execute(self, state: NovelState, query: str = "", 
                mode: str = "provide_material",
                project_name: str = "未命名项目", **kwargs) -> dict:
        """
        执行素材供应
        
        Args:
            state: 小说状态
            query: 查询内容
            mode: 模式（provide_material/provide_inspiration/provide_reference）
            project_name: 项目名称
        
        Returns:
            素材结果
        """
        self._log(f"开始搜索素材 (模式: {mode})...")
        
        if not query:
            return {
                "error": "未提供查询内容",
                "materials": [],
                "report": "无法搜索素材：未提供查询内容"
            }
        
        # 根据模式执行不同的搜索
        if mode == "provide_material":
            result = self._provide_material(query)
        elif mode == "provide_inspiration":
            result = self._provide_inspiration(query)
        elif mode == "provide_reference":
            result = self._provide_reference(query)
        else:
            result = self._provide_material(query)
        
        # 保存历史记录
        record_id = str(uuid.uuid4())[:8]
        history_record = HistoryRecord(
            id=record_id,
            function_type="material_supplier",
            project_name=project_name,
            title=f"素材供应 - {query[:50]}",
            content=query,
            result=result["report"],
            metadata={
                "mode": mode,
                "material_count": len(result["materials"]),
            }
        )
        self.history_manager.save_record(history_record)
        
        self._log(f"素材搜索完成: 找到 {len(result['materials'])} 个素材")
        
        return {
            **result,
            "history_record_id": record_id,
        }
    
    def _provide_material(self, query: str) -> dict:
        """提供写作素材"""
        self._log("搜索写作素材...")
        
        # 从知识库搜索
        knowledge_results = self._search_knowledge(query)
        
        # 从LLM生成素材
        llm_results = self._generate_material(query)
        
        # 合并结果
        materials = knowledge_results + llm_results
        
        # 生成报告
        report = self._generate_report(materials, "写作素材")
        
        return {
            "materials": materials,
            "report": report,
            "mode": "provide_material",
        }
    
    def _provide_inspiration(self, query: str) -> dict:
        """提供灵感"""
        self._log("搜索灵感素材...")
        
        prompt = f"""
请为以下主题提供创作灵感：

主题：{query}

请从以下角度提供灵感：
1. 经典作品中的类似情节
2. 现实生活中的类似事件
3. 可以借鉴的写作技巧
4. 创新的情节设计方向
5. 独特的人物设定建议

请提供具体、可操作的灵感。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_supplier_prompt())
            materials = self._parse_materials(response, "inspiration")
            report = self._generate_report(materials, "灵感素材")
            
            return {
                "materials": materials,
                "report": report,
                "mode": "provide_inspiration",
            }
        except Exception as e:
            self._log(f"搜索失败: {e}")
            return {
                "materials": [],
                "report": f"搜索失败: {e}",
                "mode": "provide_inspiration",
            }
    
    def _provide_reference(self, query: str) -> dict:
        """提供参考"""
        self._log("搜索参考素材...")
        
        prompt = f"""
请为以下内容提供参考：

内容：{query}

请从以下角度提供参考：
1. 类似作品的处理方式
2. 专业领域的知识参考
3. 历史事件的参考
4. 人物原型的参考
5. 场景描写的参考

请提供具体、详细的参考内容。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_supplier_prompt())
            materials = self._parse_materials(response, "reference")
            report = self._generate_report(materials, "参考素材")
            
            return {
                "materials": materials,
                "report": report,
                "mode": "provide_reference",
            }
        except Exception as e:
            self._log(f"搜索失败: {e}")
            return {
                "materials": [],
                "report": f"搜索失败: {e}",
                "mode": "provide_reference",
            }
    
    def _search_knowledge(self, query: str) -> List[Dict]:
        """从知识库搜索"""
        if self.knowledge_base is None:
            self.knowledge_base = load_knowledge()
        
        results = self.knowledge_base.query(query)
        
        materials = []
        for result in results:
            materials.append({
                "type": "knowledge",
                "content": result["content"],
                "source": "知识库",
                "relevance": result.get("score", 0),
            })
        
        return materials
    
    def _generate_material(self, query: str) -> List[Dict]:
        """从LLM生成素材"""
        prompt = f"""
请为以下主题提供写作素材：

主题：{query}

请提供5个具体的素材，每个素材包括：
1. 素材内容
2. 适用场景
3. 使用建议

请用JSON格式输出。
"""
        
        try:
            response = self.llm.chat(prompt, system_prompt=self._get_supplier_prompt())
            materials = self._parse_materials(response, "generated")
            return materials
        except Exception as e:
            self._log(f"生成失败: {e}")
            return []
    
    def _get_supplier_prompt(self) -> str:
        """获取供应商系统提示词"""
        return """你是一位资深的写作素材供应商，专门为作者提供写作素材、参考和灵感。

你的特点：
1. 知识渊博：了解各种类型的素材
2. 实用性强：提供的素材可以直接使用
3. 创意丰富：能够提供独特的素材
4. 分类清晰：素材分类明确，便于查找

你的目标：
- 为作者提供高质量的写作素材
- 帮助作者解决"不知道写什么"的问题
- 激发作者的创作灵感

请提供具体、详细、可操作的素材。"""
    
    def _parse_materials(self, response: str, material_type: str) -> List[Dict]:
        """解析素材"""
        materials = []
        
        paragraphs = response.split("\n")
        
        current_material = None
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 检测素材
            if any(keyword in paragraph for keyword in ["素材", "灵感", "参考", "建议"]):
                if current_material:
                    materials.append(current_material)
                
                current_material = {
                    "type": material_type,
                    "content": paragraph,
                    "source": "AI生成",
                    "usage": "",
                }
            elif current_material and ("适用" in paragraph or "使用" in paragraph):
                current_material["usage"] = paragraph
        
        if current_material:
            materials.append(current_material)
        
        # 如果没有解析出素材，创建一个通用素材
        if not materials and response:
            materials.append({
                "type": material_type,
                "content": response[:500] if len(response) > 500 else response,
                "source": "AI生成",
                "usage": "请根据需要使用",
            })
        
        return materials
    
    def _generate_report(self, materials: List[Dict], title: str) -> str:
        """生成报告"""
        if not materials:
            return f"## {title}\n\n未找到相关素材。"
        
        report_parts = [
            f"## {title}",
            "",
            f"共找到 {len(materials)} 个素材：",
            "",
        ]
        
        for i, material in enumerate(materials, 1):
            report_parts.append(f"### {i}. {material['content'][:100]}...")
            report_parts.append(f"**来源**: {material['source']}")
            if material.get('usage'):
                report_parts.append(f"**使用建议**: {material['usage']}")
            report_parts.append("")
        
        return "\n".join(report_parts)


def create_material_supplier(llm_provider: Optional[str] = None) -> MaterialSupplier:
    """创建素材供应商实例"""
    return MaterialSupplier(llm_provider)
