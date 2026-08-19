"""
技能加载器
扫描并解析 SKILL.md 文件（OpenCode/Claude Code 约定）

SKILL.md 格式:
    ---
    name: story-deslop
    description: 去除AI味...
    triggers: 去AI味, deslop
    ---
    # 正文指令（Markdown）
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Skill:
    """一个技能"""
    name: str
    description: str
    content: str
    path: str
    triggers: List[str] = field(default_factory=list)   # 显式触发词（frontmatter/引号/斜杠）
    keywords: List[str] = field(default_factory=list)   # 领域关键词（弱触发）
    source: str = "local"  # local / builtin / github

    def matches(self, text: str) -> bool:
        lowered = text.lower()
        return any(t.lower() in lowered for t in self.triggers + self.keywords if t)

    def match_score(self, text: str) -> int:
        """匹配打分：名称命中 > 显式触发词 > 领域关键词（描述中越靠前分越高）"""
        lowered = text.lower().replace(" ", "")
        if self.name.lower() in lowered:
            return 100
        best = 0
        for t in self.triggers:
            if t and t.lower() in lowered:
                best = max(best, 50 + min(len(t), 10))
        normalized_desc = self.description.replace(" ", "")
        for kw in self.keywords:
            if kw and kw in lowered:
                pos = normalized_desc.find(kw)
                position_bonus = max(0, 5 - pos // 10) if pos >= 0 else 0
                best = max(best, 10 + position_bonus + min(len(kw), 5))
        return best


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 YAML frontmatter（支持简单 key: value，无需 pyyaml）"""
    meta = {}
    if not text.startswith("---"):
        return meta, text

    end = text.find("\n---", 3)
    if end == -1:
        return meta, text

    header = text[3:end].strip()
    body = text[end + 4:].lstrip("\r\n")

    for line in header.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "triggers":
            # 支持 "a, b, c" 或 "[a, b, c]"
            value = value.strip("[]")
            meta[key] = [v.strip().strip('"').strip("'") for v in value.split(",") if v.strip()]
        else:
            meta[key] = value

    return meta, body


# 网文领域关键词：描述中出现即注册为触发词
DOMAIN_KEYWORDS = [
    "爽点", "打脸", "扮猪吃虎", "逆袭", "复仇",
    "大纲", "细纲", "提纲", "架构",
    "开篇", "黄金三章", "开头", "前三章",
    "金手指", "系统流",
    "对话", "台词", "情绪", "情感",
    "世界观", "力量体系", "设定",
    "角色", "人物", "人设",
    "起名", "取名", "书名", "标题",
    "热点", "扫榜", "榜单", "拆书", "拆文", "拆榜",
    "续写", "扩写", "仿写", "润色", "改写",
    "投稿", "签约", "出海", "英文",
    "AI味", "AI检测", "AI浓度", "AI痕迹", "去AI",
    "封面", "短篇", "长篇", "盐言", "知乎",
    "审稿", "点评", "评论", "复盘",
    "文风", "风格", "同人", "剧本", "脚本",
    "方言", "术语", "网感", "记忆",
    "伏笔", "钩子", "悬念", "节奏",
]


# 高频技能的手工别名（补充描述中未出现的常见说法）
SKILL_ALIASES = {
    "aidetect": ["AI浓度", "AI打分", "AI评分", "AI检测", "查AI", "AI痕迹", "像AI"],
    "story-deslop": ["去AI味", "降AI", "洗稿"],
    "shuangdian": ["不够爽", "没爽点", "太平淡"],
    "story-long-scan": ["扫榜", "看榜", "榜单"],
    "name": ["起名", "取名", "起名字"],
    "title": ["起标题", "书名"],
}


def _extract_triggers(name: str, description: str) -> tuple[List[str], List[str]]:
    """从描述中提取触发词，返回 (显式触发词, 领域关键词)"""
    triggers = [name]
    triggers += re.findall(r"「([^」]+)」", description)
    triggers += re.findall(r"/([a-zA-Z][\w\-]*)", description)
    for phrase in re.findall(r'"([^"]+)"', description):
        triggers += [p for p in re.split(r"[/、，,]", phrase) if p]
    triggers += SKILL_ALIASES.get(name, [])

    # 关键词匹配忽略空格（兼容 "AI 味" 这类写法）
    normalized_desc = description.replace(" ", "")
    keywords = [kw for kw in DOMAIN_KEYWORDS if kw in normalized_desc]

    seen, result = set(), []
    for t in triggers:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            result.append(t)
    keywords = [k for k in dict.fromkeys(keywords) if k not in seen]
    return result, keywords


def load_skill(skill_md_path: str, source: str = "local") -> Optional[Skill]:
    """从 SKILL.md 路径加载技能"""
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    meta, body = _parse_frontmatter(text)

    name = meta.get("name") or os.path.basename(os.path.dirname(skill_md_path))
    description = meta.get("description", "")
    triggers = meta.get("triggers", [])
    keywords: List[str] = []
    if isinstance(triggers, str):
        triggers = [triggers]
    if not triggers:
        triggers, keywords = _extract_triggers(name, description)
    else:
        triggers = [name] + [t for t in triggers if t != name]

    if not body.strip():
        return None

    return Skill(
        name=name,
        description=description,
        content=body,
        path=os.path.dirname(skill_md_path),
        triggers=triggers,
        keywords=keywords,
        source=source,
    )


def scan_skills(skills_dir: str, source: str = "local") -> List[Skill]:
    """扫描目录下所有技能（每个子目录一个 SKILL.md，也支持根目录直接放置）"""
    skills = []
    if not os.path.isdir(skills_dir):
        return skills

    candidates = []
    root_skill = os.path.join(skills_dir, "SKILL.md")
    if os.path.isfile(root_skill):
        candidates.append(root_skill)

    for entry in sorted(os.listdir(skills_dir)):
        subdir = os.path.join(skills_dir, entry)
        if not os.path.isdir(subdir) or entry.startswith("."):
            continue
        skill_md = os.path.join(subdir, "SKILL.md")
        if os.path.isfile(skill_md):
            candidates.append(skill_md)

    for path in candidates:
        skill = load_skill(path, source=source)
        if skill:
            skills.append(skill)

    return skills
