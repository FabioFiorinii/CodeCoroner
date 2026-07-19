FROM docker.io/python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs \
    npm \
    golang-go \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    ruff \
    mypy

RUN useradd -r -s /bin/false sandbox
USER sandbox
WORKDIR /workspace

COPY --chown=sandbox:sandbox scripts/ /usr/local/bin/
