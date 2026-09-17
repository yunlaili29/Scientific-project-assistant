import os

class FileParser:
    """专门负责解析单文件、多文件以及项目目录结构的解析器"""

    @staticmethod
    def read_files(file_paths):
        """
        读取多个文件并组合成格式化的 Prompt
        """
        combined_content = []
        success_files = []
        failed_files = []

        for path in file_paths:
            path = path.strip()
            if not os.path.exists(path):
                failed_files.append((path, "文件不存在"))
                continue
            if os.path.isdir(path):
                failed_files.append((path, "这是一个目录，请使用 /scan 指令"))
                continue
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                combined_content.append(f"### 文件: `{path}`\n```\n{content}\n```")
                success_files.append(path)
            except Exception as e:
                failed_files.append((path, str(e)))

        return combined_content, success_files, failed_files

    @staticmethod
    def scan_directory(dir_path, ignore_dirs=None, extensions=None):
        """
        扫描整个目录树并提取符合条件的代码/文档文件
        """
        if ignore_dirs is None:
            ignore_dirs = {".git", "__pycache__", "logs", ".venv", "node_modules", ".pytest_cache"}
        if extensions is None:
            extensions = {".py", ".md", ".json", ".txt", ".env", ".yml", ".yaml", ".sh"}

        if not os.path.exists(dir_path):
            return None, f"错误：目录 '{dir_path}' 不存在"
        if not os.path.isdir(dir_path):
            return None, f"错误：'{dir_path}' 不是一个有效的目录"

        tree_str = f"📁 目录结构: `{dir_path}`\n"
        file_contents = []
        scanned_files = []

        for root, dirs, files in os.walk(dir_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            level = root.replace(dir_path, '').count(os.sep)
            indent = '  ' * level
            tree_str += f"{indent}├── {os.path.basename(root)}/\n"
            
            subindent = '  ' * (level + 1)
            for f in files:
                ext = os.path.splitext(f)[1]
                tree_str += f"{subindent}├── {f}\n"
                
                # 如果是支持的扩展名，读取其内容
                if ext in extensions or f in {".env", "README.md"}:
                    full_path = os.path.join(root, f)
                    try:
                        with open(full_path, "r", encoding="utf-8") as file_obj:
                            content = file_obj.read()
                        file_contents.append(f"### 代码文件: `{full_path}`\n```\n{content}\n```")
                        scanned_files.append(full_path)
                    except Exception:
                        pass  # 忽略读取失败的二进制或非 UTF-8 文件

        prompt = f"项目目录扫描分析请求：\n\n{tree_str}\n\n以下是该目录下关键文件的源码内容：\n\n" + "\n\n".join(file_contents)
        return prompt, scanned_files
