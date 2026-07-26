import hashlib
from pathlib import Path
from typing import Optional

from agents.base_agent import BaseAgent

LANGUAGE_EXT_MAP = {
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

IGNORED_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.tox', '.eggs', 'dist', 'build', '.next', '.nuxt',
    'target', 'vendor', '.bundle', '.gradle', 'bin', 'obj',
    '.idea', '.vscode',
}

IGNORED_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
    '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg',
    '.woff', '.woff2', '.ttf', '.eot', '.pdf',
    '.zip', '.tar', '.gz', '.bz2', '.rar', '.7z',
    '.min.js', '.min.css', '.map',
}


def _build_parser(language: str):
    if language == 'python':
        import tree_sitter_python
        import tree_sitter
        lang = tree_sitter.Language(tree_sitter_python.language())
        return tree_sitter.Parser(lang)
    if language in ('typescript', 'javascript'):
        import tree_sitter_typescript
        import tree_sitter
        ts_lang = tree_sitter_typescript.language_typescript() if language == 'typescript' else tree_sitter_typescript.language_javascript()
        lang = tree_sitter.Language(ts_lang)
        return tree_sitter.Parser(lang)
    if language == 'go':
        import tree_sitter_go
        import tree_sitter
        lang = tree_sitter.Language(tree_sitter_go.language())
        return tree_sitter.Parser(lang)
    if language == 'rust':
        import tree_sitter_rust
        import tree_sitter
        lang = tree_sitter.Language(tree_sitter_rust.language())
        return tree_sitter.Parser(lang)
    if language == 'java':
        import tree_sitter_java
        import tree_sitter
        lang = tree_sitter.Language(tree_sitter_java.language())
        return tree_sitter.Parser(lang)
    return None


_NODE_KINDS = {
    'function_definition', 'method_definition', 'class_definition',
    'interface_declaration', 'type_alias_declaration', 'enum_declaration',
    'function_declaration', 'method_declaration', 'constructor_declaration',
    'struct_item', 'trait_item', 'impl_item', 'fn_item',
    'func_declaration', 'method_spec',
    'module', 'program', 'source_file',
}


def _extract_nodes(node, depth=0) -> list[dict]:
    results = []
    if depth > 100:
        return results
    if node.type in _NODE_KINDS:
        results.append({
            'type': node.type,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'start_col': node.start_point[1],
            'end_col': node.end_point[1],
            'text': node.text.decode('utf-8', errors='replace'),
        })
    for child in node.children:
        results.extend(_extract_nodes(child, depth + 1))
    return results


class RepositoryIndexer(BaseAgent):
    async def run(self, repo_path: str) -> dict:
        base = Path(repo_path)
        if not base.exists():
            return {'status': 'error', 'error': 'Path not found'}

        files_indexed = []
        total_bytes = 0

        for file_path in base.rglob('*'):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(base)
            if any(p in IGNORED_DIRS for p in rel.parts):
                continue
            ext = file_path.suffix.lower()
            if ext in IGNORED_EXTENSIONS:
                continue
            language = LANGUAGE_EXT_MAP.get(ext)
            if language is None:
                continue

            content = file_path.read_bytes()
            total_bytes += len(content)
            file_hash = hashlib.sha256(content).hexdigest()

            nodes = self._parse_file(file_path, content, language)

            files_indexed.append({
                'path': str(rel),
                'language': language,
                'size': len(content),
                'hash': file_hash,
                'nodes': nodes,
            })

        return {
            'status': 'ok',
            'file_count': len(files_indexed),
            'total_bytes': total_bytes,
            'files': files_indexed,
        }

    def _parse_file(self, file_path: Path, content: bytes, language: str) -> list[dict]:
        parser = _build_parser(language)
        if parser is None:
            return []
        try:
            tree = parser.parse(content)
            return _extract_nodes(tree.root_node)
        except Exception:
            return []
