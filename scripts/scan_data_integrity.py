#!/usr/bin/env python3
"""
Scan all timeframe data files for gaps and data quality issues
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")

def scan_file(filepath, timeframe):
    """Scan a single CSV file for issues"""
    
    print(f"\n{'='*60}")
    print(f"Scanning: {filepath.name}")
    print(f"{'='*60}")
    
    # Load data
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"❌ ERROR loading file: {e}")
        return {'status': 'ERROR', 'issues': [str(e)]}
    
    issues = []
    
    # 1. Check basic stats
    print(f"Total rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    
    # 2. Check for NaN in critical columns
    critical_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in critical_cols:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                issues.append(f"{nan_count} NaN values in {col}")
                print(f"⚠️  {nan_count} NaN in {col}")
    
    # 3. Check price integrity
    if 'high' in df.columns and 'low' in df.columns:
        invalid_hl = (df['high'] < df['low']).sum()
        if invalid_hl > 0:
            issues.append(f"{invalid_hl} rows where high < low")
            print(f"⚠️  {invalid_hl} high < low")
    
    if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        # Check close within high-low
        outside = ((df['close'] > df['high']) | (df['close'] < df['low'])).sum()
        if outside > 0:
            issues.append(f"{outside} closes outside high-low range")
            print(f"⚠️  {outside} close outside range")
    
    # 4. Check chronological order
    df_sorted = df.sort_values('open_time')
    if not df['open_time'].equals(df_sorted['open_time']):
        issues.append("Data not in chronological order")
        print(f"⚠️  Not chronological")
        df = df_sorted
    
    # 5. Check for time gaps
    df['open_time'] = pd.to_datetime(df['open_time'])
    df = df.sort_values('open_time').reset_index(drop=True)
    
    # Expected interval based on timeframe
    interval_map = {
        '1M': 30,      # days (approx)
        '1w': 7,       # days
        '1d': 1,       # day
        '4h': 4/24,    # days
        '1h': 1/24,    # days
        '15m': 15/1440 # days
    }
    
    expected_interval = interval_map.get(timeframe, 1/24)
    expected_delta = timedelta(days=expected_interval * 1.5)  # 50% tolerance
    
    time_diff = df['open_time'].diff().dropna()
    gaps = time_diff[time_diff > expected_delta]
    
    if len(gaps) > 0:
        issues.append(f"{len(gaps)} time gaps detected")
        print(f"⚠️  {len(gaps)} gaps found:")
        for idx in gaps.head(3).index:
            gap_size = gaps.loc[idx]
            print(f"    Gap: {df.loc[idx-1, 'open_time']} → {df.loc[idx, 'open_time']} ({gap_size})")
    else:
        print(f"✅ No gaps detected")
    
    # 6. Check for duplicates
    duplicates = df['open_time'].duplicated().sum()
    if duplicates > 0:
        issues.append(f"{duplicates} duplicate timestamps")
        print(f"⚠️  {duplicates} duplicates")
    else:
        print(f"✅ No duplicates")
    
    # 7. Date range
    print(f"\nDate range:")
    print(f"  Start: {df['open_time'].min()}")
    print(f"  End:   {df['open_time'].max()}")
    print(f"  Span:  {df['open_time'].max() - df['open_time'].min()}")
    
    # Summary
    if issues:
        print(f"\n❌ ISSUES FOUND: {len(issues)}")
        return {'status': 'WARNING', 'issues': issues}
    else:
        print(f"\n✅ CLEAN - No issues found")
        return {'status': 'OK', 'issues': []}

def main():
    print("="*60)
    print("DATA INTEGRITY SCAN")
    print("="*60)
    
    files = {
        '1M': 'ETHUSDT_1M_2022_2024.csv',
        '1w': 'ETHUSDT_1w_2022_2024.csv',
        '1d': 'ETHUSDT_1d_2022_2024.csv',
        '4h': 'ETHUSDT_4h_2022_2024.csv',
        '1h': 'ETHUSDT_1h_2022_2024.csv',
        '15m': 'ETHUSDT_15m_2019_2024.csv'
    }
    
    results = {}
    
    for tf, filename in files.items():
        filepath = DATA_DIR / filename
        if filepath.exists():
            results[tf] = scan_file(filepath, tf)
        else:
            print(f"\n❌ File not found: {filename}")
            results[tf] = {'status': 'MISSING', 'issues': ['File not found']}
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    ok_count = sum(1 for r in results.values() if r['status'] == 'OK')
    warning_count = sum(1 for r in results.values() if r['status'] == 'WARNING')
    error_count = sum(1 for r in results.values() if r['status'] in ['ERROR', 'MISSING'])
    
    print(f"\n✅ Clean:      {ok_count} files")
    print(f"⚠️  Warnings:   {warning_count} files")
    print(f"❌ Errors:     {error_count} files")
    
    if warning_count == 0 and error_count == 0:
        print(f"\n✅ ALL FILES PASSED - Ready for backtesting")
    else:
        print(f"\n⚠️  Review issues above before backtesting")

if __name__ == "__main__":
    main()
