"""
风格指南
管理文风统一要求
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class StyleGuide:
    """风格指南"""
    name: str
    
    # 基础风格
    tone: str = "中性"        # 幽默/严肃/热血/轻松
    perspective: str = "第三人称"  # 第一人称/第三人称
    
    # 句式要求
    avg_sentence_length: int = 30  # 平均句长
    dialogue_ratio: float = 0.2    # 对话比例
    
    # 描写偏好
    description_style: str = "简洁"  # 简洁/华丽/细腻
    action_style: str = "快节奏"     # 快节奏/慢节奏/适中
    
    # 禁用词/句
    forbidden_words: list = field(default_factory=list)
    forbidden_patterns: list = field(default_factory=list)
    
    # 必用元素
    required_elements: list = field(default_factory=list)
    
    # 示例
    good_examples: list = field(default_factory=list)
    bad_examples: list = field(default_factory=list)
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StyleGuideManager:
    """风格指南管理器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, "style")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.guides: dict[str, StyleGuide] = {}
        self.current_guide: str = ""
        
        self._load_all()
    
    def add_guide(self, guide: StyleGuide):
        """添加风格指南"""
        self.guides[guide.name] = guide
        self._save_guides()
    
    def set_current_guide(self, guide_name: str):
        """设置当前使用的风格"""
        if guide_name in self.guides:
            self.current_guide = guide_name
            self._save_config()
    
    def get_current_guide(self) -> Optional[StyleGuide]:
        """获取当前风格"""
        return self.guides.get(self.current_guide)
    
    def check_style_consistency(self, content: str) -> dict:
        """检查风格一致性"""
        guide = self.get_current_guide()
        if not guide:
            return {"consistent": True, "issues": []}
        
        issues = []
        
        # 检查禁用词
        for word in guide.forbidden_words:
            if word in content:
                issues.append(f"包含禁用词：{word}")
        
        # 检查句长
        sentences = content.split("。")
        if sentences:
            avg_len = sum(len(s) for s in sentences) / len(sentences)
            if avg_len > guide.avg_sentence_length * 1.5:
                issues.append(f"平均句长 {avg_len:.0f} 超过标准 {guide.avg_sentence_length}")
        
        return {
            "consistent": len(issues) == 0,
            "issues": issues,
        }
    
    def generate_style_prompt(self) -> str:
        """生成风格Prompt"""
        guide = self.get_current_guide()
        if not guide:
            return ""
        
        prompt = f"""【风格指南】
基调：{guide.tone}
视角：{guide.perspective}
平均句长：约{guide.avg_sentence_length}字
对话比例：{guide.dialogue_ratio*100:.0f}%
描写风格：{guide.description_style}
动作节奏：{guide.action_style}
"""
        
        if guide.forbidden_words:
            prompt += f"\n禁用词：{', '.join(guide.forbidden_words)}"
        
        if guide.good_examples:
            prompt += "\n\n【优秀示例】"
            for ex in guide.good_examples[:3]:
                prompt += f"\n{ex[:100]}..."
        
        return prompt
    
    def _load_all(self):
        self._load_guides()
        self._load_config()
    
    def _load_guides(self):
        filepath = os.path.join(self.data_dir, "guides.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, guide_data in data.items():
                    self.guides[name] = StyleGuide(**guide_data)
    
    def _load_config(self):
        filepath = os.path.join(self.data_dir, "config.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.current_guide = data.get("current_guide", "")
    
    def _save_guides(self):
        filepath = os.path.join(self.data_dir, "guides.json")
        data = {name: asdict(guide) for name, guide in self.guides.items()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_config(self):
        filepath = os.path.join(self.data_dir, "config.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"current_guide": self.current_guide}, f, ensure_ascii=False, indent=2)
    
    def save_all(self):
        self._save_guides()
        self._save_config()