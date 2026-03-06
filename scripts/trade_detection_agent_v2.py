#!/usr/bin/env python3
"""
ETHUSDT Enhanced Trade Detection Agent v2.0
Ports features from archived ETHUSDT_TradeBot:
- 9-state regime classification
- Weighted timeframe clusters (40/35/25)
- Signal state machine (PENDING/ACTIVE/COOLDOWN/EXPIRED)
- Entry buffer system
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
STATE_FILE = DATA_DIR / ".trade_spotlight_state_v2.json"
LOG_FILE = DATA_DIR / "trade_detection_v2.log"

# Configuration
MIN_CONFLUENCE_FOR_SETUP = 2
WEIGHTED_THRESHOLD = 0.65  # 65% weighted score required
STATE_PENDING_TIMEOUT_MINUTES = 30
STATE_COOLDOWN_MINUTES = 120
MAX_CONCURRENT_TRADES = 2

# Weighted Cluster Configuration (from archived system)
CLUSTER_WEIGHTS = {
    "macro": {  # 40%
        "1M": 0.20,
        "1W": 0.20
    },
    "intermediate": {  # 35%
        "1d": 0.20,
        "4h": 0.15
    },
    "execution": {  # 25%
        "1h": 0.15,
        "15m": 0.10
    }
}

# 9-State Regime Classification (from archived system)
REGIME_STATES = [
    "strong_uptrend",      # Price > EMA 9 > 21 > 50, ADX > 25, +DI > -DI
    "uptrend_with_pullback", # Price > EMA 50 but < EMA 9, pullback to support
    "bullish_accumulation",  # Sideways, higher lows, contracting volatility
    "ranging",               # Price between EMAs, low ADX
    "bearish_distribution",  # Sideways, lower highs, expanding volatility  
    "downtrend_with_bounce", # Price < EMA 50 but > EMA 9, bounce to resistance
    "strong_downtrend",      # Price < EMA 9 < 21 < 50, ADX > 25, -DI > +DI
    "transition",            # Mixed signals, regime change in progress
    "volatile_chop"          # High ATR, no clear direction
]

class RegimeClassifier:
    """9-state regime classification (ported from MTF Engine v3.4)"""
    
    @staticmethod
    def classify_regime(analysis_data):
        """Classify single timeframe into 9-state regime"""
        if not analysis_data or 'indicator_values' not in analysis_data:
            return "unknown"
        
        indicators = analysis_data['indicator_values']
        
        # Extract key values
        ema_bullish = indicators.get('trend', {}).get('trend_bullish', False)
        ema_bearish = indicators.get('trend', {}).get('trend_bearish', False)
        adx = indicators.get('trend_strength', {}).get('adx', 0)
        bb_width = indicators.get('volatility', {}).get('bb_width', 0)
        structure_bullish = indicators.get('structure', {}).get('structure_bullish', False)
        structure_bearish = indicators.get('structure', {}).get('structure_bearish', False)
        
        # Strong trends (ADX > 25)
        if adx > 25:
            if ema_bullish:
                return "strong_uptrend"
            elif ema_bearish:
                return "strong_downtrend"
        
        # Pullback/Bounce scenarios
        if ema_bullish and structure_bearish:
            return "uptrend_with_pullback"
        elif ema_bearish and structure_bullish:
            return "downtrend_with_bounce"
        
        # Accumulation/Distribution (sideways with structure)
        if not ema_bullish and not ema_bearish:
            if structure_bullish and bb_width < 0.1:
                return "bullish_accumulation"
            elif structure_bearish and bb_width > 0.2:
                return "bearish_distribution"
            elif bb_width > 0.3:
                return "volatile_chop"
            else:
                return "ranging"
        
        # Default
        return "transition"

class WeightedClusterAnalyzer:
    """Weighted timeframe cluster analysis (ported from MTF Engine)"""
    
    @staticmethod
    def calculate_weighted_score(analyses):
        """Calculate weighted bullish/bearish score"""
        macro_score = 0
        intermediate_score = 0
        execution_score = 0
        
        # Macro cluster (1M, 1W) - 40%
        for tf, weight in CLUSTER_WEIGHTS["macro"].items():
            if tf in analyses:
                regime = RegimeClassifier.classify_regime(analyses[tf])
                if regime in ["strong_uptrend", "uptrend_with_pullback", "bullish_accumulation"]:
                    macro_score += weight
                elif regime in ["strong_downtrend", "downtrend_with_bounce", "bearish_distribution"]:
                    macro_score -= weight
        
        # Intermediate cluster (1d, 4h) - 35%
        for tf, weight in CLUSTER_WEIGHTS["intermediate"].items():
            if tf in analyses:
                regime = RegimeClassifier.classify_regime(analyses[tf])
                if regime in ["strong_uptrend", "uptrend_with_pullback", "bullish_accumulation"]:
                    intermediate_score += weight
                elif regime in ["strong_downtrend", "downtrend_with_bounce", "bearish_distribution"]:
                    intermediate_score -= weight
        
        # Execution cluster (1h, 15m) - 25%
        for tf, weight in CLUSTER_WEIGHTS["execution"].items():
            if tf in analyses:
                regime = RegimeClassifier.classify_regime(analyses[tf])
                if regime in ["strong_uptrend", "uptrend_with_pullback", "bullish_accumulation"]:
                    execution_score += weight
                elif regime in ["strong_downtrend", "downtrend_with_bounce", "bearish_distribution"]:
                    execution_score -= weight
        
        total_score = macro_score + intermediate_score + execution_score
        max_possible = 1.0  # Sum of all weights
        normalized_score = total_score / max_possible
        
        return {
            "total_score": normalized_score,
            "macro_score": macro_score / 0.4 if macro_score != 0 else 0,
            "intermediate_score": intermediate_score / 0.35 if intermediate_score != 0 else 0,
            "execution_score": execution_score / 0.25 if execution_score != 0 else 0,
            "direction": "bullish" if normalized_score > 0.2 else "bearish" if normalized_score < -0.2 else "neutral"
        }

class SignalStateMachine:
    """Signal state management (ported from Signal Engine)"""
    
    STATES = ["PENDING", "ACTIVE", "COOLDOWN", "EXPIRED"]
    
    def __init__(self, state_file):
        self.state_file = state_file
        self.state = self.load_state()
    
    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "signals": {},
            "active_trades": [],
            "detection_history": []
        }
    
    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def create_signal(self, trade_id, setup_data):
        """Create new signal in PENDING state"""
        signal = {
            "trade_id": trade_id,
            "state": "PENDING",
            "setup": setup_data,
            "created_at": datetime.now().isoformat(),
            "pending_timeout": (datetime.now() + timedelta(minutes=STATE_PENDING_TIMEOUT_MINUTES)).isoformat(),
            "entry_confirmed": False,
            "entry_price": None,
            "entry_time": None
        }
        self.state["signals"][trade_id] = signal
        self.save_state()
        return signal
    
    def activate_signal(self, trade_id, entry_price):
        """Move signal from PENDING to ACTIVE"""
        if trade_id in self.state["signals"]:
            signal = self.state["signals"][trade_id]
            signal["state"] = "ACTIVE"
            signal["entry_confirmed"] = True
            signal["entry_price"] = entry_price
            signal["entry_time"] = datetime.now().isoformat()
            signal["cooldown_until"] = (datetime.now() + timedelta(minutes=STATE_COOLDOWN_MINUTES)).isoformat()
            self.save_state()
            return True
        return False
    
    def check_state_transitions(self):
        """Check for automatic state transitions"""
        now = datetime.now()
        
        for trade_id, signal in self.state["signals"].items():
            # PENDING → EXPIRED (timeout)
            if signal["state"] == "PENDING":
                pending_timeout = datetime.fromisoformat(signal["pending_timeout"])
                if now > pending_timeout:
                    signal["state"] = "EXPIRED"
                    signal["expired_reason"] = "Pending timeout (30 min)"
                    self.log(f"⏰ Signal {trade_id} EXPIRED: Pending timeout")
            
            # COOLDOWN check (after entry, before new signals)
            elif signal["state"] == "ACTIVE":
                cooldown_until = datetime.fromisoformat(signal.get("cooldown_until", signal["entry_time"]))
                if now > cooldown_until:
                    signal["state"] = "COOLDOWN"
                    self.log(f"🔄 Signal {trade_id} in COOLDOWN")
        
        self.save_state()
    
    def get_active_signals(self):
        """Get all ACTIVE signals"""
        return {k: v for k, v in self.state["signals"].items() if v["state"] == "ACTIVE"}
    
    def get_pending_signals(self):
        """Get all PENDING signals"""
        return {k: v for k, v in self.state["signals"].items() if v["state"] == "PENDING"}

class EnhancedTradeDetectionAgent:
    """Enhanced trade detection with ported features"""
    
    def __init__(self):
        self.state_machine = SignalStateMachine(Path(STATE_FILE))
        self.regime_classifier = RegimeClassifier()
        self.cluster_analyzer = WeightedClusterAnalyzer()
        
    def log(self, message):
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + '\n')
    
    def load_analysis(self, timeframe):
        file_path = ANALYSIS_DIR / f"{timeframe}_current.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
    
    def evaluate_setup(self):
        """Enhanced setup evaluation with 9-state and weighted scoring"""
        timeframes = ['1M', '1W', '1d', '4h', '1h', '15m']
        analyses = {}
        
        # Load all analyses
        for tf in timeframes:
            analysis = self.load_analysis(tf)
            if analysis:
                analyses[tf] = analysis
        
        if len(analyses) < 4:
            return None, "Insufficient timeframe data"
        
        # Calculate weighted cluster score
        weighted_scores = self.cluster_analyzer.calculate_weighted_score(analyses)
        
        # Classify all regimes
        regime_summary = {}
        for tf, analysis in analyses.items():
            regime = self.regime_classifier.classify_regime(analysis)
            regime_summary[tf] = regime
        
        # Determine if setup exists
        direction = weighted_scores["direction"]
        score = abs(weighted_scores["total_score"])
        
        if direction == "neutral" or score < WEIGHTED_THRESHOLD:
            return None, f"No clear setup - Weighted score: {weighted_scores['total_score']:.2f}, Direction: {direction}"
        
        # Get latest price
        price = analyses.get('1h', {}).get('metadata', {}).get('close_price', 0)
        
        setup = {
            "direction": "LONG" if direction == "bullish" else "SHORT",
            "weighted_score": weighted_scores["total_score"],
            "macro_score": weighted_scores["macro_score"],
            "intermediate_score": weighted_scores["intermediate_score"],
            "execution_score": weighted_scores["execution_score"],
            "price": price,
            "timestamp": datetime.now().isoformat(),
            "regime_summary": regime_summary,
            "total_timeframes": len(analyses)
        }
        
        return setup, None
    
    def run_detection_cycle(self):
        """Main detection cycle with state machine"""
        self.log("="*70)
        self.log("Enhanced Trade Detection v2.0 - Starting Cycle")
        self.log("="*70)
        
        # Check for state transitions
        self.state_machine.check_state_transitions()
        
        # Check existing signals
        pending_signals = self.state_machine.get_pending_signals()
        active_signals = self.state_machine.get_active_signals()
        
        if len(active_signals) >= MAX_CONCURRENT_TRADES:
            self.log(f"⚠️ Max concurrent trades ({MAX_CONCURRENT_TRADES}) reached")
            return
        
        # Evaluate new setup
        setup, error = self.evaluate_setup()
        
        if error:
            self.log(f"ℹ️ {error}")
            return
        
        # Create new signal
        trade_id = f"ETH_{setup['direction']}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        self.log(f"🎯 SETUP DETECTED: {setup['direction']}")
        self.log(f"   Weighted Score: {setup['weighted_score']:.2f}")
        self.log(f"   Macro: {setup['macro_score']:.2f} | Intermediate: {setup['intermediate_score']:.2f} | Execution: {setup['execution_score']:.2f}")
        self.log(f"   Price: {setup['price']:.2f}")
        self.log(f"   Regimes: {setup['regime_summary']}")
        
        # Create signal in PENDING state
        signal = self.state_machine.create_signal(trade_id, setup)
        self.log(f"📋 Signal created: {trade_id} (State: PENDING)")
        
        # Trigger 5m analysis for entry confirmation
        self.log("📊 Triggering 5m analysis for entry confirmation...")
        subprocess.run(['bash', '/root/.openclaw/workspace/scripts/update_5m_analysis.sh'], 
                      capture_output=True)
        
        self.log("="*70)

def main():
    agent = EnhancedTradeDetectionAgent()
    agent.run_detection_cycle()

if __name__ == "__main__":
    main()
