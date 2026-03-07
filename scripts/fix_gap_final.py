#!/usr/bin/env python3
"""
Fix the gap in 15m data - PROPER VERSION
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
FILE_PATH = DATA_DIR / "ETHUSDT_15m_2019_2024.csv"

def fetch_gap_candles():
    """Fetch the missing candles from Binance"""
    
    # The gap: 2021-12-31 08:00 to 16:00
    start_ms = int(datetime(2021, 12, 31, 8, 0).timestamp() * 1000)
    end_ms = int(datetime(2021, 12, 31, 16, 0).timestamp() * 1000)
    
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        'symbol': 'ETHUSDT',
        'interval': '15m',
        'startTime': start_ms,
        'endTime': end_ms,
        'limit': 100
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return data

def main():
    print("Fetching missing candles from Binance...")
    
    # Get the missing candles
    candles = fetch_gap_candles()
    print(f"Fetched: {len(candles)} candles")
    
    if len(candles) == 0:
        print("❌ No data returned")
        return
    
    # Load existing data
    df = pd.read_csv(FILE_PATH)
    print(f"Existing: {len(df)} candles")
    
    # Convert timestamps for comparison
    df['open_time'] = pd.to_datetime(df['open_time'])
    
    # Create DataFrame from new candles
    columns = ['ts', 'open', 'high', 'low', 'close', 'volume', 'ct', 'qv', 'trades', 'tbv', 'tbqv', 'ign']
    df_new = pd.DataFrame(candles, columns=columns)
    
    # Convert timestamp
    df_new['open_time'] = pd.to_datetime(df_new['ts'], unit='ms')
    df_new['close_time'] = pd.to_datetime(df_new['ct'], unit='ms')
    
    # Check which timestamps are missing
    existing_times = set(df['open_time'].values)
    new_times = set(df_new['open_time'].values)
    
    missing_times = new_times - existing_times
    print(f"Missing timestamps: {len(missing_times)}")
    
    if len(missing_times) == 0:
        print("All candles already exist - no gap to fill")
        return
    
    # Filter to only missing candles
    df_to_add = df_new[df_new['open_time'].isin(missing_times)].copy()
    
    # Format to match existing file
    df_to_add = df_to_add.rename(columns={
        'ts': 'open_time_raw',
        'ct': 'close_time_raw',
        'qv': 'quote_volume',
        'tbv': 'taker_buy_volume',
        'tbqv': 'taker_buy_quote_volume',
        'ign': 'ignore'
    })
    
    # Keep only needed columns in correct order
    df_to_add = df_to_add[['open_time', 'open', 'high', 'low', 'close', 'volume', 
                           'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                           'taker_buy_quote_volume', 'ignore']]
    
    # Format timestamps as strings to match
    df_to_add['open_time'] = df_to_add['open_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_to_add['close_time'] = df_to_add['close_time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # Combine
    df_combined = pd.concat([df, df_to_add], ignore_index=True)
    df_combined['open_time'] = pd.to_datetime(df_combined['open_time'])
    df_combined = df_combined.sort_values('open_time').reset_index(drop=True)
    
    print(f"Combined: {len(df_combined)} candles")
    print(f"Added: {len(df_to_add)} candles")
    
    # Save
    df_combined.to_csv(FILE_PATH, index=False)
    print(f"✅ Saved: {FILE_PATH}")
    
    # Verify gap is filled
    df_check = pd.read_csv(FILE_PATH)
    df_check['open_time'] = pd.to_datetime(df_check['open_time'])
    
    gap_check = df_check[(df_check['open_time'] >= '2021-12-31 07:00') & 
                         (df_check['open_time'] <= '2021-12-31 17:00')]
    
    print(f"\nCandles 07:00-17:00: {len(gap_check)}")
    print("\nGap status: ", end="")
    
    if len(gap_check) == 41:  # 07:00 to 17:00 = 10 hours = 40 candles + 1 extra
        print("✅ FILLED")
    else:
        print(f"⚠️  Still missing (expected ~41, got {len(gap_check)})")

if __name__ == "__main__":
    main()
