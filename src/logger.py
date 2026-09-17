import os
from datetime import datetime

class ChatLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(self.log_dir, f"chat_log_{timestamp}.md")
        self._init_log_file()

    def _init_log_file(self):
        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write("# 科研 AI 助手对话日志\n")
            f.write(f"- **记录时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")

    def log_interaction(self, user_input, assistant_response):
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(f"### 👤 User:\n{user_input}\n\n")
            f.write(f"### 🤖 Assistant:\n{assistant_response}\n\n---\n\n")
