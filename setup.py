"""Setup configuration for the AI Coding Agent package."""

from setuptools import find_packages, setup

setup(
    name="ai-coding-agent",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "nimbleagent=ai_coding_agent.cli.commands:cli",
        ],
    },
)
