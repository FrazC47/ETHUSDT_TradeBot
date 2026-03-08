#!/usr/bin/env python3
"""
Backtesting Agent
Runs strategy backtests and performance analysis
"""

import pandas as pd
import numpy as np
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

class BacktestingAgent:
    """
    Agent responsible for:
    - Running strategy backtests
    - Calculating performance metrics
    - Month-by-month analysis
    - Parameter optimization
    """
    
    def __init__(self, task_file=None):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.data_dir = self.base_dir / "data" / "indicators"
        self.results_dir = self.base_dir / "backtest_results"
        self.log_file = self.base_dir / "logs" / f"backtest_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.task = self.load_task(task_file) if task_file else None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [BACKTEST_AGENT] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_task(self, task_file):
        with open(task_file) as f:
            return json.load(f)
    
    def save_result(self, result):
        result_file = self.results_dir / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        return result_file
    
    def run_monthly_backtest(self, year: int, strategy: str = "atrade"):
        """Run backtest for specific year with month-by-month breakdown"""
        self.log(f"Running {strategy} backtest for {year}")
        
        # Load 1h data for the year
        df = pd.read_csv(self.data_dir / "1h_indicators.csv")
        df['open_time'] = pd.to_datetime(df['open_time'])
        
        # Filter to year
        df = df[(df['open_time'].dt.year == year)]
        
        if len(df) == 0:
            self.log(f"No data found for {year}")
            return None
        
        self.log(f"Loaded {len(df)} candles for {year}")
        
        # Monthly breakdown
        monthly_results = {}
        
        for month in range(1, 13):
            month_data = df[df['open_time'].dt.month == month]
            
            if len(month_data) == 0:
                continue
            
            # Simulate strategy on this month
            result = self.simulate_strategy_month(month_data, strategy)
            
            monthly_results[month] = {
                'month_name': datetime(year, month, 1).strftime('%B'),
                'trades': result['trades'],
                'wins': result['wins'],
                'losses': result['losses'],
                'win_rate': result['win_rate'],
                'profit': result['profit'],
                'return_pct': result['return_pct']
            }
            
            self.log(f"  {monthly_results[month]['month_name']}: {result['trades']} trades, {result['return_pct']:+.2f}%")
        
        # Aggregate
        total_trades = sum(m['trades'] for m in monthly_results.values())
        total_profit = sum(m['profit'] for m in monthly_results.values())
        total_wins = sum(m['wins'] for m in monthly_results.values())
        
        summary = {
            'year': year,
            'strategy': strategy,
            'total_trades': total_trades,
            'total_wins': total_wins,
            'total_losses': total_trades - total_wins,
            'win_rate': (total_wins / total_trades * 100) if total_trades > 0 else 0,
            'total_profit': total_profit,
            'annual_return_pct': (total_profit / 10),  # Assuming $1000 capital
            'monthly_breakdown': monthly_results
        }
        
        result_file = self.save_result(summary)
        self.log(f"Results saved to {result_file}")
        
        return summary
    
    def simulate_strategy_month(self, df, strategy):
        """Simulate strategy on month data"""
        # Simplified simulation
        capital = 1000
        risk_per_trade = 0.015
        
        trades = 0
        wins = 0
        profit = 0
        
        for i in range(50, len(df) - 10):
            row = df.iloc[i]
            close = row['close']
            ema9 = row.get('ema_9', close)
            ema21 = row.get('ema_21', close)
            
            # Simple EMA crossover
            if close > ema9 > ema21:
                entry = close
                stop = entry * 0.97
                target = entry * 1.06
                
                future = df.iloc[i+1:i+20]
                for _, f in future.iterrows():
                    if f['low'] <= stop:
                        trades += 1
                        profit -= capital * risk_per_trade
                        break
                    elif f['high'] >= target:
                        trades += 1
                        wins += 1
                        profit += capital * risk_per_trade * 3
                        break
        
        return {
            'trades': trades,
            'wins': wins,
            'losses': trades - wins,
            'win_rate': (wins / trades * 100) if trades > 0 else 0,
            'profit': profit,
            'return_pct': profit / 10
        }
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing: {task_name}")
        
        if "backtest_year" in task_name:
            year = params.get('year', 2024)
            strategy = params.get('strategy', 'atrade')
            result = self.run_monthly_backtest(year, strategy)
            return result is not None
        
        elif task_name == "parameter_optimization":
            self.log("Running parameter optimization...")
            # Implementation
            pass
        
        return True

def main():
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = BacktestingAgent(task_file)
    
    if task_file:
        agent.execute_task()
    else:
        agent.log("Backtesting Agent ready")

if __name__ == "__main__":
    main()
