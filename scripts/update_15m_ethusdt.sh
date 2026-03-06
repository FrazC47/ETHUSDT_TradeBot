#!/bin/bash
# ETHUSDT 15-Minute Complete Update

LOG_FILE="/root/.openclaw/workspace/data/15m_complete_$(date +%Y%m%d_%H).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT 15-Minute Update" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] =======================================" >> "$LOG_FILE"

# Step 1: Funding rate
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Funding rates..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_funding_rate.py >> "$LOG_FILE" 2>&1

# Step 2: Open Interest
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Open Interest..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_open_interest.py >> "$LOG_FILE" 2>&1

# Step 3: Long/Short Ratio
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: L/S Ratio..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_long_short_ratio.py >> "$LOG_FILE" 2>&1

# Step 4: 15m candles
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 4: 15m data..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/fetch_15m_ethusdt.py >> "$LOG_FILE" 2>&1

# Step 5: Calculate indicators
echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 5: Indicators..." >> "$LOG_FILE"
python3 /root/.openclaw/workspace/scripts/calculate_15m_indicators.py >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 15m update complete!" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
