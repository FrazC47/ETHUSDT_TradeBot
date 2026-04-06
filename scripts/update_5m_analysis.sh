#!/bin/bash
# ETHUSDT 5-Minute Analysis Update - Trade Spotlight
# Triggered on demand when trade setup identified

LOG_FILE="/root/.openclaw/workspace/data/5m_analysis_$(date +%Y%m%d_%H%M).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT 5-Minute Trade Spotlight Analysis" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Fetch 5m data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Fetching 5m data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_5m_ethusdt.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Data fetch failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Data fetch successful" >> "$LOG_FILE"

# Step 2: Calculate indicators
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Calculating precision indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_5m_indicators.py >> "$LOG_FILE" 2>&1
CALC_STATUS=$?

if [ $CALC_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Indicator calculation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Indicator calculation successful" >> "$LOG_FILE"

# Step 3: Generate analysis (with 15m + 1h + 4h context)
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Generating Trade Spotlight analysis..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/analyze_5m.py >> "$LOG_FILE" 2>&1
ANALYSIS_STATUS=$?

if [ $ANALYSIS_STATUS -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Analysis generation successful" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Analysis generation had issues" >> "$LOG_FILE"
fi

# Summary
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 5m Trade Spotlight analysis complete!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Files updated:" >> "$LOG_FILE"
echo "  - data/ETHUSDT_5m.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_5m_indicators.csv" >> "$LOG_FILE"
echo "  - data/analysis/5m_current.json" >> "$LOG_FILE"
echo "  - data/analysis/5m_log.jsonl" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
