import json
import logging
from agents.base_agent import BaseAgent
from agents.json_utils import parse_json_response

logger = logging.getLogger(__name__)

SUGGEST_FIX_PROMPT = """You are an expert software engineer. Given an error context, log analysis, bug localization, root cause analysis, and relevant source code, generate a fix suggestion.

Error Context:
{error_context}

Repo Overview:
{repo_profile}

Log Analysis:
{log_analysis}

Bug Localization:
{bug_localization}

Root Cause Analysis:
{root_cause}

Relevant Source Code Chunks:
{source_code}

Your task: analyze the bug and propose a fix. Return ONLY valid JSON with this exact structure:
{{
  "diff": "string - a unified diff (--- a/... +++ b/...) of the proposed changes to fix the bug",
  "plan": "string - a concise, step-by-step plan for implementing the fix, written as a prompt for another AI. Minimize token usage: be direct, specific, and avoid any explanatory text. Only include: file path, line ranges to modify, what to change and what to replace it with.",
  "explanation": "string - detailed explanation of why this fix is needed: what causes the bug, what the change does, what side effects it might have, and why this approach was chosen over alternatives."
}}"""


class PatchGenerator(BaseAgent):
    async def run(
        self,
        error_context: dict,
        log_analysis: dict,
        bug_localization: dict | None,
        root_cause: dict | None,
        chunks: list,
        repo_profile: str = '',
    ) -> dict:
        source_code = json.dumps([
            {
                'file_path': c.get('file_path', ''),
                'content': c.get('content', '')[:4000],
                'start_line': c.get('start_line', 0),
                'end_line': c.get('end_line', 0),
            }
            for c in (chunks or [])
        ], indent=2)

        prompt = SUGGEST_FIX_PROMPT.format(
            error_context=json.dumps(error_context, indent=2),
            repo_profile=repo_profile or '(no repo profile available)',
            log_analysis=json.dumps(log_analysis, indent=2),
            bug_localization=json.dumps(bug_localization, indent=2),
            root_cause=json.dumps(root_cause, indent=2),
            source_code=source_code,
        )
        try:
            raw = await self.ollama.generate(
                self.settings.rca_model, prompt, format='json', options={'num_predict': 1500}
            )
            result = parse_json_response(raw)
            result.setdefault('status', 'ok')
            result.setdefault('diff', '')
            result.setdefault('plan', '')
            result.setdefault('explanation', '')
            return result
        except Exception as exc:
            logger.error('PatchGenerator failed: %s', exc)
            return {
                'status': 'error',
                'error': str(exc),
                'diff': '',
                'plan': '',
                'explanation': '',
            }
