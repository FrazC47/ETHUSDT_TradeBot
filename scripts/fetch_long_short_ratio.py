#!/usr/bin/env python3
"""
ETHUSDT Long/Short Ratio Fetcher
Fetches long/short ratio from Binance Futures
"""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

# Configuration
SYMBOL = "ETHUSDT"
DATA_DIR = Path("/root/.openclaw/workspace/data")
CSV_FILE = DATA_DIR / "ETHUSDT_long_short_ratio.csv"
BINANCE_LS_URL = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"

def get_last_timestamp():
    """Get the timestamp of the last L/S ratio in CSV"""
    if not CSV_FILE.exists():
        print(f"[{datetime.now()}] ℹ️  No existing L/S ratio file")
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
            print(f"[{datetime.now()}] ℹ️  Last L/S record: {last_date.strftime('%Y-%m-%d %H:%M')}")
            return last_ts
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error reading CSV: {e}")
        return 0

def fetch_long_short_ratio():
    """Fetch long/short ratio from Binance Futures"""
    
    params = {
        "symbol": SYMBOL,
        "period": "1h",  # Hourly
        "limit": 500
    }
    
    try:
        response = requests.get(BINANCE_LS_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print(f"[{datetime.now()}] ❌ No L/S ratio data received")
            return None
        
        ls_data = []
        for item in data:
            ls_data.append([
                item['timestamp'],
                item['longAccount'],
                item['shortAccount'],
                item['longShortRatio'],
                SYMBOL
            ])
        
        first_date = datetime.fromtimestamp(data[0]['timestamp']/1000, tz=timezone.utc)
        last_date = datetime.fromtimestamp(data[-1]['timestamp']/1000, tz=timezone.utc)
        print(f"[{datetime.now()}] ✅ Received {len(ls_data)} L/S ratio records")
        print(f"[{datetime.now()}]    Range: {first_date.strftime('%Y-%m-%d %H:%M')} to {last_date.strftime('%Y-%m-%d %H:%M')}")
        return ls_data
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fetching L/S ratio: {e}")
        return None

def append_to_csv(data):
    """Append L/S ratio to CSV"""
    
    if not data:
        return 0
    
    file_exists = CSV_FILE.exists()
    
    columns = ["timestamp", "long_account_pct", "short_account_pct", "long_short_ratio", "symbol"]
    
    mode = 'a' if file_exists else 'w'
    with open(CSV_FILE, mode, newline="") as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(columns)
        
        for row in data:
            writer.writerow(row)
    
    print(f"[{datetime.now()}] ✅ Appended {len(data)} L/S records to {CSV_FILE}")
    return len(data)

def calculate_ls_metrics():
    """Calculate L/S ratio metrics"""
    import pandas as pd
    
    if not CSV_FILE.exists():
        return None
    
    try:
        df = pd.read_csv(CSV_FILE)
        if len(df) == 0:
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')
        
        # Current ratio
        current_ratio = df['long_short_ratio'].iloc[-1]
        current_long_pct = df['long_account_pct'].iloc[-1]
        
        # 24h average
        avg_24h = df['long_short_ratio'].tail(24).mean()
        
        # Extreme signals
        extreme_long = current_ratio > 3.0  # 75% long
        extreme_short = current_ratio < 0.5  # 33% long
        
        # Signal
        if extreme_long:
            signal = 'contrarian_short'
        elif extreme_short:
            signal = 'contrarian_long'
        else:
            signal = 'neutral'
        
        return {
            'current_ratio': current_ratio,
            'current_long_pct': current_long_pct,
            'avg_24h': avg_24h,
            'extreme_long': extreme_long,
            'extreme_short': extreme_short,
            'signal': signal
        }
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error calculating L/S metrics: {e}")
        return None

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT Long/Short Ratio Update")
    print("="*70)
    
    last_ts = get_last_timestamp()
    data = fetch_long_short_ratio()
    
    if data:
        count = append_to_csv(data)
        
        # Calculate and log metrics
        metrics = calculate_ls_metrics()
        if metrics:
            print(f"[{datetime.now()}] 📊 Current L/S Ratio: {metrics['current_ratio']:.2f}")
            print(f"[{datetime.now()}] 📊 Long %: {metrics['current_long_pct']:.1f}%")
            print(f"[{datetime.now()}] 📊 Signal: {metrics['signal']}")
        
        log_file = DATA_DIR / "ls_ratio_update.log"
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Appended {count} L/S records\n")
        
        print(f"[{datetime.now()}] ✅ L/S ratio update complete ({count} records)")
    else:
        print(f"[{datetime.now()}] ❌ L/S ratio update failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
