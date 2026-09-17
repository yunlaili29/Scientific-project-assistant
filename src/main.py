import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 引入 rich 库实现美化渲染
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# 初始化 rich 终端控制台
console = Console()

# 1. 加载环境变量
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    console.print("[bold red]❌ 错误：未找到 GEMINI_API_KEY，请检查 .env 文件配置！[/bold red]")
    sys.exit(1)

# 2. 初始化 Gemini 客户端
client = genai.Client(api_key=api_key)

# 3. 设定科研助手的 System Prompt
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

# 4. 创建 Chat 会话
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3,
    )
)

# 5. 准备日志存储目录与文件
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"chat_log_{timestamp}.md")

# 写入日志文件头
with open(log_filename, "w", encoding="utf-8") as f:
    f.write(f"# 科研 AI 助手对话日志\n")
    f.write(f"- **记录时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")

# 打印美化的欢迎面板
console.print(Panel.fit(
    "[bold green]🔬 科研 AI 助手已就绪！[/bold green]\n"
    "[dim]支持 Rich 美化 | 自动保存日志 | 支持本地文件读取[/dim]\n\n"
    "快捷指令：\n"
    "• [bold cyan]/read <文件路径>[/bold cyan] : 读取本地文件发送给 AI（例: /read README.md）\n"
    "• [bold cyan]exit[/bold cyan] 或 [bold cyan]quit[/bold cyan] : 退出对话",
    border_style="cyan"
))

# 6. 交互式多轮对话循环
while True:
    try:
        user_input = console.input("\n[bold cyan]👤 You:[/bold cyan] ").strip()
        if not user_input:
            continue
        
        # 退出指令
        if user_input.lower() in ["exit", "quit"]:
            console.print("\n[bold yellow]👋 助手已退出，对话日志已自动保存，祝研究顺利！[/bold yellow]")
            break

        # 处理 /read 文件读取指令
        if user_input.startswith("/read "):
            file_path = user_input[6:].strip()
            if not os.path.exists(file_path):
                console.print(f"[bold red]❌ 错误：找不到文件 '{file_path}'，请检查路径是否正确！[/bold red]")
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                console.print(f"[bold green]📄 成功读取文件: {file_path}，正在发送给 AI 分析...[/bold green]")
                # 拼接提问文本，将文件内容包装后发给 Gemini
                prompt_to_send = f"以下是文件 `{file_path}` 的完整内容，请帮我阅读并总结分析其主要内容与代码结构：\n\n```\n{file_content}\n```"
            except Exception as e:
                console.print(f"[bold red]❌ 读取文件失败: {e}[/bold red]")
                continue
        else:
            prompt_to_send = user_input

        # 发送请求给 AI
        response = chat.send_message(prompt_to_send)
        
        # 使用 rich 渲染 Markdown 回复
        console.print("\n[bold magenta]🤖 Assistant:[/bold magenta]")
        console.print(Markdown(response.text))

        # 将对话追加写入 Markdown 日志文件
        with open(log_filename, "a", encoding="utf-8") as f:
            f.write(f"### 👤 User:\n{user_input}\n\n")
            f.write(f"### 🤖 Assistant:\n{response.text}\n\n---\n\n")

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]👋 收到中断信号，程序退出。[/bold yellow]")
        break
    except Exception as e:
        console.print(f"\n[bold red]❌ 发生错误: {e}[/bold red]")
