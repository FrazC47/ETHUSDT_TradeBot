#!/usr/bin/env python3
"""
ETHUSDT 1-Minute Data Fetcher - Trade Spotlight
Ultra-precision for entry/exit timing
"""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

SYMBOL = "ETHUSDT"
INTERVAL = "1m"
DATA_DIR = Path("/root/.openclaw/workspace/data")
BINANCE_URL = "https://fapi.binance.com/fapi/v1/klines"

def get_last_timestamp():
    csv_file = DATA_DIR / "ETHUSDT_1m.csv"
    if not csv_file.exists():
        return 0
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            rows = list(reader)
            return int(rows[-1][0]) if rows else 0
    except:
        return 0

def fetch_data(start_time):
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_time + 1 if start_time > 0 else None,
        "limit": 1000
    }
    
    try:
        response = requests.get(BINANCE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
        return None

def save_data(data):
    if not data:
        return 0
    
    csv_file = DATA_DIR / "ETHUSDT_1m.csv"
    file_exists = csv_file.exists()
    columns = ["open_time", "open", "high", "low", "close", "volume",
               "close_time", "quote_volume", "trades", "taker_buy_base",
               "taker_buy_quote", "ignore"]
    
    with open(csv_file, 'a' if file_exists else 'w', newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(columns)
        for candle in data:
            writer.writerow(candle)
    
    return len(data)

def main():
    print(f"[{datetime.now()}] 1m fetch - Trade Spotlight")
    
    last_ts = get_last_timestamp()
    data = fetch_data(last_ts)
    
    if data:
        count = save_data(data)
        print(f"[{datetime.now()}] Saved {count} 1m candles")
        return count
    return 0

if __name__ == "__main__":
    main()
