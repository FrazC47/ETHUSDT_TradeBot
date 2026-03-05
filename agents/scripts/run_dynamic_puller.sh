#!/bin/bash
# ETHUSDT Dynamic Data Puller
# Runs every minute to keep data fresh

export PYTHONPATH=/root/.openclaw/workspace/ETHUSDT_TradeBot:$PYTHONPATH

LOG_FILE="/root/.openclaw/workspace/ETHUSDT_TradeBot/agents/logs/dynamic_puller_$(date +\%Y\%m\%d).log"

mkdir -p "$(dirname "$LOG_FILE")"

python3 /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/dynamic_data_puller.py >> "$LOG_FILE" 2>&1
