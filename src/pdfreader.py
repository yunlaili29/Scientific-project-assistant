import os
import re
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

    def read_pdf(self, filename: str) -> dict:
        """
        读取指定 PDF 文件，提取全文本，并将其切分为结构化段落块（Chunk），
        用于实现智能片段检索，防止 Token 爆炸。
        返回格式: {"full_text": str, "chunks": list}
        """
        filename = filename.strip()
        pdf_path = os.path.join(self.papers_dir, filename)
        
        if not os.path.exists(pdf_path):
            if os.path.exists(filename):
                pdf_path = filename
            else:
                raise FileNotFoundError(f"找不到文件: '{filename}' (请确保其位于 papers 目录下)")
        
        reader = PdfReader(pdf_path)
        full_text_list = []
        chunks = []
        
        for index, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                page_header = f"--- Page {index + 1} ---"
                full_text_list.append(f"{page_header}\n{text}")
                
                # 按段落粗切片，构建轻量级检索块
                paragraphs = text.split("\n\n")
                for p in paragraphs:
                    cleaned_p = p.strip()
                    if len(cleaned_p) > 20:  # 过滤过短的无意义碎片
                        chunks.append({
                            "page": index + 1,
                            "content": cleaned_p
                        })
        
        extracted_content = "\n".join(full_text_list).strip()
        if not extracted_content:
            raise ValueError(f"文件 '{filename}' 似乎是一个纯扫描件或图片PDF，未能提取到有效文本。")
            
        return {
            "full_text": extracted_content,
            "chunks": chunks
        }

    def retrieve_relevant_chunks(self, query: str, loaded_papers: dict, max_chunks_per_paper: int = 3) -> str:
        """
        根据用户的查询关键词，从已加载的论文片段中智能检索最相关的段落，
        实现轻量级 RAG，有效避免超长文本导致的 Token 膨胀与注意力涣散。
        """
        if not loaded_papers:
            return ""

        # 提取查询中的关键词（简单的分词或去停用词过滤）
        query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 1]
        
        retrieved_block = "\n\n=== 检索到的相关文献片段 (智能上下文) ==="
        
        for filename, data in loaded_papers.items():
            chunks = data.get("chunks", [])
            if not chunks:
                # 如果没有切片，退化为直接取前一部分
                continue
            
            # 为每个 chunk 打分
            scored_chunks = []
            for chunk in chunks:
                score = 0
                content_lower = chunk["content"].lower()
                for word in query_words:
                    if word in content_lower:
                        score += 1
                if score > 0:
                    scored_chunks.append((score, chunk))
            
            # 按匹配度降序排序
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            
            # 取最相关的若干个片段
            selected = scored_chunks[:max_chunks_per_paper]
            
            if selected:
                retrieved_block += f"\n\n--- 来自文献: {filename} ---"
                for _, chunk in selected:
                    retrieved_block += f"\n[P.{chunk['page']}] {chunk['content']}"
            else:
                # 如果没有强匹配的关键词，默认提供摘要或前置核心段落，保证基础上下文存在
                retrieved_block += f"\n\n--- 来自文献: {filename} (默认引导段落) ---"
                for chunk in chunks[:2]:
                    retrieved_block += f"\n[P.{chunk['page']}] {chunk['content']}"
                    
        return retrieved_block
