import tiktoken
from rich.console import Console

console = Console()

class ContextManager:
    def __init__(self, max_tokens: int = 16000, keep_recent: int = 4):
        """
        :param max_tokens: 触发压缩的 Token 阈值
        :param keep_recent: 压缩时强行保留的最新对话轮数 (1 轮 = 1 次 User + 1 次 Assistant)
        """
        self.max_tokens = max_tokens
        self.keep_recent_messages = keep_recent * 2
        # 使用 cl100k_base 编码器（适合大多数现代 LLM 的近似估算）
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoder = None

    def estimate_tokens(self, text: str) -> int:
        """估算字符串的 Token 数量"""
        if self.encoder:
            return len(self.encoder.encode(text))
        # 兜底算法：中英文混合情况下，粗略按 1 token ≈ 3-4 chars 估算
        return len(text) // 3

    def count_history_tokens(self, history: list) -> int:
        """计算当前完整历史记录的总 Token 数"""
        total = 0
        for msg in history:
            # 支持 dict 或 message 对象格式
            content = getattr(msg, 'text', None) or getattr(msg, 'content', '') or str(msg)
            total += self.estimate_tokens(content)
        return total

    def truncate_or_summarize(self, client, history: list) -> list:
        """
        检查 Token 是否超限。如果超限，调用轻量模型生成摘要，压缩旧历史。
        """
        current_tokens = self.count_history_tokens(history)
        
        if current_tokens <= self.max_tokens or len(history) <= self.keep_recent_messages:
            return history

        console.print(f"\n[bold yellow]⚠️ 上下文 Token 数 ({current_tokens}) 已接近设定的阈值 ({self.max_tokens})，正在执行智能压缩...[/bold yellow]")

        # 切分：需要压缩的旧消息 vs 保留的最新消息
        old_messages = history[:-self.keep_recent_messages]
        recent_messages = history[-self.keep_recent_messages:]

        # 提取旧消息文本
        old_text_block = ""
        for msg in old_messages:
            role = getattr(msg, 'role', 'user')
            text = getattr(msg, 'text', None) or getattr(msg, 'content', '')
            old_text_block += f"{role.upper()}: {text}\n"

        # 让模型生成背景摘要
        summary_prompt = (
            "请将以下前期对话历史高度概括为一份精炼的上下文背景摘要（Summary）。\n"
            "重点保留：用户核心诉求、关键决策、提及的技术细节及变量参数。\n"
            "忽略：礼貌客套话、中间纠错细节。\n\n"
            f"待压缩的历史记录：\n{old_text_block}"
        )

        try:
            summary_response = client.generate_summary(summary_prompt)
            summary_text = f"【系统前情摘要】：\n{summary_response}"
            
            console.print("[bold green]✅ 历史上下文已成功压缩并归纳为前情摘要！[/bold green]")
            
            # 构造新的历史：[摘要消息, ...最新消息]
            # 依据具体 SDK 的 Chat 结构适配，此处以标准 Role/Content 列表表示
            new_history = [{"role": "user", "parts": [summary_text]}, {"role": "model", "parts": ["收到，我已掌握前期背景，请继续。"]}]
            new_history.extend(recent_messages)
            
            return new_history
        except Exception as e:
            console.print(f"[bold red]❌ 生成历史摘要失败，执行备用裁剪策略: {e}[/bold red]")
            # 备用方案：直接丢弃极早期的消息，保障当前会话不中断
            return history[-self.keep_recent_messages:]
