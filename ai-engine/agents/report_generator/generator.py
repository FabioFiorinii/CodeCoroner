import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

REPORT_PROMPT = """You are a technical report writer. Generate a comprehensive bug analysis report in Markdown format.

Analysis Data:
{analysis_data}

Generate a well-structured Markdown report with these sections:
1. **Summary** - brief overview
2. **Error Context** - what error occurred, environment
3. **Log Analysis** - key findings from logs/stacktrace
4. **Bug Localization** - suspicious files ranked by probability
5. **Root Cause Analysis** - detailed chain of causality
6. **Conclusion** - recommended next steps

Return ONLY valid JSON with this structure:
{{
  "title": "string - report title",
  "markdown": "string - full report in Markdown format"
}}"""


class ReportGenerator(BaseAgent):
    async def run(self, analysis_data: dict) -> dict:
        prompt = REPORT_PROMPT.format(
            analysis_data=json.dumps(analysis_data, indent=2),
        )
        try:
            raw = await self.ollama.generate(self.settings.llm_model, prompt, format='json')
            result = self._parse_json(raw)
            result.setdefault('status', 'ok')
            if not result.get('markdown'):
                result['markdown'] = f"# Bug Analysis Report\n\n{raw}"
            return result
        except Exception as exc:
            logger.error('ReportGenerator failed: %s', exc)
            return {
                'status': 'error',
                'error': str(exc),
                'title': 'Bug Analysis Report',
                'markdown': f"# Bug Analysis Report\n\nReport generation failed: {exc}",
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
