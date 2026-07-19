#!/bin/sh
ruff check . --output-format=json 2>&1 || true
