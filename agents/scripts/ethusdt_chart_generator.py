#!/usr/bin/env python3
"""
ETHUSDT-Only Pattern Chart Generator
Generates interactive HTML candlestick charts for ETHUSDT only
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Configuration
DATA_DIR = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/data/raw')
OUTPUT_DIR = Path('/root/.openclaw/workspace/ETHUSDT_TradeBot/charts')
SYMBOL = 'ETHUSDT'

# Color scheme
COLORS = {
    'up': '#26a69a',
    'down': '#ef5350',
    'wick': '#787b86',
    'bg': '#131722',
    'grid': '#2a2e39',
    'text': '#d1d4dc',
    'ema9': '#FF6D00',
    'ema21': '#00BCD4',
    'ema50': '#2196F3',
    'vwap': '#FFD700',
}

def load_data(timeframe: str) -> List[Dict]:
    """Load OHLCV data for ETHUSDT"""
    filepath = DATA_DIR / f"{timeframe}.csv"
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return []
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'timestamp': int(row['open_time']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
            })
    
    return data

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate EMA"""
    if len(prices) < period:
        return prices
    
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    
    for price in prices[period:]:
        ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
    
    # Pad with None for initial values
    return [None] * (period - 1) + ema

def generate_chart(timeframe: str, data: List[Dict]) -> str:
    """Generate HTML candlestick chart"""
    if not data:
        return ""
    
    prices = [d['close'] for d in data]
    ema9 = calculate_ema(prices, 9)
    ema21 = calculate_ema(prices, 21)
    
    # Generate candlestick data
    candles = []
    for i, d in enumerate(data):
        is_bullish = d['close'] >= d['open']
        color = COLORS['up'] if is_bullish else COLORS['down']
        
        candles.append({
            'x': i,
            'open': d['open'],
            'high': d['high'],
            'low': d['low'],
            'close': d['close'],
            'color': color,
            'volume': d['volume'],
            'time': d['timestamp'],
        })
    
    # Create HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{SYMBOL} {timeframe} Chart</title>
    <script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{ background-color: {COLORS['bg']}; margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        #chart {{ width: 100%; height: 600px; }}
        .header {{ color: {COLORS['text']}; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{SYMBOL} - {timeframe} Timeframe</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div id="chart"></div>
    
    <script>
        const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
            width: document.getElementById('chart').clientWidth,
            height: 600,
            layout: {{ background: {{ color: '{COLORS['bg']}' }}, textColor: '{COLORS['text']}' }},
            grid: {{ vertLines: {{ color: '{COLORS['grid']}' }}, horzLines: {{ color: '{COLORS['grid']}' }} }},
        }});
        
        const candleSeries = chart.addCandlestickSeries({{
            upColor: '{COLORS['up']}',
            downColor: '{COLORS['down']}',
            borderUpColor: '{COLORS['up']}',
            borderDownColor: '{COLORS['down']}',
            wickUpColor: '{COLORS['wick']}',
            wickDownColor: '{COLORS['wick']}',
        }});
        
        const data = {json.dumps(candles[-200:])};  // Last 200 candles
        
        candleSeries.setData(data.map(d => ({{
            time: d.time / 1000,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close
        }})));
        
        chart.timeScale().fitContent();
    </script>
</body>
</html>
"""
    return html

def main():
    """Generate ETHUSDT charts for all timeframes"""
    print("="*70)
    print("ETHUSDT PATTERN CHART GENERATOR")
    print("="*70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timeframes = ['5m', '15m', '1h', '4h', '1d', '1w', '1M']
    
    for tf in timeframes:
        print(f"\nProcessing {SYMBOL} {tf}...")
        
        data = load_data(tf)
        if not data:
            print(f"  ❌ No data available")
            continue
        
        print(f"  📊 Loaded {len(data)} candles")
        
        html = generate_chart(tf, data)
        if not html:
            print(f"  ❌ Failed to generate chart")
            continue
        
        output_file = OUTPUT_DIR / f"{SYMBOL}_{tf}.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"  ✅ Saved: {output_file}")
    
    print("\n" + "="*70)
    print("Complete! Charts generated for all timeframes")
    print(f"Output: {OUTPUT_DIR}")
    print("="*70)

if __name__ == '__main__':
    main()
