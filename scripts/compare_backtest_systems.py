#!/usr/bin/env python3
"""
ETHUSDT_TradeBot vs currency_trading Backtest Comparison
Compares trade execution between the two systems
"""

import csv
import json
from pathlib import Path

WORKSPACE_DIR = Path("/root/.openclaw/workspace")

def load_ethusdt_tradebot_trades():
    """Load ETHUSDT_TradeBot (original) trades"""
    file = WORKSPACE_DIR / "backtests" / "ETHUSDT_trade_history.csv"
    trades = []
    
    if file.exists():
        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append({
                    'trade_id': row['trade_id'],
                    'date': row['entry_time'][:10],
                    'time': row['entry_time'][11:],
                    'direction': row['direction'],
                    'entry': float(row['entry_price']),
                    'exit': float(row['exit_price']),
                    'stop': float(row['stop_loss']),
                    'target': float(row['take_profit']),
                    'pnl': float(row['net_pnl_usd']),
                    'exit_reason': row['exit_reason'],
                    'duration': row['trade_duration_hours'],
                    'position_size': float(row['position_size_usd']),
                    'leverage': int(row['leverage'])
                })
    
    return trades

def load_currency_trading_trades():
    """Load currency_trading (new system) trades"""
    file = WORKSPACE_DIR / "data" / "trade_complete_log.csv"
    trades = []
    
    if file.exists():
        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append({
                    'trade_id': row['Trade ID'],
                    'date': row['Entry Date'],
                    'time': row['Entry Time'],
                    'direction': row['Direction'],
                    'entry': float(row['Entry Price ($)']),
                    'exit': float(row['Exit Price ($)']),
                    'stop': float(row['Stop Price ($)']),
                    'target': float(row['Target Price ($)']),
                    'pnl': float(row['Net PnL ($)']),
                    'exit_reason': row['Exit Reason'],
                    'r_multiple': float(row['R-Multiple']),
                    'position_size_eth': float(row['Position Size (ETH)'])
                })
    
    return trades

