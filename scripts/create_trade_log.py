#!/usr/bin/env python3
"""
Create trade log CSV with trade ID, timestamp, and PnL
Simple format for easy analysis
"""

import json
import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("/root/.openclaw/workspace/data")
OUTPUT_FILE = DATA_DIR / "trade_pnl_log.csv"

def create_trade_log():
    """Create simple trade log with ID, timestamp, and PnL"""
    
    # Load backtest results
    latest = sorted(DATA_DIR.glob('backtest_deterministic_*.json'))[-1]
    
    with open(latest) as f:
        data = json.load(f)
    
    trades = data['trades']
    
    # Create CSV
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Trade #', 'Trade ID', 'Entry Date', 'Entry Time', 'Direction', 'PnL ($)', 'R-Multiple', 'Exit Reason'])
        
        # Data rows
        for i, trade in enumerate(trades, 1):
            entry_dt = datetime.fromisoformat(trade['entry_time'])
            date = entry_dt.strftime('%Y-%m-%d')
            time = entry_dt.strftime('%H:%M:%S')
            
            writer.writerow([
                i,
                trade['trade_id'],
                date,
                time,
                trade['direction'],
                f"{trade['pnl']:.2f}",
                f"{trade['r_multiple']:.2f}",
                trade['exit_reason']
            ])
    
    print(f"✅ Trade log created: {OUTPUT_FILE}")
    print()
    
    # Display the data
    print("="*100)
    print("  TRADE PnL LOG")
    print("="*100)
    print()
    print(f"{'#':<6} {'Trade ID':<12} {'Date':<12} {'Time':<10} {'Dir':<6} {'PnL ($)':<12} {'R':<8} {'Exit':<15}")
    print("-"*100)
    
    for i, trade in enumerate(trades, 1):
        entry_dt = datetime.fromisoformat(trade['entry_time'])
        date = entry_dt.strftime('%Y-%m-%d')
        time = entry_dt.strftime('%H:%M:%S')
        pnl = trade['pnl']
        pnl_str = f"{pnl:+.2f}"
        
        print(f"{i:<6} {trade['trade_id']:<12} {date:<12} {time:<10} "
              f"{trade['direction']:<6} {pnl_str:<12} {trade['r_multiple']:<8.2f} {trade['exit_reason']:<15}")
    
    print("-"*100)
    
    # Summary
    total_pnl = sum(t['pnl'] for t in trades)
    wins = len([t for t in trades if t['pnl'] > 0])
    losses = len([t for t in trades if t['pnl'] <= 0])
    
    print(f"\nSUMMARY:")
    print(f"  Total Trades: {len(trades)}")
    print(f"  Winners: {wins}")
    print(f"  Losers: {losses}")
    print(f"  Total PnL: ${total_pnl:+.2f}")
    print()
    print(f"File saved to: {OUTPUT_FILE}")
    print()
    print("You can open this CSV in Excel or any spreadsheet program.")

if __name__ == "__main__":
    create_trade_log()
