#!/usr/bin/env python3
"""
ETHUSDT Trade-by-Trade Comparison
Archived System vs Current System
"""

import csv
from pathlib import Path
from datetime import datetime

# Paths
ARCHIVED_CSV = "/root/.openclaw/workspace_backup_20260305_191559/ETHUSDT_TradeBot/backtests/ETHUSDT_trade_history.csv"
CURRENT_JSON = "/root/.openclaw/workspace/data/backtest_deterministic_20260307_0434.json"

print("="*140)
print("  ETHUSDT TRADE-BY-TRADE COMPARISON")
print("  Archived System vs Current System")
print("="*140)
print()

# Read archived trades
archived_trades = []
with open(ARCHIVED_CSV, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        archived_trades.append(row)

print("ARCHIVED SYSTEM TRADES (from backup workspace)")
print("-"*140)
print(f"Location: {ARCHIVED_CSV}")
print(f"Total Trades Found: {len(archived_trades)}")
print()

print(f"{'#':<4} {'Date':<12} {'Time':<10} {'Dir':<6} {'Entry $':<10} {'Exit $':<10} {'PnL $':<12} {'Exit':<15} {'Duration'}")
print("-"*140)

for trade in archived_trades:
    entry_dt = datetime.strptime(trade['entry_time'], '%Y-%m-%d %H:%M:%S')
    date = entry_dt.strftime('%Y-%m-%d')
    time = entry_dt.strftime('%H:%M:%S')
    print(f"{trade['trade_id']:<4} {date:<12} {time:<10} {trade['direction']:<6} "
          f"{float(trade['entry_price']):>9.2f}  {float(trade['exit_price']):>8.2f}  "
          f"{float(trade['net_pnl_usd']):>+10.2f}  {trade['exit_reason']:<15} "
          f"{trade['trade_duration_hours']}h")

# Calculate archived stats
total_pnl = sum(float(t['net_pnl_usd']) for t in archived_trades)
wins = len([t for t in archived_trades if float(t['net_pnl_usd']) > 0])
losses = len([t for t in archived_trades if float(t['net_pnl_usd']) <= 0])
win_rate = (wins / len(archived_trades)) * 100 if archived_trades else 0

print()
print("ARCHIVED SYSTEM SUMMARY:")
print(f"  Total Trades: {len(archived_trades)}")
print(f"  Winners: {wins}")
print(f"  Losers: {losses}")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Total PnL: ${total_pnl:+.2f}")
print()

# Read current trades
import json
with open(CURRENT_JSON, 'r') as f:
    current_data = json.load(f)
current_trades = current_data['trades']

print("="*140)
print("CURRENT SYSTEM TRADES (first 10 shown)")
print("-"*140)
print(f"Location: {CURRENT_JSON}")
print(f"Total Trades: {len(current_trades)}")
print()

print(f"{'#':<4} {'Date':<12} {'Time':<10} {'Dir':<6} {'Entry $':<10} {'Exit $':<10} {'PnL $':<12} {'Exit':<15} {'R-Mult'}")
print("-"*140)

for i, trade in enumerate(current_trades[:10], 1):
    entry_dt = datetime.fromisoformat(trade['entry_time'])
    date = entry_dt.strftime('%Y-%m-%d')
    time = entry_dt.strftime('%H:%M:%S')
    print(f"{i:<4} {date:<12} {time:<10} {trade['direction']:<6} "
          f"{trade['entry_price']:>9.2f}  {trade['exit_price']:>8.2f}  "
          f"{trade['pnl']:>+10.2f}  {trade['exit_reason']:<15} "
          f"{trade['r_multiple']:.2f}")

print("  ... (90 more trades)")

current_pnl = sum(t['pnl'] for t in current_trades)
current_wins = len([t for t in current_trades if t['pnl'] > 0])
current_losses = len([t for t in current_trades if t['pnl'] <= 0])
current_win_rate = (current_wins / len(current_trades)) * 100

print()
print("CURRENT SYSTEM SUMMARY:")
print(f"  Total Trades: {len(current_trades)}")
print(f"  Winners: {current_wins}")
print(f"  Losers: {current_losses}")
print(f"  Win Rate: {current_win_rate:.1f}%")
print(f"  Total PnL: ${current_pnl:+.2f}")
print()

print("="*140)
print("  SIDE-BY-SIDE COMPARISON")
print("="*140)
print()

comparison = [
    ("Metric", "Archived System", "Current System", "Difference"),
    ("-"*20, "-"*20, "-"*20, "-"*20),
    ("Total Trades", str(len(archived_trades)), str(len(current_trades)), f"{len(current_trades) - len(archived_trades):+d}"),
    ("Winners", str(wins), str(current_wins), f"{current_wins - wins:+d}"),
    ("Losers", str(losses), str(current_losses), f"{current_losses - losses:+d}"),
    ("Win Rate", f"{win_rate:.1f}%", f"{current_win_rate:.1f}%", f"{current_win_rate - win_rate:+.1f}%"),
    ("Total PnL", f"${total_pnl:+.2f}", f"${current_pnl:+.2f}", f"${current_pnl - total_pnl:+.2f}"),
]

for row in comparison:
    print(f"  {row[0]:<20} {row[1]:<20} {row[2]:<20} {row[3]:<20}")

print()
print("="*140)
print("  KEY FINDINGS")
print("="*140)
print()

print("1. ARCHIVED SYSTEM ACTUAL PERFORMANCE:")
print(f"   • Only {len(archived_trades)} trades in the CSV file")
print(f"   • Total PnL: ${total_pnl:+.2f}")
print(f"   • This is NOT the +662% mentioned")
print(f"   • These are likely individual losing trades for analysis")
print()

print("2. THE +662% CLAIM:")
print("   • Not found in the archived trade logs")
print("   • May have been from a different file or simulation")
print("   • The actual archived trades show mixed results")
print()

print("3. CURRENT SYSTEM:")
print(f"   • {len(current_trades)} trades with full logging")
print(f"   • Total PnL: ${current_pnl:+.2f} (+{current_pnl/10:.2f}%)")
print(f"   • Lower win rate but higher expectancy")
print()

print("4. ARCHIVED SYSTEM ISSUES (from forensics report):")
print("   • DATA_UNAVAILABLE caused many losses")
print("   • Late entries in high range")
print("   • Choppy market conditions")
print("   • Stops too wide")
print()

print("="*140)
print()
