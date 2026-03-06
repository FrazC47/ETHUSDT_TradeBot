#!/usr/bin/env python3
"""
ETHUSDT 15-Minute Analysis Generator
Analyzes 15m timeframe with 1h + 4h + 1d context as inputs
Saves to: data/analysis/15m_current.json + 15m_log.jsonl
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
INPUT_FILE = DATA_DIR / "ETHUSDT_15m_indicators.csv"
ONE_HOUR_ANALYSIS_FILE = ANALYSIS_DIR / "1h_current.json"
FOUR_HOUR_ANALYSIS_FILE = ANALYSIS_DIR / "4h_current.json"
DAILY_ANALYSIS_FILE = ANALYSIS_DIR / "1d_current.json"

def load_parent_contexts():
    """Load 1h, 4h, and 1d analysis as context for 15m analysis"""
    contexts = {
        "one_hour": None,
        "four_hour": None,
        "daily": None,
        "loaded_count": 0,
        "fully_loaded": False
    }
    
    # Load 1h context
    if ONE_HOUR_ANALYSIS_FILE.exists():
        try:
            with open(ONE_HOUR_ANALYSIS_FILE, 'r') as f:
                one_h = json.load(f)
            contexts["one_hour"] = {
                "regime": one_h['interpretations']['regime']['classification'],
                "trend_strength": one_h['interpretations']['trend']['strength'],
                "bias": one_h['interpretations']['regime']['classification'].split('_')[0],
                "close": one_h['metadata']['close_price'],
                "key_levels": one_h['interpretations']['key_levels'],
                "fib_zone": one_h['interpretations']['fibonacci_position']['zone'],
                "alignments": one_h['interpretations']['mtf_alignment']['alignments']
            }
            contexts["loaded_count"] += 1
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 1h context: {e}")
    
    # Load 4h context
    if FOUR_HOUR_ANALYSIS_FILE.exists():
        try:
            with open(FOUR_HOUR_ANALYSIS_FILE, 'r') as f:
                four_h = json.load(f)
            contexts["four_hour"] = {
                "regime": four_h['interpretations']['regime']['classification'],
                "trend_strength": four_h['interpretations']['trend']['strength'],
                "bias": four_h['interpretations']['regime']['classification'].split('_')[0],
                "close": four_h['metadata']['close_price'],
                "key_levels": four_h['interpretations']['key_levels'],
                "fib_zone": four_h['interpretations']['fibonacci_position']['zone'],
                "alignments": four_h['interpretations']['mtf_alignment']['alignments']
            }
            contexts["loaded_count"] += 1
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 4h context: {e}")
    
    # Load 1d context
    if DAILY_ANALYSIS_FILE.exists():
        try:
            with open(DAILY_ANALYSIS_FILE, 'r') as f:
                daily = json.load(f)
            contexts["daily"] = {
                "regime": daily['interpretations']['regime']['classification'],
                "trend_strength": daily['interpretations']['trend']['strength'],
                "bias": daily['interpretations']['regime']['classification'].split('_')[0],
                "close": daily['metadata']['close_price'],
                "key_levels": daily['interpretations']['key_levels'],
                "fib_zone": daily['interpretations']['fibonacci_position']['zone'],
                "alignments": daily['interpretations']['mtf_alignment']['alignments']
            }
            contexts["loaded_count"] += 1
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 1d context: {e}")
    
    contexts["fully_loaded"] = contexts["loaded_count"] == 3
    return contexts

def ensure_dirs():
    """Ensure analysis directory exists"""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_15m():
    """Generate 15m analysis with 1h + 4h + 1d context"""
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] ❌ No 15m indicators file found")
        return None
    
    # Load all parent contexts FIRST
    parent_contexts = load_parent_contexts()
    
    df = pd.read_csv(INPUT_FILE)
    last = df.iloc[-1]
    
    def get(col, default=None):
        val = last.get(col, default)
        if pd.isna(val):
            return default
        return val
    
    close = float(get('close', 0))
    candle_date = str(get('open_time'))
    
    # Build indicator values (same 10 categories)
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
    
    # Generate 15m interpretations
    ema_bullish = indicator_values['trend']['trend_bullish']
    structure_bullish = indicator_values['structure']['structure_bullish']
    rsi = indicator_values['momentum']['rsi']
    adx = indicator_values['trend_strength']['adx']
    bb_width = indicator_values['volatility']['bb_width']
    fib_pos = indicator_values['fibonacci']['fib_position']
    sr = indicator_values['support_resistance']
    
    # 15m Regime (standalone)
    if ema_bullish and structure_bullish:
        m15_regime = "bullish_accumulation" if rsi < 60 else "bullish_momentum"
    elif not ema_bullish and not structure_bullish:
        m15_regime = "bearish_distribution"
    else:
        m15_regime = "transition"
    
    # ALIGNMENT with all three parents
    alignments = {}
    confluence_count = 0
    
    if parent_contexts["loaded_count"] > 0:
        m15_bias = m15_regime.split('_')[0]
        
        # vs 1h
        if parent_contexts["one_hour"]:
            h1_bias = parent_contexts["one_hour"]["bias"]
            if m15_bias == h1_bias:
                alignments["15m_vs_1h"] = "aligned"
                confluence_count += 1
            elif h1_bias == "bullish" and m15_bias == "bearish":
                alignments["15m_vs_1h"] = "15m_pullback_in_bullish_1h"
            elif h1_bias == "bearish" and m15_bias == "bullish":
                alignments["15m_vs_1h"] = "15m_bounce_in_bearish_1h"
            else:
                alignments["15m_vs_1h"] = "mixed"
        else:
            alignments["15m_vs_1h"] = "no_context"
        
        # vs 4h
        if parent_contexts["four_hour"]:
            h4_bias = parent_contexts["four_hour"]["bias"]
            if m15_bias == h4_bias:
                alignments["15m_vs_4h"] = "aligned"
                confluence_count += 1
            elif h4_bias == "bullish" and m15_bias == "bearish":
                alignments["15m_vs_4h"] = "15m_pullback_in_bullish_4h"
            elif h4_bias == "bearish" and m15_bias == "bullish":
                alignments["15m_vs_4h"] = "15m_bounce_in_bearish_4h"
            else:
                alignments["15m_vs_4h"] = "mixed"
        else:
            alignments["15m_vs_4h"] = "no_context"
        
        # vs Daily
        if parent_contexts["daily"]:
            daily_bias = parent_contexts["daily"]["bias"]
            if m15_bias == daily_bias:
                alignments["15m_vs_daily"] = "aligned"
                confluence_count += 1
            elif daily_bias == "bullish" and m15_bias == "bearish":
                alignments["15m_vs_daily"] = "15m_pullback_in_bullish_daily"
            elif daily_bias == "bearish" and m15_bias == "bullish":
                alignments["15m_vs_daily"] = "15m_bounce_in_bearish_daily"
            else:
                alignments["15m_vs_daily"] = "mixed"
        else:
            alignments["15m_vs_daily"] = "no_context"
        
        # Quad alignment (all 4 timeframes: 15m + 1h + 4h + 1d)
        parents_available = parent_contexts["loaded_count"]
        if confluence_count == parents_available and parents_available > 0:
            if parents_available == 3:
                alignments["quad_alignment"] = "strong_confluence"
            else:
                alignments["quad_alignment"] = "partial_confluence"
        elif confluence_count >= 1:
            alignments["quad_alignment"] = "moderate_confluence"
        else:
            alignments["quad_alignment"] = "mixed_signals"
    else:
        alignments = {
            "15m_vs_1h": "no_context",
            "15m_vs_4h": "no_context",
            "15m_vs_daily": "no_context",
            "quad_alignment": "no_context"
        }
    
    # Trend strength
    if adx > 30:
        trend_strength = "strong"
    elif adx > 20:
        trend_strength = "moderate"
    else:
        trend_strength = "weak"
    
    # Volatility
    if bb_width < 0.01:
        vol_regime = "compressed"
    elif bb_width > 0.05:
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
    
    total_indicators = sum(len(v) for v in indicator_values.values())
    
    # Build analysis WITH all three parent contexts
    analysis = {
        "metadata": {
            "candle_date": candle_date,
            "analysis_timestamp": datetime.now().isoformat(),
            "timeframe": "15m",
            "total_indicators": total_indicators,
            "close_price": close,
            "parent_timeframes": ["1h", "4h", "1d"],
            "parent_contexts_loaded": parent_contexts["loaded_count"],
            "all_parents_loaded": parent_contexts["fully_loaded"]
        },
        "indicator_values": indicator_values,
        "parent_contexts": {
            "one_hour": parent_contexts["one_hour"] if parent_contexts["one_hour"] else {"loaded": False},
            "four_hour": parent_contexts["four_hour"] if parent_contexts["four_hour"] else {"loaded": False},
            "daily": parent_contexts["daily"] if parent_contexts["daily"] else {"loaded": False},
            "summary": f"{parent_contexts['loaded_count']}/3 contexts loaded"
        } if parent_contexts["loaded_count"] > 0 else {"loaded": False, "note": "No parent contexts available"},
        "interpretations": {
            "regime": {
                "classification": m15_regime,
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
                "using_indicators": ["bull_trend_valid", "bear_trend_valid"]
            },
            "mtf_alignment": {
                "alignments": alignments,
                "confluence_count": confluence_count,
                "using_context": ["1h_regime", "4h_regime", "daily_regime"]
            }
        },
        "comprehensive_analysis": {
            "all_indicators_reviewed": True,
            "total_indicators": total_indicators,
            "categories": list(indicator_values.keys()),
            "narrative": f"15m Analysis: Close {close:.2f}. Regime: {m15_regime}. Quad alignment: {alignments.get('quad_alignment', 'N/A')}. Trend strength: {trend_strength} (ADX {adx:.1f}). Volatility: {vol_regime}. Fibonacci: {fib_zone} ({fib_pos:.2f})."
        }
    }
    
    return analysis, candle_date

def save_analysis(analysis, candle_date):
    """Save analysis to current.json and append to log.jsonl"""
    
    # Save current state
    current_file = ANALYSIS_DIR / "15m_current.json"
    with open(current_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Append to log
    log_file = ANALYSIS_DIR / "15m_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(analysis) + '\n')
    
    print(f"[{datetime.now()}] ✅ Analysis saved:")
    print(f"  - Current: {current_file}")
    print(f"  - Log: {log_file}")
    
    # Print MTF alignment info
    if analysis['metadata']['parent_contexts_loaded'] > 0:
        alignments = analysis['interpretations']['mtf_alignment']['alignments']
        print(f"  - 15m vs 1h: {alignments.get('15m_vs_1h', 'N/A')}")
        print(f"  - 15m vs 4h: {alignments.get('15m_vs_4h', 'N/A')}")
        print(f"  - 15m vs Daily: {alignments.get('15m_vs_daily', 'N/A')}")
        print(f"  - Quad Alignment: {alignments.get('quad_alignment', 'N/A')}")

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT 15-Minute Analysis Generator (with 1h + 4h + 1d context)")
    print("="*70)
    
    ensure_dirs()
    
    result = analyze_15m()
    if result:
        analysis, candle_date = result
        save_analysis(analysis, candle_date)
        print(f"[{datetime.now()}] ✅ Complete - {analysis['metadata']['total_indicators']} indicators analyzed")
    else:
        print(f"[{datetime.now()}] ❌ Analysis failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
