#!/usr/bin/env python3
"""Main entry point for Nimble Agent CLI."""

from ai_coding_agent.cli.commands import cli
from ai_coding_agent.core.logger import setup_logging

if __name__ == "__main__":
    setup_logging()
    cli()
