#!/bin/bash
# ETHUSDT 1-Minute Analysis Update - Trade Spotlight Ultra-Precision
# Triggered on demand when trade setup identified - FINAL PRECISION LAYER

LOG_FILE="/root/.openclaw/workspace/data/1m_analysis_$(date +%Y%m%d_%H%M).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT 1-Minute Trade Spotlight Ultra-Precision" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Fetch 1m data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Fetching 1m data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_1m_ethusdt.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Data fetch failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Data fetch successful" >> "$LOG_FILE"

# Step 2: Calculate indicators
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Calculating ultra-precision indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_1m_indicators.py >> "$LOG_FILE" 2>&1
CALC_STATUS=$?

if [ $CALC_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Indicator calculation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Indicator calculation successful" >> "$LOG_FILE"

# Step 3: Generate analysis (with 5m + 15m + 1h context)
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Generating Ultra-Precision analysis..." >> "$LOG_FILE"
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
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 1m Ultra-Precision analysis complete!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Files updated:" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1m.csv" >> "$LOG_FILE"
echo "  - data/ETHUSDT_1m_indicators.csv" >> "$LOG_FILE"
echo "  - data/analysis/1m_current.json" >> "$LOG_FILE"
echo "  - data/analysis/1m_log.jsonl" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
