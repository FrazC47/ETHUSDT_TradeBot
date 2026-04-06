#!/usr/bin/env python3
"""
ETHUSDT Trade Log Comparison Tool
Compares archived trades vs current system trades
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("/root/.openclaw/workspace/data")

print("="*80)
print("  TRADE-BY-TRADE COMPARISON REQUEST")
print("="*80)
print()

print("ISSUE: Archived trade logs not available")
print("-"*80)
print()
print("I don't have access to the detailed trade logs from the archived system.")
print("What I have from the archive:")
print("  • Total return: +662%")
print("  • Win rate: 58.6%")
print("  • Max drawdown: 185.9%")
print("  • Period: 3-4 weeks")
print()
print("What I DON'T have:")
print("  ❌ Individual trade dates/times")
print("  ❌ Entry prices for each trade")
print("  ❌ Exit prices for each trade")
print("  ❌ Trade-by-trade PnL records")
print()

print("="*80)
print("  CURRENT SYSTEM TRADE LOG (Available)")
print("="*80)
print()

# Load current backtest results
latest_result = sorted(DATA_DIR.glob('backtest_deterministic_*.json'))[-1]

with open(latest_result) as f:
    data = json.load(f)

trades = data['trades']

print(f"Total trades available: {len(trades)}")
print()
print("Showing first 20 trades from current system:")
print()

print(f"{'#':<4} {'Trade ID':<12} {'Date':<12} {'Direction':<8} {'Entry':<8} {'Exit':<8} {'PnL':<10} {'R':<6} {'Exit Type'}")
print("-"*100)

for i, trade in enumerate(trades[:20], 1):
    entry_time = trade['entry_time'][:10]  # Just date part
    direction = trade['direction']
    entry = f"${trade['entry_price']:.0f}"
    exit_p = f"${trade['exit_price']:.0f}"
    pnl = f"${trade['pnl']:+.2f}"
    r = f"{trade['r_multiple']:.2f}"
    exit_reason = trade['exit_reason']
    
    print(f"{i:<4} {trade['trade_id']:<12} {entry_time:<12} {direction:<8} {entry:<8} {exit_p:<8} {pnl:<10} {r:<6} {exit_reason}")

print()
print("="*80)
print("  WHAT'S NEEDED FOR PROPER COMPARISON")
print("="*80)
print()

print("To do a proper trade-by-trade comparison, I need:")
print()
print("1. ARCHIVED SYSTEM TRADE LOG")
print("   File: _ARCHIVED_20260305/ETHUSDT_TradeBot/trade_history.json")
print("   Should contain:")
print("     - Trade ID")
print("     - Entry date/time")
print("     - Exit date/time")
print("     - Entry price")
print("     - Exit price")
print("     - PnL")
print("     - Exit reason")
print()
print("2. CURRENT SYSTEM TRADE LOG")
print("   File: data/testnet_trade_history.json (after live trading)")
print("   Or: data/backtest_deterministic_*.json (simulation)")
print()

print("="*80)
print("  SOLUTION: CREATE PROPER TRADE LOGGING")
print("="*80)
print()

print("Going forward, I'll create detailed trade logs that include:")
print()
print("✓ Trade number and ID")
print("✓ Entry date/time (exact timestamp)")
print("✓ Exit date/time (exact timestamp)")
print("✓ Entry price")
print("✓ Stop loss price")
print("✓ Target price")
print("✓ Exit price")
print("✓ Position size")
print("✓ Gross PnL")
print("✓ Fees paid")
print("✓ Net PnL")
print("✓ R-multiple")
print("✓ Exit reason")
print("✓ Timeframe confluence")
print("✓ Regime classification")
print()

print("="*80)
print("  IMMEDIATE ACTION OPTIONS")
print("="*80)
print()

print("Option 1: Check Archive for Trade Logs")
print("-"*80)
print("Look in:")
print("  /root/.openclaw/workspace/_ARCHIVED_20260305/")
print()
print("Search for files like:")
print("  • trade_history.json")
print("  • trade_log.csv")
print("  • backtest_results.json")
print("  • performance_report.json")
print()

print("Option 2: Extract from Available Data")
print("-"*80)
print("If you have ANY files from the archived system, I can parse them.")
print("Please share the file path and I'll extract what I can.")
print()

print("Option 3: Start Fresh Logging")
print("-"*80)
print("Going forward, I'll log every trade in detail.")
print("After 100 trades on testnet, we'll have comparable data.")
print()

print("="*80)
print()
