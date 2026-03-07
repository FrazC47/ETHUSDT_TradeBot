#!/usr/bin/env python3
"""
Extend all timeframe data to March 7, 2026
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")

END_DATE = datetime(2026, 3, 7)
END_MS = int(END_DATE.timestamp() * 1000)

def fetch_data(symbol, interval, start_ms, end_ms):
    """Fetch klines from Binance"""
    url = "https://fapi.binance.com/fapi/v1/klines"
    all_data = []
    
    while start_ms < end_ms:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ms,
            'endTime': end_ms,
            'limit': 1000
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            
            if not data:
                break
                
            all_data.extend(data)
            start_ms = data[-1][0] + 1
            time.sleep(0.05)
            
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    return all_data

def extend_timeframe(tf_name, tf_code, filename):
    """Extend a specific timeframe"""
    print(f"\n{'='*60}")
    print(f"Extending {tf_name}")
    print(f"{'='*60}")
    
    file_path = DATA_DIR / filename
    
    # Load existing
    df_existing = pd.read_csv(file_path)
    df_existing['open_time'] = pd.to_datetime(df_existing['open_time'])
    
    last_date = df_existing['open_time'].max()
    print(f"Existing: {len(df_existing)} candles, ends {last_date}")
    
    if last_date >= pd.Timestamp('2026-03-07'):
        print(f"Already up to date!")
        return
    
    # Fetch new data
    start_ms = int(last_date.timestamp() * 1000) + 1
    
    print(f"Fetching from {last_date} to 2026-03-07...")
    new_data = fetch_data('ETHUSDT', tf_code, start_ms, END_MS)
    
    if not new_data:
        print("No new data fetched")
        return
    
    # Create DataFrame
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume',
               'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
               'taker_buy_quote_volume', 'ignore']
    
    df_new = pd.DataFrame(new_data, columns=columns)
    df_new['open_time'] = pd.to_datetime(df_new['open_time'], unit='ms')
    
    print(f"Fetched: {len(df_new)} candles")
    
    # Combine
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['open_time'])
    df_combined = df_combined.sort_values('open_time')
    
    # Save
    df_combined.to_csv(file_path, index=False)
    
    print(f"Saved: {len(df_combined)} candles total")
    print(f"Range: {df_combined['open_time'].min()} to {df_combined['open_time'].max()}")

def main():
    print("="*60)
    print("EXTENDING ALL TIMEFRAMES TO MARCH 2026")
    print("="*60)
    
    timeframes = [
        ('1M', '1M', 'ETHUSDT_1M_2022_2024.csv'),
        ('1d', '1d', 'ETHUSDT_1d_2022_2024.csv'),
        ('4h', '4h', 'ETHUSDT_4h_2022_2024.csv'),
        ('1h', '1h', 'ETHUSDT_1h_2022_2024.csv'),
        ('15m', '15m', 'ETHUSDT_15m_2019_2024.csv'),
    ]
    
    for name, code, filename in timeframes:
        extend_timeframe(name, code, filename)
    
    print("\n" + "="*60)
    print("EXTENSION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
