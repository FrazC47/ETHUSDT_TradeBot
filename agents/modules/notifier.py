#!/usr/bin/env python3
"""
ETHUSDT Agent Notifications
Sends Telegram alerts for trade events
"""

import os
import requests
from datetime import datetime
from typing import Optional

class Notifier:
    """Sends notifications via Telegram"""
    
    def __init__(self):
        # Get from environment or config
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.enabled = bool(self.bot_token and self.chat_id)
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send Telegram message"""
        if not self.enabled:
            print(f"[NOTIFY] {message}")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[NOTIFY ERROR] {e}")
            return False
    
    def notify_setup_detected(self, symbol: str, price: float, direction: str, confidence: float):
        """Notify when trade setup detected"""
        emoji = "🟢" if direction == "LONG" else "🔴"
        message = f"""
{emoji} <b>TRADE SETUP DETECTED</b> {emoji}

<b>Symbol:</b> {symbol}
<b>Price:</b> ${price:,.2f}
<b>Direction:</b> {direction}
<b>Confidence:</b> {confidence:.1f}%

<i>Analyzing entry conditions...</i>
"""
        return self.send_message(message)
    
    def notify_trade_entered(self, symbol: str, entry: float, stop: float, target: float, size: float):
        """Notify when trade entered"""
        risk = abs(entry - stop) / entry * 100
        reward = abs(target - entry) / entry * 100
        rr = reward / risk if risk > 0 else 0
        
        message = f"""
✅ <b>TRADE ENTERED</b> ✅

<b>Symbol:</b> {symbol}
<b>Entry:</b> ${entry:,.2f}
<b>Stop Loss:</b> ${stop:,.2f} ({risk:.2f}%)
<b>Target:</b> ${target:,.2f} ({reward:.2f}%)
<b>R:R:</b> 1:{rr:.1f}
<b>Position Size:</b> ${size:,.2f}

<i>Trade active - monitoring...</i>
"""
        return self.send_message(message)
    
    def notify_trade_exited(self, symbol: str, entry: float, exit_price: float, pnl: float, pnl_pct: float, reason: str):
        """Notify when trade exited"""
        emoji = "🟢" if pnl > 0 else "🔴"
        result = "PROFIT" if pnl > 0 else "LOSS"
        
        message = f"""
{emoji} <b>TRADE CLOSED - {result}</b> {emoji}

<b>Symbol:</b> {symbol}
<b>Entry:</b> ${entry:,.2f}
<b>Exit:</b> ${exit_price:,.2f}
<b>Reason:</b> {reason}

<b>P&L:</b> ${pnl:,.2f} ({pnl_pct:+.2f}%)

<i>Trade complete</i>
"""
        return self.send_message(message)
    
    def notify_analysis_summary(self, symbol: str, price: float, trend: str, filters_passed: int, setup_found: bool):
        """Send analysis summary"""
        status = "✅ SETUP FOUND" if setup_found else "❌ No Setup"
        
        message = f"""
📊 <b>ETHUSDT ANALYSIS</b> 📊

<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
<b>Price:</b> ${price:,.2f}
<b>Trend:</b> {trend}
<b>Filters:</b> {filters_passed}/8 passed

<b>Status:</b> {status}
"""
        return self.send_message(message)
    
    def notify_emergency(self, message: str):
        """Send emergency alert"""
        alert = f"""
🚨 <b>EMERGENCY ALERT</b> 🚨

{message}

<i>Immediate attention required</i>
"""
        return self.send_message(alert)

# Test
if __name__ == '__main__':
    notifier = Notifier()
    print("Notifier test:")
    print(f"Enabled: {notifier.enabled}")
    notifier.notify_analysis_summary("ETHUSDT", 2200.50, "BULLISH", 6, False)
