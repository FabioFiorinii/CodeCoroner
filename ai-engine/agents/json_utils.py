import json

_SALVAGE_CANDIDATE_LIMIT = 200


def _try_loads(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def parse_json_response(raw: str) -> dict:
    """Parse an LLM JSON response, salvaging truncated/garbled output.

    Some small models truncate the response mid-string (e.g. when hitting
    ``num_predict``). We fall back to the largest valid JSON prefix ending at
    a closing brace/bracket, and finally to best-effort repairs for common
    truncation artifacts (unterminated string, missing closing brace).
    """
    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[-1]
        if '```' in raw:
            raw = raw.rsplit('```', 1)[0]
    raw = raw.strip()
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    raw = ''.join(c for c in raw if c.isprintable() or c in '\n\r\t ')

    result = _try_loads(raw)
    if result is not None:
        return result

    candidates = [i + 1 for i, ch in enumerate(raw) if ch in '}]']
    for index in reversed(candidates[-_SALVAGE_CANDIDATE_LIMIT:]):
        result = _try_loads(raw[:index])
        if result is not None:
            return result

    for index in reversed(candidates[-_SALVAGE_CANDIDATE_LIMIT:]):
        for suffix in ('"', '"]', '"}', '}', ']'):
            result = _try_loads(raw[:index] + suffix)
            if result is not None:
                return result

    for suffix in ('"', '"}', '"}]', '"}', '}', ']'):
        result = _try_loads(raw + suffix)
        if result is not None:
            return result

    raise ValueError(f'Could not parse model JSON response: {raw[:200]!r}')