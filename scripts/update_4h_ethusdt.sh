#!/bin/bash
# ETHUSDT 4-Hour Data and Indicators Update Script
# This script calls the Python script to fetch data and calculate indicators

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/update_4h_ethusdt.py"
DATA_DIR="/root/.openclaw/workspace/data/ethusdt"
VENV_PYTHON="/root/.openclaw/workspace/venv/bin/python3"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Run the Python script with venv
"$VENV_PYTHON" "$PYTHON_SCRIPT"
