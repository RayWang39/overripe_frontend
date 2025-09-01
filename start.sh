#!/bin/bash

# Railway deployment start script
export PYTHONPATH="/app:$PYTHONPATH"
cd api
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}