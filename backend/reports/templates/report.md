# Bug Analysis Report

## Summary
{{ analysis.title|default:"Untitled Analysis" }}

**Status**: {{ analysis.status }}
**Created**: {{ analysis.created_at }}
**Repository**: {{ analysis.repository.git_url }}

## Error Context
```
{{ analysis.error_context }}
```

## Bug Localization
{% if localization %}
{% for file in localization.suspicious_files.all %}
### #{{ file.rank }} `{{ file.file_path }}` (Score: {{ file.suspicion_score }})
- Matched lines: {{ file.matched_lines }}
{% endfor %}
{% endif %}

## Root Cause Analysis
{% if root_cause %}
**Root File**: `{{ root_cause.root_file }}`
{% if root_cause.root_line %}**Line**: {{ root_cause.root_line }}{% endif %}
**Confidence**: {{ root_cause.confidence }}

### Cause Chain
{{ root_cause.cause_chain }}

### Reasoning
{{ root_cause.reasoning }}
{% endif %}

## Patch
{% if patch %}
```diff
{{ patch.diff }}
```
{% endif %}
