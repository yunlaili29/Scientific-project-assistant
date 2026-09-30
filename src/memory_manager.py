import os
from datetime import datetime
from rich.console import Console

console = Console()

class MemoryManager:
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        # 用于在内存中临时存储当前对话消息
        self.messages = []
        # 确保 logs 目录存在，如果不存在则自动创建
        os.makedirs(self.logs_dir, exist_ok=True)

    def get_messages(self) -> list:
        """
        返回当前的对话历史消息
        """
        return self.messages

    def add_message(self, role: str, content: str):
        """
        向历史中添加一条消息
        """
        self.messages.append({"role": role, "content": content})

    def save_chat_history(self, filename: str = None) -> str:
        """
        将当前的对话历史保存为 Markdown 文件
        """
        if not self.messages:
            console.print("[yellow]当前没有可保存的对话历史。[/yellow]")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.md"

        filepath = os.path.join(self.logs_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# AI Assistant Chat Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for msg in self.messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    f.write(f"**{role.upper()}**:\n{content}\n\n---\n\n")
            
            console.print(f"[green]✔ 对话历史已成功归档至: {filepath}[/green]")
            return filepath
        except Exception as e:
            console.print(f"[red]✖ 保存对话历史失败: {e}[/red]")
            return None

    def list_history_files(self) -> list:
        """
        列出 logs 目录下的所有历史对话文件
        """
        if not os.path.exists(self.logs_dir):
            return []
        files = [f for f in os.listdir(self.logs_dir) if f.endswith(".md")]
        return sorted(files, reverse=True)