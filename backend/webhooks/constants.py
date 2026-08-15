WEBHOOK_EVENTS = [
    ('analysis.created', 'Analysis created'),
    ('analysis.completed', 'Analysis completed'),
    ('analysis.failed', 'Analysis failed'),
    ('repository.indexed', 'Repository indexed'),
]

WEBHOOK_EVENT_NAMES = [name for name, _ in WEBHOOK_EVENTS]
