#!/usr/bin/env python3
"""
Download missing 1W (weekly) data from Jan 2025 to Mar 2026
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
FILE_PATH = DATA_DIR / "ETHUSDT_1w_2022_2024.csv"

def fetch_1w_data():
    """Fetch 1W candles from Jan 2025 to current"""
    
    # Start from Jan 6, 2025 (week after our last candle)
    start_ms = int(datetime(2025, 1, 6).timestamp() * 1000)
    # End at current date
    end_ms = int(datetime(2026, 3, 7).timestamp() * 1000)
    
    print(f"Fetching 1W data: 2025-01-06 to 2026-03-07")
    
    url = "https://fapi.binance.com/fapi/v1/klines"
    all_data = []
    
    while start_ms < end_ms:
        params = {
            'symbol': 'ETHUSDT',
            'interval': '1w',
            'startTime': start_ms,
            'endTime': end_ms,
            'limit': 100
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            
            if not data:
                break
                
            all_data.extend(data)
            start_ms = data[-1][0] + 1
            print(f"  Fetched {len(all_data)} weeks...")
            time.sleep(0.05)
            
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    return all_data

def main():
    print("="*60)
    print("EXTENDING 1W DATA TO MARCH 2026")
    print("="*60)
    print()
    
    # Fetch new data
    new_data = fetch_1w_data()
    print(f"\nDownloaded: {len(new_data)} weekly candles")
    
    if not new_data:
        print("No new data to add")
        return
    
    # Load existing
    df_existing = pd.read_csv(FILE_PATH)
    print(f"Existing: {len(df_existing)} candles")
    
    # Create DataFrame from new data
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume',
               'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
               'taker_buy_quote_volume', 'ignore']
    
    df_new = pd.DataFrame(new_data, columns=columns)
    df_new['open_time'] = pd.to_datetime(df_new['open_time'], unit='ms')
    
    # Combine
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined['open_time'] = pd.to_datetime(df_combined['open_time'])
    df_combined = df_combined.sort_values('open_time').drop_duplicates(subset=['open_time'])
    
    # Save
    df_combined.to_csv(FILE_PATH, index=False)
    
    print(f"\nCombined: {len(df_combined)} candles")
    print(f"Date range: {df_combined['open_time'].min()} to {df_combined['open_time'].max()}")
    print(f"✅ Saved: {FILE_PATH}")

if __name__ == "__main__":
    main()
