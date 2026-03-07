#!/bin/bash
# Update Daily ETHUSDT Data - INCREMENTAL VERSION

echo "[$(date)] Starting daily update..."

# 1. Fetch new daily candles
cd /root/.openclaw/workspace
python3 scripts/fetch_1d_ethusdt.py

# 2. Update indicators incrementally
echo "[$(date)] Updating indicators incrementally..."
python3 scripts/incremental_indicator_update.py 1d

# 3. Run analysis
echo "[$(date)] Running analysis..."
python3 scripts/analyze_1d.py

echo "[$(date)] Daily update complete!"
