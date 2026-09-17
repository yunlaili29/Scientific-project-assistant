import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. 加载环境变量
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ 错误：未找到 GEMINI_API_KEY，请检查 .env 文件配置！")
    sys.exit(1)

# 2. 初始化 Gemini 客户端
client = genai.Client(api_key=api_key)

# 3. 设定科研助手的 System Prompt（系统角色）
system_instruction = """
你是一位顶尖的科研与工程 AI 助手。你的核心使命是辅助用户进行高质量的学术研究、工程代码开发与技术文档撰写。

请遵循以下行为准则：
1. **专业与严谨**：回答需严谨客观，逻辑清晰。解释复杂概念时给出明确步骤或公式。
2. **格式优化**：
   - 编写代码时，必须使用干净、带注释的高效代码。
   - 使用 Markdown 保持排版美观，公式使用标准 LaTeX 格式。
3. **多语言学术支持**：熟练处理中文、英文及德文的学术与工程交流，术语表达需符合行业标准。
4. **简洁高效**：直击要害，拒绝冗长废话。
"""

# 4. 创建带 Memory（上下文记忆）和 System Instruction 的 Chat 会话
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3,  # 降低随机性，使科研回答更严谨
    )
)

print("=" * 50)
print("🔬 科研 AI 助手已就绪！(输入 'exit' 或 'quit' 退出对话)")
print("=" * 50)

# 5. 交互式多轮对话循环
while True:
    try:
        user_input = input("\n👤 You: ").strip()
        if not user_input:
            continue
        
        if user_input.lower() in ["exit", "quit"]:
            print("\n👋 助手已退出，祝研究顺利！")
            break

        # 发送消息并获取回复
        response = chat.send_message(user_input)
        print(f"\n🤖 Assistant:\n{response.text}")

    except KeyboardInterrupt:
        print("\n\n👋 收到中断信号，程序退出。")
        break
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
