#!/usr/bin/env python3
"""
Binance Historical Data Download Script
Downloads maximum candlestick data for backtesting
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Binance API endpoints
FUTURES_BASE = "https://fapi.binance.com/fapi/v1"
DATA_VISION_BASE = "https://data.binance.vision/data/futures/um/daily/klines"

# Rate limiting
RATE_LIMIT_DELAY = 0.1  # 100ms between requests

def fetch_klines_paginated(symbol, interval, start_time=None, end_time=None):
    """
    Fetch all available klines from Binance Futures API
    Handles pagination automatically
    """
    endpoint = f"{FUTURES_BASE}/klines"
    all_klines = []
    limit = 1500  # Max per request for futures
    
    print(f"Fetching {symbol} {interval} klines...")
    
    while True:
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
            
            all_klines.extend(data)
            
            # Update start_time for next batch
            start_time = data[-1][0] + 1
            
            # Progress update
            if len(all_klines) % 10000 == 0:
                print(f"  Fetched {len(all_klines)} candles...")
            
            # Rate limit safety
            time.sleep(RATE_LIMIT_DELAY)
            
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")
            time.sleep(1)  # Wait longer on error
            continue
    
    print(f"  Total: {len(all_klines)} candles")
    return all_klines

def klines_to_dataframe(klines):
    """Convert klines to pandas DataFrame"""
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
                    'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])
    
    return df

def download_binance_vision_data(symbol, interval, year, month):
    """
    Download data from Binance Vision (historical data dumps)
    More reliable for bulk historical data
    """
    base_url = f"{DATA_VISION_BASE}/{symbol}/{interval}"
    
    # Calculate days in month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    days_in_month = (next_month - datetime(year, month, 1)).days
    
    downloaded = 0
    
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        filename = f"{symbol}-{interval}-{date_str}.zip"
        url = f"{base_url}/{filename}"
        filepath = DATA_DIR / filename
        
        if filepath.exists():
            continue
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                downloaded += 1
                print(f"  Downloaded {filename}")
            else:
                print(f"  Not available: {filename}")
        except Exception as e:
            print(f"  Error downloading {filename}: {e}")
        
        time.sleep(0.05)  # Small delay
    
    return downloaded

def get_available_data_summary(symbol='ETHUSDT'):
    """
    Get summary of available data from Binance
    """
    print(f"\nChecking available data for {symbol}...")
    print("="*80)
    
    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']
    
    for tf in timeframes:
        # Test API to get first and last candle
        endpoint = f"{FUTURES_BASE}/klines"
        
        # Get first candle
        params = {'symbol': symbol, 'interval': tf, 'limit': 1, 'startTime': 0}
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            first_data = resp.json()
            if first_data:
                first_time = datetime.fromtimestamp(first_data[0][0] / 1000)
            else:
                first_time = "N/A"
        except:
            first_time = "Error"
        
        # Get last candle
        params = {'symbol': symbol, 'interval': tf, 'limit': 1}
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            last_data = resp.json()
            if last_data:
                last_time = datetime.fromtimestamp(last_data[0][0] / 1000)
            else:
                last_time = "N/A"
        except:
            last_time = "Error"
        
        print(f"{tf:4s} | First: {first_time} | Last: {last_time}")
        time.sleep(0.1)

def main():
    """Main execution"""
    print("="*80)
    print("  BINANCE HISTORICAL DATA DOWNLOAD")
    print("="*80)
    print()
    
    # Option 1: Get data summary
    print("Option 1: Check available data ranges")
    get_available_data_summary('ETHUSDT')
    
    print()
    print("="*80)
    print("  OPTIONS FOR FULL DOWNLOAD")
    print("="*80)
    print()
    
    print("1. API Method (for recent data, last 2-3 years):")
    print("   - Uses fapi.binance.com")
    print("   - Rate limited: ~1500 candles/request")
    print("   - Example: 1h data = ~17,500 candles/year")
    print()
    
    print("2. Binance Vision (for complete history):")
    print("   - Download from https://data.binance.vision/")
    print("   - Daily ZIP files available")
    print("   - ETHUSDT available from 2020")
    print()
    
    print("Recommended data amounts for backtesting:")
    print("  1m:  1 year = 525,600 candles (large file)")
    print("  5m:  2 years = 210,000 candles")
    print("  15m: 2 years = 70,000 candles")
    print("  1h:  3 years = 26,280 candles (recommended)")
    print("  4h:  3 years = 6,570 candles")
    print("  1d:  4 years = 1,460 candles")
    print()
    
    # Example: Download 1h data
    print("="*80)
    print("  EXAMPLE: Download ETHUSDT 1h data")
    print("="*80)
    print()
    
    print("To download specific date range:")
    print()
    print("# Define date range")
    print("start = int(datetime(2023, 1, 1).timestamp() * 1000)")
    print("end = int(datetime(2024, 12, 31).timestamp() * 1000)")
    print()
    print("# Fetch data")
    print("klines = fetch_klines_paginated('ETHUSDT', '1h', start, end)")
    print("df = klines_to_dataframe(klines)")
    print("df.to_csv('ETHUSDT_1h_2023_2024.csv', index=False)")
    print()

if __name__ == "__main__":
    main()
