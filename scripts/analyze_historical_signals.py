#!/usr/bin/env python3
"""
ETHUSDT Historical Signal Analysis
Runs detection system on historical data to capture real indicator values
"""

import pandas as pd
import json
import csv
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
                # Use index as proxy for time, or close_time if available
                if 'close_time' in df.columns:
                    df['open_time'] = pd.to_datetime(df['close_time'], unit='ms')
                else:
                    # Create synthetic timestamps
                    df['open_time'] = pd.date_range(start='2025-01-01', periods=len(df), freq='H')
                data[tf] = df.sort_values('open_time')
                print(f"  Loaded {tf}: {len(df)} candles")
            except Exception as e:
                print(f"  Warning: Could not load {tf}: {e}")
    
    return data

def get_indicator_values(timestamp, data):
    """Get indicator values at specific timestamp"""
    indicators = {}
    
    # Get 1h data (primary timeframe)
    if '1h' in data:
        df = data['1h']
        mask = df['open_time'] <= timestamp
        if mask.any():
            row = df[mask].iloc[-1]
            indicators = {
                'ema_9': row.get('ema_9', 0),
                'ema_21': row.get('ema_21', 0),
                'ema_50': row.get('ema_50', 0),
                'rsi': row.get('rsi', 50),
                'atr': row.get('atr_14', 0),
                'vwap': row.get('vwap', 0),
                'close': row.get('close', 0),
                'volume': row.get('volume', 0),
                'bb_upper': row.get('bb_upper', 0),
                'bb_lower': row.get('bb_lower', 0),
                'macd': row.get('macd', 0),
                'macd_signal': row.get('macd_signal', 0),
            }
    
    return indicators

def calculate_confluence(timestamp, data):
    """Calculate confluence score at timestamp"""
    bullish_count = 0
    bearish_count = 0
    total = 0
    
    # Check 1h, 4h, 1d
    for tf in ['1h', '4h', '1d']:
        if tf in data:
            df = data[tf]
            mask = df['open_time'] <= timestamp
            if mask.any():
                row = df[mask].iloc[-1]
                ema_bullish = row.get('ema_9', 0) > row.get('ema_21', 0)
                if ema_bullish:
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
    
    row = df[mask].iloc[-1]
    
    # Get key values
    ema_9 = row.get('ema_9', 0)
    ema_21 = row.get('ema_21', 0)
    ema_50 = row.get('ema_50', 0)
    adx = row.get('adx', 15)
    close = row.get('close', 0)
    bb_width = (row.get('bb_upper', close) - row.get('bb_lower', close)) / close if close else 0
    
    # Regime classification
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
    elif bb_width < 0.1:
        return 'bullish_accumulation' if ema_9 > ema_21 else 'bearish_distribution'
    elif bb_width > 0.2:
        return 'volatile_chop'
    else:
        return 'ranging'

def generate_historical_signals():
    """Generate historical trade signals with full analysis"""
    print("="*100)
    print("  HISTORICAL SIGNAL ANALYSIS - Loading Data")
    print("="*100)
    print()
    
    data = load_timeframe_data()
    
    if '1h' not in data:
        print("Error: No 1h data available")
        return
    
    print()
    print("Analyzing historical signals...")
    print()
    
    # Use 1h data as base
    df_1h = data['1h']
    
    # Sample every 4th candle to avoid over-trading
    sample_indices = range(0, len(df_1h), 4)
    
    signals = []
    
    for idx in sample_indices:
        if len(signals) >= 100:  # Limit to 100 signals
            break
            
        row = df_1h.iloc[idx]
        timestamp = row['open_time']
        
        # Get indicators
        indicators = get_indicator_values(timestamp, data)
        
        # Calculate confluence
        direction, confluence_count, total_tf, score = calculate_confluence(timestamp, data)
        
        # Classify regime
        regime = classify_regime(timestamp, data)
        
        # Determine if this would be a trade
        # Require: 2+ confluence, abs(score) > 0.5, not neutral
        is_signal = confluence_count >= 2 and abs(score) >= 0.5 and direction != 'NEUTRAL'
        
        if is_signal:
            # Calculate hypothetical entry/exit
            entry_price = row['close']
            atr = indicators.get('atr', entry_price * 0.02)
            
            if direction == 'LONG':
                stop_price = entry_price - (1.5 * atr)
                target_price = entry_price + (2.0 * atr)
            else:
                stop_price = entry_price + (1.5 * atr)
                target_price = entry_price - (2.0 * atr)
            
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
                'indicators': {
                    'ema_9': round(indicators.get('ema_9', 0), 2),
                    'ema_21': round(indicators.get('ema_21', 0), 2),
                    'ema_50': round(indicators.get('ema_50', 0), 2),
                    'rsi': round(indicators.get('rsi', 50), 2),
                    'atr': round(indicators.get('atr', 0), 2),
                    'vwap': round(indicators.get('vwap', 0), 2),
                    'volume': round(indicators.get('volume', 0), 2),
                },
                'logic': {
                    'ema_trend': 'BULLISH' if indicators.get('ema_9', 0) > indicators.get('ema_21', 0) else 'BEARISH',
                    'rsi_condition': 'OVERSOLD' if indicators.get('rsi', 50) < 30 else 'OVERBOUGHT' if indicators.get('rsi', 50) > 70 else 'NEUTRAL',
                    'price_vs_vwap': 'ABOVE' if entry_price > indicators.get('vwap', 0) else 'BELOW',
                    'confluence_met': confluence_count >= 2,
                    'regime_favorable': regime in ['strong_uptrend', 'uptrend_with_pullback', 'ranging'] if direction == 'LONG' else regime in ['strong_downtrend', 'downtrend_with_bounce', 'ranging'],
                },
                'decision': f"ENTER {direction} - {confluence_count} timeframes aligned, {regime} regime"
            }
            
            signals.append(signal)
    
    # Save to JSON
    output_file = DATA_DIR / "historical_signals_detailed.json"
    with open(output_file, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_signals': len(signals),
            'signals': signals
        }, f, indent=2)
    
    print(f"✅ Generated {len(signals)} historical signals")
    print(f"File saved: {output_file}")
    print()
    
    # Display summary
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
    
    # Save CSV version
    csv_file = DATA_DIR / "historical_signals.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Signal #', 'Date', 'Time', 'Direction', 'Confluence', 'Score', 'Regime',
            'Entry $', 'Stop $', 'Target $',
            'EMA 9', 'EMA 21', 'EMA 50', 'RSI', 'ATR', 'VWAP',
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
                sig['indicators']['ema_9'],
                sig['indicators']['ema_21'],
                sig['indicators']['ema_50'],
                sig['indicators']['rsi'],
                sig['indicators']['atr'],
                sig['indicators']['vwap'],
                sig['decision']
            ])
    
    print(f"CSV version saved: {csv_file}")
    print()

if __name__ == "__main__":
    generate_historical_signals()
