#!/usr/bin/env python3
"""
ETHUSDT 15-Minute Data Fetcher - Incremental
Only fetches NEW 15m candles since last update
"""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

# Configuration
SYMBOL = "ETHUSDT"
INTERVAL = "15m"  # 15-Minute
DATA_DIR = Path("/root/.openclaw/workspace/data")
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"
CSV_FILE = DATA_DIR / "ETHUSDT_15m.csv"

def get_last_timestamp():
    """Get the timestamp of the last candle in the CSV"""
    if not CSV_FILE.exists():
        print(f"[{datetime.now()}] ℹ️  No existing CSV file")
        return 0
    
    try:
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)
            if not rows:
                return 0
            last_ts = int(rows[-1][0])
            last_date = datetime.fromtimestamp(last_ts/1000, tz=timezone.utc)
            print(f"[{datetime.now()}] ℹ️  Last candle: {last_date.strftime('%Y-%m-%d %H:%M')}")
            return last_ts
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error: {e}")
        return 0

def fetch_new_data(start_time):
    """Fetch only new 15m candles"""
    
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_time + 1 if start_time > 0 else None,
        "limit": 1000
    }
    
    try:
        response = requests.get(BINANCE_FUTURES_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print(f"[{datetime.now()}] ℹ️  No new 15m candles")
            return None
        
        first_date = datetime.fromtimestamp(data[0][0]/1000, tz=timezone.utc)
        last_date = datetime.fromtimestamp(data[-1][0]/1000, tz=timezone.utc)
        print(f"[{datetime.now()}] ✅ Received {len(data)} new 15m candles")
        print(f"[{datetime.now()}]    {first_date.strftime('%Y-%m-%d %H:%M')} to {last_date.strftime('%Y-%m-%d %H:%M')}")
        return data
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return None

def append_to_csv(data):
    """Append new candles"""
    if not data:
        return 0
    
    file_exists = CSV_FILE.exists()
    columns = ["open_time", "open", "high", "low", "close", "volume",
               "close_time", "quote_volume", "trades", "taker_buy_base",
               "taker_buy_quote", "ignore"]
    
    mode = 'a' if file_exists else 'w'
    with open(CSV_FILE, mode, newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(columns)
        for candle in data:
            writer.writerow(candle)
    
    print(f"[{datetime.now()}] ✅ Appended {len(data)} candles")
    return len(data)

def main():
    print("="*70)
    print("ETHUSDT 15-Minute Data Update")
    print("="*70)
    
    last_ts = get_last_timestamp()
    data = fetch_new_data(last_ts)
    
    if data:
        count = append_to_csv(data)
        log_file = DATA_DIR / "15m_update.log"
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {count} candles\n")
        print(f"[{datetime.now()}] ✅ Complete ({count} new)")
    else:
        print(f"[{datetime.now()}] ℹ️  No update needed")
    
    print("="*70)

if __name__ == "__main__":
    main()
