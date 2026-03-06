#!/usr/bin/env python3
import json
from pathlib import Path

latest = sorted(Path('/root/.openclaw/workspace/data').glob('backtest_deterministic_*.json'))[-1]

with open(latest) as f:
    data = json.load(f)

trades = data['trades']

print("="*140)
print("  COMPLETE TRADE LOG - CURRENT SYSTEM (All 100 Trades)")
print("="*140)
print()
print(f"Total Trades: {len(trades)}")
print(f"Date Range: {trades[0]['entry_time'][:10]} to {trades[-1]['entry_time'][:10]}")
print()
print(f"{'#':<4} {'Trade ID':<10} {'Date':<12} {'Time':<10} {'Dir':<6} {'Entry $':<9} {'Stop $':<9} {'Target $':<9} {'Exit $':<9} {'PnL $':<11} {'R':<7} {'Exit Reason':<15}")
print("─"*140)

for i, t in enumerate(trades, 1):
    date = t['entry_time'][:10]
    time = t['entry_time'][11:19]
    print(f"{i:<4} {t['trade_id']:<10} {date:<12} {time:<10} {t['direction']:<6} "
          f"{t['entry_price']:>8.0f}  {t['stop_price']:>7.0f}  {t['target_price']:>8.0f}  "
          f"{t['exit_price']:>8.0f}  {t['pnl']:>+9.2f}  {t['r_multiple']:>6.2f}  {t['exit_reason']:<15}")

print()
print("="*140)
