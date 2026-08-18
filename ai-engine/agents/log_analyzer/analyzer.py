import json
import logging
from agents.base_agent import BaseAgent
from agents.json_utils import parse_json_response

logger = logging.getLogger(__name__)

ANALYZE_PROMPT = """You are a log analysis expert. Analyze the following error context and return a structured JSON response.

Repo Overview:
{repo_profile}

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
}}

Keep the response concise: summary and suggested_focus must each be at most 2 sentences."""


class LogAnalyzer(BaseAgent):
    async def run(self, error_context: dict, repo_profile: str = '') -> dict:
        prompt = ANALYZE_PROMPT.format(
            repo_profile=repo_profile or '(no repo profile available)',
            error_context=json.dumps(error_context, indent=2),
        )
        try:
            raw = await self.ollama.generate(
                self.settings.llm_model, prompt, format='json', options={'num_predict': 300}
            )
            result = parse_json_response(raw)
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
