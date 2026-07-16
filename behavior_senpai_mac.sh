#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Behavior Senpai for macOS ==="
PYTHON311="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"

if [ ! -x "$PYTHON311" ]; then
    echo "Python 3.11 is not installed. Please install it from https://www.python.org/downloads/macos/."
    exit 1
fi

# install uv
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "uv is already installed."
fi

# add PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

ZSHRC="$HOME/.zshrc"
if [ -f "$ZSHRC" ]; then
    if ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$ZSHRC"; then
        printf '%s\n' 'export PATH="$HOME/.local/bin:$PATH"' >> "$ZSHRC"
        echo "Updated $ZSHRC to include ~/.local/bin in PATH."
    else
        echo "~/.local/bin is already in PATH in $ZSHRC."
    fi
 fi

# check uv and PATH
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not found in PATH. Please ensure that ~/.local/bin is in your PATH."
    exit 1
fi

# setup Behavior Senpai
echo "Setting up Behavior Senpai..."
if [ ! -d "venv" ]; then
    uv python pin "$PYTHON311"
    uv sync
fi

uv run python src/launcher.py
