#!/usr/bin/env python3
"""
ETHUSDT Weekly Indicator Calculator
Calculates all 99 technical indicators for 1w (weekly) timeframe
Same logic as monthly calculator for consistency
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
INPUT_FILE = DATA_DIR / "ETHUSDT_1w_2022_2024.csv"
OUTPUT_FILE = DATA_DIR / "ETHUSDT_1w_indicators.csv"
METADATA_FILE = DATA_DIR / "ETHUSDT_1w_metadata.json"

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators for weekly data"""
    
    print(f"[{datetime.now()}] Calculating indicators for {len(df)} weekly candles...")
    
    df = df.copy()
    
    # Ensure timestamp is datetime
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    df.sort_index(inplace=True)
    
    # ========== TREND INDICATORS ==========
    print(f"[{datetime.now()}]  - Calculating trend indicators (EMA, SMA)...")
    
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    df['trend_bullish'] = df['ema_9'] > df['ema_21']
    df['trend_strong'] = (df['ema_9'] > df['ema_21']) & (df['ema_21'] > df['ema_50'])
    
    # ========== MOMENTUM INDICATORS ==========
    print(f"[{datetime.now()}]  - Calculating momentum indicators (RSI, MACD)...")
    
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
    print(f"[{datetime.now()}]  - Calculating volatility indicators (ATR, BBands)...")
    
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
    print(f"[{datetime.now()}]  - Calculating volume indicators (VWAP)...")
    
    df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']
    
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    df['vwap'] = df['tp_volume'].rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
    df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    
    # ========== ADX ==========
    print(f"[{datetime.now()}]  - Calculating ADX...")
    
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
    
    # ========== FIBONACCI (Retracements + Extensions) ==========
    print(f"[{datetime.now()}]  - Calculating Fibonacci retracements and extensions...")
    
    recent_high = df['high'].rolling(window=20).max()
    recent_low = df['low'].rolling(window=20).min()
    fib_range = recent_high - recent_low
    
    # Retracements
    df['fib_0'] = recent_high
    df['fib_236'] = recent_high - (fib_range * 0.236)
    df['fib_382'] = recent_high - (fib_range * 0.382)
    df['fib_500'] = recent_high - (fib_range * 0.500)
    df['fib_618'] = recent_high - (fib_range * 0.618)
    df['fib_786'] = recent_high - (fib_range * 0.786)
    df['fib_100'] = recent_low
    
    # Extensions
    df['fib_1272'] = recent_high + (fib_range * 0.272)
    df['fib_1382'] = recent_high + (fib_range * 0.382)
    df['fib_1618'] = recent_high + (fib_range * 0.618)
    df['fib_200'] = recent_high + (fib_range * 1.0)
    df['fib_2618'] = recent_high + (fib_range * 1.618)
    df['fib_4236'] = recent_high + (fib_range * 3.236)
    df['fib_position'] = (recent_high - df['close']) / fib_range
    
    # ========== STRUCTURE ==========
    print(f"[{datetime.now()}]  - Calculating structure score...")
    
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
    print(f"[{datetime.now()}]  - Calculating price action metrics...")
    
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
    
    # ========== SWING-BASED S/R LEVELS ==========
    print(f"[{datetime.now()}]  - Calculating swing-based S/R levels...")
    
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
    df['position_in_sr_zone'] = (df['close'] - df['support_1']) / (df['resistance_1'] - df['support_1']) * 100
    
    # ========== TREND LINES ==========
    print(f"[{datetime.now()}]  - Calculating trend lines (3+ touches, validated)...")
    
    trend_data = []
    for idx in df.index:
        df_hist = df.loc[:idx].copy()
        df_hist['time_num'] = np.arange(len(df_hist))
        
        # Bullish trend line (from HLs)
        swings = df_hist[df_hist['hl']].copy()
        if len(swings) >= 3:
            recent_swings = swings.tail(5)
            x = recent_swings['time_num'].values
            y = recent_swings['low'].values
            n = len(x)
            if n >= 2:
                m = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
                b = (np.sum(y) - m * np.sum(x)) / n
                avg_price = df_hist['low'].mean()
                slope_pct = (m / avg_price) * 100
                angle = np.degrees(np.arctan(slope_pct / 10))
                if 15 <= abs(angle) <= 45:
                    predicted = m * x + b
                    deviations = np.abs(y - predicted) / y * 100
                    touches = np.sum(deviations < 2.0)
                    current_time = df_hist.loc[idx, 'time_num']
                    trend_value = m * current_time + b
                else:
                    trend_value, touches, angle, slope_pct = np.nan, 0, angle, slope_pct
            else:
                trend_value, touches, angle, slope_pct = np.nan, 0, np.nan, np.nan
        else:
            trend_value, touches, angle, slope_pct = np.nan, 0, np.nan, np.nan
        
        # Bearish trend line (from LHs)
        swings_bear = df_hist[df_hist['lh']].copy()
        if len(swings_bear) >= 3:
            recent_swings_bear = swings_bear.tail(5)
            x_b = recent_swings_bear['time_num'].values
            y_b = recent_swings_bear['high'].values
            n_b = len(x_b)
            if n_b >= 2:
                m_b = (n_b * np.sum(x_b * y_b) - np.sum(x_b) * np.sum(y_b)) / (n_b * np.sum(x_b**2) - np.sum(x_b)**2)
                b_b = (np.sum(y_b) - m_b * np.sum(x_b)) / n_b
                avg_price_b = df_hist['high'].mean()
                slope_pct_b = (m_b / avg_price_b) * 100
                angle_b = np.degrees(np.arctan(slope_pct_b / 10))
                if 15 <= abs(angle_b) <= 45:
                    predicted_b = m_b * x_b + b_b
                    deviations_b = np.abs(y_b - predicted_b) / y_b * 100
                    touches_b = np.sum(deviations_b < 2.0)
                    current_time_b = df_hist.loc[idx, 'time_num']
                    trend_value_b = m_b * current_time_b + b_b
                else:
                    trend_value_b, touches_b, angle_b, slope_pct_b = np.nan, 0, angle_b, slope_pct_b
            else:
                trend_value_b, touches_b, angle_b, slope_pct_b = np.nan, 0, np.nan, np.nan
        else:
            trend_value_b, touches_b, angle_b, slope_pct_b = np.nan, 0, np.nan, np.nan
        
        trend_data.append([
            trend_value, touches, angle, slope_pct,
            trend_value_b, touches_b, angle_b, slope_pct_b
        ])
    
    trend_array = np.array(trend_data)
    
    # Bullish trend line
    df['bull_trend_line'] = trend_array[:, 0]
    df['bull_trend_touches'] = trend_array[:, 1]
    df['bull_trend_valid'] = (trend_array[:, 1] >= 3) & (np.abs(trend_array[:, 2]) >= 15) & (np.abs(trend_array[:, 2]) <= 45)
    df['bull_trend_angle'] = trend_array[:, 2]
    df['bull_trend_slope_pct'] = trend_array[:, 3]
    df['dist_to_bull_trend'] = (df['close'] - df['bull_trend_line']) / df['close'] * 100
    
    # Bearish trend line
    df['bear_trend_line'] = trend_array[:, 4]
    df['bear_trend_touches'] = trend_array[:, 5]
    df['bear_trend_valid'] = (trend_array[:, 5] >= 3) & (np.abs(trend_array[:, 6]) >= 15) & (np.abs(trend_array[:, 6]) <= 45)
    df['bear_trend_angle'] = trend_array[:, 6]
    df['bear_trend_slope_pct'] = trend_array[:, 7]
    df['dist_to_bear_trend'] = (df['bear_trend_line'] - df['close']) / df['close'] * 100
    
    # Trend line signals
    df['above_bull_trend'] = df['close'] > df['bull_trend_line']
    df['below_bear_trend'] = df['close'] < df['bear_trend_line']
    df['between_trend_lines'] = (df['close'] < df['bear_trend_line']) & (df['close'] > df['bull_trend_line'])
    df['broke_bull_trend'] = (df['close'].shift(1) > df['bull_trend_line'].shift(1)) & (df['close'] < df['bull_trend_line'])
    df['broke_bear_trend'] = (df['close'].shift(1) < df['bear_trend_line'].shift(1)) & (df['close'] > df['bear_trend_line'])
    
    # Reset index
    df.reset_index(inplace=True)
    
    return df

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT Weekly Indicator Calculator")
    print("="*70)
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] ❌ Input file not found: {INPUT_FILE}")
        return
    
    print(f"[{datetime.now()}] Loading raw data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"[{datetime.now()}] ✅ Loaded {len(df)} weekly candles")
    
    df = calculate_indicators(df)
    
    ohlcv_cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 
                  'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                  'taker_buy_quote', 'ignore']
    indicator_count = len([c for c in df.columns if c not in ohlcv_cols])
    
    print(f"[{datetime.now()}] Saving {indicator_count} indicators to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[{datetime.now()}] ✅ Saved successfully")
    
    metadata = {
        "timeframe": "1w",
        "symbol": "ETHUSDT",
        "candles": len(df),
        "indicators": indicator_count,
        "calculated_at": datetime.now().isoformat(),
        "date_range": {
            "start": df['open_time'].min().isoformat() if hasattr(df['open_time'].min(), 'isoformat') else str(df['open_time'].min()),
            "end": df['open_time'].max().isoformat() if hasattr(df['open_time'].max(), 'isoformat') else str(df['open_time'].max())
        },
        "indicator_categories": {
            "trend": ["ema_9", "ema_21", "ema_50", "ema_200", "sma_20", "sma_50", "trend_bullish", "trend_strong"],
            "momentum": ["rsi", "rsi_sma", "macd_line", "macd_signal", "macd_hist"],
            "volatility": ["atr", "atr_pct", "bb_middle", "bb_upper", "bb_lower", "bb_width", "bb_position"],
            "volume": ["volume_sma_20", "volume_ratio", "vwap", "vwap_distance"],
            "trend_strength": ["plus_di", "minus_di", "adx", "adx_trending"],
            "trend_lines": [
                "bull_trend_line", "bull_trend_touches", "bull_trend_valid", "bull_trend_angle", "bull_trend_slope_pct", "dist_to_bull_trend",
                "bear_trend_line", "bear_trend_touches", "bear_trend_valid", "bear_trend_angle", "bear_trend_slope_pct", "dist_to_bear_trend",
                "above_bull_trend", "below_bear_trend", "between_trend_lines", "broke_bull_trend", "broke_bear_trend"
            ],
            "support_resistance": [
                "resistance_1", "resistance_2", "resistance_3", "resistance_4",
                "support_1", "support_2", "support_3", "support_4",
                "dist_to_resistance_1", "dist_to_support_1",
                "sr_zone_size", "position_in_sr_zone"
            ],
            "fibonacci": [
                "fib_0", "fib_236", "fib_382", "fib_500", "fib_618", "fib_786", "fib_100",
                "fib_1272", "fib_1382", "fib_1618", "fib_200", "fib_2618", "fib_4236",
                "fib_position"
            ],
            "structure": ["hh", "hl", "lh", "ll", "structure_score", "structure_bullish", "structure_bearish"],
            "price_action": ["body_size", "upper_wick", "lower_wick", "range", "range_pct", "is_bullish", "is_bearish", "consecutive_bullish", "swing_high", "swing_low", "range_location"]
        }
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[{datetime.now()}] ✅ Metadata saved to {METADATA_FILE}")
    
    print("="*70)
    print(f"Complete! {indicator_count} indicators calculated for {len(df)} weekly candles")
    print("="*70)

if __name__ == "__main__":
    main()
