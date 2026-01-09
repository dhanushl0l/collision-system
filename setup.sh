#!/usr/bin/env bash
set -e 

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
fi

source .venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload