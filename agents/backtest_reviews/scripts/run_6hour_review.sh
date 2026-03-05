#!/bin/bash
# ETHUSDT Backtest Review - Every 6 Hours
# Runs at: 00:00, 06:00, 12:00, 18:00
# Includes both quick check AND comprehensive backtest

cd /root/.openclaw/workspace/ETHUSDT_TradeBot

# Create logs directory
mkdir -p agents/backtest_reviews/logs

LOG_FILE="agents/backtest_reviews/logs/review_$(date +\%Y\%m\%d_\%H).log"

echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"
echo "ETHUSDT 6-Hour Backtest Review - $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Step 1: Quick performance check (recent trades)
echo "[$(date '+%H:%M:%S')] Step 1: Quick performance check..." >> "$LOG_FILE"
python3 agents/backtest_reviews/quick_performance_check.py >> "$LOG_FILE" 2>&1

# Step 2: Comprehensive backtest on ALL historical data
echo "" >> "$LOG_FILE"
echo "[$(date '+%H:%M:%S')] Step 2: COMPREHENSIVE BACKTEST (all historical data)..." >> "$LOG_FILE"
python3 agents/backtest_reviews/comprehensive_backtest.py >> "$LOG_FILE" 2>&1

# Step 3: Check for degradation
echo "" >> "$LOG_FILE"
echo "[$(date '+%H:%M:%S')] Step 3: Checking for degradation..." >> "$LOG_FILE"
python3 agents/backtest_reviews/degradation_detector.py >> "$LOG_FILE" 2>&1

# Step 4: Compare to baseline
echo "" >> "$LOG_FILE"
echo "[$(date '+%H:%M:%S')] Step 4: Comparing to baseline..." >> "$LOG_FILE"
python3 agents/backtest_reviews/baseline_comparison.py >> "$LOG_FILE" 2>&1

# Step 5: Emergency adjustments if needed
if [ -f "agents/backtest_reviews/emergency_adjustment.json" ]; then
    echo "" >> "$LOG_FILE"
    echo "[$(date '+%H:%M:%S')] ⚠️  Emergency adjustment detected!" >> "$LOG_FILE"
    python3 agents/backtest_reviews/apply_emergency_fix.py >> "$LOG_FILE" 2>&1
fi

echo "" >> "$LOG_FILE"
echo "[$(date '+%H:%M:%S')] 6-Hour Review Complete" >> "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"

# Keep only last 30 days of logs
find agents/backtest_reviews/logs -name "review_*.log" -mtime +30 -delete 2>/dev/null

# Sync to GitHub
cd /root/.openclaw/workspace/ETHUSDT_TradeBot
git add backtests/latest_backtest_results.json 2>/dev/null
git commit -m "Backtest review $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || true
