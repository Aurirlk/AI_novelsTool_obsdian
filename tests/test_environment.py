"""
环境测试脚本
验证所有依赖是否正确安装
"""

import sys
print(f"Python版本: {sys.version}")
print("-" * 50)

# 测试核心依赖
dependencies = [
    ("langchain", "LangChain框架"),
    ("langgraph", "LangGraph工作流"),
    ("chromadb", "ChromaDB向量数据库"),
    ("openai", "OpenAI SDK"),
    ("zhipuai", "智谱AI SDK"),
    ("dotenv", "环境变量管理"),
    ("requests", "HTTP请求"),
    ("bs4", "BeautifulSoup"),
]

results = []
for module, name in dependencies:
    try:
        __import__(module)
        print(f"[OK] {name}: 已安装")
        results.append((name, True, None))
    except ImportError as e:
        print(f"[FAIL] {name}: 未安装 - {e}")
        results.append((name, False, str(e)))

print("-" * 50)

# 统计结果
success = sum(1 for _, installed, _ in results if installed)
total = len(results)

if success == total:
    print(f"[OK] 所有依赖已安装 ({success}/{total})")
    print("\n环境配置正确！可以开始开发。")
else:
    print(f"[FAIL] 部分依赖缺失 ({success}/{total})")
    print("\n请安装缺失的依赖:")
    for name, installed, error in results:
        if not installed:
            print(f"  - {name}: {error}")

print("\n" + "=" * 50)
print("下一步:")
print("1. 复制 .env.example 为 .env")
print("2. 填入你的API密钥")
print("3. 运行 python src/main.py 开始测试")