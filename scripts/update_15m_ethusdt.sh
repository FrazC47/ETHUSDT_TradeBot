#!/bin/bash
# Update 15M ETHUSDT Data - INCREMENTAL VERSION

echo "[$(date)] Starting 15m update..."

# 1. Fetch new 15m candles
cd /root/.openclaw/workspace
python3 scripts/fetch_15m_ethusdt.py

# 2. Update indicators incrementally
echo "[$(date)] Updating indicators incrementally..."
python3 scripts/incremental_indicator_update.py 15m

# 3. Run analysis
echo "[$(date)] Running analysis..."
python3 scripts/analyze_15m.py

echo "[$(date)] 15M update complete!"
