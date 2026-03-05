#!/usr/bin/env python3
"""
Comprehensive Backtest - Full Historical Data
Runs backtest on ALL available historical data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

class ComprehensiveBacktest:
    """Full backtest on all historical ETHUSDT data"""
    
    def __init__(self):
        self.data_dir = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/data/raw')
        self.results = {}
        
    def load_data(self, timeframe: str) -> pd.DataFrame:
        """Load historical data for a timeframe"""
        file_path = self.data_dir / f"{timeframe}.csv"
        
        if not file_path.exists():
            return None
        
        df = pd.read_csv(file_path)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # EMA
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        return df
    
    def run_backtest(self, initial_capital: float = 1000) -> dict:
        """Run comprehensive backtest on all data"""
        
        print("="*70)
        print("COMPREHENSIVE BACKTEST - ALL HISTORICAL DATA")
        print("="*70)
        print()
        
        # Load 1h data (primary timeframe)
        df = self.load_data('1h')
        if df is None:
            print("❌ No 1h data found")
            return {}
        
        print(f"📊 Loaded {len(df)} candles of 1h data")
        print(f"   From: {df.index[0]}")
        print(f"   To:   {df.index[-1]}")
        print(f"   Period: {(df.index[-1] - df.index[0]).days} days")
        print()
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Trading simulation
        capital = initial_capital
        trades = []
        position = None
        
        for i in range(30, len(df) - 1):  # Start after enough data for indicators
            row = df.iloc[i]
            
            # Skip if NaN values
            if pd.isna(row['ema_9']) or pd.isna(row['rsi']):
                continue
            
            # Entry conditions
            if position is None:
                # Long setup conditions
                trend_bullish = row['ema_9'] > row['ema_21']
                rsi_ok = 40 < row['rsi'] < 75
                volume_ok = row['volume'] > row['volume'].rolling(20).mean() * 0.6
                
                if trend_bullish and rsi_ok and volume_ok:
                    # Enter long
                    entry_price = row['close']
                    stop_loss = entry_price - row['atr'] * 1.5
                    take_profit = entry_price + row['atr'] * 3.0
                    
                    position = {
                        'entry_time': df.index[i],
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'atr': row['atr']
                    }
            
            # Exit conditions
            else:
                exit_trade = False
                exit_price = None
                exit_reason = None
                
                # Check stop loss
                if row['low'] <= position['stop_loss']:
                    exit_trade = True
                    exit_price = position['stop_loss']
                    exit_reason = 'STOP_LOSS'
                
                # Check take profit
                elif row['high'] >= position['take_profit']:
                    exit_trade = True
                    exit_price = position['take_profit']
                    exit_reason = 'TAKE_PROFIT'
                
                # Close position
                if exit_trade:
                    pnl = (exit_price - position['entry_price']) / position['entry_price']
                    pnl_usd = capital * pnl
                    capital += pnl_usd
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': df.index[i],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl_pct': pnl * 100,
                        'pnl_usd': pnl_usd,
                        'exit_reason': exit_reason,
                        'duration_hours': (df.index[i] - position['entry_time']).total_seconds() / 3600
                    })
                    
                    position = None
        
        # Calculate results
        if not trades:
            print("❌ No trades generated in backtest")
            return {}
        
        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] <= 0]
        
        results = {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': (capital - initial_capital) / initial_capital * 100,
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(trades) * 100,
            'avg_win': sum(t['pnl_usd'] for t in wins) / len(wins) if wins else 0,
            'avg_loss': sum(t['pnl_usd'] for t in losses) / len(losses) if losses else 0,
            'profit_factor': abs(sum(t['pnl_usd'] for t in wins)) / abs(sum(t['pnl_usd'] for t in losses)) if losses else float('inf'),
            'max_drawdown': self.calculate_max_drawdown(trades, initial_capital),
            'trades': trades
        }
        
        # Print results
        print("BACKTEST RESULTS:")
        print("-"*70)
        print(f"Initial Capital:    ${initial_capital:,.2f}")
        print(f"Final Capital:      ${capital:,.2f}")
        print(f"Total Return:       {results['total_return']:.2f}%")
        print(f"Total Trades:       {results['total_trades']}")
        print(f"Winning Trades:     {results['winning_trades']}")
        print(f"Losing Trades:      {results['losing_trades']}")
        print(f"Win Rate:           {results['win_rate']:.1f}%")
        print(f"Profit Factor:      {results['profit_factor']:.2f}")
        print(f"Max Drawdown:       {results['max_drawdown']:.2f}%")
        print(f"Avg Win:            ${results['avg_win']:.2f}")
        print(f"Avg Loss:           ${results['avg_loss']:.2f}")
        print("="*70)
        
        return results
    
    def calculate_max_drawdown(self, trades: list, initial_capital: float) -> float:
        """Calculate maximum drawdown"""
        equity = initial_capital
        peak = equity
        max_dd = 0
        
        for trade in trades:
            equity += trade['pnl_usd']
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            max_dd = max(max_dd, dd)
        
        return max_dd

if __name__ == '__main__':
    backtest = ComprehensiveBacktest()
    results = backtest.run_backtest(initial_capital=1000)
    
    # Save results
    if results:
        output_file = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/backtests/latest_backtest_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✅ Results saved to {output_file}")
