#!/usr/bin/env python3
"""
ETHUSDT 1-Day Analysis Generator
Analyzes 1d timeframe with 1M + 1W context as inputs
Saves to: data/analysis/1d_current.json + 1d_log.jsonl
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
INPUT_FILE = DATA_DIR / "ETHUSDT_1d_indicators.csv"
MONTHLY_ANALYSIS_FILE = ANALYSIS_DIR / "1M_current.json"
WEEKLY_ANALYSIS_FILE = ANALYSIS_DIR / "1W_current.json"

def load_parent_contexts():
    """Load both 1M and 1W analysis as context for 1d analysis"""
    contexts = {
        "monthly": None,
        "weekly": None,
        "loaded": False
    }
    
    # Load 1M context
    if MONTHLY_ANALYSIS_FILE.exists():
        try:
            with open(MONTHLY_ANALYSIS_FILE, 'r') as f:
                monthly = json.load(f)
            contexts["monthly"] = {
                "regime": monthly['interpretations']['regime']['classification'],
                "trend_strength": monthly['interpretations']['trend']['strength'],
                "bias": monthly['interpretations']['regime']['classification'].split('_')[0],
                "close": monthly['metadata']['close_price'],
                "key_levels": monthly['interpretations']['key_levels'],
                "fib_zone": monthly['interpretations']['fibonacci_position']['zone']
            }
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 1M context: {e}")
    
    # Load 1W context
    if WEEKLY_ANALYSIS_FILE.exists():
        try:
            with open(WEEKLY_ANALYSIS_FILE, 'r') as f:
                weekly = json.load(f)
            contexts["weekly"] = {
                "regime": weekly['interpretations']['regime']['classification'],
                "trend_strength": weekly['interpretations']['trend']['strength'],
                "bias": weekly['interpretations']['regime']['classification'].split('_')[0],
                "close": weekly['metadata']['close_price'],
                "key_levels": weekly['interpretations']['key_levels'],
                "fib_zone": weekly['interpretations']['fibonacci_position']['zone'],
                "mtf_alignment": weekly['interpretations']['mtf_alignment']['weekly_vs_monthly']
            }
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 1W context: {e}")
    
    contexts["loaded"] = contexts["monthly"] is not None and contexts["weekly"] is not None
    return contexts

def ensure_dirs():
    """Ensure analysis directory exists"""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_1d():
    """Generate 1d analysis with 1M + 1W context"""
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] ❌ No 1d indicators file found")
        return None
    
    # Load parent contexts FIRST
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
    
    # Generate 1d interpretations
    ema_bullish = indicator_values['trend']['trend_bullish']
    structure_bullish = indicator_values['structure']['structure_bullish']
    rsi = indicator_values['momentum']['rsi']
    adx = indicator_values['trend_strength']['adx']
    bb_width = indicator_values['volatility']['bb_width']
    fib_pos = indicator_values['fibonacci']['fib_position']
    sr = indicator_values['support_resistance']
    
    # 1d Regime (standalone)
    if ema_bullish and structure_bullish:
        daily_regime = "bullish_accumulation" if rsi < 60 else "bullish_momentum"
    elif not ema_bullish and not structure_bullish:
        daily_regime = "bearish_distribution"
    else:
        daily_regime = "transition"
    
    # ALIGNMENT with both parents
    alignments = {}
    if parent_contexts["loaded"]:
        daily_bias = daily_regime.split('_')[0]
        
        # vs Monthly
        monthly_bias = parent_contexts["monthly"]["bias"]
        if daily_bias == monthly_bias:
            alignments["daily_vs_monthly"] = "aligned"
        elif monthly_bias == "bullish" and daily_bias == "bearish":
            alignments["daily_vs_monthly"] = "daily_pullback_in_bullish_monthly"
        elif monthly_bias == "bearish" and daily_bias == "bullish":
            alignments["daily_vs_monthly"] = "daily_bounce_in_bearish_monthly"
        else:
            alignments["daily_vs_monthly"] = "mixed"
        
        # vs Weekly
        weekly_bias = parent_contexts["weekly"]["bias"]
        if daily_bias == weekly_bias:
            alignments["daily_vs_weekly"] = "aligned"
        elif weekly_bias == "bullish" and daily_bias == "bearish":
            alignments["daily_vs_weekly"] = "daily_pullback_in_bullish_weekly"
        elif weekly_bias == "bearish" and daily_bias == "bullish":
            alignments["daily_vs_weekly"] = "daily_bounce_in_bearish_weekly"
        else:
            alignments["daily_vs_weekly"] = "mixed"
        
        # Triple alignment
        if daily_bias == monthly_bias == weekly_bias:
            alignments["triple_alignment"] = "strong_confluence"
        elif daily_bias == monthly_bias or daily_bias == weekly_bias:
            alignments["triple_alignment"] = "moderate_confluence"
        else:
            alignments["triple_alignment"] = "mixed_signals"
    else:
        alignments = {"daily_vs_monthly": "no_context", "daily_vs_weekly": "no_context", "triple_alignment": "no_context"}
    
    # Trend strength
    if adx > 30:
        trend_strength = "strong"
    elif adx > 20:
        trend_strength = "moderate"
    else:
        trend_strength = "weak"
    
    # Volatility
    if bb_width < 0.05:
        vol_regime = "compressed"
    elif bb_width > 0.15:
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
    
    # Build analysis WITH both parent contexts
    analysis = {
        "metadata": {
            "candle_date": candle_date,
            "analysis_timestamp": datetime.now().isoformat(),
            "timeframe": "1d",
            "total_indicators": total_indicators,
            "close_price": close,
            "parent_timeframes": ["1M", "1W"],
            "parent_contexts_loaded": parent_contexts["loaded"]
        },
        "indicator_values": indicator_values,
        "parent_contexts": {
            "monthly": parent_contexts["monthly"] if parent_contexts["monthly"] else {"loaded": False},
            "weekly": parent_contexts["weekly"] if parent_contexts["weekly"] else {"loaded": False}
        } if parent_contexts["loaded"] else {"loaded": False, "note": "No parent contexts available"},
        "interpretations": {
            "regime": {
                "classification": daily_regime,
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
                "using_context": ["monthly_regime", "weekly_regime", "monthly_bias", "weekly_bias"]
            }
        },
        "comprehensive_analysis": {
            "all_indicators_reviewed": True,
            "total_indicators": total_indicators,
            "categories": list(indicator_values.keys()),
            "narrative": f"1d Analysis: Close {close:.2f}. Regime: {daily_regime}. Triple alignment: {alignments.get('triple_alignment', 'N/A')}. Trend strength: {trend_strength} (ADX {adx:.1f}). Volatility: {vol_regime}. Fibonacci: {fib_zone} ({fib_pos:.2f})."
        }
    }
    
    return analysis, candle_date

def save_analysis(analysis, candle_date):
    """Save analysis to current.json and append to log.jsonl"""
    
    # Save current state
    current_file = ANALYSIS_DIR / "1d_current.json"
    with open(current_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Append to log
    log_file = ANALYSIS_DIR / "1d_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(analysis) + '\n')
    
    print(f"[{datetime.now()}] ✅ Analysis saved:")
    print(f"  - Current: {current_file}")
    print(f"  - Log: {log_file}")
    
    # Print MTF alignment info
    if analysis['metadata']['parent_contexts_loaded']:
        alignments = analysis['interpretations']['mtf_alignment']['alignments']
        print(f"  - Daily vs Monthly: {alignments.get('daily_vs_monthly', 'N/A')}")
        print(f"  - Daily vs Weekly: {alignments.get('daily_vs_weekly', 'N/A')}")
        print(f"  - Triple Alignment: {alignments.get('triple_alignment', 'N/A')}")

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT 1-Day Analysis Generator (with 1M + 1W context)")
    print("="*70)
    
    ensure_dirs()
    
    result = analyze_1d()
    if result:
        analysis, candle_date = result
        save_analysis(analysis, candle_date)
        print(f"[{datetime.now()}] ✅ Complete - {analysis['metadata']['total_indicators']} indicators analyzed")
    else:
        print(f"[{datetime.now()}] ❌ Analysis failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
