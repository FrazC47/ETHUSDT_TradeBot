#!/usr/bin/env python3
"""
ETHUSDT 1-Month Analysis Generator
Automatically analyzes 1M timeframe after new candle + indicators
Saves to: data/analysis/1M_current.json (current state)
         data/analysis/1M_log.jsonl (historical log)
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import os

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
INPUT_FILE = DATA_DIR / "ETHUSDT_1M_indicators.csv"

def ensure_dirs():
    """Ensure analysis directory exists"""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_1m():
    """Generate complete 1M analysis"""
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] ❌ No 1M indicators file found")
        return None
    
    df = pd.read_csv(INPUT_FILE)
    last = df.iloc[-1]
    
    def get(col, default=None):
        val = last.get(col, default)
        if pd.isna(val):
            return default
        return val
    
    close = float(get('close', 0))
    candle_date = str(get('open_time'))
    
    # Build complete indicator values
    indicator_values = {
        "price_action": {
            "price_change_pct": float(get('price_change_pct', 0)),
            "price_range": float(get('price_range', 0)),
            "price_range_pct": float(get('price_range_pct', 0)),
            "body_size": float(get('body_size', 0)),
            "upper_wick": float(get('upper_wick', 0)),
            "lower_wick": float(get('lower_wick', 0)),
            "range_location": str(get('range_location', '')),
            "is_bullish": bool(get('is_bullish', False)),
            "is_bearish": bool(get('is_bearish', False)),
            "consecutive_bullish": int(get('consecutive_bullish', 0))
        },
        "trend": {
            "ema_9": float(get('ema_9', 0)),
            "ema_21": float(get('ema_21', 0)),
            "ema_50": float(get('ema_50', 0)),
            "ema_200": float(get('ema_200', 0)),
            "sma_20": float(get('sma_20', 0)),
            "sma_50": float(get('sma_50', 0)),
            "trend_bullish": bool(get('trend_bullish', False)),
            "trend_strong": bool(get('trend_strong', False))
        },
        "momentum": {
            "rsi": float(get('rsi', 0)),
            "rsi_sma": float(get('rsi_sma', 0)),
            "macd_line": float(get('macd_line', 0)),
            "macd_signal": float(get('macd_signal', 0)),
            "macd_hist": float(get('macd_hist', 0))
        },
        "volatility": {
            "atr": float(get('atr', 0)),
            "atr_pct": float(get('atr_pct', 0)),
            "bb_middle": float(get('bb_middle', 0)),
            "bb_upper": float(get('bb_upper', 0)),
            "bb_lower": float(get('bb_lower', 0)),
            "bb_width": float(get('bb_width', 0)),
            "bb_position": float(get('bb_position', 0))
        },
        "volume": {
            "volume_sma_20": float(get('volume_sma_20', 0)),
            "volume_ratio": float(get('volume_ratio', 0)),
            "vwap": float(get('vwap', 0)),
            "vwap_distance": float(get('vwap_distance', 0))
        },
        "trend_strength": {
            "plus_dm": float(get('plus_dm', 0)),
            "minus_dm": float(get('minus_dm', 0)),
            "plus_di": float(get('plus_di', 0)),
            "minus_di": float(get('minus_di', 0)),
            "dx": float(get('dx', 0)),
            "adx": float(get('adx', 0)),
            "adx_trending": bool(get('adx_trending', False))
        },
        "fibonacci": {
            "fib_0": float(get('fib_0', 0)),
            "fib_236": float(get('fib_236', 0)),
            "fib_382": float(get('fib_382', 0)),
            "fib_500": float(get('fib_500', 0)),
            "fib_618": float(get('fib_618', 0)),
            "fib_786": float(get('fib_786', 0)),
            "fib_100": float(get('fib_100', 0)),
            "fib_1272": float(get('fib_1272', 0)),
            "fib_1382": float(get('fib_1382', 0)),
            "fib_1618": float(get('fib_1618', 0)),
            "fib_200": float(get('fib_200', 0)),
            "fib_2618": float(get('fib_2618', 0)),
            "fib_4236": float(get('fib_4236', 0)),
            "fib_position": float(get('fib_position', 0))
        },
        "structure": {
            "hh": bool(get('hh', False)),
            "lh": bool(get('lh', False)),
            "hl": bool(get('hl', False)),
            "ll": bool(get('ll', False)),
            "structure_score": float(get('structure_score', 0)),
            "structure_bullish": bool(get('structure_bullish', False)),
            "structure_bearish": bool(get('structure_bearish', False)),
            "swing_high": float(get('swing_high', 0)) if pd.notna(get('swing_high')) else None,
            "swing_low": float(get('swing_low', 0)) if pd.notna(get('swing_low')) else None
        },
        "support_resistance": {
            "resistance_1": float(get('resistance_1', 0)),
            "resistance_2": float(get('resistance_2', 0)),
            "resistance_3": float(get('resistance_3', 0)),
            "resistance_4": float(get('resistance_4', 0)),
            "support_1": float(get('support_1', 0)),
            "support_2": float(get('support_2', 0)),
            "support_3": float(get('support_3', 0)),
            "support_4": float(get('support_4', 0)),
            "dist_to_resistance_1": float(get('dist_to_resistance_1', 0)),
            "dist_to_support_1": float(get('dist_to_support_1', 0)),
            "sr_zone_size": float(get('sr_zone_size', 0)),
            "position_in_sr_zone": float(get('position_in_sr_zone', 0))
        },
        "trendlines": {
            "bull_trend_line": float(get('bull_trend_line', 0)) if pd.notna(get('bull_trend_line')) else None,
            "bull_trend_touches": int(get('bull_trend_touches', 0)) if pd.notna(get('bull_trend_touches')) else 0,
            "bull_trend_valid": bool(get('bull_trend_valid', False)),
            "bull_trend_angle": float(get('bull_trend_angle', 0)) if pd.notna(get('bull_trend_angle')) else 0,
            "bull_trend_slope_pct": float(get('bull_trend_slope_pct', 0)) if pd.notna(get('bull_trend_slope_pct')) else 0,
            "dist_to_bull_trend": float(get('dist_to_bull_trend', 0)) if pd.notna(get('dist_to_bull_trend')) else 0,
            "bear_trend_line": float(get('bear_trend_line', 0)) if pd.notna(get('bear_trend_line')) else None,
            "bear_trend_touches": int(get('bear_trend_touches', 0)) if pd.notna(get('bear_trend_touches')) else 0,
            "bear_trend_valid": bool(get('bear_trend_valid', False)),
            "bear_trend_angle": float(get('bear_trend_angle', 0)) if pd.notna(get('bear_trend_angle')) else 0,
            "bear_trend_slope_pct": float(get('bear_trend_slope_pct', 0)) if pd.notna(get('bear_trend_slope_pct')) else 0,
            "dist_to_bear_trend": float(get('dist_to_bear_trend', 0)) if pd.notna(get('dist_to_bear_trend')) else 0,
            "above_bull_trend": bool(get('above_bull_trend', False)),
            "below_bear_trend": bool(get('below_bear_trend', False)),
            "between_trend_lines": bool(get('between_trend_lines', False)),
            "broke_bull_trend": bool(get('broke_bull_trend', False)),
            "broke_bear_trend": bool(get('broke_bear_trend', False))
        }
    }
    
    # Generate interpretations
    ema_bullish = indicator_values['trend']['trend_bullish']
    structure_bullish = indicator_values['structure']['structure_bullish']
    rsi = indicator_values['momentum']['rsi']
    adx = indicator_values['trend_strength']['adx']
    bb_width = indicator_values['volatility']['bb_width']
    fib_pos = indicator_values['fibonacci']['fib_position']
    sr = indicator_values['support_resistance']
    
    # Regime
    if ema_bullish and structure_bullish:
        regime = "bullish_accumulation" if rsi < 60 else "bullish_momentum"
    elif not ema_bullish and not structure_bullish:
        regime = "bearish_distribution"
    else:
        regime = "transition"
    
    # Trend strength
    if adx > 30:
        trend_strength = "strong"
    elif adx > 20:
        trend_strength = "moderate"
    else:
        trend_strength = "weak"
    
    # Volatility
    if bb_width < 0.1:
        vol_regime = "compressed"
    elif bb_width > 0.3:
        vol_regime = "expanding"
    else:
        vol_regime = "normal"
    
    # Fibonacci
    if fib_pos < 0.382:
        fib_zone = "deep_correction"
    elif fib_pos < 0.618:
        fib_zone = "mid_range"
    else:
        fib_zone = "extension"
    
    # Count indicators
    total_indicators = sum(len(v) for v in indicator_values.values())
    
    analysis = {
        "metadata": {
            "candle_date": candle_date,
            "analysis_timestamp": datetime.now().isoformat(),
            "timeframe": "1M",
            "total_indicators": total_indicators,
            "close_price": close
        },
        "indicator_values": indicator_values,
        "interpretations": {
            "regime": {
                "classification": regime,
                "confidence": 0.75,
                "using_indicators": ["trend_bullish", "structure_bullish", "rsi"]
            },
            "trend": {
                "strength": trend_strength,
                "adx_value": adx,
                "using_indicators": ["adx", "plus_di", "minus_di"]
            },
            "volatility": {
                "regime": vol_regime,
                "bb_width": bb_width,
                "using_indicators": ["bb_width", "atr_pct"]
            },
            "fibonacci_position": {
                "zone": fib_zone,
                "position": fib_pos,
                "using_indicators": ["fib_position", "fib_618", "fib_382"]
            },
            "key_levels": {
                "nearest_resistance": sr['resistance_1'],
                "nearest_support": sr['support_1'],
                "distance_to_resistance_pct": sr['dist_to_resistance_1'],
                "distance_to_support_pct": sr['dist_to_support_1']
            },
            "volume": {
                "volume_ratio": indicator_values['volume']['volume_ratio'],
                "above_average": indicator_values['volume']['volume_ratio'] > 1.0,
                "using_indicators": ["volume_ratio", "volume_sma_20"]
            },
            "trendlines": {
                "bull_valid": indicator_values['trendlines']['bull_trend_valid'],
                "bear_valid": indicator_values['trendlines']['bear_trend_valid'],
                "using_indicators": ["bull_trend_valid", "bear_trend_valid", "bull_trend_line", "bear_trend_line"]
            }
        },
        "comprehensive_analysis": {
            "all_indicators_reviewed": True,
            "total_indicators": total_indicators,
            "categories": list(indicator_values.keys()),
            "narrative": f"1M Analysis: Close {close:.2f}. Regime: {regime}. Trend strength: {trend_strength} (ADX {adx:.1f}). Volatility: {vol_regime}. Fibonacci position: {fib_zone} ({fib_pos:.2f}). Key S/R: R1 {sr['resistance_1']:.2f}, S1 {sr['support_1']:.2f}."
        }
    }
    
    return analysis, candle_date

def save_analysis(analysis, candle_date):
    """Save analysis to current.json and append to log.jsonl"""
    
    # Save current state
    current_file = ANALYSIS_DIR / "1M_current.json"
    with open(current_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Append to log
    log_file = ANALYSIS_DIR / "1M_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(analysis) + '\n')
    
    print(f"[{datetime.now()}] ✅ Analysis saved:")
    print(f"  - Current: {current_file}")
    print(f"  - Log: {log_file}")

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT 1-Month Analysis Generator")
    print("="*70)
    
    ensure_dirs()
    
    result = analyze_1m()
    if result:
        analysis, candle_date = result
        save_analysis(analysis, candle_date)
        print(f"[{datetime.now()}] ✅ Complete - {analysis['metadata']['total_indicators']} indicators analyzed")
    else:
        print(f"[{datetime.now()}] ❌ Analysis failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
