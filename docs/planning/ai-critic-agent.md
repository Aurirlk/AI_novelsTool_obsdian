# AI批评师智能体改进计划

## TL;DR
> **Summary**: 新增"AI批评师"智能体，实现对抗式审核功能，帮助作者发现逻辑漏洞、常识错误
> **Deliverables**: 3个新智能体文件、1个知识库模块、1个Prompt模板文件
> **Effort**: Medium
> **Parallel**: YES - 3 waves
> **Critical Path**: 知识库初始化 → 批评师智能体 → 工作流集成

## Context
### Original Request
用户希望AI作为智能工具，发挥知识库处理能力，解决作者的"常识性错误"（如历史知识不足），同时保持AI创作能力供初学者学习。

### Interview Summary
- 核心理念：AI是工具，不是替代品；两个核心能力：知识库处理 + 对抗式批评
- 保持"AI写"（供学习），增加"AI审"（对抗式）
- 知识库方案：本地知识库（ChromaDB预置历史/地理/科学知识）
- 批评风格：刁钻刻薄型
- 输出方式：对话直接输出

### Metis Review (gaps addressed)
- 需要明确知识库的具体内容和结构
- 需要设计对抗式审核的Prompt模板
- 需要确保新智能体与现有工作流兼容

## Work Objectives
### Core Objective
新增AI批评师智能体，实现对抗式审核功能，帮助作者发现逻辑漏洞、常识错误

### Deliverables
1. `src/agents/outline_critic.py` - 大纲批评师智能体
2. `src/agents/chapter_critic.py` - 章节批评师智能体
3. `src/agents/knowledge_checker.py` - 知识库检查器
4. `src/knowledge/` - 知识库模块（历史、地理、科学常识）
5. `src/prompts/critic_prompts.py` - 对抗式审核Prompt模板

### Definition of Done (verifiable conditions with commands)
- [ ] 新智能体可以独立运行：`python -c "from src.agents.outline_critic import OutlineCritic; print('OK')"`
- [ ] 知识库可以正常加载：`python -c "from src.knowledge.loader import load_knowledge; print('OK')"`
- [ ] 批评结果可以直接输出：调用智能体后返回批评报告

### Must Have
- 对抗式审核功能（刁钻刻薄风格）
- 本地知识库（历史、地理、科学常识）
- 与现有工作流兼容

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- 不修改现有AI写手智能体
- 不集成外部API（如维基百科）
- 不实现复杂UI（只在对话中输出）

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after + pytest
- QA policy: Every task has agent-executed scenarios
- Evidence: .omo/evidence/task-{N}-{slug}.{ext}

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: [foundation tasks with categories]
- Task 1: 知识库模块设计与实现
- Task 2: 对抗式审核Prompt模板设计

Wave 2: [dependent tasks with categories]
- Task 3: 大纲批评师智能体实现
- Task 4: 章节批评师智能体实现
- Task 5: 知识库检查器实现

Wave 3: [integration tasks with categories]
- Task 6: 工作流集成与测试

### Dependency Matrix (full, all tasks)
```
Task 1 (知识库) ──→ Task 3 (大纲批评师)
                ──→ Task 4 (章节批评师)
                ──→ Task 5 (知识库检查器)
Task 2 (Prompt) ──→ Task 3 (大纲批评师)
                ──→ Task 4 (章节批评师)
Task 3,4,5 ──────→ Task 6 (工作流集成)
```

