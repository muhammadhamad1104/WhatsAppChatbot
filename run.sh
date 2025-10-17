#!/usr/bin/env bash
export $(grep -v '^#' .env | xargs) 2>/dev/null || true
python -m flask --app app.main run --host=0.0.0.0 --port=8000
