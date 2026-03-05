#!/bin/bash
# ETHUSDT Auto-Implementer
# Deploys validated improvements automatically
# Runs at 6:30 AM daily (after improver)

cd /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/auto_implementer

# Create logs directory
mkdir -p logs

echo "[$(date)] Starting ETHUSDT Auto-Implementer" >> logs/cron.log

# Check for validated suggestions and deploy
python3 auto_implementer_v2.py >> logs/cron.log 2>&1

echo "[$(date)] Auto-implementer cycle complete" >> logs/cron.log
echo "---" >> logs/cron.log
