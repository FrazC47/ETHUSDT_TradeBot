#!/bin/bash
# ETHUSDT 4-Hour Complete Update
# Fetches 4h data, funding rates, AND calculates indicators

LOG_FILE="/root/.openclaw/workspace/data/4h_complete_$(date +%Y%m%d_%H).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT 4-Hour Complete Update" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Fetch funding rate first (needed for indicators)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Fetching funding rates..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_funding_rate.py >> "$LOG_FILE" 2>&1
FUNDING_STATUS=$?

if [ $FUNDING_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Funding rate fetch failed (continuing)" >> "$LOG_FILE"
fi

# Step 2: Fetch new 4h data
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Fetching 4h data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_4h_ethusdt.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Data fetch failed, aborting" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Data fetch successful" >> "$LOG_FILE"

# Step 3: Calculate indicators (includes funding rate)
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Calculating indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_4h_indicators.py >> "$LOG_FILE" 2>&1
CALC_STATUS=$?

if [ $CALC_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Indicator calculation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Indicator calculation successful" >> "$LOG_FILE"

# Summary
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 4h update complete!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Files updated:" >> "$LOG_FILE"
echo "  - data/ETHUSDT_4h.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_4h_indicators.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_funding_rate.csv" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
