#!/usr/bin/env python3
"""
ETHUSDT 4H Indicator Calculator
Calculates 139 technical indicators for 4h (4-hour) timeframe
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

DATA_DIR = Path("/root/.openclaw/workspace/data/binance_historical")
INPUT_FILE = DATA_DIR / "ETHUSDT_4h_2022_2024.csv"
OUTPUT_FILE = DATA_DIR / "ETHUSDT_4h_indicators.csv"
METADATA_FILE = DATA_DIR / "ETHUSDT_4h_metadata.json"

def calculate_candlestick_patterns(df):
    """Calculate candlestick pattern indicators"""
    patterns = {}
    
    open_price = df['open']
    high = df['high']
    low = df['low']
    close = df['close']
    
    body = close - open_price
    body_size = np.abs(body)
    upper_wick = high - np.maximum(open_price, close)
    lower_wick = np.minimum(open_price, close) - low
    range_size = high - low
    
    prev_open = open_price.shift(1)
    prev_close = close.shift(1)
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_body = prev_close - prev_open
    prev_body_size = np.abs(prev_body)
    
    patterns['cdl_doji'] = body_size <= (range_size * 0.1)
    patterns['cdl_longleg_doji'] = patterns['cdl_doji'] & (upper_wick > body_size * 2) & (lower_wick > body_size * 2)
    patterns['cdl_gravestone_doji'] = patterns['cdl_doji'] & (lower_wick <= body_size) & (upper_wick > body_size * 2)
    patterns['cdl_dragonfly_doji'] = patterns['cdl_doji'] & (upper_wick <= body_size) & (lower_wick > body_size * 2)
    patterns['cdl_hammer'] = (lower_wick > body_size * 2) & (upper_wick <= body_size * 0.5) & (close > open_price)
    patterns['cdl_inverted_hammer'] = (upper_wick > body_size * 2) & (lower_wick <= body_size * 0.5) & (close > open_price)
    patterns['cdl_hanging_man'] = (lower_wick > body_size * 2) & (upper_wick <= body_size * 0.5) & (close < open_price) & (close.shift(1) > close.shift(2))
    patterns['cdl_shooting_star'] = (upper_wick > body_size * 2) & (lower_wick <= body_size * 0.5) & (close < open_price)
    patterns['cdl_bullish_engulfing'] = (body > 0) & (prev_body < 0) & (open_price < prev_close) & (close > prev_open)
    patterns['cdl_bearish_engulfing'] = (body < 0) & (prev_body > 0) & (open_price > prev_close) & (close < prev_open)
    patterns['cdl_harami_bullish'] = (prev_body < 0) & (body > 0) & (open_price > prev_close) & (close < prev_open) & (body_size < prev_body_size * 0.5)
    patterns['cdl_harami_bearish'] = (prev_body > 0) & (body < 0) & (open_price < prev_close) & (close > prev_open) & (body_size < prev_body_size * 0.5)
    patterns['cdl_piercing_line'] = (prev_body < 0) & (body > 0) & (open_price < prev_low) & (close > (prev_open + prev_close) / 2) & (close < prev_open)
    patterns['cdl_dark_cloud_cover'] = (prev_body > 0) & (body < 0) & (open_price > prev_high) & (close < (prev_open + prev_close) / 2) & (close > prev_close)
    patterns['cdl_morning_star'] = (prev_body.shift(2) < 0) & (body_size.shift(1) < prev_body_size.shift(2) * 0.3) & (body > 0) & (close > (prev_open.shift(2) + prev_close.shift(2)) / 2)
    patterns['cdl_evening_star'] = (prev_body.shift(2) > 0) & (body_size.shift(1) < prev_body_size.shift(2) * 0.3) & (body < 0) & (close < (prev_open.shift(2) + prev_close.shift(2)) / 2)
    patterns['cdl_three_white_soldiers'] = (body > 0) & (body.shift(1) > 0) & (body.shift(2) > 0) & (close > close.shift(1)) & (close.shift(1) > close.shift(2))
    patterns['cdl_three_black_crows'] = (body < 0) & (body.shift(1) < 0) & (body.shift(2) < 0) & (close < close.shift(1)) & (close.shift(1) < close.shift(2))
    patterns['cdl_marubozu_white'] = (body > 0) & (upper_wick <= body_size * 0.05) & (lower_wick <= body_size * 0.05)
    patterns['cdl_marubozu_black'] = (body < 0) & (upper_wick <= body_size * 0.05) & (lower_wick <= body_size * 0.05)
    patterns['cdl_spinning_top'] = (body_size < range_size * 0.3) & (upper_wick > body_size) & (lower_wick > body_size)
    
    return pd.DataFrame(patterns)

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators for 4h data"""
    
    print(f"[{datetime.now()}] Calculating indicators for {len(df)} 4h candles...")
    
    df = df.copy()
    df['open_time'] = pd.to_datetime(df['open_time'])
    df.set_index('open_time', inplace=True)
    df.sort_index(inplace=True)
    
    # ========== TREND INDICATORS ==========
    print(f"[{datetime.now()}]  - Trend indicators...")
    
    for period in [5, 9, 12, 21, 26, 34, 50, 100, 200]:
        df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    for period in [10, 20, 30, 50, 100, 200]:
        df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
    
    df['trend_bullish'] = df['ema_9'] > df['ema_21']
    df['trend_strong'] = (df['ema_9'] > df['ema_21']) & (df['ema_21'] > df['ema_50'])
    df['golden_cross'] = (df['ema_50'].shift(1) <= df['ema_200'].shift(1)) & (df['ema_50'] > df['ema_200'])
    df['death_cross'] = (df['ema_50'].shift(1) >= df['ema_200'].shift(1)) & (df['ema_50'] < df['ema_200'])
    
    for period in [9, 21, 50, 200]:
        df[f'ema_{period}_dist'] = (df['close'] - df[f'ema_{period}']) / df[f'ema_{period}'] * 100
    
    # EMA slope
    for period in [9, 21, 50]:
        df[f'ema_{period}_slope'] = df[f'ema_{period}'].diff() / df[f'ema_{period}'].shift(1) * 100
    
    # ========== MOMENTUM ==========
    print(f"[{datetime.now()}]  - Momentum...")
    
    for period in [6, 10, 14, 21]:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
    
    df['rsi_overbought'] = df['rsi_14'] > 70
    df['rsi_oversold'] = df['rsi_14'] < 30
    df['rsi_divergence_bull'] = (df['low'] < df['low'].shift(1)) & (df['rsi_14'] > df['rsi_14'].shift(1))
    df['rsi_divergence_bear'] = (df['high'] > df['high'].shift(1)) & (df['rsi_14'] < df['rsi_14'].shift(1))
    
    for fast, slow, signal in [(12, 26, 9), (8, 21, 5), (19, 39, 9)]:
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        df[f'macd_{fast}_{slow}'] = ema_fast - ema_slow
        df[f'macd_signal_{fast}_{slow}'] = df[f'macd_{fast}_{slow}'].ewm(span=signal, adjust=False).mean()
        df[f'macd_hist_{fast}_{slow}'] = df[f'macd_{fast}_{slow}'] - df[f'macd_signal_{fast}_{slow}']
    
    rsi = df['rsi_14']
    rsi_min = rsi.rolling(window=14).min()
    rsi_max = rsi.rolling(window=14).max()
    df['stoch_rsi'] = (rsi - rsi_min) / (rsi_max - rsi_min) * 100
    df['stoch_rsi_k'] = df['stoch_rsi'].rolling(window=3).mean()
    df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=3).mean()
    
    low_14 = df['low'].rolling(window=14).min()
    high_14 = df['high'].rolling(window=14).max()
    df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    df['williams_r'] = -100 * (high_14 - df['close']) / (high_14 - low_14)
    
    tp = (df['high'] + df['low'] + df['close']) / 3
    tp_sma = tp.rolling(window=20).mean()
    tp_std = tp.rolling(window=20).std()
    df['cci'] = (tp - tp_sma) / (0.015 * tp_std)
    
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    raw_money_flow = typical_price * df['volume']
    positive_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=14).sum()
    negative_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=14).sum()
    money_flow_ratio = positive_flow / negative_flow
    df['mfi'] = 100 - (100 / (1 + money_flow_ratio))
    
    # ROC
    for period in [10, 20]:
        df[f'roc_{period}'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100
    
    # ========== VOLATILITY ==========
    print(f"[{datetime.now()}]  - Volatility...")
    
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    for period in [7, 14, 21]:
        df[f'atr_{period}'] = true_range.rolling(period).mean()
    df['atr_pct'] = df['atr_14'] / df['close'] * 100
    
    for period in [20, 50]:
        df[f'bb_middle_{period}'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df[f'bb_upper_{period}'] = df[f'bb_middle_{period}'] + (bb_std * 2)
        df[f'bb_lower_{period}'] = df[f'bb_middle_{period}'] - (bb_std * 2)
        df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / df[f'bb_middle_{period}']
        df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])
        df[f'bb_squeeze_{period}'] = df[f'bb_width_{period}'] < df[f'bb_width_{period}'].rolling(window=20).mean() * 0.5
    
    df['kc_middle'] = df['ema_21']
    df['kc_upper'] = df['kc_middle'] + (df['atr_14'] * 2)
    df['kc_lower'] = df['kc_middle'] - (df['atr_14'] * 2)
    
    df['dc_upper'] = df['high'].rolling(window=20).max()
    df['dc_lower'] = df['low'].rolling(window=20).min()
    df['dc_middle'] = (df['dc_upper'] + df['dc_lower']) / 2
    
    # Historical volatility
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    for period in [10, 20]:
        df[f'hist_vol_{period}'] = df['log_returns'].rolling(window=period).std() * np.sqrt(365) * 100
    
    # ========== VOLUME ==========
    print(f"[{datetime.now()}]  - Volume...")
    
    for period in [10, 20, 50]:
        df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
        df[f'volume_ema_{period}'] = df['volume'].ewm(span=period, adjust=False).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']
    df['volume_ratio_50'] = df['volume'] / df['volume_sma_50']
    df['volume_delta'] = df['volume'] - df['volume'].shift(1)
    df['volume_delta_pct'] = df['volume_delta'] / df['volume'].shift(1) * 100
    
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
    df['obv_ema'] = df['obv'].ewm(span=20, adjust=False).mean()
    
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    df['vwap'] = df['tp_volume'].rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
    df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    df['vwma_20'] = df['tp_volume'].rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
    
    # Volume profile
    df['volume_price_corr'] = df['close'].rolling(window=20).corr(df['volume'])
    
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
    df['plus_di'] = 100 * (df['plus_dm'].rolling(window=14).mean() / df['atr_14'])
    df['minus_di'] = 100 * (df['minus_dm'].rolling(window=14).mean() / df['atr_14'])
    df['dx'] = 100 * np.abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    df['adx'] = df['dx'].rolling(window=14).mean()
    df['adx_trending'] = df['adx'] > 25
    df['adx_strong'] = df['adx'] > 50
    df['adx_weak'] = df['adx'] < 20
    
    # DMI cross
    df['dmi_bull_cross'] = (df['plus_di'].shift(1) <= df['minus_di'].shift(1)) & (df['plus_di'] > df['minus_di'])
    df['dmi_bear_cross'] = (df['plus_di'].shift(1) >= df['minus_di'].shift(1)) & (df['plus_di'] < df['minus_di'])
    
    # ========== FIBONACCI ==========
    print(f"[{datetime.now()}]  - Fibonacci...")
    
    recent_high = df['high'].rolling(window=20).max()
    recent_low = df['low'].rolling(window=20).min()
    fib_range = recent_high - recent_low
    
    for level in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]:
        df[f'fib_{int(level*1000)}'] = recent_high - (fib_range * level)
    for ext in [1.272, 1.382, 1.618, 2.0, 2.618, 3.0, 4.236]:
        df[f'fib_{int(ext*1000)}'] = recent_high + (fib_range * (ext - 1))
    df['fib_position'] = (recent_high - df['close']) / fib_range
    
    # ========== STRUCTURE ==========
    print(f"[{datetime.now()}]  - Structure...")
    
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
    print(f"[{datetime.now()}]  - Price action...")
    
    df['body_size'] = np.abs(df['close'] - df['open'])
    df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
    df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
    df['range'] = df['high'] - df['low']
    df['range_pct'] = df['range'] / df['close'] * 100
    df['is_bullish'] = df['close'] > df['open']
    df['is_bearish'] = df['close'] < df['open']
    df['consecutive_bullish'] = df['is_bullish'].astype(int).groupby((df['is_bullish'] != df['is_bullish'].shift()).cumsum()).cumsum()
    df['consecutive_bearish'] = df['is_bearish'].astype(int).groupby((df['is_bearish'] != df['is_bearish'].shift()).cumsum()).cumsum()
    df['swing_high'] = swing_highs
    df['swing_low'] = swing_lows
    df['range_location'] = (df['close'] - df['low']) / (df['high'] - df['low']) * 100
    
    df['body_pct'] = df['body_size'] / df['range'] * 100
    df['upper_wick_pct'] = df['upper_wick'] / df['range'] * 100
    df['lower_wick_pct'] = df['lower_wick'] / df['range'] * 100
    
    df['gap_up'] = df['low'] > df['high'].shift(1)
    df['gap_down'] = df['high'] < df['low'].shift(1)
    
    # ========== CANDLESTICK PATTERNS ==========
    print(f"[{datetime.now()}]  - Candlestick patterns...")
    
    patterns = calculate_candlestick_patterns(df)
    for col in patterns.columns:
        df[col] = patterns[col]
    
    # ========== S/R LEVELS ==========
    print(f"[{datetime.now()}]  - S/R levels...")
    
    sr_data = []
    for idx in df.index:
        df_hist = df.loc[:idx]
        hh_vals = df_hist[df_hist['hh']]['high'].tail(4).values
        res = [np.nan] * (4 - len(hh_vals)) + list(hh_vals)
        ll_vals = df_hist[df_hist['ll']]['low'].tail(4).values
        sup = [np.nan] * (4 - len(ll_vals)) + list(ll_vals)
        sr_data.append(res + sup)
    
    sr_array = np.array(sr_data)
    for i in range(4):
        df[f'resistance_{i+1}'] = sr_array[:, i]
        df[f'support_{i+1}'] = sr_array[:, i + 4]
    
    df['dist_to_resistance_1'] = (df['resistance_1'] - df['close']) / df['close'] * 100
    df['dist_to_support_1'] = (df['close'] - df['support_1']) / df['close'] * 100
    df['sr_zone_size'] = (df['resistance_1'] - df['support_1']) / df['close'] * 100
    df['position_in_sr_zone'] = (df['close'] - df['support_1']) / (df['resistance_1'] - df['support_1'] + 0.0001) * 100
    
    # ========== TREND LINES ==========
    print(f"[{datetime.now()}]  - Trend lines...")
    
    trend_data = []
    for idx in df.index:
        df_hist = df.loc[:idx].copy()
        df_hist['time_num'] = np.arange(len(df_hist))
        
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
        
        trend_data.append([trend_value, touches, angle, slope_pct, trend_value_b, touches_b, angle_b, slope_pct_b])
    
    trend_array = np.array(trend_data)
    df['bull_trend_line'] = trend_array[:, 0]
    df['bull_trend_touches'] = trend_array[:, 1]
    df['bull_trend_valid'] = (trend_array[:, 1] >= 3) & (np.abs(trend_array[:, 2]) >= 15) & (np.abs(trend_array[:, 2]) <= 45)
    df['bull_trend_angle'] = trend_array[:, 2]
    df['bull_trend_slope_pct'] = trend_array[:, 3]
    df['dist_to_bull_trend'] = (df['close'] - df['bull_trend_line']) / df['close'] * 100
    
    df['bear_trend_line'] = trend_array[:, 4]
    df['bear_trend_touches'] = trend_array[:, 5]
    df['bear_trend_valid'] = (trend_array[:, 5] >= 3) & (np.abs(trend_array[:, 6]) >= 15) & (np.abs(trend_array[:, 6]) <= 45)
    df['bear_trend_angle'] = trend_array[:, 6]
    df['bear_trend_slope_pct'] = trend_array[:, 7]
    df['dist_to_bear_trend'] = (df['bear_trend_line'] - df['close']) / df['close'] * 100
    
    df['above_bull_trend'] = df['close'] > df['bull_trend_line']
    df['below_bear_trend'] = df['close'] < df['bear_trend_line']
    
    # Reset index
    df.reset_index(inplace=True)
    
    return df

def main():
    print("="*70)
    print("ETHUSDT 4H Indicator Calculator")
    print("="*70)
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] Input file not found: {INPUT_FILE}")
        return
    
    print(f"[{datetime.now()}] Loading raw data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"[{datetime.now()}] Loaded {len(df)} 4h candles")
    
    df = calculate_indicators(df)
    
    ohlcv_cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 
                  'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                  'taker_buy_quote_volume', 'ignore']
    indicator_count = len([c for c in df.columns if c not in ohlcv_cols])
    
    print(f"[{datetime.now()}] Saving {indicator_count} indicators to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[{datetime.now()}] Saved successfully")
    
    metadata = {
        "timeframe": "4h",
        "symbol": "ETHUSDT",
        "candles": len(df),
        "indicators": indicator_count,
        "calculated_at": datetime.now().isoformat(),
        "date_range": {"start": str(df['open_time'].min()), "end": str(df['open_time'].max())}
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[{datetime.now()}] Metadata saved to {METADATA_FILE}")
    
    print("="*70)
    print(f"Complete! {indicator_count} indicators calculated for {len(df)} 4h candles")
    print("="*70)

if __name__ == "__main__":
    main()
