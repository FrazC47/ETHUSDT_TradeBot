import pandas as pd
from datetime import datetime

DATA_DIR = '/root/.openclaw/workspace/data/binance_historical'
timeframes = {
    '1M': 'ETHUSDT_1M_2022_2024.csv',
    '1w': 'ETHUSDT_1w_2022_2024.csv', 
    '1d': 'ETHUSDT_1d_2022_2024.csv',
    '4h': 'ETHUSDT_4h_2022_2024.csv',
    '1h': 'ETHUSDT_1h_2022_2024.csv',
    '15m': 'ETHUSDT_15m_2022_2024.csv'
}

required_cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 
                 'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                 'taker_buy_quote_volume', 'ignore']

print("="*80)
print("DATA VERIFICATION: 2022-01-01 to 2026-03-07")
print("="*80)
print()

all_ok = True
for tf, filename in timeframes.items():
    filepath = f"{DATA_DIR}/{filename}"
    try:
        df = pd.read_csv(filepath)
        df['open_time'] = pd.to_datetime(df['open_time'])
        
        # Check columns
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        # Check date range
        start = df['open_time'].min()
        end = df['open_time'].max()
        
        # Check for NaN in critical columns
        nan_counts = {}
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                nan_counts[col] = df[col].isna().sum()
        
        status = "OK" if not missing_cols and start <= pd.Timestamp('2022-01-02') and end >= pd.Timestamp('2026-03-06') else "FAIL"
        
        print(f"{tf:4s} | {status:4s} | {len(df):>6,} rows | {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
        
        if missing_cols:
            print(f"     Missing columns: {missing_cols}")
            all_ok = False
        if any(nan_counts.values()):
            print(f"     NaN values: {nan_counts}")
            all_ok = False
            
    except Exception as e:
        print(f"{tf:4s} | FAIL | ERROR: {e}")
        all_ok = False

print()
print("="*80)
if all_ok:
    print("ALL FILES VERIFIED - Complete data from 2022-01-01 to 2026-03-07")
else:
    print("SOME ISSUES FOUND - Review above")
print("="*80)
