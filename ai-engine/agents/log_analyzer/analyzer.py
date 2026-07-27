import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

ANALYZE_PROMPT = """You are a log analysis expert. Analyze the following error context and return a structured JSON response.

Error Context:
{error_context}

Return ONLY valid JSON with this exact structure:
{{
  "error_type": "string - category of error (e.g. NullPointer, IndexError, SyntaxError, etc.)",
  "summary": "string - one-line summary of the error",
  "affected_files": ["list of file paths mentioned or implicated"],
  "severity": "critical|high|medium|low",
  "key_message": "string - the most important error message extracted",
  "language_detected": "string - programming language if identifiable",
  "suggested_focus": "string - what to investigate first"
}}"""


class LogAnalyzer(BaseAgent):
    async def run(self, error_context: dict) -> dict:
        prompt = ANALYZE_PROMPT.format(
            error_context=json.dumps(error_context, indent=2)
        )
        try:
            raw = await self.ollama.generate(self.settings.llm_model, prompt, format='json')
            result = self._parse_json(raw)
            result.setdefault('status', 'ok')
            return result
        except Exception as exc:
            logger.error('LogAnalyzer failed: %s', exc)
            return {
                'status': 'error',
                'error': str(exc),
                'error_type': 'unknown',
                'summary': 'Log analysis failed',
                'affected_files': [],
                'severity': 'medium',
                'key_message': str(error_context.get('error_message', '')),
                'language_detected': '',
                'suggested_focus': '',
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
