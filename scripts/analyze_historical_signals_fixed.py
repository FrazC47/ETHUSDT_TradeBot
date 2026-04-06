#!/usr/bin/env python3
"""
ETHUSDT Historical Signal Analysis - FIXED VERSION
Runs detection system on historical data to capture real indicator values
"""

import pandas as pd
import json
import csv
import numpy as np
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")

def load_timeframe_data():
    """Load all timeframe data"""
    data = {}
    timeframes = ['1M', '1w', '1d', '4h', '1h', '15m']
    
    for tf in timeframes:
        file = DATA_DIR / f"ETHUSDT_{tf}_indicators.csv"
        if file.exists():
            try:
                df = pd.read_csv(file)
                # Use close_time for timestamp
                if 'close_time' in df.columns:
                    df['open_time'] = pd.to_datetime(df['close_time'], unit='ms')
                data[tf] = df.sort_values('open_time').reset_index(drop=True)
                print(f"  Loaded {tf}: {len(df)} candles")
            except Exception as e:
                print(f"  Warning: Could not load {tf}: {e}")
    
    return data

def get_valid_value(df, idx, col, default=0):
    """Get valid (non-NaN) value from dataframe, looking backwards if needed"""
    if col not in df.columns:
        return default
    
    for i in range(idx, max(idx-100, -1), -1):
        if i >= 0:
            val = df.loc[i, col]
            if pd.notna(val):
                return val
    return default

def get_indicator_values(timestamp, data):
    """Get indicator values at specific timestamp"""
    indicators = {}
    
    # Get 1h data (primary timeframe)
    if '1h' in data:
        df = data['1h']
        mask = df['open_time'] <= timestamp
        if mask.any():
            idx = df[mask].index[-1]
            
            indicators = {
                'ema_9': get_valid_value(df, idx, 'ema_9', 0),
                'ema_21': get_valid_value(df, idx, 'ema_21', 0),
                'ema_50': get_valid_value(df, idx, 'ema_50', 0),
                'rsi': get_valid_value(df, idx, 'rsi', 50),
                'atr': get_valid_value(df, idx, 'atr', 50),
                'atr_pct': get_valid_value(df, idx, 'atr_pct', 2.5),
                'vwap': get_valid_value(df, idx, 'vwap', get_valid_value(df, idx, 'close', 2000)),
                'close': get_valid_value(df, idx, 'close', 2000),
                'volume': get_valid_value(df, idx, 'volume', 0),
                'bb_upper': get_valid_value(df, idx, 'bb_upper', 0),
                'bb_lower': get_valid_value(df, idx, 'bb_lower', 0),
                'adx': get_valid_value(df, idx, 'adx', 20),
            }
    
    return indicators

def calculate_confluence(timestamp, data):
    """Calculate confluence score at timestamp"""
    bullish_count = 0
    bearish_count = 0
    total = 0
    
    for tf in ['1h', '4h', '1d']:
        if tf in data:
            df = data[tf]
            mask = df['open_time'] <= timestamp
            if mask.any():
                idx = df[mask].index[-1]
                ema_9 = get_valid_value(df, idx, 'ema_9', 0)
                ema_21 = get_valid_value(df, idx, 'ema_21', 0)
                
                if ema_9 > ema_21:
                    bullish_count += 1
                else:
                    bearish_count += 1
                total += 1
    
    if total == 0:
        return 'NEUTRAL', 0, 0, 0
    
    if bullish_count >= 2:
        return 'LONG', bullish_count, total, bullish_count/total
    elif bearish_count >= 2:
        return 'SHORT', bearish_count, total, -bearish_count/total
    else:
        return 'NEUTRAL', 0, total, 0

