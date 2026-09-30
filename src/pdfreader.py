import os
from pypdf import PdfReader

class PDFReader:
    def __init__(self, papers_dir="papers"):
        """初始化 PDF 阅读器，默认读取根目录下的 papers 文件夹"""
        self.papers_dir = papers_dir
        if not os.path.exists(self.papers_dir):
            os.makedirs(self.papers_dir)

    def list_papers(self):
        """列出 papers 文件夹下的所有 PDF 文件"""
        if not os.path.exists(self.papers_dir):
            return []
        return [f for f in os.listdir(self.papers_dir) if f.lower().endswith(".pdf")]

    def read_pdf(self, filename: str) -> str:
        """读取指定 PDF 文件的所有页面文本"""
        # 优先在 papers 文件夹下查找，若找不到则尝试按直接路径查找
        pdf_path = os.path.join(self.papers_dir, filename)
        if not os.path.exists(pdf_path):
            if os.path.exists(filename):
                pdf_path = filename
            else:
                raise FileNotFoundError(f"找不到文件: {filename} (请确保它已放入 papers 目录下)")
        
        reader = PdfReader(pdf_path)
        full_text = []
        for index, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text.append(f"--- Page {index + 1} ---\n{text}")
        return "\n".join(full_text)
