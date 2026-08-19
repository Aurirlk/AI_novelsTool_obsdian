# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 AI 辅助中文小说创作工作站，集成多个 Claude Code Skills，支持从大纲规划到成稿输出的完整创作流程。

## 核心技能 (Skills)

项目集成了以下 Claude Code Skills，通过 `/skill-name` 调用：

- **chinese-novelist** - 分章节创作中文小说（3000-5000字/章）
- **humanizer-zh** - 去除 AI 生成痕迹，24 种模式检测
- **novelist-analyst** - 叙事结构分析和角色弧光评估
- **docx** - Word 文档生成和编辑
- **planning-with-files** - 文件化任务规划（task_plan.md, findings.md, progress.md）
- **frontend-design** - 前端界面设计（用于阅读器等）

## Python 环境

**必须使用 `uv` 运行所有 Python 脚本：**

```bash
# 添加依赖
uv add <package-name>

# 执行脚本
uv run <script.py>
```

Python 版本要求：>= 3.12

## 关键脚本

### 字数检查
```bash
# 检查单章
uv run .claude/skills/chinese-novelist/scripts/check_chapter_wordcount.py novels/<小说名>/第01章.md

# 检查全部章节
uv run .claude/skills/chinese-novelist/scripts/check_chapter_wordcount.py --all novels/<小说名>
```

### 阅读器生成
每个小说目录下有 `build_reader.py`，用于生成单文件 HTML 阅读器：
```bash
cd novels/<小说名>
uv run build_reader.py
```

## 项目结构

```
novelist-test/
├── novels/                    # 小说作品目录
│   └── <小说名>/
│       ├── 00-大纲.md         # 故事概述、章节规划
│       ├── 01-人物档案.md     # 主角、反派、配角档案
│       ├── 02-风格参考手册.md # 仿写风格分析（可选）
│       ├── 03-审查报告.md     # 质量审查结果（可选）
│       ├── 第01章.md          # 章节正文
│       ├── build_reader.py    # 阅读器生成脚本
│       └── reader.html        # 生成的阅读器
├── references/                # 仿写参考作品
│   └── *.txt                  # 参考小说原文
├── qimao/                     # 七猫平台相关资料
├── .claude/skills/            # Claude Code Skills
└── pyproject.toml             # Python 依赖配置
```

## 创作工作流

### 标准创作流程（3 阶段）
1. **阶段 1：规划** - 使用 `chinese-novelist` 生成大纲和人物档案
2. **阶段 2：创作** - 使用 `chinese-novelist` 逐章创作，每章 3000-5000 字
3. **阶段 3：润色** - 使用 `humanizer-zh` 去除 AI 痕迹

### 仿写工作流（6 阶段）
1. **Phase 1：拆书分析** - 分析参考作品风格 → `02-风格参考手册.md`
2. **Phase 2：骨架搭建** - 使用 `chinese-novelist` 生成大纲和人物档案
3. **Phase 3：逐章创作** - 使用 `chinese-novelist` 串行执行，短剧爽文节奏（2500-3500字/章）
4. **Phase 4：润色去AI** - 使用 `humanizer-zh` 检测，可并行处理
5. **Phase 5：质量审查** - 8 维度评分 + 连贯性检查
6. **Phase 6：输出成稿** - 合并章节 + 生成 Word 文档

## 质量标准

- **字数要求**：每章 ≥ 2500 字（标准创作 3000-5000 字）
- **去 AI 评分**：humanizer-zh ≥ 35/50
- **质量评分**：≥ 60/80

## 参考资料位置

- **创作指南**：`.claude/skills/chinese-novelist/references/`
  - `chapter-guide.md` - 章节结构设计
  - `hook-techniques.md` - 悬念设置技巧
  - `content-expansion.md` - 内容扩充方法
  - `quality-checklist.md` - 质量检查清单

- **风格规范**：项目根目录
  - `02-风格参考手册.md` - 当前项目风格分析

## 常见任务

### 创建新小说
```
使用 chinese-novelist 帮我写一部小说
```

### 检查章节字数
```bash
uv run .claude/skills/chinese-novelist/scripts/check_chapter_wordcount.py --all novels/<小说名>
```

### 润色章节
```
使用 humanizer-zh 润色 novels/<小说名>/第01章.md
```

### 生成阅读器
```bash
cd novels/<小说名>
uv run build_reader.py
```

### 导出 Word 文档
```
使用 docx 将 novels/<小说名> 的所有章节合并为 Word 文档
```

## 注意事项

1. **串行创作**：Phase 3 逐章创作必须串行执行，确保剧情连贯
2. **字数检查**：每章完成后立即检查字数，不足时扩充
3. **风格一致**：仿写时严格遵循 `02-风格参考手册.md` 的风格规范
4. **悬念设置**：每章结尾必须设置钩子，参考 `hook-techniques.md`
5. **去 AI 痕迹**：完成初稿后必须使用 humanizer-zh 润色

## Git 工作流

- 主分支：`main`
- 提交前检查：确保章节文件完整，字数达标
- 不提交：`node_modules/`, `.venv/`, `__pycache__/`
