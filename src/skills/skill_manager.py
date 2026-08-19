"""
技能管理器
注册、启用状态持久化、触发词匹配、技能包（整包注入）、从GitHub导入
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from typing import List, Optional

from .skill_loader import Skill, scan_skills

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SKILLS_DIR = os.path.join(_PROJECT_ROOT, "skills")
PACKS_FILE = os.path.join(DEFAULT_SKILLS_DIR, "packs.json")


class SkillPack:
    """技能包：一组技能的集合，调用时整包注入LLM"""

    def __init__(self, pack_id: str, name: str, description: str,
                 skill_names: Optional[List[str]] = None, skill_file: Optional[str] = None):
        self.id = pack_id
        self.name = name
        self.description = description
        self.skill_names = skill_names or []
        self.skill_file = skill_file  # 独立包（单SKILL.md文件路径，相对skills目录）


class SkillManager:
    """技能管理器（单例）"""

    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = skills_dir or DEFAULT_SKILLS_DIR
        os.makedirs(self.skills_dir, exist_ok=True)
        self._skills: List[Skill] = []
        self.refresh()

    # ==================== 扫描与查询 ====================

    def refresh(self):
        """重新扫描技能目录"""
        self._skills = scan_skills(self.skills_dir)

    def list_skills(self) -> List[Skill]:
        return list(self._skills)

    def get_skill(self, name: str) -> Optional[Skill]:
        for skill in self._skills:
            if skill.name == name:
                return skill
        return None

    def list_enabled(self) -> List[Skill]:
        return [s for s in self._skills if self.is_enabled(s.name)]

    def match(self, text: str) -> Optional[Skill]:
        """根据触发词匹配一个已启用的技能（按匹配分排序，同分取更专精的）"""
        best_skill, best_score = None, 0
        for skill in self.list_enabled():
            score = skill.match_score(text)
            if score > best_score or (
                    score == best_score and best_skill is not None and score > 0
                    and len(skill.keywords) < len(best_skill.keywords)):
                best_skill, best_score = skill, score
        return best_skill

    # ==================== 技能包（整包强制注入） ====================

    def list_packs(self) -> List[SkillPack]:
        """列出所有技能包"""
        packs = []
        if os.path.isfile(PACKS_FILE):
            try:
                with open(PACKS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for pack_id, info in data.get("packs", {}).items():
                    packs.append(SkillPack(
                        pack_id=pack_id,
                        name=info.get("name", pack_id),
                        description=info.get("description", ""),
                        skill_names=info.get("skills"),
                        skill_file=info.get("skill_file"),
                    ))
            except (OSError, json.JSONDecodeError):
                pass
        return packs

    def get_pack(self, pack_id: str) -> Optional[SkillPack]:
        for pack in self.list_packs():
            if pack.id == pack_id:
                return pack
        return None

    def get_pack_content(self, pack: SkillPack, max_chars: int = 24000) -> str:
        """获取技能包的完整注入内容（整包强制读取）"""
        parts = [f"# 技能包：{pack.name}\n\n{pack.description}\n"]

        if pack.skill_file:
            # 独立包：直接读取其 SKILL.md
            path = os.path.join(self.skills_dir, pack.skill_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    parts.append(f.read())
            except OSError:
                parts.append("(技能包文件缺失)")
        else:
            # 组合包：拼接包内所有已启用技能
            for name in pack.skill_names:
                skill = self.get_skill(name)
                if skill is None or not self.is_enabled(name):
                    continue
                parts.append(f"\n\n---\n\n# 技能：{skill.name}\n\n{skill.content}")

        content = "".join(parts)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n...(技能包内容过长，已截断)"
        return content

    def match_pack(self, text: str) -> Optional[SkillPack]:
        """按触发词匹配技能包（包得分=成员技能最高分）"""
        skill = self.match(text)
        if skill is None:
            return None
        for pack in self.list_packs():
            if pack.skill_file and skill.name in pack.skill_file:
                return pack
            if skill.name in pack.skill_names:
                return pack
        return None

    # ==================== 启用状态（持久化到设置库） ====================

    def is_enabled(self, name: str) -> bool:
        try:
            from src.data.settings_manager import get_settings_manager
            return bool(get_settings_manager().get_setting("skills", f"enabled_{name}", True))
        except Exception:
            return True

    def set_enabled(self, name: str, enabled: bool):
        try:
            from src.data.settings_manager import get_settings_manager
            get_settings_manager().set_setting("skills", f"enabled_{name}", enabled)
        except Exception:
            pass

    # ==================== 技能操作 ====================

    def create_skill(self, name: str, description: str, content: str,
                     triggers: Optional[List[str]] = None) -> Skill:
        """新建技能"""
        safe_name = re.sub(r"[^\w\-一-鿿]", "_", name)
        skill_dir = os.path.join(self.skills_dir, safe_name)
        os.makedirs(skill_dir, exist_ok=True)

        triggers_line = ", ".join(triggers or [])
        md = f"---\nname: {name}\ndescription: {description}\ntriggers: {triggers_line}\n---\n\n{content}\n"
        with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(md)

        self.refresh()
        return self.get_skill(name)

    def delete_skill(self, name: str) -> bool:
        """删除技能"""
        skill = self.get_skill(name)
        if not skill:
            return False
        if os.path.isdir(skill.path) and os.path.commonpath(
                [os.path.abspath(skill.path), os.path.abspath(self.skills_dir)]) == os.path.abspath(self.skills_dir):
            shutil.rmtree(skill.path, ignore_errors=True)
            self.refresh()
            return True
        return False

    # ==================== 从 GitHub 导入 ====================

    def import_from_github(self, repo_url: str) -> List[str]:
        """
        从GitHub仓库导入技能（寻找仓库内所有 SKILL.md）
        优先 git clone，失败则下载 zip 包
        返回导入的技能名称列表
        """
        repo_url = repo_url.strip().rstrip("/").removesuffix(".git")
        match = re.match(r"https?://github\.com/([\w.\-]+)/([\w.\-]+)", repo_url)
        if not match:
            raise ValueError("仅支持 https://github.com/用户名/仓库 格式的地址")
        owner, repo = match.groups()

        with tempfile.TemporaryDirectory() as tmp:
            src_dir = self._fetch_repo(owner, repo, tmp)
            imported = []
            for root, _dirs, files in os.walk(src_dir):
                if "SKILL.md" not in files:
                    continue
                skill_name = os.path.basename(root)
                dest = os.path.join(self.skills_dir, skill_name)
                if os.path.abspath(root) == os.path.abspath(src_dir):
                    dest = os.path.join(self.skills_dir, repo)
                if os.path.isdir(dest):
                    shutil.rmtree(dest)
                shutil.copytree(root, dest)
                imported.append(os.path.basename(dest))

            self.refresh()
            return imported

    def _fetch_repo(self, owner: str, repo: str, tmp: str) -> str:
        """获取仓库内容到临时目录，返回目录路径"""
        dest = os.path.join(tmp, "repo")

        # 方式一：git clone（浅克隆）
        git = shutil.which("git")
        if git:
            try:
                subprocess.run(
                    [git, "clone", "--depth", "1", f"https://github.com/{owner}/{repo}.git", dest],
                    check=True, capture_output=True, timeout=120,
                )
                return dest
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # 方式二：下载 zip（无需git）
        import requests
        for branch in ("main", "master"):
            url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            resp = requests.get(url, timeout=60)
            if resp.status_code != 200:
                continue
            zip_path = os.path.join(tmp, "repo.zip")
            with open(zip_path, "wb") as f:
                f.write(resp.content)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp)
            extracted = os.path.join(tmp, f"{repo}-{branch}")
            if os.path.isdir(extracted):
                return extracted

        raise RuntimeError("仓库下载失败，请检查地址是否正确、网络是否可用")


_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """获取技能管理器单例"""
    global _manager
    if _manager is None:
        _manager = SkillManager()
    return _manager
