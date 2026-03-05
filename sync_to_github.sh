#!/bin/bash
# ETHUSDT TradeBot Sync Script
# Copies latest data and logs to the dedicated repo and pushes to GitHub

echo "═══════════════════════════════════════════════════════════════"
echo "  ETHUSDT TradeBot - Sync to Dedicated Repository"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Destination
DEST_DIR="/root/.openclaw/workspace/ETHUSDT_TradeBot"

echo "Step 1: Syncing agent logs..."
cp $DEST_DIR/agents/logs/*.log $DEST_DIR/agents/logs/ 2>/dev/null
echo "✅ Logs synced"

echo ""
echo "Step 2: Syncing state files..."
cp $DEST_DIR/agents/state/* $DEST_DIR/agents/state/ 2>/dev/null
echo "✅ State synced"

echo ""
echo "Step 3: Committing changes..."
cd $DEST_DIR
git add -A
git commit -m "Sync: Update logs and state - $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

echo ""
echo "Step 4: Pushing to GitHub..."
git push origin main || echo "Push failed - may need authentication"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Sync Complete!"
echo "═══════════════════════════════════════════════════════════════"
