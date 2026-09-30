import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from rich.console import Console

# 加载环境变量
load_dotenv()
console = Console()

class Client:
    def __init__(self):
        # 初始化新版 google-genai 客户端
        try:
            self.client = genai.Client()
        except Exception as e:
            console.print(f"[yellow]初始化 Gemini 客户端警告: {e}[/yellow]")
            self.client = None
            
        # 使用当前官方完全支持的最新标准模型
        self.model_name = "gemini-3.8-flash"

    def generate_response(self, system_prompt: str, messages: list) -> str:
        """
        使用新版 google-genai SDK 生成回复，带 503 自动重试机制
        """
        if not self.client:
            raise ValueError("Gemini 客户端未正确初始化")

        # 格式化历史对话内容
        formatted_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        # 使用最简配置，避免触发旧版参数限制
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7
        )

        # 最多重试 3 次，应对高峰期临时过载 (503)
        max_retries = 3
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                # 调用新版客户端接口
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=formatted_contents,
                    config=config
                )
                
                console.print(f"\n[bold blue]Assistant:[/bold blue] {response.text}\n")
                return response.text
                
            except Exception as e:
                # 如果遇到 503 / 过载错误，且还有重试机会，则自动等待后重试
                if ("503" in str(e) or "UNAVAILABLE" in str(e)) and (attempt < max_retries - 1):
                    sleep_time = backoff_factor ** attempt
                    console.print(f"[yellow]服务器繁忙 (503)，正在进行第 {attempt + 1} 次自动重试，等待 {sleep_time} 秒...[/yellow]")
                    time.sleep(sleep_time)
                    continue
                
                # 其他错误或重试次数用完时，打印异常并抛出
                console.print(f"[red]Gemini API 调用异常: {e}[/red]")
                raise e