#!/bin/bash

# Create and activate virtual environment if it doesn't exist
VENV_PATH="/workspaces/nimble_agent/venv"
if [[ ! -d "$VENV_PATH" ]]; then
    echo "Creating virtual environment at $VENV_PATH"
    python -m virtualenv "$VENV_PATH"
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Create a symlink to this bashrc in the home directory for convenience
if [[ ! -f ~/.bashrc_python_env ]]; then
    ln -s "$(pwd)/.devcontainer/bashrc.sh" ~/.bashrc_python_env
    echo "source ~/.bashrc_python_env" >> ~/.bashrc
fi