#!/usr/bin/env python3
"""
ETHUSDT 1-Minute Analysis Generator - Trade Spotlight Ultra-Precision
Analyzes 1m timeframe with 5m + 15m + 1h context as inputs
Saves to: data/analysis/1m_current.json + 1m_log.jsonl
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
INPUT_FILE = DATA_DIR / "ETHUSDT_1m_indicators.csv"
FIVE_MIN_ANALYSIS_FILE = ANALYSIS_DIR / "5m_current.json"
FIFTEEN_MIN_ANALYSIS_FILE = ANALYSIS_DIR / "15m_current.json"
ONE_HOUR_ANALYSIS_FILE = ANALYSIS_DIR / "1h_current.json"

def load_parent_contexts():
    """Load 5m, 15m, and 1h analysis as context for 1m analysis"""
    contexts = {
        "five_min": None,
        "fifteen_min": None,
        "one_hour": None,
        "loaded_count": 0,
        "fully_loaded": False
    }
    
    # Load 5m context
    if FIVE_MIN_ANALYSIS_FILE.exists():
        try:
            with open(FIVE_MIN_ANALYSIS_FILE, 'r') as f:
                five_m = json.load(f)
            contexts["five_min"] = {
                "regime": five_m['interpretations']['regime']['classification'],
                "bias": "bullish" if five_m['indicator_values']['trend']['ema_bullish'] else "bearish",
                "close": five_m['metadata']['close_price'],
                "entry_signals": five_m['interpretations']['entry_signals'],
                "alignments": five_m['interpretations']['mtf_alignment']['alignments']
            }
            contexts["loaded_count"] += 1
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 5m context: {e}")
    
    # Load 15m context
    if FIFTEEN_MIN_ANALYSIS_FILE.exists():
        try:
            with open(FIFTEEN_MIN_ANALYSIS_FILE, 'r') as f:
                fifteen_m = json.load(f)
            contexts["fifteen_min"] = {
                "regime": fifteen_m['interpretations']['regime']['classification'],
                "bias": fifteen_m['interpretations']['regime']['classification'].split('_')[0],
                "close": fifteen_m['metadata']['close_price'],
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
                "bias": one_h['interpretations']['regime']['classification'].split('_')[0],
                "close": one_h['metadata']['close_price'],
                "alignments": one_h['interpretations']['mtf_alignment']['alignments']
            }
            contexts["loaded_count"] += 1
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️  Error loading 1h context: {e}")
    
    contexts["fully_loaded"] = contexts["loaded_count"] == 3
    return contexts

def ensure_dirs():
    """Ensure analysis directory exists"""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_1m():
    """Generate 1m analysis with 5m + 15m + 1h context"""
    
    if not INPUT_FILE.exists():
        print(f"[{datetime.now()}] ❌ No 1m indicators file found")
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
    
    # Build indicator values (54 ultra-precision indicators)
    indicator_values = {
        "trend": {
            "ema_9": float(get('ema_9', 0)),
            "ema_21": float(get('ema_21', 0)),
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
            "bb_squeeze": bool(get('bb_squeeze', False))
        },
        "volume": {
            "volume_sma_20": float(get('volume_sma_20', 0)),
            "volume_ratio": float(get('volume_ratio', 0)),
            "volume_spike": bool(get('volume_spike', False)),
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
            "hh_3": bool(get('hh_3', False)),
            "ll_3": bool(get('ll_3', False)),
            "micro_resistance": float(get('micro_resistance', 0)) if pd.notna(get('micro_resistance')) else None,
            "micro_support": float(get('micro_support', 0)) if pd.notna(get('micro_support')) else None
        },
        "patterns": {
            "pattern_bullish": bool(get('pattern_bullish', False)),
            "pattern_bearish": bool(get('pattern_bearish', False))
        },
        "composite": {
            "momentum_score": float(get('momentum_score', 0)),
            "momentum_bullish": bool(get('momentum_bullish', False)),
            "momentum_bearish": bool(get('momentum_bearish', False)),
            "high_confidence_long": bool(get('high_confidence_long', False)),
            "high_confidence_short": bool(get('high_confidence_short', False))
        }
    }
    
    # Generate 1m interpretations
    ema_bullish = indicator_values['trend']['ema_bullish']
    high_conf_long = indicator_values['composite']['high_confidence_long']
    high_conf_short = indicator_values['composite']['high_confidence_short']
    rsi = indicator_values['momentum']['rsi_14']
    
    # 1m Regime
    if ema_bullish and high_conf_long:
        m1_regime = "strong_bullish"
    elif ema_bullish:
        m1_regime = "bullish"
    elif not ema_bullish and high_conf_short:
        m1_regime = "strong_bearish"
    elif not ema_bullish:
        m1_regime = "bearish"
    else:
        m1_regime = "neutral"
    
    # ALIGNMENT with all three parents
    alignments = {}
    confluence_count = 0
    
    if parent_contexts["loaded_count"] > 0:
        m1_bias = "bullish" if ema_bullish else "bearish" if not ema_bullish else "neutral"
        
        # vs 5m
        if parent_contexts["five_min"]:
            m5_bias = parent_contexts["five_min"]["bias"]
            if m1_bias == m5_bias:
                alignments["1m_vs_5m"] = "aligned"
                confluence_count += 1
            elif m5_bias == "bullish" and m1_bias == "bearish":
                alignments["1m_vs_5m"] = "1m_counter_in_bullish_5m"
            elif m5_bias == "bearish" and m1_bias == "bullish":
                alignments["1m_vs_5m"] = "1m_counter_in_bearish_5m"
            else:
                alignments["1m_vs_5m"] = "mixed"
        else:
            alignments["1m_vs_5m"] = "no_context"
        
        # vs 15m
        if parent_contexts["fifteen_min"]:
            m15_bias = parent_contexts["fifteen_min"]["bias"]
            if m1_bias == m15_bias:
                alignments["1m_vs_15m"] = "aligned"
                confluence_count += 1
            elif m15_bias == "bullish" and m1_bias == "bearish":
                alignments["1m_vs_15m"] = "1m_counter_in_bullish_15m"
            elif m15_bias == "bearish" and m1_bias == "bullish":
                alignments["1m_vs_15m"] = "1m_counter_in_bearish_15m"
            else:
                alignments["1m_vs_15m"] = "mixed"
        else:
            alignments["1m_vs_15m"] = "no_context"
        
        # vs 1h
        if parent_contexts["one_hour"]:
            h1_bias = parent_contexts["one_hour"]["bias"]
            if m1_bias == h1_bias:
                alignments["1m_vs_1h"] = "aligned"
                confluence_count += 1
            elif h1_bias == "bullish" and m1_bias == "bearish":
                alignments["1m_vs_1h"] = "1m_counter_in_bullish_1h"
            elif h1_bias == "bearish" and m1_bias == "bullish":
                alignments["1m_vs_1h"] = "1m_counter_in_bearish_1h"
            else:
                alignments["1m_vs_1h"] = "mixed"
        else:
            alignments["1m_vs_1h"] = "no_context"
        
        # Quad alignment (all 4 timeframes: 1m + 5m + 15m + 1h)
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
            "1m_vs_5m": "no_context",
            "1m_vs_15m": "no_context",
            "1m_vs_1h": "no_context",
            "quad_alignment": "no_context"
        }
    
    # Ultra-precision entry/exit signals
    entry_exit = {
        "entry_long": (
            high_conf_long and 
            indicator_values['volume']['volume_spike'] and
            indicator_values['price_action']['lower_rejection'] and
            alignments.get("1m_vs_5m") == "aligned"
        ),
        "entry_short": (
            high_conf_short and 
            indicator_values['volume']['volume_spike'] and
            indicator_values['price_action']['upper_rejection'] and
            alignments.get("1m_vs_5m") == "aligned"
        ),
        "exit_long": (
            indicator_values['composite']['momentum_bearish'] or
            indicator_values['price_action']['upper_rejection'] or
            rsi > 75
        ),
        "exit_short": (
            indicator_values['composite']['momentum_bullish'] or
            indicator_values['price_action']['lower_rejection'] or
            rsi < 25
        ),
        "caution": alignments.get("quad_alignment") == "mixed_signals"
    }
    
    # Stop loss levels based on ATR
    atr = indicator_values['volatility']['atr_14']
    stop_levels = {
        "long_stop": close - (atr * 1.5),
        "short_stop": close + (atr * 1.5),
        "atr_based_risk_pct": (atr * 1.5) / close * 100
    }
    
    total_indicators = sum(len(v) for v in indicator_values.values())
    
    # Build analysis WITH all three parent contexts
    analysis = {
        "metadata": {
            "candle_date": candle_date,
            "analysis_timestamp": datetime.now().isoformat(),
            "timeframe": "1m",
            "total_indicators": total_indicators,
            "close_price": close,
            "parent_timeframes": ["5m", "15m", "1h"],
            "parent_contexts_loaded": parent_contexts["loaded_count"],
            "all_parents_loaded": parent_contexts["fully_loaded"],
            "analysis_type": "trade_spotlight_ultra_precision"
        },
        "indicator_values": indicator_values,
        "parent_contexts": {
            "five_min": parent_contexts["five_min"] if parent_contexts["five_min"] else {"loaded": False},
            "fifteen_min": parent_contexts["fifteen_min"] if parent_contexts["fifteen_min"] else {"loaded": False},
            "one_hour": parent_contexts["one_hour"] if parent_contexts["one_hour"] else {"loaded": False},
            "summary": f"{parent_contexts['loaded_count']}/3 contexts loaded"
        } if parent_contexts["loaded_count"] > 0 else {"loaded": False, "note": "No parent contexts available"},
        "interpretations": {
            "regime": {
                "classification": m1_regime,
                "using_indicators": ["ema_bullish", "high_confidence_long", "high_confidence_short"]
            },
            "entry_exit": entry_exit,
            "stop_levels": stop_levels,
            "key_levels": {
                "micro_resistance": indicator_values['micro_structure']['micro_resistance'],
                "micro_support": indicator_values['micro_structure']['micro_support'],
                "vwap": indicator_values['volume']['vwap']
            },
            "mtf_alignment": {
                "alignments": alignments,
                "confluence_count": confluence_count,
                "using_context": ["5m_regime", "15m_regime", "1h_regime"]
            }
        },
        "comprehensive_analysis": {
            "all_indicators_reviewed": True,
            "total_indicators": total_indicators,
            "categories": list(indicator_values.keys()),
            "narrative": f"1m Ultra-Precision: Close {close:.2f}. Regime: {m1_regime}. Quad alignment: {alignments.get('quad_alignment', 'N/A')}. Entry Long: {entry_exit['entry_long']}. Entry Short: {entry_exit['entry_short']}. Risk: {stop_levels['atr_based_risk_pct']:.2f}%."
        }
    }
    
    return analysis, candle_date

def save_analysis(analysis, candle_date):
    """Save analysis to current.json and append to log.jsonl"""
    
    # Save current state
    current_file = ANALYSIS_DIR / "1m_current.json"
    with open(current_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Append to log
    log_file = ANALYSIS_DIR / "1m_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(analysis) + '\n')
    
    print(f"[{datetime.now()}] ✅ Analysis saved:")
    print(f"  - Current: {current_file}")
    print(f"  - Log: {log_file}")
    
    # Print MTF alignment and entry signals
    if analysis['metadata']['parent_contexts_loaded'] > 0:
        alignments = analysis['interpretations']['mtf_alignment']['alignments']
        entry = analysis['interpretations']['entry_exit']
        stop = analysis['interpretations']['stop_levels']
        print(f"  - 1m vs 5m: {alignments.get('1m_vs_5m', 'N/A')}")
        print(f"  - 1m vs 15m: {alignments.get('1m_vs_15m', 'N/A')}")
        print(f"  - 1m vs 1h: {alignments.get('1m_vs_1h', 'N/A')}")
        print(f"  - Quad Alignment: {alignments.get('quad_alignment', 'N/A')}")
        print(f"  - Entry Long: {entry['entry_long']}")
        print(f"  - Entry Short: {entry['entry_short']}")
        print(f"  - Long Stop: {stop['long_stop']:.2f}")
        print(f"  - Short Stop: {stop['short_stop']:.2f}")

def main():
    """Main function"""
    print("="*70)
    print("ETHUSDT 1-Minute Analysis Generator - Ultra-Precision Entry/Exit")
    print("Parent contexts: 5m + 15m + 1h")
    print("="*70)
    
    ensure_dirs()
    
    result = analyze_1m()
    if result:
        analysis, candle_date = result
        save_analysis(analysis, candle_date)
        print(f"[{datetime.now()}] ✅ Complete - {analysis['metadata']['total_indicators']} ultra-precision indicators analyzed")
    else:
        print(f"[{datetime.now()}] ❌ Analysis failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
