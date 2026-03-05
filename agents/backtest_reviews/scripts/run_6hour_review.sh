#!/bin/bash
# ETHUSDT Backtest Review - Every 6 Hours
# Runs at: 00:00, 06:00, 12:00, 18:00
# Quick performance check and parameter adjustment

cd /root/.openclaw/workspace/ETHUSDT_TradeBot

# Create logs directory
mkdir -p agents/backtest_reviews/logs

LOG_FILE="agents/backtest_reviews/logs/review_$(date +\%Y\%m\%d_\%H).log"

echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"
echo "ETHUSDT 6-Hour Backtest Review - $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Step 1: Analyze recent trades
echo "[$(date '+%H:%M:%S')] Step 1: Analyzing recent trades..." >> "$LOG_FILE"
python3 agents/backtest_reviews/quick_performance_check.py >> "$LOG_FILE" 2>&1

# Step 2: Check for performance degradation
echo "[$(date '+%H:%M:%S')] Step 2: Checking for degradation..." >> "$LOG_FILE"
python3 agents/backtest_reviews/degradation_detector.py >> "$LOG_FILE" 2>&1

# Step 3: Quick backtest with current parameters
echo "[$(date '+%H:%M:%S')] Step 3: Running quick backtest..." >> "$LOG_FILE"
python3 agents/backtest_reviews/quick_backtest.py >> "$LOG_FILE" 2>&1

# Step 4: Compare to baseline
echo "[$(date '+%H:%M:%S')] Step 4: Comparing to baseline..." >> "$LOG_FILE"
python3 agents/backtest_reviews/baseline_comparison.py >> "$LOG_FILE" 2>&1

# Step 5: Emergency adjustments if needed
if [ -f "agents/backtest_reviews/emergency_adjustment.json" ]; then
    echo "[$(date '+%H:%M:%S')] ⚠️  Emergency adjustment detected!" >> "$LOG_FILE"
    python3 agents/backtest_reviews/apply_emergency_fix.py >> "$LOG_FILE" 2>&1
fi

echo "" >> "$LOG_FILE"
echo "[$(date '+%H:%M:%S')] 6-Hour Review Complete" >> "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"

# Keep only last 30 days of logs
find agents/backtest_reviews/logs -name "review_*.log" -mtime +30 -delete 2>/dev/null
