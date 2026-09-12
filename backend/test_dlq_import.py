from common.celery import DLQTask
from config.celery import app

print('app.Task:', app.Task)
print('DLQTask:', DLQTask)
print('Is subclass:', issubclass(app.Task, DLQTask))

# Test dlq functions import
print('DLQ functions imported OK')
