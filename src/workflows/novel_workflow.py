"""
小说生成工作流
定义从创意到成品的完整流程
"""

from typing import Optional
from src.models.schemas import NovelState
from src.agents.outline_agent import OutlineAgent
from src.agents.writer_agent import WriterAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.polisher_agent import PolisherAgent


class NovelWorkflow:
    """小说生成工作流"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        """
        初始化工作流
        
        Args:
            llm_provider: LLM提供商
        """
        self.llm_provider = llm_provider
        
        # 初始化智能体
        self.outline_agent = OutlineAgent(llm_provider)
        self.writer_agent = WriterAgent(llm_provider)
        self.reviewer_agent = ReviewerAgent(llm_provider)
        self.polisher_agent = PolisherAgent(llm_provider)
        
        # 工作流状态
        self.state = NovelState()
        self.max_retries = 3  # 最大重试次数
    
    def run(self, idea: str, num_chapters: int = 5) -> NovelState:
        """
        运行小说生成工作流
        
        Args:
            idea: 用户的一句话创意
            num_chapters: 生成章节数
        
        Returns:
            完成的小说状态
        """
        print("=" * 60)
        print("开始小说生成工作流")
        print(f"创意: {idea}")
        print(f"章节数: {num_chapters}")
        print("=" * 60)
        
        # 阶段1：生成大纲
        print("\n[阶段1] 生成故事大纲...")
        result = self.outline_agent.execute(self.state, idea=idea)
        self.state = result["state"]
        print(f"大纲生成完成: {self.state.story_bible.title}")
        
        # 阶段2：逐章生成
        print(f"\n[阶段2] 开始生成{num_chapters}章内容...")
        for chapter_num in range(1, num_chapters + 1):
            self._generate_chapter(chapter_num)
        
        # 阶段3：完成
        print("\n" + "=" * 60)
        print("小说生成完成!")
        print(f"标题: {self.state.story_bible.title}")
        print(f"总章数: {len(self.state.chapters)}")
        print(f"总字数: {self.state.total_words}")
        print("=" * 60)
        
        return self.state
    
    def _generate_chapter(self, chapter_num: int):
        """
        生成单个章节（包含审核重试）
        
        Args:
            chapter_num: 章节号
        """
        print(f"\n--- 第{chapter_num}章 ---")
        
        # 步骤1：生成章节细纲
        print(f"[1/4] 生成细纲...")
        outline_result = self.outline_agent.generate_chapter_outline(self.state, chapter_num)
        
        # 步骤2：撰写章节
        print(f"[2/4] 撰写内容...")
        write_result = self.writer_agent.execute(self.state, chapter_num=chapter_num)
        self.state = write_result["state"]
        chapter = write_result["chapter"]
        
        # 步骤3：审核（带重试）
        print(f"[3/4] 审核内容...")
        approved = False
        for retry in range(self.max_retries):
            review_result = self.reviewer_agent.execute(self.state, chapter_num=chapter_num)
            result = review_result["result"]
            
            if result["passed"]:
                approved = True
                print(f"审核通过 (第{retry + 1}次)")
                break
            else:
                print(f"审核不通过 (第{retry + 1}次): {len(result['issues'])}个问题")
                for issue in result["issues"]:
                    print(f"  - {issue}")
                
                # 重写
                if retry < self.max_retries - 1:
                    print(f"重新撰写...")
                    write_result = self.writer_agent.execute(self.state, chapter_num=chapter_num)
                    self.state = write_result["state"]
        
        if not approved:
            print(f"警告: 第{chapter_num}章在{self.max_retries}次重试后仍未通过审核")
        
        # 步骤4：润色
        print(f"[4/4] 润色内容...")
        polish_result = self.polisher_agent.execute(self.state, chapter_num=chapter_num)
        self.state = polish_result["state"]
        
        # 输出统计
        print(f"完成: {chapter.title} ({chapter.word_count}字)")
    
    def get_novel_text(self) -> str:
        """获取完整小说文本"""
        if not self.state.story_bible:
            return ""
        
        parts = []
        parts.append(f"# {self.state.story_bible.title}\n")
        parts.append(f"题材: {self.state.story_bible.genre}\n")
        parts.append(f"主题: {self.state.story_bible.theme}\n")
        parts.append("\n---\n")
        
        for chapter in self.state.chapters:
            parts.append(f"\n## {chapter.title}\n")
            parts.append(chapter.content)
            parts.append("\n")
        
        return "\n".join(parts)
    
    def save_novel(self, filepath: str = "data/novels/novel.txt"):
        """保存小说到文件"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.get_novel_text())
        
        print(f"小说已保存到: {filepath}")


def run_workflow(idea: str, num_chapters: int = 5, llm_provider: Optional[str] = None) -> NovelState:
    """
    运行小说生成工作流（快捷函数）
    
    Args:
        idea: 用户创意
        num_chapters: 章节数
        llm_provider: LLM提供商
    
    Returns:
        小说状态
    """
    workflow = NovelWorkflow(llm_provider)
    state = workflow.run(idea, num_chapters)
    workflow.save_novel()
    return state


if __name__ == "__main__":
    # 测试工作流（不调用LLM）
    print("=" * 60)
    print("小说生成工作流 - 结构测试")
    print("=" * 60)
    
    # 创建工作流实例
    workflow = NovelWorkflow()
    
    # 测试状态初始化
    print("\n1. 初始化状态...")
    print(f"   章节数: {len(workflow.state.chapters)}")
    print(f"   角色数: {len(workflow.state.characters)}")
    print(f"   钩子数: {len(workflow.state.hooks)}")
    
    # 测试智能体初始化
    print("\n2. 初始化智能体...")
    print(f"   大纲师: {workflow.outline_agent.name}")
    print(f"   码字工: {workflow.writer_agent.name}")
    print(f"   督察: {workflow.reviewer_agent.name}")
    print(f"   运营: {workflow.polisher_agent.name}")
    
    print("\n3. 工作流结构验证完成!")
    print("\n注意: 实际运行需要配置LLM API密钥")
    print("请复制 .env.example 为 .env 并填入API密钥")