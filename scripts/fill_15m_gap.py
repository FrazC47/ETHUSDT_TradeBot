#!/usr/bin/env python3
"""
Fill the gap in 15m data (2021-12-31 08:00 to 16:00)
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
FILE_PATH = DATA_DIR / "ETHUSDT_15m_2019_2024.csv"

def download_gap_data():
    """Download the missing 8 hours of 15m candles"""
    
    # Gap: 2021-12-31 08:00 to 2021-12-31 16:00
    start_ms = int(datetime(2021, 12, 31, 8, 0).timestamp() * 1000)
    end_ms = int(datetime(2021, 12, 31, 16, 0).timestamp() * 1000)
    
    print("Downloading missing 15m candles...")
    print(f"Gap: 2021-12-31 08:00 → 2021-12-31 16:00")
    print(f"Expected: 32 candles (8 hours × 4 candles/hour)")
    
    endpoint = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        'symbol': 'ETHUSDT',
        'interval': '15m',
        'startTime': start_ms,
        'endTime': end_ms,
        'limit': 100
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"Downloaded: {len(data)} candles")
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def merge_and_save(new_candles):
    """Merge new candles with existing data"""
    
    # Load existing data
    df_existing = pd.read_csv(FILE_PATH)
    print(f"Existing: {len(df_existing)} candles")
    
    # Convert new candles to DataFrame
    columns = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
        'taker_buy_quote_volume', 'ignore'
    ]
    
    df_new = pd.DataFrame(new_candles, columns=columns)
    
    # Convert timestamp to string format matching existing
    df_new['open_time'] = pd.to_datetime(df_new['open_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
    df_new['close_time'] = pd.to_datetime(df_new['close_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # Merge and sort
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined['open_time'] = pd.to_datetime(df_combined['open_time'])
    df_combined = df_combined.sort_values('open_time').reset_index(drop=True)
    
    # Remove any duplicates
    df_combined = df_combined.drop_duplicates(subset=['open_time'], keep='first')
    
    print(f"Combined: {len(df_combined)} candles")
    print(f"Duplicates removed: {len(df_existing) + len(df_new) - len(df_combined)}")
    
    # Save
    df_combined.to_csv(FILE_PATH, index=False)
    print(f"Saved: {FILE_PATH}")
    
    return df_combined

def verify_fix(df):
    """Verify the gap is filled"""
    print("\nVerifying fix...")
    
    # Check around the gap area
    df['open_time'] = pd.to_datetime(df['open_time'])
    gap_area = df[(df['open_time'] >= '2021-12-31 07:00') & (df['open_time'] <= '2021-12-31 17:00')]
    
    print(f"\nCandles around gap area (2021-12-31 07:00-17:00):")
    for _, row in gap_area.iterrows():
        print(f"  {row['open_time']}")
    
    # Check for gaps
    time_diff = gap_area['open_time'].diff().dropna()
    gaps = time_diff[time_diff > pd.Timedelta(minutes=20)]  # 15m + 5m tolerance
    
    if len(gaps) == 0:
        print("\n✅ Gap filled successfully - no gaps detected")
        return True
    else:
        print(f"\n⚠️  {len(gaps)} gaps still present")
        return False

def main():
    print("="*60)
    print("FILLING GAP IN 15m DATA")
    print("="*60)
    print()
    
    # Download missing data
    new_candles = download_gap_data()
    
    if not new_candles:
        print("❌ Failed to download gap data")
        return
    
    # Merge and save
    df_combined = merge_and_save(new_candles)
    
    # Verify
    success = verify_fix(df_combined)
    
    print("\n" + "="*60)
    if success:
        print("✅ GAP FILLED SUCCESSFULLY")
    else:
        print("⚠️  GAP FILL INCOMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
