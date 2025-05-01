#!/bin/bash

set -e

# Create /usr/local/bin if it doesn't exist
if [ ! -d "/usr/local/bin" ]; then
    echo "📁 Creating /usr/local/bin directory..."
    sudo mkdir -p /usr/local/bin
fi

# Create the symlink with sudo
echo "🔗 Creating symlink in /usr/local/bin..."
sudo ln -sf "$NIMBLEAGENT_PATH" "/usr/local/bin/nimbleagent" || {
    echo "❌ Failed to create symlink. Please run 'sudo ln -sf $NIMBLEAGENT_PATH /usr/local/bin/nimbleagent' manually."
    exit 1
}