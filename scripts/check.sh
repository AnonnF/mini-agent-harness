#!/usr/bin/env bash
set -euo pipefail

echo "==> ruff format"
ruff format .

echo "==> ruff check"
ruff check .

echo "==> mypy"
mypy src

echo "==> pytest"
pytest -v

echo "ALL CHECKS PASSED!"