#!/bin/bash

# Exit on any error
set -e

# Ensure script is run from project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run script from project root"
    exit 1
fi

# Ensure virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Run ./scripts/setup.sh first"
        exit 1
    fi
fi

if [ ! -d "test_workspace" ]; then
    mkdir -p test_workspace
fi

# delete all files in test_workspace
rm -rf test_workspace/*

echo "🤖 Running CLI command to build flutter app..."

# Run the Flutter command in the new workspace
echo "🚀 Running test command in workspace..."
if ! python main.py run --workspace-path "test_workspace" --max-iterations 30 "Create a Flutter app with a cool swirling animation. When that's finished, run it in Chrome"; then
    echo "❌ CLI test failed"
    exit 1
fi

echo "✅ CLI test complete!"
