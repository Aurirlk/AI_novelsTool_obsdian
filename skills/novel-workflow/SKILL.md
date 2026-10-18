---
name: novel-workflow
description: 中文网文全流程模板库：故事概念、简要/详细大纲、场景清单、世界观、人物档案、修订指南。可用于「大纲」「细纲」「场景」「世界观」「人物」「修订」「拆书」等工作。
triggers: 大纲, 细纲, 场景, 世界观, 人物档案, 修订, 拆书
---

# 中文网文全流程模板库（novel-workflow）

本技能内置一套从「故事概念 → 大纲 → 场景 → 正文 → 修订」的完整创作工作流模板，
文件位于本技能目录的 `templates/` 下。生成内容时请严格按对应模板的结构输出。

## 模板清单与用途

| 模板 | 用途 |
|------|------|
| `story-concept-template.md` | 故事概念：一句话卖点、目标读者、冲突内核 |
| `outline-brief-template.md` | 简要大纲：卷/章骨架、节奏点 |
| `outline-detailed-template.md` | 详细大纲：逐章事件、情绪曲线、章末钩子 |
| `scenes-template.md` | 场景清单：场景目标/冲突/转折/信息释放 |
| `scene-writing-techniques.md` | 场景写作技巧：节奏、视角、信息层 |
| `sensory-writing-guide.md` | 感官写作：五感描写、场景沉浸 |
| `world-building-template.md` | 世界观：规则/力量体系/组织/地理 |
| `character-profiles-template.md` | 人物档案：动机/弧光/关系网 |
| `reference-analysis-template.md` | 参考书/对标作品拆解 |
| `revision-guide-template.md` | 修订指南：一稿→四稿质检清单 |
| `short-story-template.md` | 短篇/单篇模板 |

## 使用规则

1. 用户提出创作需求时，先判断阶段（概念/大纲/细纲/场景/人物/修订），选用对应模板。
2. 生成内容必须覆盖模板中全部章节，不要省略占位项（可写「待补充」）。
3. 涉及具体书籍时，优先读取该书的 大纲/细纲/角色/悬念 数据后再生成，避免与已有设定冲突。
4. 修订场景：对照 `revision-guide-template.md` 的质检清单逐项检查，给出问题点与修改建议，不直接整段重写。

## 配置说明

`config.example.toml` 为对应 MCP 工作流服务器的配置示例（Dashboard 目录、语言等），可按需参考。
