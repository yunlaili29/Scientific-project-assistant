import os
from dotenv import load_dotenv
from google import genai

# 1. 加载 .env 环境变量
load_dotenv()

# 2. 从环境变量中读取 Gemini Key
api_key = os.getenv("GEMINI_API_KEY")

# 3. 初始化 Gemini 客户端
client = genai.Client(api_key=api_key)

# 4. 向 Gemini 发送请求
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="你好！请用一句话简短介绍一下你自己。",
)

# 5. 打印 Gemini 的回答
print(response.text)

