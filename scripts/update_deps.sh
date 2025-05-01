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

echo "🔍 Checking for outdated packages..."
pip list --outdated

echo "📦 Installing latest versions..."

# Update main requirements
echo "Updating requirements.txt..."
pip install -U click langchain langchain-core langchain-community langchain-openai openai python-dotenv
pip freeze | grep -E "click==|langchain==|langchain-core==|langchain-community==|langchain-openai==|openai==|python-dotenv==" > ai_coding_agent/core/requirements.txt


# Update test requirements
echo "Updating tests/requirements.txt..."
pip install -U pytest pytest-asyncio pytest-timeout coverage
pip freeze | grep -E "pytest==|pytest-asyncio==|pytest-timeout==|coverage==" > tests/requirements.txt

echo "✅ All dependencies updated to latest versions!"
echo "💡 Run ./scripts/clean.sh && ./scripts/setup.sh to apply the changes" 