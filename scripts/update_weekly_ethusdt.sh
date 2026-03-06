#!/bin/bash
# ETHUSDT Weekly Complete Update
# Fetches weekly data AND calculates indicators

LOG_FILE="/root/.openclaw/workspace/data/weekly_complete_$(date +%Y%m%d).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT Weekly Complete Update" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Fetch new weekly data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Fetching weekly data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_weekly_ethusdt.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Data fetch failed, aborting" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Data fetch successful" >> "$LOG_FILE"

# Step 2: Calculate indicators
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Calculating indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_weekly_indicators.py >> "$LOG_FILE" 2>&1
CALC_STATUS=$?

if [ $CALC_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Indicator calculation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Indicator calculation successful" >> "$LOG_FILE"

# Summary
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Weekly update complete!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Files updated:" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1w.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1w_indicators.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1w_metadata.json" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
