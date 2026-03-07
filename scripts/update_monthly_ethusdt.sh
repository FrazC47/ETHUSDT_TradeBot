#!/bin/bash
# Update Monthly ETHUSDT Data - INCREMENTAL VERSION

echo "[$(date)] Starting monthly update..."

# 1. Fetch new monthly candles
cd /root/.openclaw/workspace
python3 scripts/fetch_1m_ethusdt.py

# 2. Update indicators incrementally (only new candles)
echo "[$(date)] Updating indicators incrementally..."
python3 scripts/incremental_indicator_update.py 1M

# 3. Run analysis
echo "[$(date)] Running analysis..."
python3 scripts/analyze_1M.py

echo "[$(date)] Monthly update complete!"
