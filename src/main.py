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
    console.print(Panel.fit("=== Scientific Project Assistant (Production RAG Edition) ===", style="bold green"))
    console.print("提示: 输入 [cyan]/role[/cyan] 切换角色，输入 [cyan]/save[/cyan] 保存对话，输入 [cyan]/history[/cyan] 查看历史")
    console.print("文献与导出指令:")
    console.print("  [cyan]/papers[/cyan] - 查看 papers 文件夹及当前加载状态")
    console.print("  [cyan]/read <文件名.pdf>[/cyan] - 加载并解析论文（支持多篇同时加载）")
    console.print("  [cyan]/clear[/cyan] - 清空当前加载的所有论文上下文")
    console.print("  [cyan]/export [文件名.md][/cyan] - 将当前对话与分析结果导出为 Markdown 报告")
    console.print("  [cyan]exit[/cyan] - 退出程序\n")

    client = Client()
    memory = MemoryManager()
    pdf_reader = PDFReader()

    base_system_prompt = "你是一个专业的科研与工程助手，擅长文献阅读、多篇论文横向对比、结构仿真与学术答疑。"
    
    # 存储已加载的论文结构化数据：{filename: {"full_text": str, "chunks": list}}
    loaded_papers = {}

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                memory.save_chat_history()
                console.print("[bold yellow]已自动保存对话记录。再见！[/bold yellow]")
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
                console.print()
                continue

            # 指令：保存对话
            if user_input.lower() == "/save":
                memory.save_to_file()
                console.print("[green]对话已成功保存到本地！[/green]\n")
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
                    console.print(f"\n[cyan]当前共有 {len(loaded_papers)} 篇论文在上下文中。系统已启用智能片段检索，按需向模型提供关联内容。[/cyan]")
                console.print()
                continue

            # 指令：导出分析报告到 reports/ 文件夹
            if user_input.lower().startswith("/export"):
                parts = user_input.split(maxsplit=1)
                export_filename = parts[1].strip() if len(parts) > 1 else "research_analysis_report.md"
                if not export_filename.endswith(".md"):
                    export_filename += ".md"
                
                reports_dir = "reports"
                os.makedirs(reports_dir, exist_ok=True)
                export_path = os.path.join(reports_dir, export_filename)
                
                try:
                    messages = memory.get_messages()
                    with open(export_path, "w", encoding="utf-8") as f:
                        f.write("# Scientific Project Assistant - 分析报告\n\n")
                        f.write("## 📚 已加载关联文献\n")
                        if loaded_papers:
                            for name in loaded_papers.keys():
                                f.write(f"- `{name}`\n")
                        else:
                            f.write("- 无特定加载文献\n")
                        f.write("\n---\n\n## 💬 对话记录与分析结论\n\n")
                        for msg in messages:
                            role = "### 🧑‍💻 You" if msg["role"] == "user" else "### 🤖 Assistant"
                            f.write(f"{role}\n\n{msg['content']}\n\n---\n\n")
                    
                    console.print(f"[bold green]✓ 报告已成功导出至: {export_path}[/bold green]\n")
                except Exception as e:
                    console.print(f"[red]导出报告失败: {e}[/red]\n")
                continue

            # 指令：读取指定论文 (/read filename.pdf)
            if user_input.lower().startswith("/read "):
                filename = user_input[6:].strip()
                if not filename:
                    console.print("[red]请指定文件名，例如: /read 1.pdf[/red]\n")
                    continue
                try:
                    console.print(f"[cyan]正在解析与切片论文: {filename} ...[/cyan]")
                    paper_data = pdf_reader.read_pdf(filename)
                    
                    # 存入多论文字典
                    loaded_papers[filename] = paper_data
                    
                    console.print(f"[bold green]✓ 成功加载 [{filename}]！切片数: {len(paper_data['chunks'])} 个。当前上下文中共有 {len(loaded_papers)} 篇文献。[/bold green]")
                    console.print(f"[cyan]提示：系统已准备就绪，你可以随时提问。[/cyan]\n")
                except Exception as e:
                    console.print(f"[red]读取论文失败: {e}[/red]\n")
                continue

            # ==========================================
            # 常规对话处理（集成智能 RAG 检索）
            # ==========================================
            
            # 1. 根据用户输入，从已加载的论文中智能检索最相关的段落
            rag_context_block = pdf_reader.retrieve_relevant_chunks(user_input, loaded_papers)
            
            active_system_prompt = base_system_prompt + rag_context_block
            
            # 2. 先将用户的当前输入记录到内存历史中
            memory.add_message("user", user_input)
            
            # 3. 获取完整的历史消息列表发送给大模型
            messages = memory.get_messages()

            # 4. 调用大模型生成回复
            response_text = client.generate_response(active_system_prompt, messages)
            
            if not response_text:
                console.print("[yellow]警告：模型返回内容为空，请稍后重试。[/yellow]\n")
                continue

            # 5. 将助手的回复记录到内存历史中
            memory.add_message("assistant", response_text)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]程序已中断。[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]发生系统错误: {e}[/red]")

if __name__ == "__main__":
    main()
