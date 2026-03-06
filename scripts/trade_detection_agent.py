#!/usr/bin/env python3
"""
ETHUSDT Trade Detection Agent
Monitors MTF analysis and detects trade setups automatically
Triggers Trade Spotlight when conditions met
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
STATE_FILE = DATA_DIR / ".trade_spotlight_state.json"
LOG_FILE = DATA_DIR / "trade_detection.log"

# Configuration
MIN_CONFLUENCE_FOR_SETUP = 2  # Need 2+ timeframes aligned
MIN_REGIME_CONFIDENCE = 0.75
MAX_CONCURRENT_TRADES = 3

class TradeDetectionAgent:
    def __init__(self):
        self.state = self.load_state()
        self.setup_detected = False
        self.current_setup = None
        
    def load_state(self):
        """Load or initialize trade spotlight state"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            "status": "INACTIVE",
            "active_trades": [],
            "last_check": None,
            "detection_history": []
        }
    
    def save_state(self):
        """Save current state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def log(self, message):
        """Log to file and print"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + '\n')
    
    def load_analysis(self, timeframe):
        """Load analysis file for given timeframe"""
        file_path = ANALYSIS_DIR / f"{timeframe}_current.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
    
    def evaluate_mtf_confluence(self):
        """Evaluate multi-timeframe confluence for trade setup"""
        timeframes = ['1M', '1W', '1d', '4h', '1h', '15m']
        analyses = {}
        
        for tf in timeframes:
            analysis = self.load_analysis(tf)
            if analysis:
                analyses[tf] = analysis
        
        if len(analyses) < 4:  # Need at least 4 timeframes
            return None, "Insufficient timeframe data"
        
        # Extract biases
        biases = {}
        for tf, analysis in analyses.items():
            if 'interpretations' in analysis and 'regime' in analysis['interpretations']:
                regime = analysis['interpretations']['regime']['classification']
                biases[tf] = regime.split('_')[0]  # bullish/bearish/transition
        
        # Count confluence
        bullish_count = sum(1 for b in biases.values() if b == 'bullish')
        bearish_count = sum(1 for b in biases.values() if b == 'bearish')
        transition_count = sum(1 for b in biases.values() if b == 'transition')
        
        total = len(biases)
        
        # Determine setup
        if bullish_count >= MIN_CONFLUENCE_FOR_SETUP and bullish_count > bearish_count:
            direction = "LONG"
            strength = bullish_count / total
        elif bearish_count >= MIN_CONFLUENCE_FOR_SETUP and bearish_count > bullish_count:
            direction = "SHORT"
            strength = bearish_count / total
        else:
            return None, f"No clear setup - Bullish:{bullish_count}, Bearish:{bearish_count}, Transition:{transition_count}"
        
        # Get latest price from 1h
        price = analyses.get('1h', {}).get('metadata', {}).get('close_price', 0)
        
        setup = {
            "direction": direction,
            "strength": strength,
            "confluence_count": bullish_count if direction == "LONG" else bearish_count,
            "total_timeframes": total,
            "price": price,
            "timestamp": datetime.now().isoformat(),
            "biases": biases,
            "timeframe_analyses": {tf: {
                "regime": analyses[tf]['interpretations']['regime']['classification'],
                "confidence": analyses[tf]['interpretations']['regime']['confidence']
            } for tf in analyses if 'interpretations' in analyses[tf]}
        }
        
        return setup, None
    
    def check_entry_conditions(self):
        """Check if entry conditions are met on 5m/1m"""
        # Load 5m analysis if available
        m5_analysis = self.load_analysis('5m')
        m1_analysis = self.load_analysis('1m')
        
        if not m5_analysis:
            return False, "No 5m analysis available"
        
        entry_signals = m5_analysis.get('interpretations', {}).get('entry_signals', {})
        
        if entry_signals.get('long_setup') and self.current_setup['direction'] == 'LONG':
            return True, "5m long setup confirmed"
        elif entry_signals.get('short_setup') and self.current_setup['direction'] == 'SHORT':
            return True, "5m short setup confirmed"
        
        # Check 1m if available
        if m1_analysis:
            m1_entry = m1_analysis.get('interpretations', {}).get('entry_exit', {})
            if m1_entry.get('entry_long') and self.current_setup['direction'] == 'LONG':
                return True, "1m long entry confirmed"
            elif m1_entry.get('entry_short') and self.current_setup['direction'] == 'SHORT':
                return True, "1m short entry confirmed"
        
        return False, "Entry conditions not met"
    
    def activate_trade_spotlight(self, setup):
        """Activate trade spotlight for detected setup"""
        trade_id = f"ETH_{setup['direction']}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        self.log(f"🎯 SETUP DETECTED: {setup['direction']} | Confluence: {setup['confluence_count']}/{setup['total_timeframes']} | Price: {setup['price']:.2f}")
        
        # Update state
        self.state['status'] = 'ACTIVE'
        self.state['current_setup'] = setup
        self.state['trade_id'] = trade_id
        
        # Record in history
        self.state['detection_history'].append({
            'trade_id': trade_id,
            'setup': setup,
            'detected_at': datetime.now().isoformat()
        })
        
        self.save_state()
        
        # Trigger 5m analysis immediately
        self.log("📊 Triggering 5m analysis...")
        subprocess.run(['bash', '/root/.openclaw/workspace/scripts/update_5m_analysis.sh'], 
                      capture_output=True)
        
        return trade_id
    
    def monitor_active_trade(self):
        """Monitor active trade for entry/exit"""
        if self.state['status'] != 'ACTIVE':
            return
        
        setup = self.state.get('current_setup')
        if not setup:
            return
        
        # Check if entry conditions met
        entry_met, reason = self.check_entry_conditions()
        
        if entry_met:
            self.log(f"✅ ENTRY SIGNAL: {reason}")
            
            # If 1m not already running, trigger it
            m1_analysis = self.load_analysis('1m')
            if not m1_analysis:
                self.log("📊 Triggering 1m ultra-precision analysis...")
                subprocess.run(['bash', '/root/.openclaw/workspace/scripts/update_1m_analysis.sh'],
                              capture_output=True)
        
        # Check for exit conditions (simplified - would check position PnL, stop loss, etc.)
        # This would integrate with actual trading execution
        
    def run_detection_cycle(self):
        """Main detection cycle"""
        self.log("="*70)
        self.log("Trade Detection Agent - Starting Cycle")
        self.log("="*70)
        
        # Step 1: Evaluate MTF confluence
        setup, error = self.evaluate_mtf_confluence()
        
        if error:
            self.log(f"ℹ️  {error}")
            return
        
        # Step 2: Check if we already have active trade
        if self.state['status'] == 'ACTIVE':
            self.log(f"📊 Active trade monitoring: {self.state.get('trade_id', 'N/A')}")
            self.monitor_active_trade()
            return
        
        # Step 3: Check if setup is strong enough
        if setup['strength'] >= 0.5 and setup['confluence_count'] >= MIN_CONFLUENCE_FOR_SETUP:
            self.current_setup = setup
            trade_id = self.activate_trade_spotlight(setup)
            self.log(f"🚀 Trade Spotlight ACTIVATED: {trade_id}")
        else:
            self.log(f"ℹ️  Setup detected but below threshold - Strength: {setup['strength']:.2f}, Confluence: {setup['confluence_count']}")
        
        self.state['last_check'] = datetime.now().isoformat()
        self.save_state()
        
        self.log("="*70)
    
    def deactivate_trade(self, reason="Manual"):
        """Deactivate current trade"""
        if self.state['status'] == 'ACTIVE':
            trade_id = self.state.get('trade_id', 'N/A')
            self.log(f"🛑 Trade DEACTIVATED: {trade_id} | Reason: {reason}")
            
            self.state['status'] = 'INACTIVE'
            self.state['current_setup'] = None
            self.state['trade_id'] = None
            self.save_state()

def main():
    """Main entry point"""
    agent = TradeDetectionAgent()
    agent.run_detection_cycle()

if __name__ == "__main__":
    main()
