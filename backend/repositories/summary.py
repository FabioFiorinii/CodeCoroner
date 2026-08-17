from collections import Counter
from pathlib import Path

IGNORED_DIRS = {
    '.git',
    '__pycache__',
    'node_modules',
    '.venv',
    'venv',
    '.tox',
    '.eggs',
    'dist',
    'build',
    '.next',
    '.nuxt',
    'target',
    'vendor',
    '.bundle',
    '.gradle',
    'bin',
    'obj',
    '.idea',
    '.vscode',
    '.DS_Store',
}

IGNORED_EXTENSIONS = {
    '.pyc',
    '.pyo',
    '.so',
    '.dll',
    '.dylib',
    '.exe',
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.ico',
    '.svg',
    '.woff',
    '.woff2',
    '.ttf',
    '.eot',
    '.pdf',
    '.zip',
    '.tar',
    '.gz',
    '.bz2',
    '.rar',
    '.7z',
    '.min.js',
    '.min.css',
    '.map',
}

README_NAMES = ('README.md', 'README.rst', 'README.txt', 'README')

MAX_README_CHARS = 2000
MAX_TOP_DIRS = 15


def build_repo_summary(repo_path: Path) -> str:
    lines = []

    readme = _readme_excerpt(repo_path)
    if readme:
        lines.append('# Repository Overview\n')
        lines.append(readme)

    files = []
    dir_counts: Counter = Counter()
    for fp in repo_path.rglob('*'):
        if not fp.is_file():
            continue
        rel = fp.relative_to(repo_path)
        if any(p in IGNORED_DIRS for p in rel.parts):
            continue
        if fp.suffix.lower() in IGNORED_EXTENSIONS:
            continue
        files.append(rel)
        dir_counts[rel.parts[0] if len(rel.parts) > 1 else '.'] += 1

    if not files:
        return '\n'.join(lines).strip()

    ext_counts: Counter = Counter(fp.suffix.lower() or '(none)' for fp in files)
    top_ext = ext_counts.most_common(8)

    lines.append('## Layout')
    lines.append(f'Total source files: {len(files)}')
    top_dirs = dir_counts.most_common(MAX_TOP_DIRS)
    lines.append(
        'Top-level directories: ' + ', '.join(f'{name} ({count} files)' for name, count in top_dirs)
    )
    lines.append(
        'Dominant file extensions: ' + ', '.join(f'{ext} ({count})' for ext, count in top_ext)
    )

    return '\n'.join(lines).strip()


def _readme_excerpt(repo_path: Path) -> str:
    for name in README_NAMES:
        candidate = repo_path / name
        if candidate.is_file():
            try:
                text = candidate.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            return text[:MAX_README_CHARS].strip()
    return ''
