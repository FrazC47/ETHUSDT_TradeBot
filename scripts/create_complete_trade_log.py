#!/usr/bin/env python3
"""
Create comprehensive trade log CSV with entry/exit prices
"""

import json
import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("/root/.openclaw/workspace/data")
OUTPUT_FILE = DATA_DIR / "trade_complete_log.csv"

def create_complete_trade_log():
    """Create comprehensive trade log with all price data"""
    
    # Load backtest results
    latest = sorted(DATA_DIR.glob('backtest_deterministic_*.json'))[-1]
    
    with open(latest) as f:
        data = json.load(f)
    
    trades = data['trades']
    config = data['config']
    
    # Create CSV
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header with all price data
        writer.writerow([
            'Trade #', 'Trade ID', 
            'Entry Date', 'Entry Time', 'Exit Date', 'Exit Time',
            'Direction', 
            'Entry Price ($)', 'Stop Price ($)', 'Target Price ($)', 'Exit Price ($)',
            'Position Size (ETH)', 'Gross PnL ($)', 'Fees ($)', 'Net PnL ($)',
            'R-Multiple', 'Exit Reason'
        ])
        
        # Data rows
        for i, trade in enumerate(trades, 1):
            entry_dt = datetime.fromisoformat(trade['entry_time'])
            exit_dt = datetime.fromisoformat(trade['exit_time'])
            
            # Calculate gross PnL and fees
            gross_pnl = trade['pnl'] + trade['fees']
            
            writer.writerow([
                i,
                trade['trade_id'],
                entry_dt.strftime('%Y-%m-%d'),
                entry_dt.strftime('%H:%M:%S'),
                exit_dt.strftime('%Y-%m-%d'),
                exit_dt.strftime('%H:%M:%S'),
                trade['direction'],
                f"{trade['entry_price']:.2f}",
                f"{trade['stop_price']:.2f}",
                f"{trade['target_price']:.2f}",
                f"{trade['exit_price']:.2f}",
                f"{trade['position_size']:.4f}",
                f"{gross_pnl:.2f}",
                f"{trade['fees']:.2f}",
                f"{trade['pnl']:.2f}",
                f"{trade['r_multiple']:.2f}",
                trade['exit_reason']
            ])
    
    print(f"✅ Complete trade log created: {OUTPUT_FILE}")
    print()
    
    # Display summary table
    print("="*140)
    print("  COMPLETE TRADE LOG (with Entry/Exit Prices)")
    print("="*140)
    print()
    print(f"{'#':<5} {'ID':<10} {'Entry Date':<12} {'Entry $':<10} {'Exit $':<10} {'Target $':<10} {'PnL $':<12} {'R':<6} {'Exit':<12}")
    print("-"*140)
    
    for i, trade in enumerate(trades[:20], 1):  # Show first 20
        entry_dt = datetime.fromisoformat(trade['entry_time'])
        date = entry_dt.strftime('%Y-%m-%d')
        print(f"{i:<5} {trade['trade_id']:<10} {date:<12} "
              f"{trade['entry_price']:>9.2f}  {trade['exit_price']:>8.2f}  {trade['target_price']:>8.2f}  "
              f"{trade['pnl']:>+10.2f}  {trade['r_multiple']:<6.2f} {trade['exit_reason']:<12}")
    
    print("  ...")
    print()
    
    # Show last 10
    print(f"{'#':<5} {'ID':<10} {'Entry Date':<12} {'Entry $':<10} {'Exit $':<10} {'Target $':<10} {'PnL $':<12} {'R':<6} {'Exit':<12}")
    print("-"*140)
    for i, trade in enumerate(trades[-10:], len(trades)-9):
        entry_dt = datetime.fromisoformat(trade['entry_time'])
        date = entry_dt.strftime('%Y-%m-%d')
        print(f"{i:<5} {trade['trade_id']:<10} {date:<12} "
              f"{trade['entry_price']:>9.2f}  {trade['exit_price']:>8.2f}  {trade['target_price']:>8.2f}  "
              f"{trade['pnl']:>+10.2f}  {trade['r_multiple']:<6.2f} {trade['exit_reason']:<12}")
    
    print("-"*140)
    
    # Summary
    total_pnl = sum(t['pnl'] for t in trades)
    total_fees = sum(t['fees'] for t in trades)
    wins = len([t for t in trades if t['pnl'] > 0])
    losses = len([t for t in trades if t['pnl'] <= 0])
    
    print(f"\nSUMMARY:")
    print(f"  Total Trades: {len(trades)}")
    print(f"  Winners: {wins}")
    print(f"  Losers: {losses}")
    print(f"  Gross PnL: ${total_pnl + total_fees:+.2f}")
    print(f"  Fees: ${total_fees:.2f}")
    print(f"  Net PnL: ${total_pnl:+.2f}")
    print()
    print(f"File saved to: {OUTPUT_FILE}")
    print()
    print("Columns in CSV:")
    print("  1. Trade #")
    print("  2. Trade ID")
    print("  3-4. Entry Date/Time")
    print("  5-6. Exit Date/Time")
    print("  7. Direction (LONG/SHORT)")
    print("  8. Entry Price ($)")
    print("  9. Stop Price ($)")
    print("  10. Target Price ($)")
    print("  11. Exit Price ($)")
    print("  12. Position Size (ETH)")
    print("  13. Gross PnL ($)")
    print("  14. Fees ($)")
    print("  15. Net PnL ($)")
    print("  16. R-Multiple")
    print("  17. Exit Reason")

if __name__ == "__main__":
    create_complete_trade_log()
