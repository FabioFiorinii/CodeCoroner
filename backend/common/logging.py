import json
import logging
from datetime import UTC, datetime

SKIPPED_ATTRS = {
    'name',
    'msg',
    'args',
    'levelname',
    'levelno',
    'pathname',
    'filename',
    'module',
    'exc_info',
    'exc_text',
    'stack_info',
    'lineno',
    'funcName',
    'created',
    'msecs',
    'relativeCreated',
    'thread',
    'threadName',
    'processName',
    'process',
    'message',
    'asctime',
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'ts': datetime.now(UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith('_') or key in SKIPPED_ATTRS:
                continue
            payload[key] = value
        return json.dumps(payload, default=str)
