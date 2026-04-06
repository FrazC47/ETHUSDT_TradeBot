#!/usr/bin/env python3
"""
ETHUSDT Trade Spotlight Daemon
Continuously monitors trade state and manages 5m/1m data collection
"""

import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"
STATE_FILE = DATA_DIR / ".trade_spotlight_state.json"
LOG_FILE = DATA_DIR / "spotlight_daemon.log"

# Configuration
CHECK_INTERVAL_SECONDS = 60  # Check every minute
M5_UPDATE_INTERVAL = 300     # Update 5m every 5 minutes
M1_UPDATE_INTERVAL = 60      # Update 1m every 1 minute
INACTIVITY_TIMEOUT = 1800    # Auto-deactivate after 30 min inactivity

class SpotlightDaemon:
    def __init__(self):
        self.state = self.load_state()
        self.last_m5_update = None
        self.last_m1_update = None
        self.running = True
        
    def load_state(self):
        """Load current state"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"status": "INACTIVE"}
    
    def save_state(self):
        """Save state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + '\n')
    
    def update_m5(self):
        """Trigger 5m analysis update"""
        self.log("📊 Updating 5m analysis...")
        result = subprocess.run(
            ['bash', '/root/.openclaw/workspace/scripts/update_5m_analysis.sh'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            self.log("✅ 5m update complete")
            self.last_m5_update = datetime.now()
        else:
            self.log(f"❌ 5m update failed: {result.stderr[:100]}")
    
    def update_m1(self):
        """Trigger 1m analysis update"""
        self.log("📊 Updating 1m analysis...")
        result = subprocess.run(
            ['bash', '/root/.openclaw/workspace/scripts/update_1m_analysis.sh'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            self.log("✅ 1m update complete")
            self.last_m1_update = datetime.now()
        else:
            self.log(f"❌ 1m update failed: {result.stderr[:100]}")
    
    def check_inactivity_timeout(self):
        """Check if trade has been inactive too long"""
        if not self.state.get('last_check'):
            return False
        
        last_check = datetime.fromisoformat(self.state['last_check'])
        if datetime.now() - last_check > timedelta(seconds=INACTIVITY_TIMEOUT):
            return True
        return False
    
    def run_active_mode(self):
        """Run when trade spotlight is ACTIVE"""
        now = datetime.now()
        
        # Check 5m update needed
        if not self.last_m5_update or (now - self.last_m5_update).seconds >= M5_UPDATE_INTERVAL:
            self.update_m5()
        
        # Check 1m update needed  
        if not self.last_m1_update or (now - self.last_m1_update).seconds >= M1_UPDATE_INTERVAL:
            self.update_m1()
        
        # Check inactivity timeout
        if self.check_inactivity_timeout():
            self.log("⏰ Inactivity timeout - deactivating trade spotlight")
            self.state['status'] = 'INACTIVE'
            self.state['deactivation_reason'] = 'Inactivity timeout (30 min)'
            self.save_state()
    
    def run_inactive_mode(self):
        """Run when trade spotlight is INACTIVE"""
        # Just wait - detection agent will activate when setup found
        pass
    
    def run(self):
        """Main daemon loop"""
        self.log("="*70)
        self.log("Trade Spotlight Daemon STARTED")
        self.log(f"Check interval: {CHECK_INTERVAL_SECONDS}s")
        self.log(f"5m update interval: {M5_UPDATE_INTERVAL}s")
        self.log(f"1m update interval: {M1_UPDATE_INTERVAL}s")
        self.log("="*70)
        
        try:
            while self.running:
                # Reload state (in case detection agent changed it)
                self.state = self.load_state()
                
                if self.state.get('status') == 'ACTIVE':
                    self.run_active_mode()
                else:
                    self.run_inactive_mode()
                
                # Wait before next check
                time.sleep(CHECK_INTERVAL_SECONDS)
                
        except KeyboardInterrupt:
            self.log("🛑 Daemon stopped by user")
        except Exception as e:
            self.log(f"❌ Daemon error: {e}")
        
        self.log("="*70)
        self.log("Trade Spotlight Daemon STOPPED")
        self.log("="*70)

def main():
    daemon = SpotlightDaemon()
    daemon.run()

if __name__ == "__main__":
    main()
