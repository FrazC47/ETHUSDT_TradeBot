#!/bin/bash
# Pause reports temporarily
# Create this file to pause, remove to resume

PAUSE_FILE="/root/.openclaw/workspace/ETHUSDT_TradeBot/.PAUSE_REPORTS"

if [ -f "$PAUSE_FILE" ]; then
    echo "Reports are PAUSED. Remove $PAUSE_FILE to resume."
    exit 0
fi

# Run the actual script
exec "$@"
