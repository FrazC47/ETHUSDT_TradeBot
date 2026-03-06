#!/usr/bin/env python3
"""
ETHUSDT Funding Rate Fetcher
Fetches funding rate data from Binance Futures
Updates every 8 hours (00:00, 08:00, 16:00 UTC)
"""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

# Configuration
SYMBOL = "ETHUSDT"
DATA_DIR = Path("/root/.openclaw/workspace/data")
CSV_FILE = DATA_DIR / "ETHUSDT_funding_rate.csv"
BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"

def get_last_timestamp():
    """Get the timestamp of the last funding rate in CSV"""
    if not CSV_FILE.exists():
        print(f"[{datetime.now()}] ℹ️  No existing funding rate file")
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
            print(f"[{datetime.now()}] ℹ️  Last funding rate: {last_date.strftime('%Y-%m-%d %H:%M')}")
            return last_ts
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error reading CSV: {e}")
        return 0

def fetch_funding_rates(start_time):
    """Fetch funding rates from Binance Futures"""
    
    params = {
        "symbol": SYMBOL,
        "startTime": start_time + 1 if start_time > 0 else None,
        "limit": 1000
    }
    
    try:
        response = requests.get(BINANCE_FUNDING_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print(f"[{datetime.now()}] ℹ️  No new funding rates available")
            return None
        
        # Convert to list format for CSV
        funding_data = []
        for item in data:
            funding_data.append([
                item['fundingTime'],
                item['fundingRate'],
                item.get('markPrice', ''),
                item.get('symbol', SYMBOL)
            ])
        
        first_date = datetime.fromtimestamp(data[0]['fundingTime']/1000, tz=timezone.utc)
        last_date = datetime.fromtimestamp(data[-1]['fundingTime']/1000, tz=timezone.utc)
        print(f"[{datetime.now()}] ✅ Received {len(funding_data)} funding rate records")
        print(f"[{datetime.now()}]    Range: {first_date.strftime('%Y-%m-%d %H:%M')} to {last_date.strftime('%Y-%m-%d %H:%M')}")
        return funding_data
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fetching funding rates: {e}")
        return None

def append_to_csv(data):
    """Append funding rates to CSV"""
    
    if not data:
        return 0
    
    file_exists = CSV_FILE.exists()
    
    columns = ["funding_time", "funding_rate", "mark_price", "symbol"]
    
    mode = 'a' if file_exists else 'w'
    with open(CSV_FILE, mode, newline="") as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(columns)
        
        for row in data:
            writer.writerow(row)
    
    print(f"[{datetime.now()}] ✅ Appended {len(data)} funding rates to {CSV_FILE}")
    return len(data)

def calculate_funding_metrics():
    """Calculate funding rate metrics for use in indicators"""
    import pandas as pd  # Import here to avoid NameError
    
    if not CSV_FILE.exists():
        return None
    
    try:
        df = pd.read_csv(CSV_FILE)
        if len(df) == 0:
            return None
        
        # Calculate metrics
        current_rate = df['funding_rate'].iloc[-1]
        avg_24h = df['funding_rate'].tail(3).mean()  # Last 3 = 24h
        avg_7d = df['funding_rate'].tail(21).mean()  # Last 21 = 7 days
        max_24h = df['funding_rate'].tail(3).max()
        min_24h = df['funding_rate'].tail(3).min()
        
        # Extreme funding signals
        is_extreme_long = current_rate > 0.001  # > 0.1%
        is_extreme_short = current_rate < -0.001  # < -0.1%
        
        return {
            'current_rate': current_rate,
            'avg_24h': avg_24h,
            'avg_7d': avg_7d,
            'max_24h': max_24h,
            'min_24h': min_24h,
            'is_extreme_long': is_extreme_long,
            'is_extreme_short': is_extreme_short,
            'signal': 'contrarian_short' if is_extreme_long else ('contrarian_long' if is_extreme_short else 'neutral')
        }
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error calculating metrics: {e}")
        return None

def main():
    """Main function"""
    import pandas as pd  # Import here for metrics calculation
    
    print("="*70)
    print("ETHUSDT Funding Rate Update")
    print("="*70)
    
    last_ts = get_last_timestamp()
    data = fetch_funding_rates(last_ts)
    
    if data:
        count = append_to_csv(data)
        
        # Calculate and log metrics
        metrics = calculate_funding_metrics()
        if metrics:
            print(f"[{datetime.now()}] 📊 Current funding rate: {metrics['current_rate']:.4%}")
            print(f"[{datetime.now()}] 📊 24h average: {metrics['avg_24h']:.4%}")
            print(f"[{datetime.now()}] 📊 Signal: {metrics['signal']}")
        
        log_file = DATA_DIR / "funding_rate_update.log"
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - Appended {count} funding rates\n")
        
        print(f"[{datetime.now()}] ✅ Funding rate update complete ({count} new records)")
    else:
        print(f"[{datetime.now()}] ℹ️  No update needed")
    
    print("="*70)

if __name__ == "__main__":
    main()
