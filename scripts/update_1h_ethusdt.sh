#!/bin/bash
# Update 1H ETHUSDT Data - INCREMENTAL VERSION

echo "[$(date)] Starting 1h update..."

# 1. Fetch new 1h candles
cd /root/.openclaw/workspace
python3 scripts/fetch_1h_ethusdt.py

# 2. Update indicators incrementally
echo "[$(date)] Updating indicators incrementally..."
python3 scripts/incremental_indicator_update.py 1h

# 3. Run analysis
echo "[$(date)] Running analysis..."
python3 scripts/analyze_1h.py

echo "[$(date)] 1H update complete!"
