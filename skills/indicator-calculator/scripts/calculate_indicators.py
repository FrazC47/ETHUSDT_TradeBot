#!/usr/bin/env python3
"""
Technical Indicator Calculator
Generic script to calculate all indicators for any timeframe

Usage: python3 calculate_indicators.py <timeframe> <input_file> <output_file>
Example: python3 calculate_indicators.py 1w data/ETHUSDT_1w.csv data/ETHUSDT_1w_indicators.csv
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

def calculate_indicators(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Calculate all technical indicators"""
    
    print(f"[{datetime.now()}] Calculating indicators for {len(df)} {timeframe} candles...")
    
    df = df.copy()
    
    # Ensure timestamp is datetime
    if 'open_time' in df.columns:
        df['open_time'] = pd.to_datetime(df['open_time'])
        df.set_index('open_time', inplace=True)
        df.sort_index(inplace=True)
    
    # ========== TREND INDICATORS ==========
    print(f"[{datetime.now()}]  - Trend indicators (EMA, SMA)...")
    
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    df['trend_bullish'] = df['ema_9'] > df['ema_21']
    df['trend_strong'] = (df['ema_9'] > df['ema_21']) & (df['ema_21'] > df['ema_50'])
    
    # ========== MOMENTUM INDICATORS ==========
    print(f"[{datetime.now()}]  - Momentum indicators (RSI, MACD)...")
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi_sma'] = df['rsi'].rolling(window=14).mean()
    
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema_12 - ema_26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd_line'] - df['macd_signal']
    
    # ========== VOLATILITY ==========
    print(f"[{datetime.now()}]  - Volatility indicators (ATR, BBands)...")
    
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['atr'] = true_range.rolling(14).mean()
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # ========== VOLUME + VWAP ==========
    print(f"[{datetime.now()}]  - Volume indicators...")
    
    df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']
    
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    df['vwap'] = df['tp_volume'].rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
    df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    
    # ========== ADX ==========
    print(f"[{datetime.now()}]  - ADX...")
    
    df['plus_dm'] = np.where(
        (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
        np.maximum(df['high'] - df['high'].shift(1), 0),
        0
    )
    df['minus_dm'] = np.where(
        (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
        np.maximum(df['low'].shift(1) - df['low'], 0),
        0
    )
    df['plus_di'] = 100 * (df['plus_dm'].rolling(window=14).mean() / df['atr'])
    df['minus_di'] = 100 * (df['minus_dm'].rolling(window=14).mean() / df['atr'])
    df['dx'] = 100 * np.abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    df['adx'] = df['dx'].rolling(window=14).mean()
    df['adx_trending'] = df['adx'] > 25
    
    # ========== FIBONACCI ==========
    print(f"[{datetime.now()}]  - Fibonacci retracements and extensions...")
    
    recent_high = df['high'].rolling(window=20).max()
    recent_low = df['low'].rolling(window=20).min()
    fib_range = recent_high - recent_low
    
    df['fib_0'] = recent_high
    df['fib_236'] = recent_high - (fib_range * 0.236)
    df['fib_382'] = recent_high - (fib_range * 0.382)
    df['fib_500'] = recent_high - (fib_range * 0.500)
    df['fib_618'] = recent_high - (fib_range * 0.618)
    df['fib_786'] = recent_high - (fib_range * 0.786)
    df['fib_100'] = recent_low
    df['fib_1272'] = recent_high + (fib_range * 0.272)
    df['fib_1382'] = recent_high + (fib_range * 0.382)
    df['fib_1618'] = recent_high + (fib_range * 0.618)
    df['fib_200'] = recent_high + (fib_range * 1.0)
    df['fib_2618'] = recent_high + (fib_range * 1.618)
    df['fib_4236'] = recent_high + (fib_range * 3.236)
    df['fib_position'] = (recent_high - df['close']) / fib_range
    
    # ========== STRUCTURE ==========
    print(f"[{datetime.now()}]  - Structure score...")
    
    swing_highs = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
    swing_lows = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
    
    df['hh'] = swing_highs & (df['high'] > df['high'].shift(2).where(swing_highs.shift(1).cumsum() > 0, df['high']))
    df['lh'] = swing_highs & (df['high'] < df['high'].shift(2).where(swing_highs.shift(1).cumsum() > 0, df['high']))
    df['hl'] = swing_lows & (df['low'] > df['low'].shift(2).where(swing_lows.shift(1).cumsum() > 0, df['low']))
    df['ll'] = swing_lows & (df['low'] < df['low'].shift(2).where(swing_lows.shift(1).cumsum() > 0, df['low']))
    
    hh_count = df['hh'].rolling(window=10).sum()
    hl_count = df['hl'].rolling(window=10).sum()
    lh_count = df['lh'].rolling(window=10).sum()
    ll_count = df['ll'].rolling(window=10).sum()
    
    bullish_signals = hh_count + hl_count
    bearish_signals = lh_count + ll_count
    total_signals = bullish_signals + bearish_signals
    df['structure_score'] = np.where(total_signals > 0, (bullish_signals - bearish_signals) / total_signals, 0)
    df['structure_bullish'] = df['structure_score'] > 0.3
    df['structure_bearish'] = df['structure_score'] < -0.3
    
    # ========== PRICE ACTION ==========
    print(f"[{datetime.now()}]  - Price action metrics...")
    
    df['body_size'] = np.abs(df['close'] - df['open'])
    df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
    df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
    df['range'] = df['high'] - df['low']
    df['range_pct'] = df['range'] / df['close'] * 100
    df['is_bullish'] = df['close'] > df['open']
    df['is_bearish'] = df['close'] < df['open']
    df['consecutive_bullish'] = df['is_bullish'].astype(int).groupby((df['is_bullish'] != df['is_bullish'].shift()).cumsum()).cumsum()
    df['swing_high'] = swing_highs
    df['swing_low'] = swing_lows
    df['range_location'] = (df['close'] - df['low']) / (df['high'] - df['low']) * 100
    
    # ========== S/R LEVELS ==========
    print(f"[{datetime.now()}]  - Support/Resistance levels...")
    
    sr_data = []
    for idx in df.index:
        df_hist = df.loc[:idx]
        
        hh_vals = df_hist[df_hist['hh']]['high'].tail(4).values
        res = [np.nan] * (4 - len(hh_vals)) + list(hh_vals)
        
        ll_vals = df_hist[df_hist['ll']]['low'].tail(4).values
        sup = [np.nan] * (4 - len(ll_vals)) + list(ll_vals)
        
        sr_data.append(res + sup)
    
    sr_array = np.array(sr_data)
    df['resistance_1'] = sr_array[:, 0]
    df['resistance_2'] = sr_array[:, 1]
    df['resistance_3'] = sr_array[:, 2]
    df['resistance_4'] = sr_array[:, 3]
    df['support_1'] = sr_array[:, 4]
    df['support_2'] = sr_array[:, 5]
    df['support_3'] = sr_array[:, 6]
    df['support_4'] = sr_array[:, 7]
    
    df['dist_to_resistance_1'] = (df['resistance_1'] - df['close']) / df['close'] * 100
    df['dist_to_support_1'] = (df['close'] - df['support_1']) / df['close'] * 100
    df['sr_zone_size'] = (df['resistance_1'] - df['support_1']) / df['close'] * 100
    df['position_in_sr_zone'] = (df['close'] - df['support_1']) / (df['resistance_1'] - df['support_1'])
    
    # ========== TREND LINES ==========
    print(f"[{datetime.now()}]  - Trend lines...")
    
    def calculate_trend_lines(df):
        """Calculate trend lines with 3+ touches"""
        n = len(df)
        bull_lines = np.full(n, np.nan)
        bear_lines = np.full(n, np.nan)
        bull_touches = np.zeros(n)
        bear_touches = np.zeros(n)
        bull_valid = np.full(n, False)
        bear_valid = np.full(n, False)
        bull_angles = np.full(n, np.nan)
        bear_angles = np.full(n, np.nan)
        bull_slopes = np.full(n, np.nan)
        bear_slopes = np.full(n, np.nan)
        
        for i in range(50, n):
            lows = df['low'].iloc[i-50:i]
            highs = df['high'].iloc[i-50:i]
            
            # Bull trend line (connecting higher lows)
            swing_lows_idx = df['swing_low'].iloc[i-50:i]
            swing_low_values = lows[swing_lows_idx]
            
            if len(swing_low_values) >= 3:
                x = np.arange(len(swing_low_values))
                y = swing_low_values.values
                slope, intercept = np.polyfit(x, y, 1)
                bull_lines[i] = slope * (len(x) - 1) + intercept
                bull_touches[i] = len(swing_low_values)
                bull_valid[i] = slope > 0
                bull_angles[i] = np.degrees(np.arctan(slope))
                bull_slopes[i] = slope / np.mean(y) * 100
            
            # Bear trend line (connecting lower highs)
            swing_highs_idx = df['swing_high'].iloc[i-50:i]
            swing_high_values = highs[swing_highs_idx]
            
            if len(swing_high_values) >= 3:
                x = np.arange(len(swing_high_values))
                y = swing_high_values.values
                slope, intercept = np.polyfit(x, y, 1)
                bear_lines[i] = slope * (len(x) - 1) + intercept
                bear_touches[i] = len(swing_high_values)
                bear_valid[i] = slope < 0
                bear_angles[i] = np.degrees(np.arctan(slope))
                bear_slopes[i] = slope / np.mean(y) * 100
        
        return (bull_lines, bear_lines, bull_touches, bear_touches, bull_valid, bear_valid,
                bull_angles, bear_angles, bull_slopes, bear_slopes)
    
    (bull_lines, bear_lines, bull_touches, bear_touches, bull_valid, bear_valid,
     bull_angles, bear_angles, bull_slopes, bear_slopes) = calculate_trend_lines(df)
    
    df['bull_trend_line'] = bull_lines
    df['bull_trend_touches'] = bull_touches
    df['bull_trend_valid'] = bull_valid
    df['bull_trend_angle'] = bull_angles
    df['bull_trend_slope_pct'] = bull_slopes
    df['dist_to_bull_trend'] = (df['close'] - df['bull_trend_line']) / df['close'] * 100
    
    df['bear_trend_line'] = bear_lines
    df['bear_trend_touches'] = bear_touches
    df['bear_trend_valid'] = bear_valid
    df['bear_trend_angle'] = bear_angles
    df['bear_trend_slope_pct'] = bear_slopes
    df['dist_to_bear_trend'] = (df['close'] - df['bear_trend_line']) / df['close'] * 100
    
    df['above_bull_trend'] = df['close'] > df['bull_trend_line']
    df['below_bear_trend'] = df['close'] < df['bear_trend_line']
    df['between_trend_lines'] = df['above_bull_trend'] & (df['close'] < df['bear_trend_line'])
    df['broke_bull_trend'] = (df['close'].shift(1) > df['bull_trend_line'].shift(1)) & (df['close'] < df['bull_trend_line'])
    df['broke_bear_trend'] = (df['close'].shift(1) < df['bear_trend_line'].shift(1)) & (df['close'] > df['bear_trend_line'])
    
    df.reset_index(inplace=True)
    
    return df

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 calculate_indicators.py <timeframe> <input_file> <output_file>")
        print("Example: python3 calculate_indicators.py 1w data/ETHUSDT_1w.csv data/ETHUSDT_1w_indicators.csv")
        sys.exit(1)
    
    timeframe = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    
    print(f"="*60)
    print(f"Indicator Calculator - {timeframe}")
    print(f"="*60)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()
    
    # Load data
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} candles")
    
    # Calculate indicators
    df = calculate_indicators(df, timeframe)
    
    # Save
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved {len(df)} rows with {len(df.columns)} columns to {output_file}")
    
    # Summary
    print(f"\nDate range: {df['open_time'].min()} to {df['open_time'].max()}")
    print(f"Columns: {len(df.columns)} (106 expected)")
    
    # Count NaN in key indicators
    print("\nNaN counts (early rows expected):")
    for col in ['rsi', 'macd_line', 'adx', 'fib_position']:
        if col in df.columns:
            nan = df[col].isna().sum()
            print(f"  {col}: {nan}")

if __name__ == "__main__":
    main()
