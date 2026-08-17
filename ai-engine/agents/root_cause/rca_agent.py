import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

RCA_PROMPT = """You are a root cause analysis expert. The program crashed with the error below.

Error Context:
{error_context}

Log Analysis:
{log_analysis}

Repo Overview:
{repo_profile}

The exception was raised in the innermost stacktrace frame, at a specific file and line listed in the Error Context above. The candidates below are the top suspicious files (source code), ordered by suspicion. The root cause is in one of these files.

Candidate source code:
{candidate_list}

Instructions:
1. The root cause file is almost always the source file that appears in the innermost stacktrace frame (e.g. "thefuck/rules/switch_lang.py"). If such a file is in the candidate list, make it root_file.
2. root_file MUST be an EXACT path from the candidate list. NEVER pick a test file (paths containing "tests/" or starting with "test_").
3. root_line must be a real line number visible in that candidate's code that directly triggers or explains the error.
4. cause_chain: explain in 3-5 short steps how the error propagates.

Return ONLY valid JSON with this exact structure:
{{
  "summary": "string - root cause summary, at most 2 sentences",
  "root_file": "string - EXACT path from the candidate list",
  "root_line": number,
  "cause_chain": "string",
  "confidence": 0.0-1.0,
  "reasoning": "string - at most 5 sentences"
}}"""


class RootCauseAgent(BaseAgent):
    async def run(
        self,
        repo_id: str,
        error_context: dict,
        log_analysis: dict,
        suspicious_files: list,
        chunks: list,
        repo_profile: str = '',
    ) -> dict:
        candidate_list = '\n\n'.join(
            f'[{i}] {c.get("file_path", "")} (lines {c.get("start_line", 0)}-{c.get("end_line", 0)})\n```{c.get("language", "")}\n'
            + c.get('content', '')[:4000]
            + '\n```'
            for i, c in enumerate(chunks or [], start=1)
        )
        if not candidate_list:
            candidate_list = '(no source candidates available; rely on the stacktrace in Error Context)'

        prompt = RCA_PROMPT.format(
            error_context=json.dumps(error_context, indent=2),
            log_analysis=json.dumps(log_analysis, indent=2),
            repo_profile=repo_profile or '(no repo profile available)',
            suspicious_files=json.dumps(suspicious_files, indent=2),
            candidate_list=candidate_list,
        )
        try:
            raw = await self.ollama.generate(
                self.settings.rca_model, prompt, format='json', options={'num_predict': 600}
            )
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
