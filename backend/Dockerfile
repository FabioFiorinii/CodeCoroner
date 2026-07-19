FROM docker.io/python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r django && useradd -r -g django django

COPY --chown=django:django . .

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

USER django

CMD ["python", "-m", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
