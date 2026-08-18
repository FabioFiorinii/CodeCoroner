import json
import logging
import re
from agents.base_agent import BaseAgent
from agents.json_utils import parse_json_response

logger = logging.getLogger(__name__)

STACKTRACE_FILE_RE = re.compile(r'File "([^"]+)"')

LOCALIZE_PROMPT = """You are a bug localization expert. The program crashed with the error below.

Log Analysis:
{log_analysis}

Error Context:
{error_context}

Repo Overview:
{repo_profile}

The exception was raised in the innermost stacktrace frame. The chunks below are the candidate files, ordered by relevance (stacktrace files first). One of them contains the code where the error is raised.

Candidate chunks:
{candidate_list}

Instructions:
1. Check each candidate's code and find the one that can raise the observed error. The innermost stacktrace file is the primary suspect; if its code matches the error pattern, it is the answer.
2. Prefer source files (e.g. "thefuck/rules/switch_lang.py") over test files (e.g. "tests/rules/test_switch_lang.py").
3. Include at least the top 3 most suspicious candidates, ranked by descending score.
4. "file_path" MUST be an exact string from the candidate list above. NEVER invent a path.

Return ONLY valid JSON with this exact structure:
{{
  "summary": "string - brief summary, at most 2 sentences",
  "suspicious_files": [
    {{
      "file_path": "string - EXACT path from the candidate list",
      "score": 0.0-1.0,
      "evidence": "string - why this file is suspicious",
      "rank": 1
    }}
  ]
}}"""


class BugLocalizer(BaseAgent):
    async def run(
        self,
        repo_id: str,
        error_context: dict,
        log_analysis: dict,
        chunks: list,
        repo_profile: str = '',
    ) -> dict:
        stacktrace_files = self._extract_stacktrace_files(error_context)
        limit = 3 if stacktrace_files else 5
        ordered_chunks = self._order_chunks(chunks, stacktrace_files, limit=limit)
        candidate_list = '\n\n'.join(
            f'[{i}] {c.get("file_path", "")}\n```{c.get("language", "")}\n'
            + c.get('content', '')[:2500 if self._is_stacktrace_file(c, stacktrace_files) else 1000]
            + '\n```'
            for i, c in enumerate(ordered_chunks, start=1)
        )

        prompt = LOCALIZE_PROMPT.format(
            log_analysis=json.dumps(log_analysis, indent=2),
            error_context=json.dumps(error_context, indent=2),
            repo_profile=repo_profile or '(no repo profile available)',
            candidate_list=candidate_list,
        )
        try:
            raw = await self.ollama.generate(
                self.settings.llm_model, prompt, format='json', options={'num_predict': 450}
            )
            result = parse_json_response(raw)
            result.setdefault('status', 'ok')
            return result
        except Exception as exc:
            logger.error('BugLocalizer failed: %s', exc)
            return {
                'status': 'error',
                'error': str(exc),
                'summary': 'Bug localization failed',
                'suspicious_files': [],
            }

    def _extract_stacktrace_files(self, error_context: dict) -> list[str]:
        files = []
        for key in ('stacktrace', 'logs'):
            text = error_context.get(key)
            if not isinstance(text, str):
                continue
            for match in STACKTRACE_FILE_RE.finditer(text):
                path = match.group(1)
                if path not in files:
                    files.append(path)
        return files

    def _is_stacktrace_file(self, chunk: dict, stacktrace_files: list[str]) -> bool:
        path = chunk.get('file_path', '') or ''
        return any(path == f or path.endswith(f) or f.endswith(path) for f in stacktrace_files)

    def _order_chunks(self, chunks: list, stacktrace_files: list[str], limit: int = 10) -> list:
        chunks = list(chunks or [])
        matched = [c for c in chunks if self._is_stacktrace_file(c, stacktrace_files)]
        rest = [c for c in chunks if not self._is_stacktrace_file(c, stacktrace_files)]
        return (matched + rest)[:limit]