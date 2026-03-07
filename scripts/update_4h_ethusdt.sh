#!/bin/bash
# Update 4H ETHUSDT Data - INCREMENTAL VERSION

echo "[$(date)] Starting 4h update..."

# 1. Fetch new 4h candles
cd /root/.openclaw/workspace
python3 scripts/fetch_4h_ethusdt.py

# 2. Update indicators incrementally
echo "[$(date)] Updating indicators incrementally..."
python3 scripts/incremental_indicator_update.py 4h

# 3. Run analysis
echo "[$(date)] Running analysis..."
python3 scripts/analyze_4h.py

echo "[$(date)] 4H update complete!"
