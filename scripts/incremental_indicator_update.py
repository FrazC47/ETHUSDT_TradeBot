#!/usr/bin/env python3
"""
Incremental Indicator Calculator
Only calculates indicators for NEW candles, appends to existing file
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

DATA_DIR = Path("/root/.openclaw/workspace/data")
RAW_DIR = DATA_DIR / "raw"
INDICATORS_DIR = DATA_DIR / "indicators"

def calculate_new_indicators(timeframe, calculate_func):
    """
    Calculate indicators only for new candles and append
    """
    raw_file = RAW_DIR / f"{timeframe}.csv"
    indicator_file = INDICATORS_DIR / f"{timeframe}_indicators.csv"
    
    print(f"[{datetime.now()}] Processing {timeframe}...")
    
    # Load raw data
    df_raw = pd.read_csv(raw_file)
    df_raw['open_time'] = pd.to_datetime(df_raw['open_time'])
    
    # Check if indicator file exists
    if indicator_file.exists():
        df_existing = pd.read_csv(indicator_file)
        df_existing['open_time'] = pd.to_datetime(df_existing['open_time'])
        
        # Find new candles
        last_calculated = df_existing['open_time'].max()
        df_new = df_raw[df_raw['open_time'] > last_calculated].copy()
        
        if len(df_new) == 0:
            print(f"  No new candles to calculate")
            return
        
        print(f"  Existing: {len(df_existing)} candles")
        print(f"  New: {len(df_new)} candles to calculate")
        
        # Calculate indicators for ALL data (needed for rolling windows)
        # But only save the NEW rows
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
        df_all = calculate_func(df_all)
        
        # Keep only new rows
        df_new_calculated = df_all[df_all['open_time'] > last_calculated].copy()
        
        # Append to existing file
        df_combined = pd.concat([df_existing, df_new_calculated], ignore_index=True)
        df_combined.to_csv(indicator_file, index=False)
        
        print(f"  Saved: {len(df_combined)} total candles")
    else:
        # First run - calculate all
        print(f"  First run - calculating all {len(df_raw)} candles")
        df_calculated = calculate_func(df_raw)
        df_calculated.to_csv(indicator_file, index=False)
        print(f"  Saved: {len(df_calculated)} candles")

# Import the calculation functions from existing scripts
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('timeframe', choices=['1M', '1w', '1d', '4h', '1h', '15m'])
    args = parser.parse_args()
    
    # Import the appropriate calculation function
    if args.timeframe == '1w':
        from calculate_weekly_indicators import calculate_indicators
    elif args.timeframe == '1d':
        from calculate_daily_indicators import calculate_indicators
    elif args.timeframe == '1M':
        from calculate_monthly_indicators import calculate_indicators
    else:
        print(f"Using default calculation for {args.timeframe}")
        # Use 1h calculation as default
        from calculate_1h_indicators import calculate_indicators
    
    calculate_new_indicators(args.timeframe, calculate_indicators)

if __name__ == "__main__":
    main()
