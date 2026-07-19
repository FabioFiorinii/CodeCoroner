from pathlib import Path
from typing import Optional

LANGUAGE_MAP = {
    '.py': 'python',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.mjs': 'javascript',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.c': 'c',
    '.h': 'c',
}

class SemanticChunker:
    def __init__(self):
        self.parsers = {}

    def detect_language(self, file_path: str) -> Optional[str]:
        ext = Path(file_path).suffix
        return LANGUAGE_MAP.get(ext)

    def chunk_file(self, file_path: str, content: str, language: str) -> list[dict]:
        chunks = []
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
