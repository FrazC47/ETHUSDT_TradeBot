#!/usr/bin/env python3
"""
ETHUSDT Agent Notifications - DISABLED
All alerts are currently turned off.
"""

class Notifier:
    """Notifier - Currently disabled"""
    
    def __init__(self):
        self.enabled = False
    
    def send_message(self, message: str, **kwargs):
        """Disabled - no messages sent"""
        return False
    
    def notify_setup_detected(self, **kwargs):
        """Disabled"""
        pass
    
    def notify_trade_entered(self, **kwargs):
        """Disabled"""
        pass
    
    def notify_trade_exited(self, **kwargs):
        """Disabled"""
        pass
    
    def notify_analysis_summary(self, **kwargs):
        """Disabled"""
        pass
    
    def notify_emergency(self, **kwargs):
        """Disabled"""
        pass
