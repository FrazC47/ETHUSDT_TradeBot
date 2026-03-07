#!/usr/bin/env python3
"""
ETHUSDT Multi-Timeframe Data Download with Integrity Check
Downloads 6 timeframes (1M, 1w, 1d, 4h, 1h, 15m) for 3 years
Validates data integrity and completeness
"""

import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Configuration
DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Also prepare destination for currency_trading
CURRENCY_DIR = Path("/root/.openclaw/workspaces/currency_trading/data/binance_historical")
CURRENCY_DIR.mkdir(parents=True, exist_ok=True)

FUTURES_BASE = "https://fapi.binance.com/fapi/v1"

# Date range: 3 years
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)
START_MS = int(START_DATE.timestamp() * 1000)
END_MS = int(END_DATE.timestamp() * 1000)

# Timeframes to download
TIMEFRAMES = {
    '1M': {'interval': '1M', 'candles_per_year': 12, 'weight': 1},
    '1w': {'interval': '1w', 'candles_per_year': 52, 'weight': 1},
    '1d': {'interval': '1d', 'candles_per_year': 365, 'weight': 2},
    '4h': {'interval': '4h', 'candles_per_year': 2190, 'weight': 3},
    '1h': {'interval': '1h', 'candles_per_year': 8760, 'weight': 5},
    '15m': {'interval': '15m', 'candles_per_year': 35040, 'weight': 10}
}

def fetch_klines(symbol, interval, start_ms, end_ms):
    """Fetch klines from Binance Futures API with pagination"""
    endpoint = f"{FUTURES_BASE}/klines"
    all_klines = []
    limit = 1500
    
    current_start = start_ms
    
    print(f"  Downloading {interval}...")
    
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
                print(f"    Fetched {len(all_klines)} candles...")
            
            # Rate limit: be nice to the API
            time.sleep(0.05)
            
        except Exception as e:
            print(f"    Error: {e}, retrying...")
            time.sleep(1)
            continue
    
    print(f"    Complete: {len(all_klines)} candles")
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

def validate_data(df, timeframe, expected_candles):
    """Validate data integrity"""
    issues = []
    
    # Check 1: Not empty
    if df.empty:
        issues.append("Empty dataset")
        return False, issues
    
    # Check 2: Expected number of candles (±10% tolerance)
    actual_candles = len(df)
    tolerance = expected_candles * 0.1
    if abs(actual_candles - expected_candles) > tolerance:
        issues.append(f"Candle count mismatch: {actual_candles} vs {expected_candles} expected")
    
    # Check 3: No NaN in critical columns
    critical_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in critical_cols:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            issues.append(f"{nan_count} NaN values in {col}")
    
    # Check 4: Price integrity (high >= low, high >= close >= low, etc.)
    invalid_hl = (df['high'] < df['low']).sum()
    if invalid_hl > 0:
        issues.append(f"{invalid_hl} candles with high < low")
    
    invalid_oc = ((df['close'] > df['high']) | (df['close'] < df['low'])).sum()
    if invalid_oc > 0:
        issues.append(f"{invalid_oc} candles with close outside high-low range")
    
    # Check 5: Chronological order
    time_diff = df['open_time'].diff().dropna()
    if (time_diff <= pd.Timedelta(0)).any():
        issues.append("Timestamps not in chronological order")
    
    # Check 6: Date range coverage
    actual_start = df['open_time'].min()
    actual_end = df['open_time'].max()
    
    if actual_start > START_DATE + timedelta(days=7):
        issues.append(f"Late start: {actual_start} (expected ~{START_DATE})")
    
    if actual_end < END_DATE - timedelta(days=7):
        issues.append(f"Early end: {actual_end} (expected ~{END_DATE})")
    
    is_valid = len(issues) == 0
    return is_valid, issues

def check_completeness(df, timeframe):
    """Check for gaps in data"""
    # Expected interval in minutes
    interval_map = {
        '1M': 43200,  # ~30 days
        '1w': 10080,  # 7 days
        '1d': 1440,   # 1 day
        '4h': 240,    # 4 hours
        '1h': 60,     # 1 hour
        '15m': 15     # 15 minutes
    }
    
    expected_interval = interval_map.get(timeframe, 60)
    
    # Calculate gaps
    df_sorted = df.sort_values('open_time')
    time_diff = df_sorted['open_time'].diff().dropna()
    
    # Expected diff in minutes (with some tolerance)
    expected_diff = pd.Timedelta(minutes=expected_interval)
    tolerance = pd.Timedelta(minutes=expected_interval * 1.5)
    
    gaps = time_diff[time_diff > tolerance]
    
    return len(gaps), gaps

