import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

LOCALIZE_PROMPT = """You are a bug localization expert. Given error context and code chunks from the repository, identify which files are most likely to contain the bug.

Log Analysis:
{log_analysis}

Error Context:
{error_context}

Top Code Chunks (from vector similarity search):
{chunks}

For each chunk, analyze:
1. Does the code pattern match the error type?
2. Could the logic in this chunk produce the observed error?
3. Is this file directly implicated by the error message or stacktrace?

Return ONLY valid JSON with this exact structure:
{{
  "summary": "string - brief summary of localization findings",
  "suspicious_files": [
    {{
      "file_path": "string",
      "score": 0.0-1.0,
      "evidence": "string - why this file is suspicious",
      "rank": 1
    }}
  ]
}}

Rank suspicious files by score descending (highest suspicion first). Include at least the top 3-5 files. If no files seem relevant, return empty suspicious_files array."""


class BugLocalizer(BaseAgent):
    async def run(self, repo_id: str, error_context: dict, log_analysis: dict, chunks: list) -> dict:
        chunks_text = json.dumps([
            {
                'file_path': c.get('file_path', ''),
                'language': c.get('language', ''),
                'content': c.get('content', '')[:2000],
                'similarity': c.get('similarity', 0),
            }
            for c in (chunks or [])
        ], indent=2)

        prompt = LOCALIZE_PROMPT.format(
            log_analysis=json.dumps(log_analysis, indent=2),
            error_context=json.dumps(error_context, indent=2),
            chunks=chunks_text,
        )
        try:
            raw = await self.ollama.generate(self.settings.llm_model, prompt, format='json')
            result = self._parse_json(raw)
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

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[-1]
            if '```' in raw:
                raw = raw.rsplit('```', 1)[0]
        raw = raw.strip()
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1:
            raw = raw[start:end+1]
        raw = ''.join(c for c in raw if c.isprintable() or c in '\n\r\t ')
        return json.loads(raw)
