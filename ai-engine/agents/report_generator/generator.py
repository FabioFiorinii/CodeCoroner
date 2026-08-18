import json
import logging
from agents.base_agent import BaseAgent
from agents.json_utils import parse_json_response

logger = logging.getLogger(__name__)

REPORT_PROMPT = """You are a technical report writer. Write a bug analysis report in Markdown that summarizes the findings of the whole analysis pipeline.

Repo Overview:
{repo_profile}

Analysis Data (results of each pipeline step):
{analysis_data}

Write a Markdown report (300-450 words) with these sections:
## Summary
2-3 sentences: what failed, in which component, and the overall verdict.

## Error Context
One short paragraph: the error message, where it was raised (file:line from the stacktrace), and the environment.

## Log Analysis
2-3 sentences on the key findings from the log/stacktrace analysis step.

## Bug Localization
A short bullet list of the top suspicious files with their suspicion score. Highlight the file ranked first.

## Root Cause
Root file and line, the causal chain, and confidence. Use the findings of the root cause step verbatim where possible.

## Fix Direction
A short bullet list of recommended next steps based on the fix suggestion step (diff, plan, explanation). If the fix suggestion is missing, note what to investigate.

Rules:
- Ground every claim in the Analysis Data. Do NOT invent details, file names, or line numbers that are not present.
- Prefer source files over test files when describing the root cause.
- Be direct; skip filler.

Return ONLY valid JSON with this structure:
{{
  "title": "string - short report title",
  "markdown": "string - the full Markdown report"
}}"""


class ReportGenerator(BaseAgent):
    async def run(self, analysis_data: dict, repo_profile: str = '') -> dict:
        prompt = REPORT_PROMPT.format(
            repo_profile=repo_profile or '(no repo profile available)',
            analysis_data=json.dumps(analysis_data, indent=2),
        )
        try:
            raw = await self.ollama.generate(
                self.settings.llm_model, prompt, format='json', options={'num_predict': 1000}
            )
            result = parse_json_response(raw)
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
