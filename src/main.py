import os
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.client import GeminiAssistant
from src.logger import ChatLogger

console = Console()

def print_welcome_panel():
    """打印顶部欢迎面板"""
    console.print(Panel.fit(
        "[bold green]🔬 科研 AI 助手已就绪 (Day 10 CLI 指令集版)！[/bold green]\n"
        "[dim]模块化架构 | Rich 美化 | 自动日志 | 本地文件读取 | 503 重试[/dim]\n\n"
        "快捷指令：\n"
        "• [bold cyan]/read <文件路径>[/bold cyan] : 读取本地文件发送给 AI（例: /read README.md）\n"
        "• [bold cyan]/clear[/bold cyan]          : 清空屏幕并重置界面\n"
        "• [bold cyan]/history[/bold cyan]        : 查看当前会话的对话历史列表与计数\n"
        "• [bold cyan]/help[/bold cyan]           : 查看所有快捷指令说明\n"
        "• [bold cyan]exit[/bold cyan] 或 [bold cyan]quit[/bold cyan] : 退出对话",
        border_style="cyan"
    ))

def print_help():
    """打印美化的帮助表格"""
    table = Table(title="💡 快捷指令说明清单", border_style="dim")
    table.add_column("指令", style="cyan", no_wrap=True)
    table.add_column("功能说明", style="white")
    table.add_column("使用示例", style="dim")

    table.add_row("/read <path>", "读取本地文本/代码文件并提交给 AI 分析", "/read README.md")
    table.add_row("/clear", "清除终端内容，恢复干净整洁界面", "/clear")
    table.add_row("/history", "统计当前会话轮次，并打印历史提问摘要", "/history")
    table.add_row("/help", "显示此指令帮助菜单", "/help")
    table.add_row("exit / quit", "安全退出助手，自动保存 Markdown 日志", "exit")

    console.print(table)

def main():
    # 初始化组件
    assistant = GeminiAssistant(console)
    logger = ChatLogger()

    # 内存中维护会话历史摘要列表
    history_records = []

    # 首次进入打印欢迎面板
    print_welcome_panel()

    # 主对话循环
    while True:
        try:
            user_input = console.input("\n[bold cyan]👤 You:[/bold cyan] ").strip()
            if not user_input:
                continue

            # 1. 退出指令
            if user_input.lower() in ["exit", "quit"]:
                console.print("\n[bold yellow]👋 助手已退出，对话日志已自动保存，祝科研顺利！[/bold yellow]")
                break

            # 2. 清屏指令 /clear
            if user_input.lower() == "/clear":
                console.clear()
                print_welcome_panel()
                console.print("[dim green]✨ 屏幕已清空[/dim green]")
                continue

            # 3. 帮助指令 /help
            if user_input.lower() == "/help":
                print_help()
                continue

            # 4. 历史记录指令 /history
            if user_input.lower() == "/history":
                if not history_records:
                    console.print("[yellow]ℹ️ 当前会话暂无历史对话记录。[/yellow]")
                else:
                    table = Table(title=f"📜 会话历史摘要 (共 {len(history_records)} 轮)", border_style="cyan")
                    table.add_column("序号", style="dim", width=6)
                    table.add_column("类型", style="bold yellow", width=10)
                    table.add_column("输入内容 / 摘要", style="white")

                    for idx, record in enumerate(history_records, 1):
                        table.add_row(str(idx), record["type"], record["summary"])

                    console.print(table)
                continue

            # 5. 文件读取指令 /read
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
                    
                    # 存入历史记录摘要
                    history_records.append({
                        "type": "文件分析",
                        "summary": f"/read {file_path}"
                    })
                except Exception as e:
                    console.print(f"[bold red]❌ 读取文件失败: {e}[/bold red]")
                    continue
            else:
                prompt_to_send = user_input
                # 存入历史记录摘要（裁剪前 30 个字）
                summary_text = user_input[:30] + "..." if len(user_input) > 30 else user_input
                history_records.append({
                    "type": "普通问答",
                    "summary": summary_text
                })

            # 请求 AI 并处理响应
            response = assistant.send_message_with_retry(prompt_to_send)

            console.print("\n[bold magenta]🤖 Assistant:[/bold magenta]")
            console.print(Markdown(response.text))

            # 记录本地 Markdown 日志文件
            logger.log_interaction(user_input, response.text)

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]👋 收到中断信号，程序退出。[/bold yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 发生错误: {e}[/bold red]")

if __name__ == "__main__":
    main()
