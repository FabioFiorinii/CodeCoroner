import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

REPORT_PROMPT = """You are a technical report writer. Generate a CONCISE bug analysis report in Markdown format.

Repo Overview:
{repo_profile}

Analysis Data:
{analysis_data}

Generate a short Markdown report (max 250 words total) with these sections:
1. **Summary** - 1-2 sentences
2. **Error Context** - error message and environment in one line
3. **Root Cause** - root file/line and cause in 2-3 sentences
4. **Fix Direction** - recommended next steps as a short bullet list

Do not repeat the full error context or stacktrace. Be direct and skip fluff.

Return ONLY valid JSON with this structure:
{{
  "title": "string - short report title",
  "markdown": "string - concise Markdown report"
}}"""


class ReportGenerator(BaseAgent):
    async def run(self, analysis_data: dict, repo_profile: str = '') -> dict:
        prompt = REPORT_PROMPT.format(
            repo_profile=repo_profile or '(no repo profile available)',
            analysis_data=json.dumps(analysis_data, indent=2),
        )
        try:
            raw = await self.ollama.generate(
                self.settings.llm_model, prompt, format='json', options={'num_predict': 450}
            )
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
