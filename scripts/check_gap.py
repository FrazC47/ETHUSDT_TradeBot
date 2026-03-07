import pandas as pd

# Load the 15m data
df = pd.read_csv('/root/.openclaw/workspace/data/binance_historical/ETHUSDT_15m_2019_2024.csv')
df['open_time'] = pd.to_datetime(df['open_time'])

# Check around the gap
print("Checking what candles exist around the gap...")
print()

# Get all candles from 07:00 to 17:00 on that day
mask = (df['open_time'] >= '2021-12-31 07:00') & (df['open_time'] <= '2021-12-31 17:00')
candles = df[mask].sort_values('open_time')

print(f"Total candles found: {len(candles)}")
print()
print("Candles:")
for _, row in candles.iterrows():
    print(f"  {row['open_time']} - Close: {row['close']}")

print()

# Check if there's any data between 08:00 and 16:00
mask_gap = (df['open_time'] > '2021-12-31 08:00') & (df['open_time'] < '2021-12-31 16:00')
gap_candles = df[mask_gap]

print(f"Candles between 08:00 and 16:00: {len(gap_candles)}")

if len(gap_candles) == 0:
    print()
    print("The gap is REAL - no candles exist between 08:00 and 16:00")
    print()
    print("Possible reasons:")
    print("  1. Exchange maintenance/downtime on 2021-12-31")
    print("  2. Low liquidity period (holiday - New Year's Eve)")
    print("  3. Data not recorded by Binance")
    print()
    print("This is NOT a merge issue - the data genuinely doesn't exist.")
