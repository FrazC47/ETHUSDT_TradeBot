#!/usr/bin/env python3
"""
ETHUSDT Open Interest Fetcher
Fetches open interest data from Binance Futures
"""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path
import time

# Configuration
SYMBOL = "ETHUSDT"
DATA_DIR = Path("/root/.openclaw/workspace/data")
CSV_FILE = DATA_DIR / "ETHUSDT_open_interest.csv"
BINANCE_OI_URL = "https://fapi.binance.com/fapi/v1/openInterest"

def get_last_timestamp():
    """Get the timestamp of the last OI record in CSV"""
    if not CSV_FILE.exists():
        print(f"[{datetime.now()}] ℹ️  No existing OI file")
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
            print(f"[{datetime.now()}] ℹ️  Last OI record: {last_date.strftime('%Y-%m-%d %H:%M')}")
            return last_ts
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error reading CSV: {e}")
        return 0

def fetch_open_interest():
    """Fetch current open interest from Binance Futures"""
    
    try:
        response = requests.get(BINANCE_OI_URL, params={"symbol": SYMBOL}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'openInterest' not in data:
            print(f"[{datetime.now()}] ❌ No OI data received")
            return None
        
        timestamp = data['time']  # API uses 'time' not 'timestamp'
        oi_value = float(data['openInterest'])
        
        record_time = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
        print(f"[{datetime.now()}] ✅ Received OI: {oi_value:,.0f} at {record_time.strftime('%Y-%m-%d %H:%M')}")
        
        return {
            'timestamp': timestamp,
            'open_interest': oi_value,
            'symbol': SYMBOL
        }
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fetching OI: {e}")
        return None

def fetch_historical_oi(start_time):
    """Fetch historical open interest"""
    
    params = {
        "symbol": SYMBOL,
        "period": "1h",  # Hourly data
        "startTime": start_time + 1 if start_time > 0 else None,
        "limit": 500
    }
    
    try:
        response = requests.get("https://fapi.binance.com/fapi/v1/openInterestHist", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None
        
        oi_data = []
        for item in data:
            oi_data.append([
                item['timestamp'],
                item['sumOpenInterest'],
                item['sumOpenInterestValue'],
                SYMBOL
            ])
        
        print(f"[{datetime.now()}] ✅ Received {len(oi_data)} historical OI records")
        return oi_data
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fetching historical OI: {e}")
        return None

def append_to_csv(data):
    """Append OI data to CSV"""
    
    if not data:
        return 0
    
    file_exists = CSV_FILE.exists()
    
    columns = ["timestamp", "open_interest", "oi_value_usd", "symbol"]
    
    mode = 'a' if file_exists else 'w'
    with open(CSV_FILE, mode, newline="") as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(columns)
        
        if isinstance(data, dict):
            # Single record
            writer.writerow([data['timestamp'], data['open_interest'], '', data['symbol']])
            count = 1
        else:
            # List of records
            for row in data:
                writer.writerow(row)
            count = len(data)
    
    print(f"[{datetime.now()}] ✅ Appended {count} OI records to {CSV_FILE}")
    return count

def calculate_oi_metrics():
    """Calculate OI metrics for use in indicators"""
    import pandas as pd
    
    if not CSV_FILE.exists():
        return None
    
    try:
        df = pd.read_csv(CSV_FILE)
        if len(df) == 0:
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')
        
        # Calculate metrics
        current_oi = df['open_interest'].iloc[-1]
        oi_24h_ago = df['open_interest'].iloc[-24] if len(df) >= 24 else df['open_interest'].iloc[0]
        oi_change_24h = ((current_oi - oi_24h_ago) / oi_24h_ago) * 100
        
        oi_7d_ago = df['open_interest'].iloc[-168] if len(df) >= 168 else df['open_interest'].iloc[0]
        oi_change_7d = ((current_oi - oi_7d_ago) / oi_7d_ago) * 100
        
        # OI trend
        oi_sma_24 = df['open_interest'].tail(24).mean()
        oi_above_sma = current_oi > oi_sma_24
        
        return {
            'current_oi': current_oi,
            'oi_change_24h': oi_change_24h,
            'oi_change_7d': oi_change_7d,
            'oi_above_sma': oi_above_sma,
            'oi_trend': 'rising' if oi_change_24h > 0 else 'falling'
        }
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error calculating OI metrics: {e}")
        return None

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT Open Interest Update")
    print("="*70)
    
    last_ts = get_last_timestamp()
    
    # Try to fetch historical data first
    data = fetch_historical_oi(last_ts)
    
    if not data:
        # Fall back to current snapshot
        print(f"[{datetime.now()}] ℹ️  Fetching current OI snapshot...")
        data = fetch_open_interest()
    
    if data:
        count = append_to_csv(data)
        
        # Calculate and log metrics
        metrics = calculate_oi_metrics()
        if metrics:
            print(f"[{datetime.now()}] 📊 Current OI: {metrics['current_oi']:,.0f}")
            print(f"[{datetime.now()}] 📊 24h change: {metrics['oi_change_24h']:+.2f}%")
            print(f"[{datetime.now()}] 📊 Trend: {metrics['oi_trend']}")
        
        log_file = DATA_DIR / "oi_update.log"
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Appended {count} OI records\n")
        
        print(f"[{datetime.now()}] ✅ OI update complete ({count} records)")
    else:
        print(f"[{datetime.now()}] ❌ OI update failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
