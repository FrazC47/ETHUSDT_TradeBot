#!/bin/bash
# ETHUSDT Improver - Daily Analysis
# Runs at 6:00 AM daily

cd /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/improver

# Create logs directory
mkdir -p logs

# Run improvement cycle
echo "[$(date)] Starting ETHUSDT Improvement cycle" >> logs/cron.log

# Analyze recent trades
python3 ethusdt_improver.py >> logs/cron.log 2>&1

# Run backtest on suggestions
if [ -f "validated_suggestion.json" ]; then
    echo "[$(date)] Testing validated suggestion..." >> logs/cron.log
    python3 backtest_runner.py >> logs/cron.log 2>&1
fi

# Track missed opportunities
python3 missed_opportunity_tracker.py >> logs/cron.log 2>&1

echo "[$(date)] ETHUSDT Improvement cycle complete" >> logs/cron.log
echo "---" >> logs/cron.log
