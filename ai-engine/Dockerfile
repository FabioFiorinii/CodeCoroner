FROM docker.io/python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r agent && useradd -r -g agent agent

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=agent:agent . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

USER agent

CMD ["python", "-m", "agents.agent_server"]
