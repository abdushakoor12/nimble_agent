#!/bin/bash

# Exit on any error
set -e

# Ensure script is run from project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run script from project root"
    exit 1
fi

# Create logs directory
mkdir -p logs/logs logs/reports

# Start logging
exec 1> >(tee -a "logs/logs/ci.log") 2>&1

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env file..."
    export $(cat .env | xargs)
fi

echo "🔍 Running CI checks..."

# Format check
echo "🔎 Checking code formatting with ruff..."
if ! ruff format --check . ; then
    echo "❌ Formatting errors found"
    exit 1
fi
echo "✅ Format check passed"

# Lint check
echo "🔎 Checking for lint errors with ruff..."
if ! ruff check . ; then
    echo "❌ Linting errors found"
    exit 1
fi
echo "✅ Lint check passed"

# Pyright check
echo "🔎 Checking for type errors with pyright..."
if ! pyright --level warning; then
    echo "❌ Type errors found"
    exit 1
fi
echo "✅ Type check passed"

# Set Python environment variables for tests
export PYTHONPATH="."
export PYTEST_ASYNCIO_MODE="auto"
export PYTHONWARNINGS="ignore::RuntimeWarning,ignore::DeprecationWarning"

# Run tests with coverage
echo "🧪 Running tests with coverage..."
if ! coverage run -m pytest -x ai_coding_agent/tests/; then
    echo "❌ Tests failed"
    exit 1
fi

# Generate coverage report
echo "📈 Generating coverage report..."
coverage html

# Check coverage
echo "📊 Checking test coverage..."
if ! coverage report --fail-under=91 | tee logs/reports/coverage.txt; then
    echo "❌ Test coverage below minimum"
    exit 1
fi
echo "✅ Test coverage check passed"

echo "✅ All CI checks passed!" 

