#!/bin/bash
# Update Weekly ETHUSDT Data - INCREMENTAL VERSION

echo "[$(date)] Starting weekly update..."

# 1. Fetch new weekly candles
cd /root/.openclaw/workspace
python3 scripts/fetch_1w_ethusdt.py

# 2. Update indicators incrementally
echo "[$(date)] Updating indicators incrementally..."
python3 scripts/incremental_indicator_update.py 1w

# 3. Run analysis
echo "[$(date)] Running analysis..."
python3 scripts/analyze_1w.py

echo "[$(date)] Weekly update complete!"
