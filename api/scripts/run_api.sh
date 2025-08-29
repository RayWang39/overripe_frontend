#!/bin/bash

# IYP Method Chain Translation API Startup Script

echo "🔄 Starting IYP Method Chain Translation API..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment. Consider activating one."
    echo "   Run: pyenv activate overripe"
fi

# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$API_DIR")"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 API directory: $API_DIR"

# Install API dependencies if needed
if [ ! -f "$API_DIR/requirements.txt" ]; then
    echo "❌ Error: API requirements.txt not found"
    exit 1
fi

if [ ! -d "$API_DIR/__pycache__" ]; then
    echo "📦 Installing API dependencies..."
    pip install -r "$API_DIR/requirements.txt"
fi

# Check if core iyp_query library is available
if [ ! -d "$PROJECT_ROOT/iyp_query" ]; then
    echo "❌ Error: iyp_query library not found at $PROJECT_ROOT/iyp_query"
    echo "   Make sure the iyp_query library is in the project root"
    exit 1
fi

# Start the API server
echo "🚀 Starting FastAPI server..."
echo "   API will be available at: http://localhost:8001"
echo "   Test interface at: http://localhost:8001"
echo "   API docs at: http://localhost:8001/docs"
echo "   Demo script: python demos/method_chain_demo.py"
echo ""
echo "Press Ctrl+C to stop the server"

# Set PYTHONPATH to include project root and start server
cd "$API_DIR" && PYTHONPATH="$PROJECT_ROOT" python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload