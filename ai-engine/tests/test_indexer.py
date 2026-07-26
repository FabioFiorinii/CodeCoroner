import pytest
import tempfile
from pathlib import Path
from agents.repository_indexer.indexer import RepositoryIndexer, _extract_nodes, _build_parser, LANGUAGE_EXT_MAP


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / 'src').mkdir()
        (base / 'src' / 'main.py').write_text('''import os

def hello():
    print("hello")

class Calculator:
    def add(self, a, b):
        return a + b
''')
        (base / 'src' / 'utils.ts').write_text('''export function greet(name: string): string {
    return `Hello ${name}`;
}

export interface User {
    id: number;
    name: string;
}
''')
        (base / 'README.md').write_text('# Ignored')
        (base / 'ignored.pyc').write_text('binary')
        yield base


class TestIndexer:
    @pytest.mark.asyncio
    async def test_index_python_file(self, temp_repo):
        indexer = RepositoryIndexer()
        result = await indexer.run(str(temp_repo))
        assert result['status'] == 'ok'
        assert result['file_count'] == 2
        paths = [f['path'] for f in result['files']]
        assert 'src/main.py' in paths
        assert 'src/utils.ts' in paths

    @pytest.mark.asyncio
    async def test_index_ignores_pyc(self, temp_repo):
        indexer = RepositoryIndexer()
        result = await indexer.run(str(temp_repo))
        paths = [f['path'] for f in result['files']]
        assert 'ignored.pyc' not in paths

    @pytest.mark.asyncio
    async def test_index_ignores_readme(self, temp_repo):
        indexer = RepositoryIndexer()
        result = await indexer.run(str(temp_repo))
        paths = [f['path'] for f in result['files']]
        assert 'README.md' not in paths

    @pytest.mark.asyncio
    async def test_index_nonexistent_path(self):
        indexer = RepositoryIndexer()
        result = await indexer.run('/nonexistent/path')
        assert result['status'] == 'error'

    @pytest.mark.asyncio
    async def test_python_nodes_extracted(self, temp_repo):
        indexer = RepositoryIndexer()
        result = await indexer.run(str(temp_repo))
        py_file = next(f for f in result['files'] if f['path'] == 'src/main.py')
        node_types = [n['type'] for n in py_file['nodes']]
        assert 'function_definition' in node_types
        assert 'class_definition' in node_types

    @pytest.mark.asyncio
    async def test_typescript_nodes_extracted(self, temp_repo):
        indexer = RepositoryIndexer()
        result = await indexer.run(str(temp_repo))
        ts_file = next(f for f in result['files'] if f['path'] == 'src/utils.ts')
        node_types = [n['type'] for n in ts_file['nodes']]
        assert 'function_declaration' in node_types or 'function_definition' in node_types

    def test_language_map(self):
        assert LANGUAGE_EXT_MAP['.py'] == 'python'
        assert LANGUAGE_EXT_MAP['.ts'] == 'typescript'
        assert LANGUAGE_EXT_MAP['.go'] == 'go'
        assert LANGUAGE_EXT_MAP['.rs'] == 'rust'
