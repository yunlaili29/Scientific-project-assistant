import os
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.client import GeminiAssistant
from src.logger import ChatLogger
from src.file_parser import FileParser

console = Console()

def print_welcome_panel():
    """打印顶部欢迎面板"""
    console.print(Panel.fit(
        "[bold green]🔬 科研 AI 助手已就绪 (Day 11 项目级代码库解析版)！[/bold green]\n"
        "[dim]模块化架构 | Rich 美化 | 自动日志 | 503 重试 | 多文件/代码库扫描[/dim]\n\n"
        "快捷指令：\n"
        "• [bold cyan]/read <文件1> [文件2...][/bold cyan] : 读取单个或多个本地文件进行联合分析\n"
        "• [bold cyan]/scan <目录路径>[/bold cyan]          : 扫描整个代码目录树并对源码进行整体 Review\n"
        "• [bold cyan]/clear[/bold cyan]                       : 清空屏幕并重置界面\n"
        "• [bold cyan]/history[/bold cyan]                     : 查看当前会话的历史摘要列表\n"
        "• [bold cyan]/help[/bold cyan]                        : 查看所有快捷指令说明\n"
        "• [bold cyan]exit[/bold cyan] 或 [bold cyan]quit[/bold cyan]             : 退出对话",
        border_style="cyan"
    ))

def print_help():
    """打印美化的帮助表格"""
    table = Table(title="💡 快捷指令说明清单", border_style="dim")
    table.add_column("指令", style="cyan", no_wrap=True)
    table.add_column("功能说明", style="white")
    table.add_column("使用示例", style="dim")

    table.add_row("/read <files>", "读取单文件或多文件，进行跨文件联合分析", "/read src/client.py src/main.py")
    table.add_row("/scan <dir>", "扫描整个项目/源码目录，提取架构并进行全局 Code Review", "/scan src/")
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

            # 5. 项目目录扫描指令 /scan
            if user_input.startswith("/scan "):
                dir_path = user_input[6:].strip()
                console.print(f"[bold green]🔍 正在扫描目录 '{dir_path}' 及其代码文件...[/bold green]")
                
                prompt_to_send, scanned_files = FileParser.scan_directory(dir_path)
                if isinstance(scanned_files, str):  # 返回错误信息
                    console.print(f"[bold red]❌ {scanned_files}[/bold red]")
                    continue
                
                console.print(f"[bold green]✅ 成功扫描 {len(scanned_files)} 个代码文件，发送至 AI 分析...[/bold green]")
                history_records.append({
                    "type": "目录扫描",
                    "summary": f"/scan {dir_path} ({len(scanned_files)} 个文件)"
                })

            # 6. 单文件/多文件读取指令 /read
            elif user_input.startswith("/read "):
                file_paths = user_input[6:].strip().split()
                if not file_paths:
                    console.print("[bold red]❌ 错误：请提供至少一个文件路径！[/bold red]")
                    continue

                combined_content, success_files, failed_files = FileParser.read_files(file_paths)

                for path, err in failed_files:
                    console.print(f"[yellow]⚠️ 忽略 '{path}': {err}[/yellow]")

                if not success_files:
                    console.print("[bold red]❌ 没有成功读取到任何有效文件！[/bold red]")
                    continue

                console.print(f"[bold green]📄 成功读取 {len(success_files)} 个文件，正在联合发送给 AI 分析...[/bold green]")
                prompt_to_send = f"请联合分析以下 {len(success_files)} 个文件的内容：\n\n" + "\n\n".join(combined_content)
                
                history_records.append({
                    "type": "文件联合分析",
                    "summary": f"/read {' '.join(success_files)}"
                })

            else:
                prompt_to_send = user_input
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
