#!/usr/bin/env python3
"""
ETHUSDT 5-Minute Analysis Generator - Trade Spotlight
Analyzes 5m timeframe with 15m + 1h + 4h context as inputs
Saves to: data/analysis/5m_current.json + 5m_log.jsonl
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
INPUT_FILE = DATA_DIR / "ETHUSDT_5m_indicators.csv"
FIFTEEN_MIN_ANALYSIS_FILE = ANALYSIS_DIR / "15m_current.json"
ONE_HOUR_ANALYSIS_FILE = ANALYSIS_DIR / "1h_current.json"
FOUR_HOUR_ANALYSIS_FILE = ANALYSIS_DIR / "4h_current.json"

def load_parent_contexts():
    """Load 15m, 1h, and 4h analysis as context for 5m analysis"""
    contexts = {
        "fifteen_min": None,
        "one_hour": None,
        "four_hour": None,
        "loaded_count": 0,
        "fully_loaded": False
    }
    
    # Load 15m context
    if FIFTEEN_MIN_ANALYSIS_FILE.exists():
        try:
            with open(FIFTEEN_MIN_ANALYSIS_FILE, 'r') as f:
                fifteen_m = json.load(f)
            contexts["fifteen_min"] = {
                "regime": fifteen_m['interpretations']['regime']['classification'],
                "trend_strength": fifteen_m['interpretations']['trend']['strength'],
                "bias": fifteen_m['interpretations']['regime']['classification'].split('_')[0],
                "close": fifteen_m['metadata']['close_price'],
                "key_levels": fifteen_m['interpretations']['key_levels'],
                "fib_zone": fifteen_m['interpretations']['fibonacci_position']['zone'],
                "alignments": fifteen_m['interpretations']['mtf_alignment']['alignments']
            }
            contexts["loaded_count"] += 1
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 15m context: {e}")
    
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
    
    contexts["fully_loaded"] = contexts["loaded_count"] == 3
    return contexts

def ensure_dirs():
    """Ensure analysis directory exists"""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_5m():
    """Generate 5m analysis with 15m + 1h + 4h context"""
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] ❌ No 5m indicators file found")
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
    
    # Build indicator values (52 precision indicators)
    indicator_values = {
        "trend": {
            "ema_9": float(get('ema_9', 0)),
            "ema_21": float(get('ema_21', 0)),
            "ema_50": float(get('ema_50', 0)),
            "ema_bullish": bool(get('ema_bullish', False)),
            "ema_bearish": bool(get('ema_bearish', False)),
            "ema_trend_strength": float(get('ema_trend_strength', 0))
        },
        "momentum": {
            "rsi_14": float(get('rsi_14', 0)),
            "rsi_sma_7": float(get('rsi_sma_7', 0)),
            "rsi_oversold": bool(get('rsi_oversold', False)),
            "rsi_overbought": bool(get('rsi_overbought', False))
        },
        "volatility": {
            "atr_14": float(get('atr_14', 0)),
            "atr_pct": float(get('atr_pct', 0)),
            "bb_upper": float(get('bb_upper', 0)),
            "bb_lower": float(get('bb_lower', 0)),
            "bb_width": float(get('bb_width', 0)),
            "bb_squeeze": bool(get('bb_squeeze', False))
        },
        "volume": {
            "volume_sma_20": float(get('volume_sma_20', 0)),
            "volume_ratio": float(get('volume_ratio', 0)),
            "vwap": float(get('vwap', 0)),
            "vwap_distance": float(get('vwap_distance', 0)),
            "above_vwap": bool(get('above_vwap', False)),
            "below_vwap": bool(get('below_vwap', False))
        },
        "price_action": {
            "body_size_pct": float(get('body_size_pct', 0)),
            "upper_wick_pct": float(get('upper_wick_pct', 0)),
            "lower_wick_pct": float(get('lower_wick_pct', 0)),
            "is_bullish": bool(get('is_bullish', False)),
            "upper_rejection": bool(get('upper_rejection', False)),
            "lower_rejection": bool(get('lower_rejection', False))
        },
        "micro_structure": {
            "hh_5": bool(get('hh_5', False)),
            "ll_5": bool(get('ll_5', False)),
            "micro_resistance": float(get('micro_resistance', 0)) if pd.notna(get('micro_resistance')) else None,
            "micro_support": float(get('micro_support', 0)) if pd.notna(get('micro_support')) else None,
            "dist_to_micro_res": float(get('dist_to_micro_res', 0)),
            "dist_to_micro_sup": float(get('dist_to_micro_sup', 0))
        },
        "patterns": {
            "pattern_hammer": bool(get('pattern_hammer', False)),
            "pattern_bullish_engulfing": bool(get('pattern_bullish_engulfing', False)),
            "pattern_bearish_engulfing": bool(get('pattern_bearish_engulfing', False)),
            "pattern_doji": bool(get('pattern_doji', False)),
            "pattern_signal": int(get('pattern_signal', 0))
        },
        "composite": {
            "momentum_score": float(get('momentum_score', 0)),
            "momentum_bullish": bool(get('momentum_bullish', False)),
            "momentum_bearish": bool(get('momentum_bearish', False))
        }
    }
    
    # Generate 5m interpretations
    ema_bullish = indicator_values['trend']['ema_bullish']
    momentum_bullish = indicator_values['composite']['momentum_bullish']
    rsi = indicator_values['momentum']['rsi_14']
    
    # 5m Regime (simplified for precision)
    if ema_bullish and momentum_bullish:
        m5_regime = "bullish_momentum"
    elif not ema_bullish and not momentum_bullish:
        m5_regime = "bearish_momentum"
    else:
        m5_regime = "mixed"
    
    # ALIGNMENT with all three parents
    alignments = {}
    confluence_count = 0
    
    if parent_contexts["loaded_count"] > 0:
        m5_bias = "bullish" if ema_bullish else "bearish" if not ema_bullish else "neutral"
        
        # vs 15m
        if parent_contexts["fifteen_min"]:
            m15_bias = parent_contexts["fifteen_min"]["bias"]
            if m5_bias == m15_bias:
                alignments["5m_vs_15m"] = "aligned"
                confluence_count += 1
            elif m15_bias == "bullish" and m5_bias == "bearish":
                alignments["5m_vs_15m"] = "5m_counter_in_bullish_15m"
            elif m15_bias == "bearish" and m5_bias == "bullish":
                alignments["5m_vs_15m"] = "5m_counter_in_bearish_15m"
            else:
                alignments["5m_vs_15m"] = "mixed"
        else:
            alignments["5m_vs_15m"] = "no_context"
        
        # vs 1h
        if parent_contexts["one_hour"]:
            h1_bias = parent_contexts["one_hour"]["bias"]
            if m5_bias == h1_bias:
                alignments["5m_vs_1h"] = "aligned"
                confluence_count += 1
            elif h1_bias == "bullish" and m5_bias == "bearish":
                alignments["5m_vs_1h"] = "5m_counter_in_bullish_1h"
            elif h1_bias == "bearish" and m5_bias == "bullish":
                alignments["5m_vs_1h"] = "5m_counter_in_bearish_1h"
            else:
                alignments["5m_vs_1h"] = "mixed"
        else:
            alignments["5m_vs_1h"] = "no_context"
        
        # vs 4h
        if parent_contexts["four_hour"]:
            h4_bias = parent_contexts["four_hour"]["bias"]
            if m5_bias == h4_bias:
                alignments["5m_vs_4h"] = "aligned"
                confluence_count += 1
            elif h4_bias == "bullish" and m5_bias == "bearish":
                alignments["5m_vs_4h"] = "5m_counter_in_bullish_4h"
            elif h4_bias == "bearish" and m5_bias == "bullish":
                alignments["5m_vs_4h"] = "5m_counter_in_bearish_4h"
            else:
                alignments["5m_vs_4h"] = "mixed"
        else:
            alignments["5m_vs_4h"] = "no_context"
        
        # Quad alignment (all 4 timeframes: 5m + 15m + 1h + 4h)
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
            "5m_vs_15m": "no_context",
            "5m_vs_1h": "no_context",
            "5m_vs_4h": "no_context",
            "quad_alignment": "no_context"
        }
    
    # Entry signals
    entry_signals = {
        "long_setup": (
            indicator_values['composite']['momentum_bullish'] and 
            indicator_values['volume']['volume_ratio'] > 1.5 and
            indicator_values['volume']['above_vwap'] and
            alignments.get("5m_vs_15m") == "aligned"
        ),
        "short_setup": (
            indicator_values['composite']['momentum_bearish'] and 
            indicator_values['volume']['volume_ratio'] > 1.5 and
            indicator_values['volume']['below_vwap'] and
            alignments.get("5m_vs_15m") == "aligned"
        ),
        "caution": alignments.get("quad_alignment") == "mixed_signals"
    }
    
    total_indicators = sum(len(v) for v in indicator_values.values())
    
    # Build analysis WITH all three parent contexts
    analysis = {
        "metadata": {
            "candle_date": candle_date,
            "analysis_timestamp": datetime.now().isoformat(),
            "timeframe": "5m",
            "total_indicators": total_indicators,
            "close_price": close,
            "parent_timeframes": ["15m", "1h", "4h"],
            "parent_contexts_loaded": parent_contexts["loaded_count"],
            "all_parents_loaded": parent_contexts["fully_loaded"],
            "analysis_type": "trade_spotlight_precision"
        },
        "indicator_values": indicator_values,
        "parent_contexts": {
            "fifteen_min": parent_contexts["fifteen_min"] if parent_contexts["fifteen_min"] else {"loaded": False},
            "one_hour": parent_contexts["one_hour"] if parent_contexts["one_hour"] else {"loaded": False},
            "four_hour": parent_contexts["four_hour"] if parent_contexts["four_hour"] else {"loaded": False},
            "summary": f"{parent_contexts['loaded_count']}/3 contexts loaded"
        } if parent_contexts["loaded_count"] > 0 else {"loaded": False, "note": "No parent contexts available"},
        "interpretations": {
            "regime": {
                "classification": m5_regime,
                "using_indicators": ["ema_bullish", "momentum_bullish"]
            },
            "entry_signals": entry_signals,
            "key_levels": {
                "micro_resistance": indicator_values['micro_structure']['micro_resistance'],
                "micro_support": indicator_values['micro_structure']['micro_support'],
                "vwap": indicator_values['volume']['vwap']
            },
            "mtf_alignment": {
                "alignments": alignments,
                "confluence_count": confluence_count,
                "using_context": ["15m_regime", "1h_regime", "4h_regime"]
            }
        },
        "comprehensive_analysis": {
            "all_indicators_reviewed": True,
            "total_indicators": total_indicators,
            "categories": list(indicator_values.keys()),
            "narrative": f"5m Trade Spotlight: Close {close:.2f}. Regime: {m5_regime}. Quad alignment: {alignments.get('quad_alignment', 'N/A')}. Long setup: {entry_signals['long_setup']}. Short setup: {entry_signals['short_setup']}."
        }
    }
    
    return analysis, candle_date

def save_analysis(analysis, candle_date):
    """Save analysis to current.json and append to log.jsonl"""
    
    # Save current state
    current_file = ANALYSIS_DIR / "5m_current.json"
    with open(current_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Append to log
    log_file = ANALYSIS_DIR / "5m_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(analysis) + '\n')
    
    print(f"[{datetime.now()}] ✅ Analysis saved:")
    print(f"  - Current: {current_file}")
    print(f"  - Log: {log_file}")
    
    # Print MTF alignment info
    if analysis['metadata']['parent_contexts_loaded'] > 0:
        alignments = analysis['interpretations']['mtf_alignment']['alignments']
        entry = analysis['interpretations']['entry_signals']
        print(f"  - 5m vs 15m: {alignments.get('5m_vs_15m', 'N/A')}")
        print(f"  - 5m vs 1h: {alignments.get('5m_vs_1h', 'N/A')}")
        print(f"  - 5m vs 4h: {alignments.get('5m_vs_4h', 'N/A')}")
        print(f"  - Quad Alignment: {alignments.get('quad_alignment', 'N/A')}")
        print(f"  - Long Setup: {entry['long_setup']}")
        print(f"  - Short Setup: {entry['short_setup']}")

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT 5-Minute Analysis Generator - Trade Spotlight")
    print("Parent contexts: 15m + 1h + 4h")
    print("="*70)
    
    ensure_dirs()
    
    result = analyze_5m()
    if result:
        analysis, candle_date = result
        save_analysis(analysis, candle_date)
        print(f"[{datetime.now()}] ✅ Complete - {analysis['metadata']['total_indicators']} precision indicators analyzed")
    else:
        print(f"[{datetime.now()}] ❌ Analysis failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
