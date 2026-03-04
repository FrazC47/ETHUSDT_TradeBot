#!/usr/bin/env python3
"""
Dynamic Frequency Escalation for ETHUSDT Trading
Automatically increases monitoring frequency as trade setup develops
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict
import json
import os

class MonitoringMode(Enum):
    """Monitoring frequency modes"""
    IDLE = "idle"              # No active setup (15 min checks)
    WATCH = "watch"            # Early signals detected (10 min checks)
    ALERT = "alert"            # Setup forming (5 min checks)
    ACTIVE = "active"          # Trade imminent (1 min checks)
    IN_POSITION = "in_position" # Managing open trade (1 min checks)

class DynamicFrequencyManager:
    """
    Manages dynamic monitoring frequency based on trade setup progression
    """
    
    # Frequency settings (in minutes)
    FREQUENCIES = {
        MonitoringMode.IDLE: 15,
        MonitoringMode.WATCH: 10,
        MonitoringMode.ALERT: 5,
        MonitoringMode.ACTIVE: 1,
        MonitoringMode.IN_POSITION: 1
    }
    
    # State file for persistence
    STATE_FILE = "/root/.openclaw/workspace/ETHUSDT_TradeBot/agents/config/dynamic_frequency_state.json"
    
    def __init__(self):
        self.current_mode = MonitoringMode.IDLE
        self.setup_score = 0  # 0-100, likelihood of trade
        self.last_check = datetime.now()
        self.escalation_history = []
        self.load_state()
    
    def load_state(self):
        """Load state from file"""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.current_mode = MonitoringMode(data.get('mode', 'idle'))
                    self.setup_score = data.get('score', 0)
                    self.escalation_history = data.get('history', [])
            except:
                pass
    
    def save_state(self):
        """Save state to file"""
        data = {
            'mode': self.current_mode.value,
            'score': self.setup_score,
            'last_update': datetime.now().isoformat(),
            'history': self.escalation_history[-10:]  # Keep last 10
        }
        os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
        with open(self.STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def analyze_setup_progression(self, 
                                  mtf_score: float,
                                  fundamental_score: float,
                                  price_action: Dict,
                                  existing_position: bool = False) -> MonitoringMode:
        """
        Analyze market conditions and determine monitoring frequency
        
        Args:
            mtf_score: Multi-timeframe alignment score (0-100)
            fundamental_score: Fundamental analysis score (0-100)
            price_action: Dict with 'trend_strength', 'volume_surge', 'support_test'
            existing_position: Whether we're already in a trade
        """
        
        # Calculate composite setup score
        self.setup_score = self._calculate_setup_score(
            mtf_score, fundamental_score, price_action
        )
        
        # Determine mode based on score and conditions
        if existing_position:
            new_mode = MonitoringMode.IN_POSITION
        elif self.setup_score >= 85:
            new_mode = MonitoringMode.ACTIVE
        elif self.setup_score >= 70:
            new_mode = MonitoringMode.ALERT
        elif self.setup_score >= 50:
            new_mode = MonitoringMode.WATCH
        else:
            new_mode = MonitoringMode.IDLE
        
        # Log escalation if mode changed
        if new_mode != self.current_mode:
            self.escalation_history.append({
                'timestamp': datetime.now().isoformat(),
                'from_mode': self.current_mode.value,
                'to_mode': new_mode.value,
                'setup_score': self.setup_score
            })
            self.current_mode = new_mode
            self.save_state()
            self._send_escalation_alert()
        
        return self.current_mode
    
    def _calculate_setup_score(self, mtf_score: float, 
                               fundamental_score: float,
                               price_action: Dict) -> int:
        """Calculate composite setup likelihood score"""
        
        # Weights
        mtf_weight = 0.40
        fund_weight = 0.30
        price_weight = 0.30
        
        # Price action components
        trend_strength = price_action.get('trend_strength', 0)  # 0-100
        volume_surge = price_action.get('volume_surge', 0)      # 0-100
        support_test = price_action.get('support_test', 0)      # 0-100
        
        price_component = (trend_strength * 0.4 + 
                          volume_surge * 0.3 + 
                          support_test * 0.3)
        
        # Composite score
        score = (mtf_score * mtf_weight + 
                fundamental_score * fund_weight + 
                price_component * price_weight)
        
        return int(min(100, max(0, score)))
    
    def _send_escalation_alert(self):
        """Send alert when frequency escalates"""
        freq = self.FREQUENCIES[self.current_mode]
        
        alerts = {
            MonitoringMode.WATCH: f"👀 WATCH MODE: Setup developing (checking every 10 min)",
            MonitoringMode.ALERT: f"⚠️ ALERT MODE: Setup forming (checking every 5 min)",
            MonitoringMode.ACTIVE: f"🎯 ACTIVE MODE: Trade imminent (checking every 1 min)",
            MonitoringMode.IN_POSITION: f"📊 IN POSITION: Managing trade (checking every 1 min)",
            MonitoringMode.IDLE: f"😴 IDLE MODE: No setup (checking every 15 min)"
        }
        
        message = alerts.get(self.current_mode, "Mode changed")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        # TODO: Send to Telegram/Discord notification
        # self.send_notification(message)
    
    def should_run_now(self) -> bool:
        """Check if agent should run based on current frequency"""
        freq_minutes = self.FREQUENCIES[self.current_mode]
        time_since_last = (datetime.now() - self.last_check).total_seconds() / 60
        
        if time_since_last >= freq_minutes:
            self.last_check = datetime.now()
            return True
        return False
    
    def get_next_run_time(self) -> datetime:
        """Calculate next scheduled run time"""
        freq_minutes = self.FREQUENCIES[self.current_mode]
        return self.last_check + timedelta(minutes=freq_minutes)
    
    def print_status(self):
        """Print current monitoring status"""
        print("="*70)
        print("DYNAMIC FREQUENCY MONITORING")
        print("="*70)
        print(f"Current Mode:        {self.current_mode.value.upper()}")
        print(f"Setup Score:         {self.setup_score}/100")
        print(f"Check Frequency:     Every {self.FREQUENCIES[self.current_mode]} minutes")
        print(f"Next Check:          {self.get_next_run_time().strftime('%H:%M:%S')}")
        print()
        
        if self.escalation_history:
            print("Recent Escalations:")
            for esc in self.escalation_history[-3:]:
                print(f"  {esc['timestamp'][:19]}: {esc['from_mode']} → {esc['to_mode']} (score: {esc['setup_score']})")
        
        print("="*70)

# Integration with trading agent
def check_and_run_agent():
    """
    Main entry point - call this instead of running agent directly
    Only runs agent if it's time based on dynamic frequency
    """
    manager = DynamicFrequencyManager()
    
    if manager.should_run_now():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running ETHUSDT agent...")
        # TODO: Call actual agent
        # from ethusdt_agent import main
        # main()
        return True
    else:
        next_run = manager.get_next_run_time()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Skipping - next run at {next_run.strftime('%H:%M:%S')}")
        return False

# Example usage
if __name__ == '__main__':
    manager = DynamicFrequencyManager()
    
    print("Example: Dynamic frequency escalation\n")
    
    # Simulate progression from idle to active trade
    scenarios = [
        # (mtf_score, fund_score, price_action, position)
        (30, 40, {'trend_strength': 20, 'volume_surge': 10, 'support_test': 0}, False),
        (55, 60, {'trend_strength': 50, 'volume_surge': 40, 'support_test': 30}, False),
        (75, 80, {'trend_strength': 70, 'volume_surge': 60, 'support_test': 50}, False),
        (90, 85, {'trend_strength': 85, 'volume_surge': 80, 'support_test': 75}, False),
        (90, 85, {'trend_strength': 85, 'volume_surge': 80, 'support_test': 75}, True),  # In position
    ]
    
    for mtf, fund, price, pos in scenarios:
        mode = manager.analyze_setup_progression(mtf, fund, price, pos)
        manager.print_status()
        print()