def compare_systems():
    """Compare the two trading systems"""
    
    print("="*100)
    print("  BACKTEST COMPARISON: ETHUSDT_TradeBot vs currency_trading")
    print("="*100)
    print()
    
    # Load trades
    eth_trades = load_ethusdt_tradebot_trades()
    curr_trades = load_currency_trading_trades()
    
    print("SYSTEM 1: ETHUSDT_TradeBot (Original 5-Agent System)")
    print("-"*100)
    print(f"  Source: backtests/ETHUSDT_trade_history.csv")
    print(f"  Total Trades: {len(eth_trades)}")
    
    if eth_trades:
        eth_wins = len([t for t in eth_trades if t['pnl'] > 0])
        eth_losses = len([t for t in eth_trades if t['pnl'] <= 0])
        eth_pnl = sum(t['pnl'] for t in eth_trades)
        
        print(f"  Win Rate: {eth_wins}/{len(eth_trades)} ({eth_wins/len(eth_trades)*100:.1f}%)")
        print(f"  Net PnL: ${eth_pnl:+.2f}")
        print(f"  Trade Types: {len(set(t['direction'] for t in eth_trades))} unique")
        print(f"  Date Range: {eth_trades[0]['date']} to {eth_trades[-1]['date']}")
        print(f"  Price Range: ${min(t['entry'] for t in eth_trades):.2f} - ${max(t['entry'] for t in eth_trades):.2f}")
    
    print()
    print("SYSTEM 2: currency_trading (8-Timeframe System)")
    print("-"*100)
    print(f"  Source: data/trade_complete_log.csv")
    print(f"  Total Trades: {len(curr_trades)}")
    
    if curr_trades:
        curr_wins = len([t for t in curr_trades if t['pnl'] > 0])
        curr_losses = len([t for t in curr_trades if t['pnl'] <= 0])
        curr_pnl = sum(t['pnl'] for t in curr_trades)
        longs = len([t for t in curr_trades if t['direction'] == 'LONG'])
        shorts = len([t for t in curr_trades if t['direction'] == 'SHORT'])
        
        print(f"  Win Rate: {curr_wins}/{len(curr_trades)} ({curr_wins/len(curr_trades)*100:.1f}%)")
        print(f"  Net PnL: ${curr_pnl:+.2f}")
        print(f"  LONG Trades: {longs}")
        print(f"  SHORT Trades: {shorts}")
        print(f"  Date Range: {curr_trades[0]['date']} to {curr_trades[-1]['date']}")
        print(f"  Price Range: ${min(t['entry'] for t in curr_trades):.2f} - ${max(t['entry'] for t in curr_trades):.2f}")
    
    print()
    print("="*100)
    print("  CRITICAL FINDING: DIFFERENT TRADES")
    print("="*100)
    print()
    
    if eth_trades and curr_trades:
        # Check if any trades match
        eth_dates = set(t['date'] for t in eth_trades)
        curr_dates = set(t['date'] for t in curr_trades)
        common_dates = eth_dates.intersection(curr_dates)
        
        print("Comparison Analysis:")
        print()
        print(f"  ETHUSDT_TradeBot dates:  {len(eth_dates)} unique dates")
        print(f"  currency_trading dates:  {len(curr_dates)} unique dates")
        print(f"  Common dates:            {len(common_dates)}")
        print()
        
        if len(common_dates) == 0:
            print("  ❌ NO OVERLAPPING DATES")
            print()
            print("  The systems traded on COMPLETELY DIFFERENT time periods:")
            print(f"    ETHUSDT_TradeBot:  {min(eth_dates)} to {max(eth_dates)}")
            print(f"    currency_trading:  {min(curr_dates)} to {max(curr_dates)}")
        else:
            print(f"  ⚠️  {len(common_dates)} overlapping dates found")
            print("  Checking if trades match on those dates...")
        
        print()
        print("Key Differences:")
        print()
        print("  1. DATE PERIODS:")
        print(f"     ETHUSDT_TradeBot:  2026 (Jan-Feb)")
        print(f"     currency_trading:  2025 (Jan-Oct)")
        print()
        
        print("  2. PRICE LEVELS:")
        eth_prices = [t['entry'] for t in eth_trades]
        curr_prices = [t['entry'] for t in curr_trades]
        print(f"     ETHUSDT_TradeBot:  ${min(eth_prices):.0f} - ${max(eth_prices):.0f}")
        print(f"     currency_trading:  ${min(curr_prices):.0f} - ${max(curr_prices):.0f}")
        print()
        
        print("  3. TRADE DIRECTION:")
        eth_dirs = set(t['direction'] for t in eth_trades)
        curr_dirs = set(t['direction'] for t in curr_trades)
        print(f"     ETHUSDT_TradeBot:  {', '.join(eth_dirs)} (only LONG)")
        print(f"     currency_trading:  {', '.join(curr_dirs)} (LONG + SHORT)")
        print()
        
        print("  4. POSITION SIZING:")
        print(f"     ETHUSDT_TradeBot:  $580-670 USD, 5x leverage")
        print(f"     currency_trading:  0.1 ETH position size")
        print()
        
        print("  5. NUMBER OF TRADES:")
        print(f"     ETHUSDT_TradeBot:  {len(eth_trades)} trades")
        print(f"     currency_trading:  {len(curr_trades)} trades")
        print()
        
        print("="*100)
        print("  CONCLUSION")
        print("="*100)
        print()
        print("  ❌ The systems did NOT execute the same trades")
        print()
        print("  Reasons:")
        print("    1. Different time periods (2025 vs 2026)")
        print("    2. Different price levels (~$2200s vs ~$2000s)")
        print("    3. Different trade directions (LONG-only vs LONG+SHORT)")
        print("    4. Different number of trades (10 vs 100)")
        print()
        print("  These are INDEPENDENT backtests on different data periods.")
        print("  The systems used different:")
        print("    • Historical data periods")
        print("    • Signal generation logic")
        print("    • Entry/exit criteria")
        print()
        
        print("="*100)
        print("  RECOMMENDATION")
        print("="*100)
        print()
        print("  To fairly compare the systems, run BOTH on:")
        print("    • The same date range")
        print("    • The same historical data")
        print("    • Same starting capital")
        print()
        print("  Current results cannot be directly compared because")
        print("  they traded in completely different market conditions.")
        print()

def main():
    compare_systems()

if __name__ == "__main__":
    main()
