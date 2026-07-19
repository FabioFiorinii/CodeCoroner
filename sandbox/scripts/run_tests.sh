#!/bin/sh
pytest -x --tb=short -q --json-report 2>&1 || true