### Agent Dispatch Summary (wave → task count → categories)
Wave 1: 2 tasks (knowledge, prompts)
Wave 2: 3 tasks (agents)
Wave 3: 1 tasks (integration)

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [ ] 1. 知识库模块设计与实现

  **What to do**:
  1. 创建 `src/knowledge/` 目录结构
  2. 设计知识库数据结构（历史、地理、科学常识）
  3. 实现知识库加载器，使用ChromaDB存储
  4. 预置基础知识（中国历史朝代、世界地理、基础科学）

  **Must NOT do**:
  - 不集成外部API
  - 不实现复杂的知识更新机制

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 需要设计数据结构和实现加载逻辑
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [3, 4, 5] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `src/core/vector_store.py:20-80` - ChromaDB使用方式
  - Pattern: `src/memory/entity_dictionary.py` - 数据结构设计参考

  **Acceptance Criteria** (agent-executable only):
  - [ ] 知识库模块可以正常导入：`python -c "from src.knowledge.loader import load_knowledge; print('OK')"`
  - [ ] 知识库包含至少100条基础知识记录

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 知识库加载测试
    Tool: Bash
    Steps: 运行 `python -c "from src.knowledge.loader import load_knowledge; kb = load_knowledge(); print(f'Loaded {len(kb)} records')"`
    Expected: 输出 "Loaded 100+ records"
    Evidence: .omo/evidence/task-1-knowledge-load.txt

  Scenario: 知识库查询测试
    Tool: Bash
    Steps: 运行 `python -c "from src.knowledge.loader import load_knowledge; kb = load_knowledge(); print(kb.query('唐朝'))"`
    Expected: 返回唐朝相关信息
    Evidence: .omo/evidence/task-1-knowledge-query.txt
  ```

  **Commit**: YES | Message: `feat(knowledge): 新增知识库模块` | Files: [src/knowledge/*]

---

- [ ] 2. 对抗式审核Prompt模板设计

  **What to do**:
  1. 创建 `src/prompts/` 目录
  2. 设计大纲批评Prompt模板（刁钻刻薄风格）
  3. 设计章节批评Prompt模板
  4. 设计知识库检查Prompt模板

  **Must NOT do**:
  - 不设计温和型Prompt
  - 不实现Prompt动态生成

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: 需要设计Prompt文案
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [3, 4] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `src/agents/outline_agent.py:85-101` - 现有Prompt设计参考
  - Pattern: `src/agents/reviewer_agent.py:180-189` - 审核Prompt参考

  **Acceptance Criteria** (agent-executable only):
  - [ ] Prompt模板可以正常导入：`python -c "from src.prompts.critic_prompts import OUTLINE_CRITIC_PROMPT; print('OK')"`
  - [ ] Prompt包含"刁钻刻薄"关键词

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: Prompt模板导入测试
    Tool: Bash
    Steps: 运行 `python -c "from src.prompts.critic_prompts import OUTLINE_CRITIC_PROMPT, CHAPTER_CRITIC_PROMPT, KNOWLEDGE_CHECK_PROMPT; print('All prompts loaded')"`
    Expected: 输出 "All prompts loaded"
    Evidence: .omo/evidence/task-2-prompt-import.txt

  Scenario: Prompt内容验证
    Tool: Bash
    Steps: 运行 `python -c "from src.prompts.critic_prompts import OUTLINE_CRITIC_PROMPT; assert '刁钻' in OUTLINE_CRITIC_PROMPT or '刻薄' in OUTLINE_CRITIC_PROMPT; print('OK')"`
    Expected: 输出 "OK"
    Evidence: .omo/evidence/task-2-prompt-content.txt
  ```

  **Commit**: YES | Message: `feat(prompts): 新增对抗式审核Prompt模板` | Files: [src/prompts/*]

---

- [ ] 3. 大纲批评师智能体实现

  **What to do**:
  1. 创建 `src/agents/outline_critic.py`
  2. 继承 `BaseAgent` 基类
  3. 实现 `execute()` 方法，接收人类大纲
  4. 调用知识库检查常识错误
  5. 输出刁钻刻薄的批评报告

  **Must NOT do**:
  - 不修改现有大纲师智能体
  - 不实现大纲生成功能

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 需要实现智能体逻辑
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [6] | Blocked By: [1, 2]

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `src/agents/base.py` - BaseAgent基类
  - Pattern: `src/agents/outline_agent.py` - 大纲师智能体参考
  - Pattern: `src/prompts/critic_prompts.py` - Prompt模板（待创建）

  **Acceptance Criteria** (agent-executable only):
  - [ ] 智能体可以正常导入：`python -c "from src.agents.outline_critic import OutlineCritic; print('OK')"`
  - [ ] 智能体可以执行批评：传入大纲后返回批评报告

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 大纲批评测试
    Tool: Bash
    Steps: 运行测试脚本，传入测试大纲
    Expected: 返回包含"问题"、"建议"的批评报告
    Evidence: .omo/evidence/task-3-outline-critic.txt

  Scenario: 知识库检查测试
    Tool: Bash
    Steps: 运行测试脚本，传入包含历史错误的大纲
    Expected: 检测出历史错误并指出
    Evidence: .omo/evidence/task-3-knowledge-check.txt
  ```

  **Commit**: YES | Message: `feat(agents): 新增大纲批评师智能体` | Files: [src/agents/outline_critic.py]

---

- [ ] 4. 章节批评师智能体实现

  **What to do**:
  1. 创建 `src/agents/chapter_critic.py`
  2. 继承 `BaseAgent` 基类
  3. 实现 `execute()` 方法，接收人类章节
  4. 检查逻辑漏洞、情节硬伤、常识错误
  5. 输出刁钻刻薄的批评报告

  **Must NOT do**:
  - 不修改现有评论家智能体
  - 不实现章节生成功能

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 需要实现智能体逻辑
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [6] | Blocked By: [1, 2]

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `src/agents/base.py` - BaseAgent基类
  - Pattern: `src/agents/critic_agent.py` - 现有评论家参考
  - Pattern: `src/prompts/critic_prompts.py` - Prompt模板（待创建）

  **Acceptance Criteria** (agent-executable only):
  - [ ] 智能体可以正常导入：`python -c "from src.agents.chapter_critic import ChapterCritic; print('OK')"`
  - [ ] 智能体可以执行批评：传入章节后返回批评报告

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 章节批评测试
    Tool: Bash
    Steps: 运行测试脚本，传入测试章节
    Expected: 返回包含"逻辑漏洞"、"情节硬伤"的批评报告
    Evidence: .omo/evidence/task-4-chapter-critic.txt

  Scenario: 常识错误检查测试
    Tool: Bash
    Steps: 运行测试脚本，传入包含常识错误的章节
    Expected: 检测出常识错误并指出
    Evidence: .omo/evidence/task-4-knowledge-error.txt
  ```

  **Commit**: YES | Message: `feat(agents): 新增章节批评师智能体` | Files: [src/agents/chapter_critic.py]

---

- [ ] 5. 知识库检查器实现

  **What to do**:
  1. 创建 `src/agents/knowledge_checker.py`
  2. 继承 `BaseAgent` 基类
  3. 实现 `execute()` 方法，接收文本内容
  4. 调用知识库检查常识错误
  5. 返回检查结果

  **Must NOT do**:
  - 不实现外部API调用
  - 不实现知识库更新功能

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 需要实现智能体逻辑
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [6] | Blocked By: [1]

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `src/agents/base.py` - BaseAgent基类
  - Pattern: `src/knowledge/loader.py` - 知识库加载器（待创建）

  **Acceptance Criteria** (agent-executable only):
  - [ ] 智能体可以正常导入：`python -c "from src.agents.knowledge_checker import KnowledgeChecker; print('OK')"`
  - [ ] 智能体可以检查常识错误：传入文本后返回检查结果

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 常识检查测试
    Tool: Bash
    Steps: 运行测试脚本，传入包含历史错误的文本
    Expected: 检测出历史错误并指出
    Evidence: .omo/evidence/task-5-knowledge-check.txt

  Scenario: 正确文本检查测试
    Tool: Bash
    Steps: 运行测试脚本，传入正确的文本
    Expected: 返回"未发现常识错误"
    Evidence: .omo/evidence/task-5-correct-text.txt
  ```

  **Commit**: YES | Message: `feat(agents): 新增知识库检查器` | Files: [src/agents/knowledge_checker.py]

---

- [ ] 6. 工作流集成与测试

  **What to do**:
  1. 在 `workflow_engine.py` 中注册新智能体
  2. 创建批评工作流（用户上传大纲/章节 → AI批评师审核 → 输出批评报告）
  3. 测试完整流程
  4. 更新 `__init__.py` 导出新智能体

  **Must NOT do**:
  - 不修改现有小说生成工作流
  - 不实现复杂UI

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 需要集成多个模块
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: [] | Blocked By: [3, 4, 5]

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `src/core/workflow_engine.py:89-91` - register_agent方法
  - Pattern: `src/core/workflow_engine.py:105-136` - create_novel_workflow参考

  **Acceptance Criteria** (agent-executable only):
  - [ ] 新智能体已注册：`python -c "from src.core.workflow_engine import get_workflow_engine; engine = get_workflow_engine(); print('outline_critic' in engine.agents)"`
  - [ ] 批评工作流可以执行：调用批评工作流后返回批评报告

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 工作流注册测试
    Tool: Bash
    Steps: 运行 `python -c "from src.core.workflow_engine import get_workflow_engine; engine = get_workflow_engine(); print('outline_critic' in engine.agents)"`
    Expected: 输出 "True"
    Evidence: .omo/evidence/task-6-workflow-register.txt

  Scenario: 批评工作流测试
    Tool: Bash
    Steps: 运行测试脚本，调用批评工作流
    Expected: 返回批评报告
    Evidence: .omo/evidence/task-6-workflow-test.txt
  ```

  **Commit**: YES | Message: `feat(workflow): 集成AI批评师工作流` | Files: [src/core/workflow_engine.py, src/agents/__init__.py]

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check — deep

## Commit Strategy
- 每个任务完成后独立提交
- 提交信息格式：`feat(scope): description`
- 最终合并到主分支

## Success Criteria
1. 新增3个批评师智能体可以正常工作
2. 知识库包含至少100条基础知识
3. 对抗式审核功能可以检测逻辑漏洞、常识错误
4. 批评结果在对话中直接输出
5. 与现有工作流兼容，不影响AI写手功能
