#!/usr/bin/env python3
"""
Candlestick Pattern Detector for Daily Timeframe
Detects 16 key patterns and adds as boolean columns to indicators
"""

import pandas as pd
import numpy as np

def detect_candlestick_patterns(df):
    """
    Detect candlestick patterns for daily timeframe.
    Adds boolean columns for each pattern detected.
    """
    
    patterns = pd.DataFrame(index=df.index)
    
    # Basic candle components
    body = abs(df['close'] - df['open'])
    body_pct = body / df[['open', 'close']].max(axis=1) * 100
    upper_wick = df['high'] - df[['open', 'close']].max(axis=1)
    lower_wick = df[['open', 'close']].min(axis=1) - df['low']
    total_range = df['high'] - df['low']
    
    # Avoid division by zero
    total_range = total_range.replace(0, np.nan)
    
    upper_wick_pct = upper_wick / total_range * 100
    lower_wick_pct = lower_wick / total_range * 100
    body_position = (df['close'] - df['low']) / total_range * 100
    
    is_bullish = df['close'] > df['open']
    is_bearish = df['close'] < df['open']
    
    # ========== SINGLE CANDLE PATTERNS ==========
    
    # Doji - very small body (less than 5% of range)
    patterns['pattern_doji'] = body_pct < 5
    
    # Dragonfly Doji - long lower wick, small body at top
    patterns['pattern_dragonfly_doji'] = (
        (body_pct < 5) & 
        (lower_wick_pct > 60) & 
        (upper_wick_pct < 10)
    )
    
    # Gravestone Doji - long upper wick, small body at bottom
    patterns['pattern_gravestone_doji'] = (
        (body_pct < 5) & 
        (upper_wick_pct > 60) & 
        (lower_wick_pct < 10)
    )
    
    # Hammer - small body at top, long lower wick (2x body), after downtrend
    patterns['pattern_hammer'] = (
        (body_pct < 30) & 
        (lower_wick > 2 * body) & 
        (upper_wick_pct < 10) &
        (body_position > 60)
    )
    
    # Inverted Hammer - small body at bottom, long upper wick
    patterns['pattern_inverted_hammer'] = (
        (body_pct < 30) & 
        (upper_wick > 2 * body) & 
        (lower_wick_pct < 10) &
        (body_position < 40)
    )
    
    # Shooting Star - small body at bottom, long upper wick, after uptrend
    patterns['pattern_shooting_star'] = (
        (body_pct < 30) & 
        (upper_wick > 2 * body) & 
        (lower_wick_pct < 10) &
        (body_position < 40)
    )
    
    # Spinning Top - small body, long upper and lower wicks (indecision)
    patterns['pattern_spinning_top'] = (
        (body_pct < 30) & 
        (upper_wick_pct > 30) & 
        (lower_wick_pct > 30)
    )
    
    # ========== TWO CANDLE PATTERNS ==========
    
    prev_body = body.shift(1)
    prev_is_bullish = is_bullish.shift(1)
    prev_is_bearish = is_bearish.shift(1)
    prev_open = df['open'].shift(1)
    prev_close = df['close'].shift(1)
    prev_high = df['high'].shift(1)
    prev_low = df['low'].shift(1)
    
    # Bullish Engulfing - current candle completely engulfs previous (after bearish)
    patterns['pattern_bullish_engulfing'] = (
        is_bullish & 
        prev_is_bearish &
        (df['open'] < prev_close) & 
        (df['close'] > prev_open) &
        (body > 1.2 * prev_body)  # Current body larger than previous
    )
    
    # Bearish Engulfing - current candle completely engulfs previous (after bullish)
    patterns['pattern_bearish_engulfing'] = (
        is_bearish & 
        prev_is_bullish &
        (df['open'] > prev_close) & 
        (df['close'] < prev_open) &
        (body > 1.2 * prev_body)
    )
    
    # Tweezer Bottom - two candles with same low, first bearish, second bullish
    patterns['pattern_tweezer_bottom'] = (
        (abs(df['low'] - prev_low) / df['low'] < 0.001) &  # Same low (0.1% tolerance)
        prev_is_bearish & 
        is_bullish
    )
    
    # Tweezer Top - two candles with same high, first bullish, second bearish
    patterns['pattern_tweezer_top'] = (
        (abs(df['high'] - prev_high) / df['high'] < 0.001) &  # Same high (0.1% tolerance)
        prev_is_bullish & 
        is_bearish
    )
    
    # Bullish Harami - small body inside previous large body (after bearish)
    patterns['pattern_bullish_harami'] = (
        is_bullish &
        prev_is_bearish &
        (df['open'] > prev_close) &
        (df['close'] < prev_open) &
        (body < 0.7 * prev_body)  # Current body smaller than previous
    )
    
    # Bearish Harami - small body inside previous large body (after bullish)
    patterns['pattern_bearish_harami'] = (
        is_bearish &
        prev_is_bullish &
        (df['close'] > prev_open) &
        (df['open'] < prev_close) &
        (body < 0.7 * prev_body)
    )
    
    # ========== THREE CANDLE PATTERNS ==========
    
    prev2_open = df['open'].shift(2)
    prev2_close = df['close'].shift(2)
    prev2_is_bullish = is_bullish.shift(2)
    prev2_is_bearish = is_bearish.shift(2)
    
    # Morning Star - bearish, small body (star), bullish (strong reversal at bottom)
    patterns['pattern_morning_star'] = (
        prev2_is_bearish &  # First: bearish
        prev_is_bearish &   # Second: small body (gap down ideally)
        is_bullish &        # Third: bullish
        (body.shift(2) > body.shift(1) * 2) &  # First body larger than second
        (body > body.shift(1) * 2) &           # Third body larger than second
        (df['close'] > (prev2_open + prev2_close) / 2)  # Closes above first candle midpoint
    )
    
    # Evening Star - bullish, small body (star), bearish (strong reversal at top)
    patterns['pattern_evening_star'] = (
        prev2_is_bullish &  # First: bullish
        prev_is_bullish &   # Second: small body (gap up ideally)
        is_bearish &        # Third: bearish
        (body.shift(2) > body.shift(1) * 2) &  # First body larger than second
        (body > body.shift(1) * 2) &           # Third body larger than second
        (df['close'] < (prev2_open + prev2_close) / 2)  # Closes below first candle midpoint
    )
    
    # Three White Soldiers - three consecutive bullish candles with higher closes
    patterns['pattern_three_white_soldiers'] = (
        prev2_is_bullish & 
        prev_is_bullish & 
        is_bullish &
        (prev2_close < prev_close) & 
        (prev_close < df['close']) &  # Each closes higher
        (body.shift(2) > body.shift(1) * 0.5) &  # Bodies similar size
        (body.shift(1) > body * 0.5)
    )
    
    # Three Black Crows - three consecutive bearish candles with lower closes
    patterns['pattern_three_black_crows'] = (
        prev2_is_bearish & 
        prev_is_bearish & 
        is_bearish &
        (prev2_close > prev_close) & 
        (prev_close > df['close']) &  # Each closes lower
        (body.shift(2) > body.shift(1) * 0.5) &  # Bodies similar size
        (body.shift(1) > body * 0.5)
    )
    
    # Pattern strength score (number of patterns detected)
    patterns['pattern_count'] = patterns.sum(axis=1)
    
    # Pattern direction (bullish = +1, bearish = -1, neutral = 0)
    bullish_patterns = [
        'pattern_hammer', 'pattern_inverted_hammer', 'pattern_dragonfly_doji',
        'pattern_bullish_engulfing', 'pattern_tweezer_bottom', 'pattern_bullish_harami',
        'pattern_morning_star', 'pattern_three_white_soldiers'
    ]
    bearish_patterns = [
        'pattern_shooting_star', 'pattern_gravestone_doji', 'pattern_bearish_engulfing',
        'pattern_tweezer_top', 'pattern_bearish_harami', 'pattern_evening_star',
        'pattern_three_black_crows'
    ]
    
    patterns['pattern_bullish_score'] = patterns[bullish_patterns].sum(axis=1)
    patterns['pattern_bearish_score'] = patterns[bearish_patterns].sum(axis=1)
    patterns['pattern_bias'] = patterns['pattern_bullish_score'] - patterns['pattern_bearish_score']
    
    return patterns


if __name__ == '__main__':
    # Test
    import sys
    from pathlib import Path
    
    DATA_DIR = Path("/root/.openclaw/workspace/data")
    df = pd.read_csv(DATA_DIR / "ETHUSDT_1d.csv")
    
    patterns = detect_candlestick_patterns(df)
    
    print("Candlestick Patterns Detected:")
    print("="*50)
    for col in patterns.columns:
        if col.startswith('pattern_') and col not in ['pattern_count', 'pattern_bullish_score', 'pattern_bearish_score', 'pattern_bias']:
            count = patterns[col].sum()
            print(f"{col:30s}: {count:3d} occurrences")
    
    print("="*50)
    print(f"Total patterns detected: {patterns['pattern_count'].sum()}")
    print(f"Bullish signals: {patterns['pattern_bullish_score'].sum()}")
    print(f"Bearish signals: {patterns['pattern_bearish_score'].sum()}")
