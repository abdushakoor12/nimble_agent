"""Test suite for the AI Coding Agent project.

This package contains all tests for the AI Coding Agent, including:
- API authentication tests
- CLI tests
- End-to-end tests
- Toolkit unit tests
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
