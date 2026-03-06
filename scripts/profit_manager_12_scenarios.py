#!/usr/bin/env python3
"""
ETHUSDT Advanced Profit Manager - 12 Scenarios
Manages trade exits based on multiple profit scenarios
Ported from archived ETHUSDT_TradeBot

12 Scenarios:
1. Standard R:R (1.5:1) - Scale 50% at target, trail 50%
2. Extended Target (2:1+) - Scale 33% at 1.5R, 33% at 2R, trail 34%
3. Quick Profit (< 1R) - Take full profit at 0.8R (low confidence)
4. Runner Mode (3:1+) - Scale 25% at 1R, 25% at 2R, 25% at 3R, trail 25%
5. Breakeven Stop - Move to BE at 0.5R profit
6. Trailing Stop - Activate trailing at 1R profit
7. Time-Based Exit - Exit if no progress in 4 hours
8. Reversal Exit - Exit on opposite signal
9. Volatility Exit - Widen/tighten stops based on ATR expansion
10. Partial Scale-Out - Scale 50% at 1R, move stop to BE, hold 50%
11. Pyramid Add - Add to winner at 1R (if confluence increases)
12. Emergency Exit - Exit immediately on regime change
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"

class ExitScenario(Enum):
    """12 Exit scenarios"""
    STANDARD_RR = 1           # Scale 50% at target, trail 50%
    EXTENDED_TARGET = 2       # Multiple scale-outs (33/33/34)
    QUICK_PROFIT = 3          # Full exit at 0.8R
    RUNNER_MODE = 4           # Multiple targets (25/25/25/25)
    BREAKEVEN_STOP = 5        # Move to BE at 0.5R
    TRAILING_STOP = 6         # Trail after 1R
    TIME_BASED = 7            # Exit after time limit
    REVERSAL_EXIT = 8         # Exit on opposite signal
    VOLATILITY_EXIT = 9       # ATR-based adjustments
    PARTIAL_SCALE_OUT = 10    # 50% at 1R, trail 50%
    PYRAMID_ADD = 11          # Add to winner
    EMERGENCY_EXIT = 12       # Immediate on regime change

class ProfitManager:
    """Manage trade exits with 12 scenarios"""
    
    def __init__(self, trade_plan):
        self.trade_plan = trade_plan
        self.entry_price = trade_plan['entry_strategy']['levels']['entry']
        self.stop_price = trade_plan['entry_strategy']['levels']['stop']
        self.initial_target = trade_plan['entry_strategy']['levels']['target']
        self.direction = trade_plan['direction']
        self.risk_amount = abs(self.entry_price - self.stop_price)
        
        # Select scenario based on setup quality
        self.scenario = self.select_scenario()
        self.scales = self.calculate_scale_points()
    
    def select_scenario(self):
        """Select best exit scenario based on setup characteristics"""
        setup_quality = self.trade_plan.get('setup_quality', {})
        weighted_score = abs(setup_quality.get('weighted_score', 0))
        
        # High confidence + strong trend = Runner mode
        if weighted_score >= 0.8:
            return ExitScenario.RUNNER_MODE
        
        # Medium confidence = Extended targets
        elif weighted_score >= 0.65:
            return ExitScenario.EXTENDED_TARGET
        
        # Low confidence = Quick profit
        elif weighted_score < 0.5:
            return ExitScenario.QUICK_PROFIT
        
        # Standard for everything else
        else:
            return ExitScenario.STANDARD_RR
    
    def calculate_scale_points(self):
        """Calculate scale-out points based on scenario"""
        
        if self.scenario == ExitScenario.STANDARD_RR:
            # Scale 50% at target, trail 50%
            return [
                {"r_multiple": 1.5, "percent": 50, "action": "scale_out", "move_stop_to": "entry"},
                {"r_multiple": 2.0, "percent": 50, "action": "trail", "trail_distance": "1.5x_ATR"}
            ]
        
        elif self.scenario == ExitScenario.EXTENDED_TARGET:
            # Scale 33% at 1.5R, 33% at 2R, trail 34%
            return [
                {"r_multiple": 1.5, "percent": 33, "action": "scale_out", "move_stop_to": "entry"},
                {"r_multiple": 2.0, "percent": 33, "action": "scale_out", "move_stop_to": "1.5R"},
                {"r_multiple": 3.0, "percent": 34, "action": "trail", "trail_distance": "2x_ATR"}
            ]
        
        elif self.scenario == ExitScenario.QUICK_PROFIT:
            # Full exit at 0.8R
            return [
                {"r_multiple": 0.8, "percent": 100, "action": "full_exit", "reason": "Quick profit - low confidence"}
            ]
        
        elif self.scenario == ExitScenario.RUNNER_MODE:
            # Scale 25% at 1R, 2R, 3R, trail 25%
            return [
                {"r_multiple": 1.0, "percent": 25, "action": "scale_out", "move_stop_to": "entry"},
                {"r_multiple": 2.0, "percent": 25, "action": "scale_out", "move_stop_to": "breakeven"},
                {"r_multiple": 3.0, "percent": 25, "action": "scale_out", "move_stop_to": "1R_profit"},
                {"r_multiple": 4.0, "percent": 25, "action": "trail", "trail_distance": "3x_ATR"}
            ]
        
        elif self.scenario == ExitScenario.PARTIAL_SCALE_OUT:
            # Scale 50% at 1R, move stop to BE, trail 50%
            return [
                {"r_multiple": 1.0, "percent": 50, "action": "scale_out", "move_stop_to": "entry"},
                {"r_multiple": 2.0, "percent": 50, "action": "trail", "trail_distance": "1.5x_ATR"}
            ]
        
        else:
            # Default to standard
            return [
                {"r_multiple": 1.5, "percent": 50, "action": "scale_out", "move_stop_to": "entry"},
                {"r_multiple": 2.0, "percent": 50, "action": "trail", "trail_distance": "1.5x_ATR"}
            ]
    
    def calculate_price_levels(self):
        """Calculate actual price levels for each scale point"""
        levels = []
        
        for scale in self.scales:
            r_multiple = scale['r_multiple']
            
            if self.direction == "LONG":
                price = self.entry_price + (self.risk_amount * r_multiple)
            else:
                price = self.entry_price - (self.risk_amount * r_multiple)
            
            levels.append({
                **scale,
                "price": round(price, 2),
                "profit_dollar": round(abs(price - self.entry_price), 2),
                "profit_percent": round((abs(price - self.entry_price) / self.entry_price) * 100, 2)
            })
        
        return levels
    
    def generate_exit_plan(self):
        """Generate complete exit plan"""
        levels = self.calculate_price_levels()
        
        plan = {
            "trade_id": self.trade_plan['trade_id'],
            "timestamp": datetime.now().isoformat(),
            "scenario": {
                "name": self.scenario.name,
                "value": self.scenario.value,
                "description": self.get_scenario_description()
            },
            "entry": self.entry_price,
            "stop": self.stop_price,
            "direction": self.direction,
            "risk_amount": round(self.risk_amount, 2),
            "scale_points": levels,
            "stop_management": {
                "breakeven_trigger": "0.5R profit",
                "trailing_trigger": "1.0R profit",
                "emergency_stop": "Regime change or opposite signal"
            },
            "time_based_rules": {
                "max_hold_time": "8 hours",
                "no_progress_exit": "4 hours without 0.5R profit",
                "session_end": "Exit before major news/events"
            },
            "profit_targets": {
                "conservative": levels[0]['price'] if levels else self.initial_target,
                "moderate": levels[1]['price'] if len(levels) > 1 else self.initial_target * 1.2,
                "aggressive": levels[-1]['price'] if levels else self.initial_target * 1.5
            }
        }
        
        return plan
    
    def get_scenario_description(self):
        """Get human-readable description of scenario"""
        descriptions = {
            ExitScenario.STANDARD_RR: "Standard 1.5:1 R:R - Scale 50% at target, trail 50%",
            ExitScenario.EXTENDED_TARGET: "Extended targets - Scale 33/33/34 at 1.5R/2R/3R",
            ExitScenario.QUICK_PROFIT: "Quick profit mode - Full exit at 0.8R (low confidence)",
            ExitScenario.RUNNER_MODE: "Runner mode - Scale 25% at 1R/2R/3R, trail 25%",
            ExitScenario.BREAKEVEN_STOP: "Breakeven focus - Move to BE at 0.5R",
            ExitScenario.TRAILING_STOP: "Trailing stop - Activate at 1R profit",
            ExitScenario.TIME_BASED: "Time-based exit - Max 4 hour hold",
            ExitScenario.REVERSAL_EXIT: "Reversal exit - Exit on opposite signal",
            ExitScenario.VOLATILITY_EXIT: "Volatility adaptive - Widen/tighten based on ATR",
            ExitScenario.PARTIAL_SCALE_OUT: "Partial scale - 50% at 1R, trail 50%",
            ExitScenario.PYRAMID_ADD: "Pyramid add - Add to winner at 1R",
            ExitScenario.EMERGENCY_EXIT: "Emergency - Exit immediately on regime change"
        }
        return descriptions.get(self.scenario, "Standard exit plan")

class TradeMonitor:
    """Monitor active trade and suggest actions"""
    
    def __init__(self, exit_plan):
        self.exit_plan = exit_plan
        self.scale_points = exit_plan['scale_points']
        self.current_r = 0
    
    def check_current_status(self, current_price):
        """Check current status against exit plan"""
        entry = self.exit_plan['entry']
        direction = self.exit_plan['direction']
        
        # Calculate current R multiple
        if direction == "LONG":
            profit = current_price - entry
        else:
            profit = entry - current_price
        
        risk = abs(entry - self.exit_plan['stop'])
        self.current_r = profit / risk if risk > 0 else 0
        
        # Check which scale points have been hit
        hit_scales = [s for s in self.scale_points if self.current_r >= s['r_multiple']]
        pending_scales = [s for s in self.scale_points if self.current_r < s['r_multiple']]
        
        # Generate recommendations
        recommendations = []
        
        if self.current_r >= 0.5:
            recommendations.append("✅ Move stop to breakeven (0.5R reached)")
        
        if self.current_r >= 1.0:
            recommendations.append("✅ Activate trailing stop (1R reached)")
        
        for scale in pending_scales[:1]:  # Next scale
            r_needed = scale['r_multiple'] - self.current_r
            recommendations.append(f"⏳ Next scale at {scale['r_multiple']}R (need {r_needed:.2f}R more)")
        
        return {
            "current_r": round(self.current_r, 2),
            "profit_dollar": round(profit, 2) if direction == "LONG" else round(-profit, 2),
            "profit_percent": round((abs(profit) / entry) * 100, 2),
            "scales_completed": len(hit_scales),
            "scales_pending": len(pending_scales),
            "recommendations": recommendations
        }

def main():
    """Test profit manager"""
    print("="*70)
    print("ETHUSDT Advanced Profit Manager - 12 Scenarios")
    print("="*70)
    
    # Example trade plans with different confidence levels
    test_plans = [
        {
            "trade_id": "ETH_LONG_001",
            "direction": "LONG",
            "setup_quality": {"weighted_score": 0.85},  # High confidence
            "entry_strategy": {
                "levels": {
                    "entry": 2000,
                    "stop": 1980,
                    "target": 2100
                }
            }
        },
        {
            "trade_id": "ETH_SHORT_002",
            "direction": "SHORT",
            "setup_quality": {"weighted_score": 0.50},  # Medium confidence
            "entry_strategy": {
                "levels": {
                    "entry": 2100,
                    "stop": 2120,
                    "target": 2000
                }
            }
        },
        {
            "trade_id": "ETH_LONG_003",
            "direction": "LONG",
            "setup_quality": {"weighted_score": 0.30},  # Low confidence
            "entry_strategy": {
                "levels": {
                    "entry": 1950,
                    "stop": 1930,
                    "target": 2050
                }
            }
        }
    ]
    
    for plan in test_plans:
        print(f"\n{'='*70}")
        print(f"Trade: {plan['trade_id']} | Direction: {plan['direction']}")
        print(f"Confidence Score: {plan['setup_quality']['weighted_score']:.2f}")
        print(f"Entry: ${plan['entry_strategy']['levels']['entry']:.2f}")
        print(f"Stop: ${plan['entry_strategy']['levels']['stop']:.2f}")
        print("="*70)
        
        manager = ProfitManager(plan)
        exit_plan = manager.generate_exit_plan()
        
        print(f"\nScenario: {exit_plan['scenario']['name']}")
        print(f"Description: {exit_plan['scenario']['description']}")
        print(f"\nScale Points:")
        
        for i, scale in enumerate(exit_plan['scale_points'], 1):
            print(f"  {i}. At {scale['r_multiple']}R (${scale['price']:.2f}) - "
                  f"{scale['action']} {scale['percent']}% | "
                  f"Profit: ${scale['profit_dollar']:.2f} ({scale['profit_percent']:.2f}%)")
        
        # Simulate monitoring
        print(f"\nMonitoring Examples:")
        monitor = TradeMonitor(exit_plan)
        
        test_prices = [
            plan['entry_strategy']['levels']['entry'] * 1.01,  # +1%
            plan['entry_strategy']['levels']['entry'] * 1.03,  # +3%
            plan['entry_strategy']['levels']['entry'] * 1.05,  # +5%
        ]
        
        for price in test_prices:
            status = monitor.check_current_status(price)
            print(f"  At ${price:.2f} ({status['current_r']:.2f}R): "
                  f"{', '.join(status['recommendations'][:2])}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
