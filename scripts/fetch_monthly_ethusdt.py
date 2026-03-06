#!/usr/bin/env python3
"""
ETHUSDT Monthly Data Fetcher - Efficient Version
Only fetches new candles and appends to existing data
"""

import requests
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import time

# Configuration
SYMBOL = "ETHUSDT"
INTERVAL = "1M"  # Monthly
DATA_DIR = Path("/root/.openclaw/workspace/data")
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"
CSV_FILE = DATA_DIR / "ETHUSDT_1M.csv"

def get_last_timestamp():
    """Get the timestamp of the last candle in the CSV"""
    if not CSV_FILE.exists():
        print(f"[{datetime.now()}] ℹ️  No existing CSV file, will fetch all data")
        return 0
    
    try:
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)
            if not rows:
                return 0
            last_ts = int(rows[-1][0])  # First column is open_time
            last_date = datetime.fromtimestamp(last_ts/1000, tz=timezone.utc)
            print(f"[{datetime.now()}] ℹ️  Last candle in CSV: {last_date.strftime('%Y-%m-%d')}")
            return last_ts
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error reading CSV: {e}")
        return 0

def fetch_new_data(start_time):
    """Fetch only new monthly candles from Binance Futures"""
    
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_time + 1,  # Start after last candle
        "limit": 100
    }
    
    try:
        response = requests.get(BINANCE_FUTURES_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print(f"[{datetime.now()}] ℹ️  No new monthly candles available")
            return None
        
        first_date = datetime.fromtimestamp(data[0][0]/1000, tz=timezone.utc)
        last_date = datetime.fromtimestamp(data[-1][0]/1000, tz=timezone.utc)
        print(f"[{datetime.now()}] ✅ Received {len(data)} new monthly candles")
        print(f"[{datetime.now()}]    Range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
        return data
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fetching data: {e}")
        return None

def append_to_csv(data):
    """Append new candles to existing CSV"""
    
    if not data:
        return 0
    
    # Check if file exists (need header?)
    file_exists = CSV_FILE.exists()
    
    # CSV columns matching Binance API response
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ]
    
    # Append to CSV
    mode = 'a' if file_exists else 'w'
    with open(CSV_FILE, mode, newline="") as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(columns)
        
        for candle in data:
            writer.writerow(candle)
    
    print(f"[{datetime.now()}] ✅ Appended {len(data)} candles to {CSV_FILE}")
    return len(data)

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT Monthly Data Update - Efficient Append Mode")
    print("="*70)
    
    # Get last timestamp from existing data
    last_ts = get_last_timestamp()
    
    # Fetch only new data
    data = fetch_new_data(last_ts)
    
    if data:
        # Append to CSV
        count = append_to_csv(data)
        
        # Log success
        log_file = DATA_DIR / "monthly_update.log"
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Appended {count} monthly candles\n")
        
        print(f"[{datetime.now()}] ✅ Monthly data update complete ({count} new candles)")
    else:
        print(f"[{datetime.now()}] ℹ️  No update needed (no new candles)")
    
    print("="*70)

if __name__ == "__main__":
    main()
