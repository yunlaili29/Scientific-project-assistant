# src/client.py
import time
from google import genai
from google.genai import types
from src.config import API_KEY, SYSTEM_INSTRUCTION

class GeminiAssistant:
    def __init__(self, console):
        self.console = console
        self.client = genai.Client(api_key=API_KEY)
        self.current_role = "default"
        self.system_instruction = SYSTEM_INSTRUCTION
        self._init_chat()

    def _init_chat(self):
        """初始化或重新建立对话会话"""
        self.chat = self.client.chats.create(
            model="gemini-3.6-flash",
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.3,
            )
        )

    def set_system_instruction(self, new_instruction: str, role_key: str):
        """动态更新 System Instruction 并重置/同步对话状态"""
        self.system_instruction = new_instruction
        self.current_role = role_key
        # 重新加载 chat 实例，使新的 System Prompt 立即生效
        self._init_chat()

    def reset_chat(self):
        """重置对话会话"""
        self._init_chat()

    def get_history(self):
        """获取当前对话历史"""
        return self.chat.get_history()

    def send_message_with_retry(self, prompt, max_retries=3):
        """带有指数退避自动重试机制的消息发送方法"""
        for attempt in range(1, max_retries + 1):
            try:
                return self.chat.send_message(prompt)
            except Exception as e:
                error_str = str(e)
                if "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str:
                    if attempt < max_retries:
                        wait_time = attempt * 2
                        self.console.print(f"[bold yellow]⚠️ 服务器繁忙 (503)，正在重试 ({attempt}/{max_retries})，等待 {wait_time} 秒...[/bold yellow]")
                        time.sleep(wait_time)
                        continue
                raise e
