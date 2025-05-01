#!/bin/bash

set -e

if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run script from project root"
    exit 1
fi

echo "🧹 Cleaning development environment..."

if [ -n "$VIRTUAL_ENV" ]; then
    echo "📤 Deactivating virtual environment..."
    deactivate || {
        echo "⚠️ Failed to deactivate virtual environment"
        # Continue anyway as we're removing it
    }
fi

if [ -d "venv" ]; then
    echo "🗑️ Removing virtual environment..."
    rm -rf venv
fi

echo "🗑️ Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

echo "🗑️ Removing coverage files..."
rm -f .coverage
rm -rf htmlcov/

echo "🗑️ Removing pytest cache..."
rm -rf .pytest_cache/
rm -rf ai_coding_agent/tests/.pytest_cache/

echo "🗑️ Removing test workspace..."
rm -rf test_workspace/


echo "🗑️ Removing build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

echo "🗑️ Removing logs and reports..."
rm -rf logs/

echo "✅ Clean complete!"
echo "💡 Run ./scripts/setup.sh to reinstall the development environment" 