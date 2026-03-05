#!/usr/bin/env python3
"""
Quick Performance Check - 6 Hour Review
Analyzes recent trading performance
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta

def quick_performance_check():
    """Quick analysis of last 6 hours of trading"""
    
    print("="*70)
    print("QUICK PERFORMANCE CHECK")
    print("="*70)
    
    # Load recent trades
    trades_file = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/backtests/ETHUSDT_trade_history.csv')
    
    if not trades_file.exists():
        print("No trade history found")
        return
    
    trades = []
    with open(trades_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append({
                'date': row['entry_time'],
                'pnl': float(row['net_pnl_usd']),
                'result': 'WIN' if float(row['net_pnl_usd']) > 0 else 'LOSS'
            })
    
    if not trades:
        print("No trades recorded yet")
        return
    
    # Calculate metrics
    total_trades = len(trades)
    wins = len([t for t in trades if t['result'] == 'WIN'])
    losses = total_trades - wins
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(t['pnl'] for t in trades)
    avg_trade = total_pnl / total_trades if total_trades > 0 else 0
    
    print(f"\nOverall Performance:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Wins: {wins} | Losses: {losses}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Total P&L: ${total_pnl:,.2f}")
    print(f"  Avg Trade: ${avg_trade:.2f}")
    
    # Recent performance (last 6 trades)
    recent = trades[-6:] if len(trades) >= 6 else trades
    recent_pnl = sum(t['pnl'] for t in recent)
    recent_wins = len([t for t in recent if t['result'] == 'WIN'])
    
    print(f"\nRecent Performance (last {len(recent)} trades):")
    print(f"  P&L: ${recent_pnl:,.2f}")
    print(f"  Wins: {recent_wins}/{len(recent)}")
    
    if recent_wins <= len(recent) * 0.3:  # Less than 30% win rate
        print(f"  ⚠️  WARNING: Low win rate detected")
    elif recent_pnl < -100:
        print(f"  ⚠️  WARNING: Significant recent losses")
    else:
        print(f"  ✅ Recent performance acceptable")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    quick_performance_check()
