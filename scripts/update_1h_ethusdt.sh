#!/bin/bash
# ETHUSDT 1-Hour Complete Update
# Fetches 1h data, funding rates, OI, L/S ratio, AND calculates indicators + analysis

LOG_FILE="/root/.openclaw/workspace/data/1h_complete_$(date +%Y%m%d_%H).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT 1-Hour Complete Update" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Fetch funding rate
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Fetching funding rates..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_funding_rate.py >> "$LOG_FILE" 2>&1

# Step 2: Fetch Open Interest
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Fetching open interest..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_open_interest.py >> "$LOG_FILE" 2>&1

# Step 3: Fetch Long/Short Ratio
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Fetching long/short ratio..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_long_short_ratio.py >> "$LOG_FILE" 2>&1

# Step 4: Fetch 1h data
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 4: Fetching 1h data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_1h_ethusdt.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Data fetch failed, aborting" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Data fetch successful" >> "$LOG_FILE"

# Step 5: Calculate indicators
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 5: Calculating indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_1h_indicators.py >> "$LOG_FILE" 2>&1
CALC_STATUS=$?

if [ $CALC_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Indicator calculation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Indicator calculation successful" >> "$LOG_FILE"

# Step 6: Generate analysis (with 4h + 1d + 1W context)
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 6: Generating analysis (with 4h + 1d + 1W context)..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/analyze_1h.py >> "$LOG_FILE" 2>&1
ANALYSIS_STATUS=$?

if [ $ANALYSIS_STATUS -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Analysis generation successful" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Analysis generation had issues" >> "$LOG_FILE"
fi

# Summary
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 1h update complete!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Files updated:" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1h.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1h_indicators.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_funding_rate.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_open_interest.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_long_short_ratio.csv" >> "$LOG_FILE"
echo "  - data/analysis/1h_current.json" >> "$LOG_FILE"
echo "  - data/analysis/1h_log.jsonl" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
