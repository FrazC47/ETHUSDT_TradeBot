#!/bin/bash
# ETHUSDT TradeBot Sync Script
# Copies latest data and logs to the dedicated repo and pushes to GitHub

echo "═══════════════════════════════════════════════════════════════"
echo "  ETHUSDT TradeBot - Sync to Dedicated Repository"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Source and destination
SOURCE_DATA="/root/.openclaw/workspace/data/binance/ETHUSDT"
SOURCE_INDICATORS="/root/.openclaw/workspace/data/indicators/ETHUSDT_indicators.json"
DEST_DIR="/root/.openclaw/workspace/ETHUSDT_TradeBot"

echo "Step 1: Syncing data files..."
cp -r $SOURCE_DATA/* $DEST_DIR/data/ 2>/dev/null
cp $SOURCE_INDICATORS $DEST_DIR/data/ 2>/dev/null
echo "✅ Data synced"

echo ""
echo "Step 2: Syncing agent logs..."
cp /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/logs/* $DEST_DIR/agents/logs/ 2>/dev/null
echo "✅ Logs synced"

echo ""
echo "Step 3: Syncing state files..."
cp /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/state/* $DEST_DIR/agents/state/ 2>/dev/null
echo "✅ State synced"

echo ""
echo "Step 4: Committing changes..."
cd $DEST_DIR
git add -A
git commit -m "Sync: Update data, logs, and state - $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

echo ""
echo "Step 5: Pushing to GitHub..."
git push origin main || echo "Push failed - may need authentication"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Sync Complete!"
echo "═══════════════════════════════════════════════════════════════"
