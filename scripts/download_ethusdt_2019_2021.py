#!/usr/bin/env python3
"""
Download ETHUSDT 15m candles from Binance Futures API
Period: 2019-11-27 to 2021-12-31 16:00
"""

import requests
import pandas as pd
import time
from datetime import datetime
from pathlib import Path

# Configuration
DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "ETHUSDT_15m_2019_2024.csv"
EXISTING_FILE = DATA_DIR / "ETHUSDT_15m_2022_2024.csv"

FUTURES_BASE = "https://fapi.binance.com/fapi/v1"

# Date range: 2019-11-27 to 2021-12-31 16:00:00
START_DATE = datetime(2019, 11, 27)
END_DATE = datetime(2021, 12, 31, 16, 0, 0)
START_MS = int(START_DATE.timestamp() * 1000)
END_MS = int(END_DATE.timestamp() * 1000)

def fetch_klines(symbol, interval, start_ms, end_ms):
    """Fetch klines from Binance Futures API with pagination"""
    endpoint = f"{FUTURES_BASE}/klines"
    all_klines = []
    limit = 1500
    
    current_start = start_ms
    
    print(f"Downloading {interval} candles from {START_DATE} to {END_DATE}...")
    
    while current_start < end_ms:
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'startTime': current_start,
            'endTime': end_ms
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
            
            all_klines.extend(data)
            
            # Update start time for next batch
            current_start = data[-1][0] + 1
            
            # Progress update
            if len(all_klines) % 5000 == 0:
                print(f"  Fetched {len(all_klines)} candles...")
            
            # Rate limit: 0.05s delay between requests
            time.sleep(0.05)
            
        except Exception as e:
            print(f"  Error: {e}, retrying...")
            time.sleep(1)
            continue
    
    print(f"  Complete: {len(all_klines)} candles downloaded")
    return all_klines

def klines_to_dataframe(klines):
    """Convert klines to DataFrame"""
    columns = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
        'taker_buy_quote_volume', 'ignore'
    ]
    
    df = pd.DataFrame(klines, columns=columns)
    
    # Convert timestamps
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    
    # Convert numeric columns
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                    'quote_volume', 'trades', 'taker_buy_volume', 
                    'taker_buy_quote_volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def download_historical_data():
    """Download ETHUSDT 15m data from 2019-11-27 to 2021-12-31"""
    
    print("="*80)
    print("  ETHUSDT 15m HISTORICAL DATA DOWNLOAD")
    print("="*80)
    print()
    print(f"Symbol: ETHUSDT")
    print(f"Period: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Download data
    klines = fetch_klines('ETHUSDT', '15m', START_MS, END_MS)
    
    if not klines:
        print("❌ Failed to download data")
        return None
    
    # Convert to DataFrame
    df = klines_to_dataframe(klines)
    
    # Show date range
    print(f"  Date range: {df['open_time'].min()} to {df['open_time'].max()}")
    print(f"  Total candles: {len(df)}")
    
    return df

def merge_with_existing(new_df):
    """Merge new data with existing 2022-2024 data"""
    
    print()
    print("="*80)
    print("  MERGING WITH EXISTING DATA")
    print("="*80)
    print()
    
    if not EXISTING_FILE.exists():
        print(f"❌ Existing file not found: {EXISTING_FILE}")
        return new_df
    
    # Read existing data
    print(f"Reading existing data from: {EXISTING_FILE}")
    existing_df = pd.read_csv(EXISTING_FILE)
    existing_df['open_time'] = pd.to_datetime(existing_df['open_time'])
    existing_df['close_time'] = pd.to_datetime(existing_df['close_time'])
    
    print(f"  Existing candles: {len(existing_df)}")
    print(f"  Existing range: {existing_df['open_time'].min()} to {existing_df['open_time'].max()}")
    
    # Merge dataframes
    print()
    print("Merging datasets...")
    combined_df = pd.concat([new_df, existing_df], ignore_index=True)
    
    # Sort by open_time (chronological order)
    combined_df = combined_df.sort_values('open_time').reset_index(drop=True)
    
    # Remove duplicates based on open_time
    before_dedup = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['open_time'], keep='first')
    after_dedup = len(combined_df)
    
    duplicates_removed = before_dedup - after_dedup
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate candles")
    else:
        print(f"  No duplicates found")
    
    print(f"  Combined candles: {len(combined_df)}")
    print(f"  Combined range: {combined_df['open_time'].min()} to {combined_df['open_time'].max()}")
    
    return combined_df

def save_data(df):
    """Save merged data to CSV"""
    
    print()
    print("="*80)
    print("  SAVING DATA")
    print("="*80)
    print()
    
    df.to_csv(OUTPUT_FILE, index=False)
    
    # Get file size
    file_size = OUTPUT_FILE.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"✅ Saved to: {OUTPUT_FILE}")
    print(f"   File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
    
    return file_size

def generate_report(df, download_count):
    """Generate final report"""
    
    print()
    print("="*80)
    print("  FINAL REPORT")
    print("="*80)
    print()
    
    print(f"Total candles downloaded: {download_count:,}")
    print(f"Date range covered: {df['open_time'].min()} to {df['open_time'].max()}")
    print(f"Total candles in merged file: {len(df):,}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / (1024 * 1024):.2f} MB")
    print()
    print("✅ Task completed successfully!")

def main():
    print("\n" + "="*80)
    print("  STARTING ETHUSDT 15m HISTORICAL DATA DOWNLOAD")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    # Step 1: Download historical data (2019-2021)
    new_df = download_historical_data()
    
    if new_df is None or new_df.empty:
        print("❌ Download failed")
        return
    
    download_count = len(new_df)
    
    # Step 2: Merge with existing data (2022-2024)
    combined_df = merge_with_existing(new_df)
    
    # Step 3: Save merged data
    save_data(combined_df)
    
    # Step 4: Generate report
    generate_report(combined_df, download_count)
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed/60:.1f} minutes")

if __name__ == "__main__":
    main()
