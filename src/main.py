import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# 确保能正确导入同级 src 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client import Client
from memory_manager import MemoryManager
from pdfreader import PDFReader

load_dotenv()
console = Console()

def main():
    console.print(Panel.fit("=== Scientific Project Assistant (Multi-Paper Edition) ===", style="bold green"))
    console.print("提示: 输入 [cyan]/role[/cyan] 切换角色，输入 [cyan]/save[/cyan] 保存对话，输入 [cyan]/history[/cyan] 查看历史")
    console.print("文献指令:")
    console.print("  [cyan]/papers[/cyan] - 查看 papers 目录及当前加载状态")
    console.print("  [cyan]/read <文件名.pdf>[/cyan] - 加载并阅读论文（可多次输入加载多篇）")
    console.print("  [cyan]/clear[/cyan] - 清空当前加载的所有论文上下文")
    console.print("  [cyan]exit[/cyan] - 退出程序\n")

    client = Client()
    memory = MemoryManager()
    pdf_reader = PDFReader()

    base_system_prompt = "你是一个专业的科研与工程助手，擅长文献阅读、多篇论文横向对比、结构仿真与学术答疑。"
    
    # 用字典存储多篇已加载的论文：{filename: text}
    loaded_papers = {}

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                console.print("[bold yellow]再见！[/bold yellow]")
                break

            # 指令：切换系统角色
            if user_input.lower() == "/role":
                new_role = console.input("[bold cyan]请输入新的系统角色设定 (System Prompt): [/bold cyan]").strip()
                if new_role:
                    base_system_prompt = new_role
                    console.print(f"[green]角色已更新成功！[/green]\n")
                continue

            # 指令：查看历史对话
            if user_input.lower() == "/history":
                messages = memory.get_messages()
                if not messages:
                    console.print("[yellow]当前没有历史对话记录。[/yellow]")
                else:
                    console.print("[bold cyan]=== 历史对话记录 ===[/bold cyan]")
                    for msg in messages:
                        role_label = "You" if msg["role"] == "user" else "Assistant"
                        console.print(f"[bold]{role_label}:[/bold] {msg['content'][:100]}...")
                continue

            # 指令：保存对话
            if user_input.lower() == "/save":
                memory.save_to_file()
                console.print("[green]对话已成功保存！[/green]")
                continue

            # 指令：清空已加载的论文
            if user_input.lower() == "/clear":
                loaded_papers.clear()
                console.print("[green]已清空所有当前加载的论文上下文。[/green]\n")
                continue

            # 指令：查看论文列表及加载状态
            if user_input.lower() == "/papers":
                all_papers = pdf_reader.list_papers()
                if not all_papers:
                    console.print("[yellow]papers 文件夹下暂无 PDF 文件。[/yellow]")
                else:
                    console.print("[bold cyan]papers 文件夹下的论文及加载状态：[/bold cyan]")
                    for idx, paper in enumerate(all_papers, 1):
                        status = "[green][已加载][/green]" if paper in loaded_papers else "[dim][未加载][/dim]"
                        console.print(f"  {idx}. {paper} {status}")
                if loaded_papers:
                    console.print(f"\n[cyan]当前共有 {len(loaded_papers)} 篇论文在上下文中。你可以直接让 AI 对它们进行对比或提问。[/cyan]")
                console.print()
                continue

            # 指令：读取指定论文 (/read filename.pdf)
            if user_input.lower().startswith("/read "):
                filename = user_input[6:].strip()
                if not filename:
                    console.print("[red]请指定文件名，例如: /read 1.pdf[/red]\n")
                    continue
                try:
                    console.print(f"[cyan]正在读取论文: {filename} ...[/cyan]")
                    paper_text = pdf_reader.read_pdf(filename)
                    
                    # 存入多论文字典
                    loaded_papers[filename] = paper_text
                    
                    # 动态拼接所有已加载论文的上下文
                    paper_context_block = "\n\n=== 当前已加载的科研文献库 ==="
                    for name, text in loaded_papers.items():
                        paper_context_block += f"\n\n--- 文献名称: {name} ---\n{text}"
                    
                    active_system_prompt = base_system_prompt + paper_context_block
                    
                    # 提示用户
                    console.print(f"[bold green]✓ 成功加载 [{filename}]！当前上下文中共有 {len(loaded_papers)} 篇文献。[/bold green]")
                    console.print(f"[cyan]提示：你可以继续使用 /read 加载更多论文，或者直接提问（如：'请对比这些论文的方法异同'）。[/cyan]\n")
                except Exception as e:
                    console.print(f"[red]读取论文失败: {e}[/red]\n")
                continue

            # 常规对话处理：构建实时的系统提示词（自动携带所有已加载的论文库）
            paper_context_block = ""
            if loaded_papers:
                paper_context_block = "\n\n=== 当前已加载的科研文献库 ==="
                for name, text in loaded_papers.items():
                    paper_context_block += f"\n\n--- 文献名称: {name} ---\n{text}"

            active_system_prompt = base_system_prompt + paper_context_block
            
            messages = memory.get_messages()
            messages.append({"role": "user", "content": user_input})

            # 调用大模型生成回复
            response_text = client.generate_response(active_system_prompt, messages)

            # 记录到对话历史
            memory.add_message("user", user_input)
            memory.add_message("assistant", response_text)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]程序已中断。[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]发生错误: {e}[/red]")

if __name__ == "__main__":
    main()
