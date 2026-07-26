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

EXPOSE 8002

CMD ["uvicorn", "agents.agent_server:app", "--host", "0.0.0.0", "--port", "8002"]
