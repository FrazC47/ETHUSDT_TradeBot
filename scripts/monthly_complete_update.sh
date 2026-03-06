#!/bin/bash
# ETHUSDT Monthly Complete Update
# Fetches new monthly data AND calculates indicators

LOG_FILE="/root/.openclaw/workspace/data/monthly_complete_$(date +%Y%m).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT Monthly Complete Update" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Fetch new monthly data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Fetching monthly data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_monthly_ethusdt.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Data fetch failed, aborting" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Data fetch successful" >> "$LOG_FILE"

# Step 2: Calculate indicators
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Calculating indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_monthly_indicators.py >> "$LOG_FILE" 2>&1
CALC_STATUS=$?

if [ $CALC_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Indicator calculation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Indicator calculation successful" >> "$LOG_FILE"

# Summary
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Generating analysis..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/analyze_1m.py >> "$LOG_FILE" 2>&1
ANALYSIS_STATUS=$?

if [ $ANALYSIS_STATUS -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Analysis generation successful" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Analysis generation had issues" >> "$LOG_FILE"
fi

# Summary
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Monthly update complete!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Files updated:" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1M.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1M_indicators.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1M_metadata.json" >> "$LOG_FILE"
echo "  - data/analysis/1M_current.json" >> "$LOG_FILE"
echo "  - data/analysis/1M_log.jsonl" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
