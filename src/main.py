import os
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.client import GeminiAssistant
from src.logger import ChatLogger

console = Console()

def main():
    # 初始化组件
    assistant = GeminiAssistant(console)
    logger = ChatLogger()

    # 欢迎面板
    console.print(Panel.fit(
        "[bold green]🔬 科研 AI 助手已就绪 (已完成 Day 9 模块化架构重构)！[/bold green]\n"
        "[dim]模块化解耦 | Rich 美化 | 自动日志 | 本地文件读取 | 503 自动重试[/dim]\n\n"
        "快捷指令：\n"
        "• [bold cyan]/read <文件路径>[/bold cyan] : 读取本地文件发送给 AI（例: /read README.md）\n"
        "• [bold cyan]exit[/bold cyan] 或 [bold cyan]quit[/bold cyan] : 退出对话",
        border_style="cyan"
    ))

    # 主对话循环
    while True:
        try:
            user_input = console.input("\n[bold cyan]👤 You:[/bold cyan] ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                console.print("\n[bold yellow]👋 助手已退出，对话日志已自动保存！[/bold yellow]")
                break

            # 处理 /read 指令
            if user_input.startswith("/read "):
                file_path = user_input[6:].strip()
                if not os.path.exists(file_path):
                    console.print(f"[bold red]❌ 错误：找不到文件 '{file_path}'[/bold red]")
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    console.print(f"[bold green]📄 成功读取: {file_path}，发送中...[/bold green]")
                    prompt_to_send = f"以下是文件 `{file_path}` 的完整内容，请帮我阅读并总结分析：\n\n```\n{file_content}\n```"
                except Exception as e:
                    console.print(f"[bold red]❌ 读取文件失败: {e}[/bold red]")
                    continue
            else:
                prompt_to_send = user_input

            # 请求 AI 并处理响应
            response = assistant.send_message_with_retry(prompt_to_send)

            console.print("\n[bold magenta]🤖 Assistant:[/bold magenta]")
            console.print(Markdown(response.text))

            # 记录日志
            logger.log_interaction(user_input, response.text)

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]👋 收到中断信号，程序退出。[/bold yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 发生错误: {e}[/bold red]")

if __name__ == "__main__":
    main()
