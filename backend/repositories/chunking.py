from pathlib import Path
from typing import Any

LANGUAGE_MAP = {
    '.py': 'python',
    '.pyw': 'python',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.swift': 'swift',
    '.scala': 'scala',
    '.rb': 'ruby',
    '.php': 'php',
    '.php4': 'php',
    '.php5': 'php',
    '.pl': 'perl',
    '.pm': 'perl',
    '.r': 'r',
    '.R': 'r',
    '.lua': 'lua',
    '.ex': 'elixir',
    '.exs': 'elixir',
    '.hs': 'haskell',
    '.lhs': 'haskell',
    '.clj': 'clojure',
    '.cljs': 'clojure',
    '.cljc': 'clojure',
    '.dart': 'dart',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.hh': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.cs': 'csharp',
    '.fs': 'fsharp',
    '.fsx': 'fsharp',
    '.sql': 'sql',
    '.sh': 'shell',
    '.bash': 'shell',
    '.zsh': 'shell',
    '.ps1': 'powershell',
    '.psm1': 'powershell',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    '.vue': 'vue',
    '.svelte': 'svelte',
    '.astro': 'astro',
    '.json': 'json',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.rst': 'markdown',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    '.tf': 'terraform',
    '.tfvars': 'terraform',
    '.dockerfile': 'dockerfile',
    '.Dockerfile': 'dockerfile',
    '.lock': 'text',
}

class SemanticChunker:
    def __init__(self):
        self.parsers = {}

    def detect_language(self, file_path: str) -> str | None:
        ext = Path(file_path).suffix
        return LANGUAGE_MAP.get(ext)

    def chunk_file(self, file_path: str, content: str, language: str) -> list[dict]:
        chunks: list[dict[str, Any]] = []
        lines = content.split('\n')
        total_lines = len(lines)

        if total_lines == 0:
            return chunks

        if total_lines <= 100:
            chunks.append({
                'chunk_type': 'module',
                'start_line': 1,
                'end_line': total_lines,
                'content': content,
                'tokens_count': len(content.split()),
                'metadata': {},
            })
            return chunks

        current_start = 1
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if any(stripped.startswith(kw) for kw in
                   ['def ', 'class ', 'async def ', '@']):
                if current_start < i:
                    block = '\n'.join(lines[current_start - 1:i - 1])
                    if block.strip():
                        chunks.append({
                            'chunk_type': 'block',
                            'start_line': current_start,
                            'end_line': i - 1,
                            'content': block,
                            'tokens_count': len(block.split()),
                            'metadata': {},
                        })
                current_start = i

        remaining = '\n'.join(lines[current_start - 1:])
        if remaining.strip():
            chunks.append({
                'chunk_type': 'block',
                'start_line': current_start,
                'end_line': total_lines,
                'content': remaining,
                'tokens_count': len(remaining.split()),
                'metadata': {},
            })

        for chunk in chunks:
            if chunk['chunk_type'] == 'block' and (chunk['end_line'] - chunk['start_line']) > 100:
                self._split_large_chunk(chunk, lines)

        return chunks

    def _split_large_chunk(self, chunk: dict, lines: list[str]) -> list[dict]:
        sub_chunks = []
        for start in range(chunk['start_line'] - 1, chunk['end_line'], 100):
            end = min(start + 100, chunk['end_line'])
            block = '\n'.join(lines[start:end])
            sub_chunks.append({
                'chunk_type': 'block',
                'start_line': start + 1,
                'end_line': end,
                'content': block,
                'tokens_count': len(block.split()),
                'metadata': {'parent_start': chunk['start_line']},
            })
        return sub_chunks
