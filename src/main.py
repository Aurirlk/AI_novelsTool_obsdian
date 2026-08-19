"""
AI网文写作智能体 - 主入口
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """主函数"""
    print("=" * 60)
    print("AI网文写作智能体 v0.1.0")
    print("=" * 60)
    
    # 检查环境配置
    from config.settings import LLM_CONFIG, DEFAULT_LLM_PROVIDER
    
    api_key = LLM_CONFIG.get(DEFAULT_LLM_PROVIDER, {}).get("api_key")
    
    if not api_key or api_key.startswith("your_"):
        print("\n[警告] 未配置API密钥!")
        print("\n请按以下步骤配置:")
        print("1. 复制 .env.example 为 .env")
        print("2. 填入API密钥（推荐使用智谱GLM，永久免费）")
        print("3. 获取地址: https://open.bigmodel.cn/")
        print("\n当前为演示模式，将展示工作流结构...\n")
        
        demo_mode()
    else:
        print(f"\n使用 {DEFAULT_LLM_PROVIDER} 模型")
        interactive_mode()


def demo_mode():
    """演示模式（不调用LLM）"""
    from src.models.schemas import NovelState, StoryBible, Character, CharacterRole, Hook, HookStatus
    
    print("=" * 60)
    print("演示模式 - 展示核心功能结构")
    print("=" * 60)
    
    # 创建示例状态
    state = NovelState()
    
    # 创建故事圣经
    state.story_bible = StoryBible(
        title="废柴逆袭：科学修仙传",
        genre="玄幻",
        theme="用科学方法修仙",
        worldview="一个传统的修仙世界，但主角用科学思维颠覆一切",
        power_system="炼气、筑基、金丹、元婴、化神、渡劫、大乘",
    )
    
    # 创建角色
    protagonist = Character(
        id="char_001",
        name="林云",
        role=CharacterRole.PROTAGONIST,
        personality="聪明、理性、善于分析",
        background="现代物理学博士，穿越到修仙世界",
        current_location="青云镇",
    )
    
    mentor = Character(
        id="char_002",
        name="玄清子",
        role=CharacterRole.SUPPORTING,
        personality="神秘、睿智、不拘小节",
        background="隐世高手，看中林云的天赋",
        current_location="青云山",
    )
    
    state.characters = {
        protagonist.id: protagonist,
        mentor.id: mentor,
    }
    
    # 创建钩子
    hook1 = Hook(
        id="hook_001",
        content="林云发现修仙世界的灵气与现代物理学有某种联系",
        status=HookStatus.PLANTED,
        planted_chapter=1,
        expected_resolve=10,
        related_characters=["char_001"],
    )
    
    state.hooks = {hook1.id: hook1}
    
    # 显示状态
    print("\n【故事设定】")
    print(f"标题: {state.story_bible.title}")
    print(f"题材: {state.story_bible.genre}")
    print(f"主题: {state.story_bible.theme}")
    
    print("\n【角色列表】")
    for char in state.characters.values():
        print(f"- {char.name}({char.role.value}): {char.personality}")
    
    print("\n【活跃钩子】")
    for hook in state.get_active_hooks():
        print(f"- {hook.content}")
    
    print("\n" + "=" * 60)
    print("工作流结构:")
    print("1. 大纲师 -> 生成故事大纲和章节细纲")
    print("2. 码字工 -> 根据细纲撰写章节内容")
    print("3. 督察   -> 审核内容一致性和质量")
    print("4. 运营   -> 错别字修正、生成标题和预告")
    print("=" * 60)
    
    # 展示记忆管理
    from src.utils.memory import MemoryManager
    
    memory = MemoryManager()
    memory.add_character(protagonist)
    memory.add_character(mentor)
    memory.add_hook(hook1)
    
    print("\n【记忆管理演示】")
    print(memory.get_memory_context(current_chapter=1))


def interactive_mode():
    """交互模式（需要API密钥）"""
    from src.workflows.novel_workflow import NovelWorkflow
    
    print("\n请输入您的小说创意（一句话描述）:")
    idea = input("> ").strip()
    
    if not idea:
        idea = "废柴少年偶得修仙系统，用科学方法在修仙世界逆袭"
        print(f"使用默认创意: {idea}")
    
    print("\n请输入要生成的章节数（默认5章）:")
    num_input = input("> ").strip()
    num_chapters = int(num_input) if num_input.isdigit() else 5
    
    print(f"\n开始生成{num_chapters}章小说...")
    print("创意: {idea}")
    
    # 运行工作流
    workflow = NovelWorkflow()
    state = workflow.run(idea, num_chapters)
    
    # 保存结果
    workflow.save_novel()
    
    print("\n生成完成!")


if __name__ == "__main__":
    main()