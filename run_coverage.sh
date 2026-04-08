#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

coverage erase

# ETL/unit tests
coverage run -m unittest discover -s tests -v

# Django API tests
(
  cd backend
  python -m coverage run --append manage.py test -v 2
)

coverage report

