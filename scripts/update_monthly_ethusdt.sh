#!/bin/bash
# ETHUSDT Monthly Data Update Script
# Runs on 1st of every month to fetch previous month's candle

LOG_FILE="/root/.openclaw/workspace/data/monthly_update_$(date +%Y%m).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting ETHUSDT monthly data update" >> "$LOG_FILE"

# Run the Python fetcher
python3 /root/.openclaw/workspace/scripts/fetch_monthly_ethusdt.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Monthly update successful" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Monthly update failed" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"
