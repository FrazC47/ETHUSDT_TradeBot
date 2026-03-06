#!/usr/bin/env python3
"""
ETHUSDT 1-Minute Indicator Calculator - Trade Spotlight
Ultra-precision indicators for entry/exit timing (~25 indicators)
Optimized for 1m noise handling
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))
from candlestick_patterns import detect_candlestick_patterns

DATA_DIR = Path("/root/.openclaw/workspace/data")
INPUT_FILE = DATA_DIR / "ETHUSDT_1m.csv"
OUTPUT_FILE = DATA_DIR / "ETHUSDT_1m_indicators.csv"

def calculate_indicators(df):
    """Calculate precision indicators for 1m trading (noise-filtered)"""
    print(f"[{datetime.now()}] Calculating 1m indicators...")
    
    df = df.copy()
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    df.sort_index(inplace=True)
    
    # ========== TREND (Fast, responsive) ==========
    print(f"[{datetime.now()}]  - EMA trend...")
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # 1m: Skip 50 EMA - too slow. Use faster signals.
    df['ema_bullish'] = df['ema_9'] > df['ema_21']
    df['ema_bearish'] = df['ema_9'] < df['ema_21']
    df['ema_trend_strength'] = (df['ema_9'] - df['ema_21']) / df['ema_21'] * 100
    
    # ========== MOMENTUM (Smoothed for noise) ==========
    print(f"[{datetime.now()}]  - RSI (smoothed)...")
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    # Extra smoothing for 1m
    df['rsi_sma_7'] = df['rsi_14'].rolling(window=7).mean()
    df['rsi_oversold'] = df['rsi_14'] < 30
    df['rsi_overbought'] = df['rsi_14'] > 70
    
    # ========== VOLATILITY ==========
    print(f"[{datetime.now()}]  - ATR / Bollinger Bands...")
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr_14'] = true_range.rolling(14).mean()
    df['atr_pct'] = df['atr_14'] / df['close'] * 100
    
    # Tighter Bollinger for 1m scalping
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(20).mean() * 0.8
    
    # ========== VOLUME / VWAP ==========
    print(f"[{datetime.now()}]  - Volume / VWAP...")
    df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']
    df['volume_spike'] = df['volume_ratio'] > 2.0  # Key for 1m confirmation
    
    # Session VWAP (reset every 4 hours for 1m)
    df['session'] = (df.index.hour // 4)
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    
    # Calculate VWAP per session
    df['vwap'] = df.groupby('session').apply(
        lambda x: x['tp_volume'].cumsum() / x['volume'].cumsum()
    ).reset_index(0, drop=True)
    
    df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    df['above_vwap'] = df['close'] > df['vwap']
    df['below_vwap'] = df['close'] < df['vwap']
    
    # ========== PRICE ACTION (Critical for 1m) ==========
    print(f"[{datetime.now()}]  - Price action...")
    df['range'] = df['high'] - df['low']
    df['range_pct'] = df['range'] / df['close'] * 100
    df['body_size'] = np.abs(df['close'] - df['open'])
    df['body_size_pct'] = df['body_size'] / df['close'] * 100
    df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
    df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
    df['upper_wick_pct'] = df['upper_wick'] / df['range'] * 100
    df['lower_wick_pct'] = df['lower_wick'] / df['range'] * 100
    
    # Wick analysis - key for 1m rejection signals
    df['upper_rejection'] = df['upper_wick_pct'] > 60  # Long upper wick
    df['lower_rejection'] = df['lower_wick_pct'] > 60  # Long lower wick
    df['is_bullish'] = df['close'] > df['open']
    df['is_bearish'] = df['close'] < df['open']
    
    # ========== MICRO STRUCTURE (3-bar for 1m speed) ==========
    print(f"[{datetime.now()}]  - Micro structure...")
    df['hh_3'] = df['high'] == df['high'].rolling(window=3, center=True).max()
    df['ll_3'] = df['low'] == df['low'].rolling(window=3, center=True).min()
    
    # Immediate micro levels
    recent_hh = df[df['hh_3']]['high'].tail(2)
    recent_ll = df[df['ll_3']]['low'].tail(2)
    df['micro_resistance'] = recent_hh.iloc[-1] if len(recent_hh) > 0 else np.nan
    df['micro_support'] = recent_ll.iloc[-1] if len(recent_ll) > 0 else np.nan
    df['dist_to_micro_res'] = (df['micro_resistance'] - df['close']) / df['close'] * 100
    df['dist_to_micro_sup'] = (df['close'] - df['micro_support']) / df['close'] * 100
    
    # ========== CANDLESTICK PATTERNS ==========
    print(f"[{datetime.now()}]  - Pattern detection...")
    pattern_df = detect_candlestick_patterns(df)
    key_patterns = ['pattern_hammer', 'pattern_inverted_hammer', 'pattern_shooting_star',
                    'pattern_bullish_engulfing', 'pattern_bearish_engulfing', 'pattern_doji']
    for col in key_patterns:
        if col in pattern_df.columns:
            df[col] = pattern_df[col]
    
    df['pattern_bullish'] = df.get('pattern_hammer', 0) | df.get('pattern_bullish_engulfing', 0)
    df['pattern_bearish'] = df.get('pattern_shooting_star', 0) | df.get('pattern_bearish_engulfing', 0)
    
    # ========== COMPOSITE SCORE (1m optimized) ==========
    print(f"[{datetime.now()}]  - Momentum score...")
    # Heavier weight on volume for 1m confirmation
    trend_score = np.where(df['ema_bullish'], 0.5, -0.5)
    rsi_score = (df['rsi_14'] - 50) / 100  # Gentler scaling
    volume_score = np.where(df['volume_spike'], 1.0, df['volume_ratio'] - 1) * 0.5
    vwap_score = np.where(df['above_vwap'], 0.5, -0.5) * np.minimum(np.abs(df['vwap_distance']) / 0.3, 1)
    rejection_score = np.where(df['lower_rejection'], 0.5, 0) - np.where(df['upper_rejection'], 0.5, 0)
    
    df['momentum_score'] = trend_score + rsi_score + volume_score + vwap_score + rejection_score
    df['momentum_bullish'] = df['momentum_score'] > 0.5
    df['momentum_bearish'] = df['momentum_score'] < -0.5
    df['high_confidence_long'] = df['momentum_bullish'] & df['volume_spike'] & df['above_vwap']
    df['high_confidence_short'] = df['momentum_bearish'] & df['volume_spike'] & df['below_vwap']
    
    # Cleanup
    df.drop(['typical_price', 'tp_volume', 'session'], axis=1, errors='ignore', inplace=True)
    
    df.reset_index(inplace=True)
    return df

def main():
    print("="*70)
    print("ETHUSDT 1-Minute Precision Indicators - Trade Spotlight")
    print("="*70)
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] No input file")
        return
    
    df = pd.read_csv(INPUT_FILE)
    print(f"[{datetime.now()}] Loaded {len(df)} 1m candles")
    
    df = calculate_indicators(df)
    
    ohlcv = ['open_time', 'open', 'high', 'low', 'close', 'volume',
             'close_time', 'quote_volume', 'trades', 'taker_buy_base',
             'taker_buy_quote', 'ignore']
    indicator_count = len([c for c in df.columns if c not in ohlcv])
    
    print(f"[{datetime.now()}] Saving {indicator_count} indicators...")
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[{datetime.now()}] ✅ Complete - {indicator_count} precision indicators")
    print("="*70)

if __name__ == "__main__":
    main()
