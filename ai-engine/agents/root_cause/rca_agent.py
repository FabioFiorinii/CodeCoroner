import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

RCA_PROMPT = """You are a root cause analysis expert. Given error context, bug localization results, and source code, determine the root cause of the bug.

Error Context:
{error_context}

Log Analysis:
{log_analysis}

Suspicious Files (ranked by suspicion):
{suspicious_files}

Source Code of Top Suspicious Files:
{source_code}

Analyze deeply and determine:
1. What is the root cause of this bug?
2. Which specific file and line is responsible?
3. What is the chain of causality?
4. How confident are you in this analysis?

Return ONLY valid JSON with this exact structure:
{{
  "summary": "string - one-line root cause summary",
  "root_file": "string - file path containing the root cause",
  "root_line": number | null - line number of the root cause,
  "cause_chain": "string - detailed step-by-step chain of causality",
  "confidence": 0.0-1.0,
  "reasoning": "string - detailed reasoning for the conclusion"
}}"""


class RootCauseAgent(BaseAgent):
    async def run(self, repo_id: str, error_context: dict, log_analysis: dict, suspicious_files: list, chunks: list) -> dict:
        source_code = json.dumps([
            {
                'file_path': c.get('file_path', ''),
                'content': c.get('content', '')[:3000],
                'start_line': c.get('start_line', 0),
                'end_line': c.get('end_line', 0),
            }
            for c in (chunks or [])
        ], indent=2)

        prompt = RCA_PROMPT.format(
            error_context=json.dumps(error_context, indent=2),
            log_analysis=json.dumps(log_analysis, indent=2),
            suspicious_files=json.dumps(suspicious_files, indent=2),
            source_code=source_code,
        )
        try:
            raw = await self.ollama.generate(self.settings.rca_model, prompt, format='json')
            result = self._parse_json(raw)
            result.setdefault('status', 'ok')
            return result
        except Exception as exc:
            logger.error('RootCauseAgent failed: %s', exc)
            return {
                'status': 'error',
                'error': str(exc),
                'summary': 'Root cause analysis failed',
                'root_file': '',
                'root_line': None,
                'cause_chain': '',
                'confidence': 0.0,
                'reasoning': '',
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
