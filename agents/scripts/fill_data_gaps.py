#!/usr/bin/env python3
"""
ETHUSDT Data Gap Filler
Fills any missing data across all timeframes
"""

import requests
import csv
from pathlib import Path
from datetime import datetime, timedelta
import time

class ETHUSDTDataFiller:
    """Fills data gaps for all ETHUSDT timeframes"""
    
    BASE_URL = "https://api.binance.com/api/v3/klines"
    SYMBOL = "ETHUSDT"
    
    TIMEFRAMES = {
        '1M': {'interval': '1M', 'limit': 100, 'ms_per_candle': 30 * 24 * 60 * 60 * 1000},  # Monthly
        '1w': {'interval': '1w', 'limit': 100, 'ms_per_candle': 7 * 24 * 60 * 60 * 1000},   # Weekly
        '1d': {'interval': '1d', 'limit': 100, 'ms_per_candle': 24 * 60 * 60 * 1000},       # Daily
        '4h': {'interval': '4h', 'limit': 100, 'ms_per_candle': 4 * 60 * 60 * 1000},        # 4 Hour
        '1h': {'interval': '1h', 'limit': 100, 'ms_per_candle': 60 * 60 * 1000},            # 1 Hour
        '15m': {'interval': '15m', 'limit': 100, 'ms_per_candle': 15 * 60 * 1000},          # 15 Minute
        '5m': {'interval': '5m', 'limit': 100, 'ms_per_candle': 5 * 60 * 1000},             # 5 Minute
    }
    
    def __init__(self):
        self.data_dir = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/data/raw')
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_last_timestamp(self, timeframe: str) -> int:
        """Get the last timestamp from existing data file"""
        file_path = self.data_dir / f"{timeframe}.csv"
        
        if not file_path.exists():
            return 0
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    return int(rows[-1]['open_time'])
        except Exception as e:
            print(f"Error reading {timeframe}: {e}")
        
        return 0
    
    def fetch_data(self, interval: str, start_time: int = None, limit: int = 100) -> list:
        """Fetch data from Binance API"""
        params = {
            'symbol': self.SYMBOL,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {interval}: {e}")
            return []
    
    def append_to_csv(self, timeframe: str, data: list):
        """Append new data to CSV file"""
        if not data:
            return
        
        file_path = self.data_dir / f"{timeframe}.csv"
        
        # Check if file exists
        file_exists = file_path.exists()
        
        # Read existing timestamps to avoid duplicates
        existing_timestamps = set()
        if file_exists:
            try:
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        existing_timestamps.add(int(row['open_time']))
            except:
                pass
        
        # Filter out duplicates
        new_data = [candle for candle in data if candle[0] not in existing_timestamps]
        
        if not new_data:
            print(f"  No new data for {timeframe}")
            return
        
        # Write to CSV
        mode = 'a' if file_exists else 'w'
        with open(file_path, mode, newline='') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                    'taker_buy_quote_volume', 'ignore'
                ])
            
            for candle in new_data:
                writer.writerow(candle)
        
        print(f"  Added {len(new_data)} new candles to {timeframe}")
    
    def fill_gaps(self):
        """Fill data gaps for all timeframes"""
        print("="*70)
        print("ETHUSDT DATA GAP FILLER")
        print("="*70)
        print()
        
        for timeframe, config in self.TIMEFRAMES.items():
            print(f"Processing {timeframe}...")
            
            # Get last timestamp
            last_ts = self.get_last_timestamp(timeframe)
            
            if last_ts == 0:
                print(f"  No existing data, fetching recent {config['limit']} candles")
                # Fetch recent data
                data = self.fetch_data(config['interval'], limit=config['limit'])
            else:
                last_date = datetime.fromtimestamp(last_ts / 1000)
                now = datetime.now()
                hours_missing = (now - last_date).total_seconds() / 3600
                
                print(f"  Last data: {last_date.strftime('%Y-%m-%d %H:%M')} ({hours_missing:.1f} hours ago)")
                
                if hours_missing < 0.5:  # Less than 30 minutes
                    print(f"  ✓ Data is current, skipping")
                    continue
                
                # Fetch data from last timestamp
                data = self.fetch_data(config['interval'], start_time=last_ts + 1, limit=config['limit'])
            
            # Append to CSV
            self.append_to_csv(timeframe, data)
            
            # Rate limit
            time.sleep(0.5)
            print()
        
        print("="*70)
        print("Data gap filling complete!")
        print("="*70)

if __name__ == '__main__':
    filler = ETHUSDTDataFiller()
    filler.fill_gaps()
