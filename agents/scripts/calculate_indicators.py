#!/usr/bin/env python3
"""
Indicator Pre-Calculator
Calculates and saves all indicators for each timeframe
Run once after data updates, then load pre-calculated indicators
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

class IndicatorCalculator:
    """Pre-calculates all technical indicators for all timeframes"""
    
    def __init__(self):
        self.data_dir = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/data/raw')
        self.indicator_dir = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/data/indicators')
        self.indicator_dir.mkdir(parents=True, exist_ok=True)
        
        # Timeframes to process
        self.timeframes = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']
        
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive indicators for a dataframe"""
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # ========== TREND INDICATORS ==========
        # EMAs
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # SMAs
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Trend direction
        df['trend_bullish'] = df['ema_9'] > df['ema_21']
        df['trend_strong'] = (df['ema_9'] > df['ema_21']) & (df['ema_21'] > df['ema_50'])
        
        # ========== MOMENTUM INDICATORS ==========
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_sma'] = df['rsi'].rolling(window=14).mean()
        
        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd_line'] = ema_12 - ema_26
        df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd_line'] - df['macd_signal']
        
        # ========== VOLATILITY INDICATORS ==========
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ========== VOLUME INDICATORS ==========
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_trend'] = df['volume'].rolling(window=5).mean() / df['volume'].rolling(window=20).mean()
        
        # ========== PRICE ACTION ==========
        # Candle characteristics
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
        df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
        df['range'] = df['high'] - df['low']
        df['range_pct'] = df['range'] / df['close'] * 100
        
        # Bullish/Bearish candles
        df['is_bullish'] = df['close'] > df['open']
        df['is_bearish'] = df['close'] < df['open']
        
        # Consecutive candles
        df['consecutive_bullish'] = df['is_bullish'].astype(int).groupby((df['is_bullish'] != df['is_bullish'].shift()).cumsum()).cumsum()
        
        # ========== SUPPORT/RESISTANCE LEVELS ==========
        # Swing highs/lows
        df['swing_high'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
        df['swing_low'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
        
        # ========== RANGE LOCATION ==========
        df['range_location'] = (df['close'] - df['low']) / (df['high'] - df['low']) * 100
        
        return df
    
    def process_timeframe(self, timeframe: str):
        """Process a single timeframe"""
        print(f"\nProcessing {timeframe}...")
        
        # Load raw data
        input_file = self.data_dir / f"{timeframe}.csv"
        if not input_file.exists():
            print(f"  ❌ Raw data not found: {input_file}")
            return False
        
        df = pd.read_csv(input_file)
        print(f"  📊 Loaded {len(df)} candles")
        
        # Convert timestamp
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate all indicators
        print(f"  🧮 Calculating indicators...")
        df = self.calculate_all_indicators(df)
        
        # Count calculated indicators
        indicator_count = len([c for c in df.columns if c not in 
                              ['open', 'high', 'low', 'close', 'volume', 'close_time', 
                               'quote_volume', 'trades', 'taker_buy_volume', 
                               'taker_buy_quote_volume', 'ignore']])
        
        print(f"  ✅ Calculated {indicator_count} indicators")
        
        # Save to CSV
        output_file = self.indicator_dir / f"{timeframe}_indicators.csv"
        df.to_csv(output_file)
        print(f"  💾 Saved to {output_file}")
        
        # Save metadata
        metadata = {
            'timeframe': timeframe,
            'candles': len(df),
            'indicators': indicator_count,
            'calculated_at': datetime.now().isoformat(),
            'date_range': {
                'start': df.index[0].isoformat(),
                'end': df.index[-1].isoformat()
            }
        }
        
        metadata_file = self.indicator_dir / f"{timeframe}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
    
    def run(self):
        """Process all timeframes"""
        print("="*70)
        print("INDICATOR PRE-CALCULATOR")
        print("="*70)
        print(f"\nCalculating indicators for all {len(self.timeframes)} timeframes...")
        print(f"Raw data from: {self.data_dir}")
        print(f"Output to: {self.indicator_dir}")
        print()
        
        success_count = 0
        for tf in self.timeframes:
            if self.process_timeframe(tf):
                success_count += 1
        
        print("\n" + "="*70)
        print(f"Complete! Processed {success_count}/{len(self.timeframes)} timeframes")
        print("="*70)
        
        # Save summary
        summary = {
            'calculated_at': datetime.now().isoformat(),
            'timeframes_processed': success_count,
            'total_timeframes': len(self.timeframes),
            'indicator_dir': str(self.indicator_dir)
        }
        
        with open(self.indicator_dir / 'calculation_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

if __name__ == '__main__':
    calculator = IndicatorCalculator()
    calculator.run()