def classify_regime(timestamp, data):
    """Classify market regime at timestamp"""
    if '1h' not in data:
        return 'unknown'
    
    df = data['1h']
    mask = df['open_time'] <= timestamp
    if not mask.any():
        return 'unknown'
    
    idx = df[mask].index[-1]
    
    ema_9 = get_valid_value(df, idx, 'ema_9', 0)
    ema_21 = get_valid_value(df, idx, 'ema_21', 0)
    ema_50 = get_valid_value(df, idx, 'ema_50', 0)
    adx = get_valid_value(df, idx, 'adx', 15)
    close = get_valid_value(df, idx, 'close', 2000)
    bb_upper = get_valid_value(df, idx, 'bb_upper', close)
    bb_lower = get_valid_value(df, idx, 'bb_lower', close)
    
    bb_width = (bb_upper - bb_lower) / close if close > 0 else 0
    
    trend_bullish = ema_9 > ema_21 > ema_50
    trend_bearish = ema_9 < ema_21 < ema_50
    strong_trend = adx > 25
    
    if trend_bullish and strong_trend:
        return 'strong_uptrend'
    elif trend_bullish and not strong_trend:
        return 'uptrend_with_pullback'
    elif trend_bearish and strong_trend:
        return 'strong_downtrend'
    elif trend_bearish and not strong_trend:
        return 'downtrend_with_bounce'
    elif bb_width < 0.05:
        return 'bullish_accumulation' if ema_9 > ema_21 else 'bearish_distribution'
    elif bb_width > 0.15:
        return 'volatile_chop'
    else:
        return 'ranging'

def generate_historical_signals():
    """Generate historical trade signals with full analysis"""
    print("="*100)
    print("  HISTORICAL SIGNAL ANALYSIS - Loading Data (FIXED)")
    print("="*100)
    print()
    
    data = load_timeframe_data()
    
    if '1h' not in data:
        print("Error: No 1h data available")
        return
    
    print()
    print("Analyzing historical signals with proper indicator values...")
    print()
    
    df_1h = data['1h']
    
    # Sample every 4th candle
    sample_indices = range(0, len(df_1h), 4)
    
    signals = []
    
    for idx in sample_indices:
        if len(signals) >= 100:
            break
        
        row = df_1h.iloc[idx]
        timestamp = row['open_time']
        
        # Get indicators with proper NaN handling
        indicators = get_indicator_values(timestamp, data)
        
        # Calculate confluence
        direction, confluence_count, total_tf, score = calculate_confluence(timestamp, data)
        
        # Classify regime
        regime = classify_regime(timestamp, data)
        
        # Determine signal
        is_signal = confluence_count >= 2 and abs(score) >= 0.5 and direction != 'NEUTRAL'
        
        if is_signal and indicators['atr'] > 0:
            entry_price = indicators['close']
            atr = indicators['atr']
            
            if direction == 'LONG':
                stop_price = entry_price - (1.5 * atr)
                target_price = entry_price + (2.5 * atr)
            else:
                stop_price = entry_price + (1.5 * atr)
                target_price = entry_price - (2.5 * atr)
            
            # Calculate R multiple
            risk = abs(entry_price - stop_price)
            reward = abs(target_price - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            signal = {
                'signal_num': len(signals) + 1,
                'timestamp': timestamp.isoformat(),
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S'),
                'direction': direction,
                'confluence': f"{confluence_count}/{total_tf}",
                'score': round(score, 2),
                'regime': regime,
                'entry_price': round(entry_price, 2),
                'stop_price': round(stop_price, 2),
                'target_price': round(target_price, 2),
                'rr_ratio': round(rr_ratio, 2),
                'indicators': {
                    'ema_9': round(indicators['ema_9'], 2),
                    'ema_21': round(indicators['ema_21'], 2),
                    'ema_50': round(indicators['ema_50'], 2),
                    'rsi': round(indicators['rsi'], 2),
                    'atr': round(indicators['atr'], 2),
                    'atr_pct': round(indicators['atr_pct'], 3),
                    'vwap': round(indicators['vwap'], 2),
                    'volume': round(indicators['volume'], 2),
                    'adx': round(indicators['adx'], 2),
                    'bb_upper': round(indicators['bb_upper'], 2),
                    'bb_lower': round(indicators['bb_lower'], 2),
                },
                'logic': {
                    'ema_trend': 'BULLISH' if indicators['ema_9'] > indicators['ema_21'] else 'BEARISH',
                    'rsi_condition': 'OVERSOLD' if indicators['rsi'] < 30 else 'OVERBOUGHT' if indicators['rsi'] > 70 else 'NEUTRAL',
                    'price_vs_vwap': 'ABOVE' if entry_price > indicators['vwap'] else 'BELOW',
                    'adx_strength': 'STRONG' if indicators['adx'] > 25 else 'WEAK',
                    'confluence_met': confluence_count >= 2,
                    'regime_favorable': regime in ['strong_uptrend', 'uptrend_with_pullback'] if direction == 'LONG' else regime in ['strong_downtrend', 'downtrend_with_bounce'],
                },
                'decision': f"ENTER {direction} | {confluence_count}TFs aligned | {regime} | R:R {rr_ratio:.1f}:1"
            }
            
            signals.append(signal)
    
    # Save to JSON
    output_file = DATA_DIR / "historical_signals_complete.json"
    with open(output_file, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_signals': len(signals),
            'signals': signals
        }, f, indent=2)
    
    print(f"✅ Generated {len(signals)} historical signals with complete indicators")
    print(f"File saved: {output_file}")
    print()
    
    display_signals(signals)
    
    return signals