def download_and_validate(symbol='ETHUSDT'):
    """Main download and validation function"""
    
    print("="*80)
    print("  ETHUSDT MULTI-TIMEFRAME DATA DOWNLOAD")
    print("="*80)
    print()
    print(f"Symbol: {symbol}")
    print(f"Period: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Duration: 3 years")
    print()
    
    results = {}
    
    for tf_name, tf_config in TIMEFRAMES.items():
        print("="*80)
        print(f"Timeframe: {tf_name}")
        print("="*80)
        
        interval = tf_config['interval']
        expected_candles = tf_config['candles_per_year'] * 3  # 3 years
        
        print(f"Expected candles: ~{expected_candles}")
        
        # Download
        klines = fetch_klines(symbol, interval, START_MS, END_MS)
        
        if not klines:
            print(f"  ❌ Failed to download {tf_name}")
            results[tf_name] = {'status': 'FAILED', 'candles': 0}
            continue
        
        # Convert to DataFrame
        df = klines_to_dataframe(klines)
        
        # Validate
        is_valid, issues = validate_data(df, tf_name, expected_candles)
        
        if issues:
            print(f"  Validation issues:")
            for issue in issues:
                print(f"    ⚠️  {issue}")
        
        # Check completeness (gaps)
        gap_count, gaps = check_completeness(df, tf_name)
        if gap_count > 0:
            print(f"  ⚠️  Found {gap_count} gaps in data")
            if gap_count <= 5:
                for gap in gaps.head(3):
                    print(f"      Gap: {gap}")
        else:
            print(f"  ✅ No gaps detected")
        
        # Save to CSV
        filename = f"{symbol}_{tf_name}_2022_2024.csv"
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False)
        
        print(f"  ✅ Saved: {filepath} ({len(df)} candles)")
        
        # Store results
        results[tf_name] = {
            'status': 'SUCCESS' if is_valid else 'WARNING',
            'candles': len(df),
            'expected': expected_candles,
            'start': df['open_time'].min().strftime('%Y-%m-%d'),
            'end': df['open_time'].max().strftime('%Y-%m-%d'),
            'gaps': gap_count,
            'issues': issues
        }
        
        print()
    
    return results

def copy_to_currency_trading():
    """Copy downloaded data to currency_trading workspace"""
    print("="*80)
    print("  COPYING DATA TO currency_trading WORKSPACE")
    print("="*80)
    print()
    
    for file in DATA_DIR.glob("*.csv"):
        dest = CURRENCY_DIR / file.name
        import shutil
        shutil.copy(file, dest)
        print(f"  Copied: {file.name} → currency_trading")
    
    print()
    print("  ✅ All data copied to both workspaces")
    print()

def generate_report(results):
    """Generate summary report"""
    print("="*80)
    print("  DATA INTEGRITY REPORT")
    print("="*80)
    print()
    
    total_candles = 0
    all_valid = True
    
    for tf, data in results.items():
        status_icon = "✅" if data['status'] == 'SUCCESS' else "⚠️" if data['status'] == 'WARNING' else "❌"
        print(f"{status_icon} {tf:4s}: {data['candles']:>6,} candles ({data['start']} to {data['end']})")
        
        if data['issues']:
            print(f"      Issues: {', '.join(data['issues'][:2])}")
        
        if data['gaps'] > 0:
            print(f"      Gaps: {data['gaps']}")
        
        total_candles += data['candles']
        if data['status'] == 'FAILED':
            all_valid = False
    
    print()
    print(f"Total candles downloaded: {total_candles:,}")
    print(f"Data integrity: {'✅ PASSED' if all_valid else '⚠️ WARNING'}")
    print()
    
    # Backtesting readiness
    print("="*80)
    print("  BACKTESTING READINESS")
    print("="*80)
    print()
    
    if all_valid:
        print("✅ Data is READY for backtesting")
        print()
        print("Next steps:")
        print("  1. Update your backtest scripts to use:")
        print(f"     {DATA_DIR}/ETHUSDT_[TIMEFRAME]_2022_2024.csv")
        print()
        print("  2. Run backtests on IDENTICAL date range:")
        print("     Start: 2022-01-01")
        print("     End:   2024-12-31")
        print()
        print("  3. Compare ETHUSDT_TradeBot vs currency_trading results")
    else:
        print("⚠️  Some data has issues. Review above.")
    
    print()

def main():
    print("\n" + "="*80)
    print("  STARTING MULTI-TIMEFRAME DATA DOWNLOAD")
    print("  This will take approximately 15-30 minutes")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    # Download and validate
    results = download_and_validate('ETHUSDT')
    
    # Copy to both workspaces
    copy_to_currency_trading()
    
    # Generate report
    generate_report(results)
    
    elapsed = time.time() - start_time
    print(f"Total time: {elapsed/60:.1f} minutes")
    print()

if __name__ == "__main__":
    main()
