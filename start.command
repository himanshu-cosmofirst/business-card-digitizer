#!/bin/bash
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
    .venv/bin/python server.py
else
    python3 server.py
fi
