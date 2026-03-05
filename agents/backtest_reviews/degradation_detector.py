#!/usr/bin/env python3
"""
Degradation Detector - 6 Hour Review
Detects if strategy performance is degrading
"""

import json
import csv
from pathlib import Path
from datetime import datetime

def degradation_detector():
    """Detect performance degradation"""
    
    print("="*70)
    print("DEGRADATION DETECTOR")
    print("="*70)
    
    # Load trade history
    trades_file = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/backtests/ETHUSDT_trade_history.csv')
    
    if not trades_file.exists():
        print("No trade history available")
        return
    
    trades = []
    with open(trades_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append({
                'pnl': float(row['net_pnl_usd']),
                'result': 'WIN' if float(row['net_pnl_usd']) > 0 else 'LOSS'
            })
    
    if len(trades) < 10:
        print(f"Insufficient data ({len(trades)} trades), need 10+ for analysis")
        return
    
    # Split into first half and second half
    mid = len(trades) // 2
    first_half = trades[:mid]
    second_half = trades[mid:]
    
    # Calculate metrics for each half
    first_wins = len([t for t in first_half if t['result'] == 'WIN'])
    second_wins = len([t for t in second_half if t['result'] == 'WIN'])
    
    first_wr = first_wins / len(first_half) * 100
    second_wr = second_wins / len(second_half) * 100
    
    first_pnl = sum(t['pnl'] for t in first_half)
    second_pnl = sum(t['pnl'] for t in second_half)
    
    print(f"\nFirst Half ({len(first_half)} trades):")
    print(f"  Win Rate: {first_wr:.1f}%")
    print(f"  P&L: ${first_pnl:,.2f}")
    
    print(f"\nSecond Half ({len(second_half)} trades):")
    print(f"  Win Rate: {second_wr:.1f}%")
    print(f"  P&L: ${second_pnl:,.2f}")
    
    # Detect degradation
    wr_drop = first_wr - second_wr
    pnl_drop = first_pnl - second_pnl
    
    print(f"\nChange:")
    print(f"  Win Rate: {wr_drop:+.1f}%")
    print(f"  P&L: ${pnl_drop:,.2f}")
    
    # Alert conditions
    alerts = []
    if wr_drop > 20:
        alerts.append("Win rate dropped significantly")
    if pnl_drop > 200:
        alerts.append("Profitability declining")
    if second_wr < 40:
        alerts.append("Recent win rate below 40%")
    
    if alerts:
        print(f"\n⚠️  DEGRADATION ALERTS:")
        for alert in alerts:
            print(f"  • {alert}")
        
        # Create emergency adjustment flag
        emergency_file = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/agents/backtest_reviews/emergency_adjustment.json')
        emergency_file.parent.mkdir(parents=True, exist_ok=True)
        with open(emergency_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'alerts': alerts,
                'wr_drop': wr_drop,
                'pnl_drop': pnl_drop
            }, f, indent=2)
        print(f"\n🚨 Emergency adjustment flag created")
    else:
        print(f"\n✅ No degradation detected")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    degradation_detector()
