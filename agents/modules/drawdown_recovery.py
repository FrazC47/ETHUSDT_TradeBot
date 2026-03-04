#!/usr/bin/env python3
"""
Drawdown Recovery Protocol
Manages trading during and after drawdown periods
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

class RecoveryMode(Enum):
    """Recovery mode states"""
    NORMAL = "normal"           # Normal trading
    CAUTIOUS = "cautious"       # Reduced size after small DD
    DEFENSIVE = "defensive"     # Minimal size after medium DD
    RECOVERY = "recovery"       # Focus on base hits after large DD
    PAUSED = "paused"           # Stop trading after max DD

@dataclass
class DrawdownMetrics:
    """Current drawdown metrics"""
    current_drawdown_pct: float
    max_drawdown_pct: float
    consecutive_losses: int
    days_in_drawdown: int
    recovery_progress_pct: float  # % recovered from max DD

class DrawdownRecoveryManager:
    """
    Manages trading behavior during drawdown periods
    Implements automatic recovery protocols
    """
    
    # Drawdown thresholds
    CAUTIOUS_THRESHOLD = 0.05      # 5% DD = reduce size
    DEFENSIVE_THRESHOLD = 0.10     # 10% DD = minimal size
    RECOVERY_THRESHOLD = 0.15      # 15% DD = recovery mode
    MAX_DD_THRESHOLD = 0.20        # 20% DD = pause trading
    
    # Recovery triggers
    CONSECUTIVE_LOSSES_LIMIT = 3   # After 3 losses, go cautious
    DAYS_IN_DD_LIMIT = 7           # After 7 days in DD, reassess
    
    def __init__(self):
        self.peak_equity = 0
        self.current_equity = 0
        self.loss_streak = 0
        self.dd_start_date = None
        self.mode = RecoveryMode.NORMAL
        self.mode_history = []
        
    def update_equity(self, current_equity: float, trade_result: Optional[float] = None):
        """
        Update equity and check drawdown status
        
        Args:
            current_equity: Current account equity
            trade_result: P&L of last trade (None if no new trade)
        """
        self.current_equity = current_equity
        
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.loss_streak = 0
            self.dd_start_date = None
            self._set_mode(RecoveryMode.NORMAL)
        
        # Update loss streak
        if trade_result is not None:
            if trade_result < 0:
                self.loss_streak += 1
                if self.dd_start_date is None:
                    self.dd_start_date = datetime.now()
            else:
                self.loss_streak = 0
        
        # Calculate metrics
        metrics = self.get_metrics()
        
        # Determine appropriate mode
        new_mode = self._determine_mode(metrics)
        if new_mode != self.mode:
            self._set_mode(new_mode)
    
    def _determine_mode(self, metrics: DrawdownMetrics) -> RecoveryMode:
        """Determine recovery mode based on metrics"""
        
        # Max drawdown - PAUSE
        if metrics.current_drawdown_pct >= self.MAX_DD_THRESHOLD:
            return RecoveryMode.PAUSED
        
        # Large drawdown - RECOVERY MODE
        if metrics.current_drawdown_pct >= self.RECOVERY_THRESHOLD:
            return RecoveryMode.RECOVERY
        
        # Medium drawdown - DEFENSIVE
        if metrics.current_drawdown_pct >= self.DEFENSIVE_THRESHOLD:
            return RecoveryMode.DEFENSIVE
        
        # Small drawdown - CAUTIOUS
        if metrics.current_drawdown_pct >= self.CAUTIOUS_THRESHOLD:
            return RecoveryMode.CAUTIOUS
        
        # Consecutive losses trigger
        if self.loss_streak >= self.CONSECUTIVE_LOSSES_LIMIT:
            return RecoveryMode.CAUTIOUS
        
        # Extended time in drawdown
        if metrics.days_in_drawdown >= self.DAYS_IN_DD_LIMIT:
            return RecoveryMode.DEFENSIVE
        
        return RecoveryMode.NORMAL
    
    def _set_mode(self, mode: RecoveryMode):
        """Set recovery mode and log change"""
        if mode != self.mode:
            self.mode_history.append({
                'timestamp': datetime.now(),
                'from_mode': self.mode.value,
                'to_mode': mode.value,
                'equity': self.current_equity,
                'drawdown': self.get_metrics().current_drawdown_pct
            })
            self.mode = mode
            
            # Alert on significant mode changes
            if mode in [RecoveryMode.RECOVERY, RecoveryMode.PAUSED]:
                self._send_alert(mode)
    
    def _send_alert(self, mode: RecoveryMode):
        """Send alert for significant mode changes"""
        alerts = {
            RecoveryMode.RECOVERY: "🚨 RECOVERY MODE: Large drawdown detected. Focus on small wins.",
            RecoveryMode.PAUSED: "⛔ TRADING PAUSED: Max drawdown reached. Manual review required."
        }
        print(alerts.get(mode, f"Mode changed to: {mode.value}"))
    
    def get_metrics(self) -> DrawdownMetrics:
        """Calculate current drawdown metrics"""
        if self.peak_equity == 0:
            return DrawdownMetrics(0, 0, 0, 0, 0)
        
        current_dd = (self.peak_equity - self.current_equity) / self.peak_equity
        max_dd = max(current_dd, getattr(self, '_max_dd', 0))
        
        days_in_dd = 0
        if self.dd_start_date:
            days_in_dd = (datetime.now() - self.dd_start_date).days
        
        # Recovery progress (if we have a previous max DD)
        recovery_pct = 0
        if hasattr(self, '_max_dd') and self._max_dd > 0:
            recovery_pct = (self._max_dd - current_dd) / self._max_dd * 100
        
        metrics = DrawdownMetrics(
            current_drawdown_pct=current_dd,
            max_drawdown_pct=max_dd,
            consecutive_losses=self.loss_streak,
            days_in_drawdown=days_in_dd,
            recovery_progress_pct=recovery_pct
        )
        
        self._max_dd = max_dd
        
        return metrics
    
    def get_adjusted_parameters(self) -> Dict:
        """Get trading parameters adjusted for current recovery mode"""
        
        base_params = {
            'risk_per_trade': 0.03,
            'position_scale': 1.0,
            'volume_threshold': 1.0,
            'min_score': 70,
            'max_trades_per_day': 3,
            'partial_exit_1': 0.25,
            'partial_exit_2': 0.25,
            'trailing_activation': 0.03
        }
        
        adjustments = {
            RecoveryMode.NORMAL: {
                'description': 'Normal trading parameters',
                'adjustments': {}
            },
            RecoveryMode.CAUTIOUS: {
                'description': 'After 5% DD or 3 losses - Reduced size, higher quality',
                'adjustments': {
                    'risk_per_trade': 0.02,      # 2% instead of 3%
                    'position_scale': 0.7,        # 70% size
                    'volume_threshold': 1.2,      # Higher quality only
                    'min_score': 75,              # Better setups only
                    'max_trades_per_day': 2       # Fewer trades
                }
            },
            RecoveryMode.DEFENSIVE: {
                'description': 'After 10% DD - Minimal exposure, preserve capital',
                'adjustments': {
                    'risk_per_trade': 0.01,      # 1% risk
                    'position_scale': 0.5,        # Half size
                    'volume_threshold': 1.5,      # Only best setups
                    'min_score': 80,              # A+ setups only
                    'max_trades_per_day': 1,      # One trade max
                    'partial_exit_1': 0.5,        # Take profit faster
                    'trailing_activation': 0.02   # Trail earlier
                }
            },
            RecoveryMode.RECOVERY: {
                'description': 'After 15% DD - Base hits only, rebuild confidence',
                'adjustments': {
                    'risk_per_trade': 0.01,      # Minimal risk
                    'position_scale': 0.4,        # Small size
                    'volume_threshold': 1.8,      # Only exceptional setups
                    'min_score': 85,              # Perfect setups only
                    'max_trades_per_day': 1,
                    'partial_exit_1': 0.5,        # Quick profits
                    'partial_exit_2': 0.3,
                    'trailing_activation': 0.015  # Very tight trailing
                }
            },
            RecoveryMode.PAUSED: {
                'description': 'After 20% DD - STOP TRADING, manual review required',
                'adjustments': {
                    'risk_per_trade': 0,
                    'position_scale': 0,
                    'max_trades_per_day': 0       # NO TRADES
                }
            }
        }
        
        mode_adjustment = adjustments.get(self.mode, adjustments[RecoveryMode.NORMAL])
        
        # Apply adjustments
        adjusted = base_params.copy()
        adjusted.update(mode_adjustment['adjustments'])
        adjusted['mode'] = self.mode.value
        adjusted['mode_description'] = mode_adjustment['description']
        
        return adjusted
    
    def get_recovery_plan(self) -> str:
        """Get recommended recovery actions"""
        metrics = self.get_metrics()
        
        plans = {
            RecoveryMode.NORMAL: "Continue normal trading. Monitor for any degradation.",
            
            RecoveryMode.CAUTIOUS: """
