#!/bin/bash

# Show Python version and environment info
echo "Python environment information:"
echo "----------------------------"
python --version
pip --version
echo

# Check if pytest is installed and working
echo "Checking pytest installation:"
echo "----------------------------"
if command -v pytest &> /dev/null; then
    pytest --version
    echo "pytest is installed ✅"
else
    echo "pytest is NOT installed ❌"
fi

if python -c "import pytest_asyncio" &> /dev/null; then
    echo "pytest-asyncio is installed ✅"
    python -c "import pytest_asyncio; print(f'Version: {pytest_asyncio.__version__}')"
else
    echo "pytest-asyncio is NOT installed ❌"
fi

echo
echo "Installed Python packages:"
echo "----------------------------"
pip list | grep -E "pytest|asyncio"
echo

echo "Environment Variables:"
echo "----------------------------"
echo "PYTHONPATH: $PYTHONPATH"
echo "PYTEST_ASYNCIO_MODE: $PYTEST_ASYNCIO_MODE"
echo "PYTHONWARNINGS: $PYTHONWARNINGS"
echo

# Print info about directory structure
echo "Test directory structure:"
echo "----------------------------"
if [ -d "ai_coding_agent/tests" ]; then
    ls -la ai_coding_agent/tests
else
    echo "Tests directory not found!"
fi 