def display_signals(signals):
    """Display signals in readable format"""
    print("="*100)
    print("  SAMPLE HISTORICAL SIGNALS (First 10)")
    print("="*100)
    print()
    
    for sig in signals[:10]:
        print(f"SIGNAL #{sig['signal_num']}")
        print("-"*100)
        print(f"  Timestamp:    {sig['date']} {sig['time']}")
        print(f"  Direction:    {sig['direction']}")
        print(f"  Confluence:   {sig['confluence']} (score: {sig['score']})")
        print(f"  Regime:       {sig['regime']}")
        print(f"  R:R Ratio:    {sig['rr_ratio']}:1")
        print()
        print(f"  PRICES:")
        print(f"    Entry:      ${sig['entry_price']}")
        print(f"    Stop:       ${sig['stop_price']}")
        print(f"    Target:     ${sig['target_price']}")
        print()
        print(f"  INDICATORS:")
        for key, val in sig['indicators'].items():
            print(f"    {key:12} {val}")
        print()
        print(f"  LOGIC:")
        for key, val in sig['logic'].items():
            print(f"    {key:20} {val}")
        print()
        print(f"  DECISION:     {sig['decision']}")
        print()
        print()
    
    # Save CSV
    csv_file = DATA_DIR / "historical_signals_complete.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Signal #', 'Date', 'Time', 'Direction', 'Confluence', 'Score', 'Regime',
            'Entry $', 'Stop $', 'Target $', 'R:R',
            'EMA 9', 'EMA 21', 'EMA 50', 'RSI', 'ATR', 'ATR%', 'VWAP', 'ADX',
            'Decision'
        ])
        
        for sig in signals:
            writer.writerow([
                sig['signal_num'],
                sig['date'],
                sig['time'],
                sig['direction'],
                sig['confluence'],
                sig['score'],
                sig['regime'],
                sig['entry_price'],
                sig['stop_price'],
                sig['target_price'],
                sig['rr_ratio'],
                sig['indicators']['ema_9'],
                sig['indicators']['ema_21'],
                sig['indicators']['ema_50'],
                sig['indicators']['rsi'],
                sig['indicators']['atr'],
                sig['indicators']['atr_pct'],
                sig['indicators']['vwap'],
                sig['indicators']['adx'],
                sig['decision']
            ])
    
    print(f"CSV saved: {csv_file}")
    print()

if __name__ == "__main__":
    generate_historical_signals()
