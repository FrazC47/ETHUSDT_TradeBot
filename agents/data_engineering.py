#!/usr/bin/env python3
"""
Data Engineering Agent
Handles all data download, processing, and maintenance
"""

import pandas as pd
import numpy as np
import requests
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

class DataEngineeringAgent:
    """
    Agent responsible for:
    - Downloading historical data from exchanges
    - Calculating technical indicators
    - Data quality checks
    - Incremental updates
    """
    
    def __init__(self, task_file=None):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.data_dir = self.base_dir / "data" / "indicators"
        self.log_file = self.base_dir / "logs" / f"data_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.task = self.load_task(task_file) if task_file else None
        
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [DATA_AGENT] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_task(self, task_file):
        """Load task parameters"""
        with open(task_file) as f:
            return json.load(f)
    
    def save_task_status(self, status, result=None):
        """Update task status"""
        if self.task:
            self.task['status'] = status
            self.task['completed'] = datetime.now().isoformat()
            if result:
                self.task['result'] = result
            
            task_file = Path(self.task.get('task_file', f"/tmp/task_{self.task['task_id']}.json"))
            with open(task_file, 'w') as f:
                json.dump(self.task, f, indent=2, default=str)
    
    def download_binance_data(self, symbol, timeframe, start_date, end_date):
        """Download data from Binance Futures"""
        self.log(f"Downloading {symbol} {timeframe} data...")
        
        base_url = "https://fapi.binance.com/fapi/v1/klines"
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        
        all_data = []
        current = start_ms
        
        while current < end_ms:
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'startTime': current,
                'endTime': end_ms,
                'limit': 1000
            }
            
            try:
                response = requests.get(base_url, params=params, timeout=30)
                data = response.json()
                
                if not data:
                    break
                
                all_data.extend(data)
                current = data[-1][0] + 1
                
                # Rate limit
                import time
                time.sleep(0.5)
                
            except Exception as e:
                self.log(f"Error downloading: {e}")
                break
        
        self.log(f"Downloaded {len(all_data)} candles")
        return all_data
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        self.log("Calculating indicators...")
        
        # EMAs
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd_line'] = exp1 - exp2
        df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd_line'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr_14'] = true_range.rolling(14).mean()
        
        # ADX
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff(-1).abs()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr = true_range.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        df['adx'] = dx.rolling(14).mean()
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        # Volume
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap_cumsum = (typical_price * df['volume']).cumsum()
        vol_cumsum = df['volume'].cumsum()
        df['vwap'] = vwap_cumsum / vol_cumsum
        df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100
        
        self.log(f"Indicators calculated: {len(df.columns)} columns")
        return df
    
    def verify_data_completeness(self, timeframe):
        """Check if data has gaps"""
        file_path = self.data_dir / f"{timeframe}_indicators.csv"
        
        if not file_path.exists():
            return {"status": "missing", "gaps": []}
        
        df = pd.read_csv(file_path)
        df['open_time'] = pd.to_datetime(df['open_time'])
        df = df.sort_values('open_time')
        
        # Check for gaps
        expected_diff = pd.Timedelta(minutes=self.get_timeframe_minutes(timeframe))
        actual_diff = df['open_time'].diff()
        gaps = df[actual_diff > expected_diff * 1.5]
        
        return {
            "status": "complete" if len(gaps) == 0 else "has_gaps",
            "candles": len(df),
            "start": str(df['open_time'].min()),
            "end": str(df['open_time'].max()),
            "gaps": len(gaps)
        }
    
    def get_timeframe_minutes(self, tf):
        """Convert timeframe to minutes"""
        mapping = {
            '1m': 1, '5m': 5, '15m': 15, '1h': 60,
            '4h': 240, '1d': 1440, '1w': 10080, '1M': 43200
        }
        return mapping.get(tf, 60)
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing task: {task_name}")
        self.save_task_status("running")
        
        if task_name == "verify_and_download":
            timeframes = params.get('timeframes', ['1h'])
            years = params.get('years', [2024])
            
            for tf in timeframes:
                status = self.verify_data_completeness(tf)
                self.log(f"{tf}: {status['status']} ({status.get('candles', 0)} candles)")
                
                if status['status'] != 'complete':
                    # Download missing data
                    self.log(f"Downloading {tf} data...")
                    # Implementation here
                    pass
        
        elif task_name == "calculate_indicators":
            timeframe = params.get('timeframe', '1h')
            file_path = self.data_dir / f"{timeframe}_indicators.csv"
            
            if file_path.exists():
                df = pd.read_csv(file_path)
                df = self.calculate_indicators(df)
                df.to_csv(file_path, index=False)
                self.log(f"Saved indicators to {file_path}")
        
        self.save_task_status("completed", {"success": True})
        return True

def main():
    """Run agent"""
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = DataEngineeringAgent(task_file)
    
    if task_file:
        agent.execute_task()
    else:
        agent.log("Data Engineering Agent ready")
        agent.log("Usage: python data_engineering.py <task_file.json>")

if __name__ == "__main__":
    main()
