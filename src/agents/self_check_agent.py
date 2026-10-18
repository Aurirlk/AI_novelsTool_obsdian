"""
自检子 Agent（goink InjectMessage 模式）

触发条件：AI 通过 write_chapter 写入正文 >500 字。
行为：
- 以"只读白名单"工具集（list_books / read_book / read_chapter /
  list_characters / read_character / list_hooks / list_events）做一轮质检；
- 质检报告作为 ToolResult 文本返回主 Agent 上下文（等价 goink 注入
  InjectMessage 供主 Agent 决策）；
- 任何失败（无 API key / 网络错误 / 超时）只产生占位文本，绝不阻塞正文流程。
"""

from typing import List

# 自检子 Agent 只读白名单（禁止任何写入工具）
_READ_ONLY_NAMES = {
    "list_books", "read_book", "read_chapter",
    "list_characters", "read_character",
    "list_hooks", "list_events",
}

_SYSTEM_PROMPT = """你是网文质检审稿员（自检子 Agent，只读模式）。

你的任务：对刚写入的章节正文做快速质检，输出一份简洁、可执行的质检报告。

硬性规则：
1. 你只能调用白名单内的**只读**工具核实现有数据（书籍章节/角色设定/悬念钩子/时间线事件）。
2. 禁止写入、禁止修改任何数据。
3. 报告控制在 200 字以内，使用如下模板：
   【质检报告】
   - 与既定设定的冲突：<有则列出具体冲突点；无则写"无">
   - 悬念/钩子处理：<新埋/回收/遗忘线索的观察>
   - 节奏与内容密度：<一段话>
   - 建议：<1-3 条可执行建议>
4. 如果无法核实（如书/角色数据不存在），如实说明"暂无法核实"即可，不要编造。"""


def run_self_check(book_name: str, chapter_title: str, content: str,
                   max_rounds: int = 3) -> str:
    """
    执行一次正文自检。

    Returns:
        质检报告文本（失败时返回占位说明，绝不抛出）
    """
    try:
        from src.utils.llm import LLMClient
        client = LLMClient()
    except Exception as e:
        return f"（自动质检跳过：LLM 不可用 - {e}）"

    try:
        from src.tools.project_tools import get_project_tools, get_project_tool_handler
        tools = get_project_tools(["project"])
        tools = [t for t in tools if t["function"]["name"] in _READ_ONLY_NAMES]
        _inner = get_project_tool_handler(["project"])

        # handler 层二次拦截：即使模型误调白名单之外的写工具，也绝不执行
        def read_only_handler(name: str, arguments_json: str) -> str:
            if name not in _READ_ONLY_NAMES:
                return f"禁止调用 {name}：质检子 Agent 为只读模式，只能调用白名单只读工具。"
            return _inner(name, arguments_json)

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content":
                f"书籍《{book_name}》章节「{chapter_title}」刚刚被写入 "
                f"{len(content)} 字正文，请执行质检。\n\n章节全文如下：\n{content[:12000]}"},
        ]
        report = client.chat_with_tools(messages, tools, read_only_handler, max_rounds=max_rounds)
        return (report or "（质检无输出）").strip()
    except Exception as e:
        return f"（自动质检失败：{e}）"