Recovery Actions:
1. Reduce position size to 70%
2. Only take A-grade setups (score ≥75)
3. Take profits more aggressively
4. Review recent losses for patterns
5. Consider taking a break after next loss
""",
            RecoveryMode.DEFENSIVE: """
Recovery Actions:
1. Reduce to 50% position size
2. Only exceptional setups (score ≥80)
3. Maximum 1 trade per day
4. Tighten stops to 1.0x ATR
5. Take 50% profit at first target
6. Manual review of strategy recommended
""",
            RecoveryMode.RECOVERY: """
Recovery Actions:
1. Minimal 40% position size
2. Only perfect setups (score ≥85)
3. Focus on "base hits" - small consistent wins
4. Take profits quickly (50% at +2%)
5. Rebuild confidence with small wins
6. Review strategy fundamentals
""",
            RecoveryMode.PAUSED: """
STOP TRADING IMMEDIATELY

Required Actions:
1. Do NOT take any new trades
2. Close existing positions if appropriate
3. Manual strategy review required
4. Analyze what went wrong
5. Paper trade until confidence restored
6. Consider reducing leverage or changing strategy
7. Resume only after 3 consecutive paper trade wins
"""
        }
        
        return plans.get(self.mode, "Unknown mode")
    
    def print_status(self):
        """Print current drawdown status"""
        metrics = self.get_metrics()
        params = self.get_adjusted_parameters()
        
        print("="*70)
        print("DRAWDOWN RECOVERY STATUS")
        print("="*70)
        print(f"Current Equity:       ${self.current_equity:,.2f}")
        print(f"Peak Equity:          ${self.peak_equity:,.2f}")
        print(f"Current Drawdown:     {metrics.current_drawdown_pct*100:.1f}%")
        print(f"Max Drawdown:         {metrics.max_drawdown_pct*100:.1f}%")
        print(f"Consecutive Losses:   {metrics.consecutive_losses}")
        print(f"Days in Drawdown:     {metrics.days_in_drawdown}")
        print()
        print(f"Recovery Mode:        {self.mode.value.upper()}")
        print(f"Description:          {params['mode_description']}")
        print()
        print("ADJUSTED PARAMETERS:")
        print("-"*70)
        print(f"Risk Per Trade:       {params['risk_per_trade']*100:.1f}%")
        print(f"Position Scale:       {params['position_scale']*100:.0f}%")
        print(f"Volume Threshold:     {params['volume_threshold']}x")
        print(f"Min Score:            {params['min_score']}")
        print(f"Max Trades/Day:       {params['max_trades_per_day']}")
        print()
        print("RECOVERY PLAN:")
        print("-"*70)
        print(self.get_recovery_plan())
        print("="*70)

# Example usage
if __name__ == '__main__':
    manager = DrawdownRecoveryManager()
    
    # Simulate equity progression
    print("Simulating equity progression...\n")
    
    # Start at $10,000
    manager.update_equity(10000)
    manager.print_status()
    print()
    
    # Lose some trades - 5% DD
    print("After losing trades (5% DD)...")
    manager.update_equity(9500, -200)
    manager.update_equity(9300, -200)
    manager.update_equity(9200, -100)
    manager.print_status()
    print()
    
    # More losses - 10% DD
    print("After more losses (10% DD)...")
    manager.update_equity(8800, -400)
    manager.update_equity(8600, -200)
    manager.print_status()
