#!/usr/bin/env python3
"""
ETHUSDT Entry Buffer System
Calculates optimal entry/exit prices with configurable offsets
Ported from archived ETHUSDT_TradeBot buffer system
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"

# Buffer Configuration (in price points, not percentage)
# ETHUSDT: 1 pip = $0.01, but we use dollar amounts
BUFFER_CONFIG = {
    "conservative": {
        "entry_offset": 5.0,      # $5 better price
        "stop_offset": 8.0,       # $8 beyond swing
        "target_offset": 5.0      # $5 before target
    },
    "moderate": {
        "entry_offset": 3.0,
        "stop_offset": 5.0,
        "target_offset": 3.0
    },
    "aggressive": {
        "entry_offset": 1.0,
        "stop_offset": 3.0,
        "target_offset": 1.0
    }
}

class EntryBufferCalculator:
    """Calculate buffered entry/exit prices"""
    
    def __init__(self, aggression_level="moderate"):
        self.config = BUFFER_CONFIG.get(aggression_level, BUFFER_CONFIG["moderate"])
    
    def calculate_long_levels(self, current_price, support_level, resistance_level, atr):
        """
        Calculate buffered levels for LONG position
        
        Entry: Below current price (front-run support test)
        Stop: Below support (avoid wick stop-out)
        Target: Before resistance (front-run MMs)
        """
        entry = current_price - self.config["entry_offset"]
        
        # Stop below support, but not more than 1.5x ATR
        stop_from_support = support_level - self.config["stop_offset"]
        stop_from_atr = current_price - (atr * 1.5)
        stop = max(stop_from_support, stop_from_atr)
        
        # Target before resistance
        target = resistance_level - self.config["target_offset"]
        
        # Ensure positive R:R
        risk = entry - stop
        reward = target - entry
        r_ratio = reward / risk if risk > 0 else 0
        
        return {
            "direction": "LONG",
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
            "risk": round(risk, 2),
            "reward": round(reward, 2),
            "r_ratio": round(r_ratio, 2),
            "valid": r_ratio >= 1.5  # Minimum 1.5:1 R:R
        }
    
    def calculate_short_levels(self, current_price, resistance_level, support_level, atr):
        """
        Calculate buffered levels for SHORT position
        
        Entry: Above current price (front-run resistance test)
        Stop: Above resistance (avoid wick stop-out)
        Target: Above support (front-run MMs)
        """
        entry = current_price + self.config["entry_offset"]
        
        # Stop above resistance, but not more than 1.5x ATR
        stop_from_resistance = resistance_level + self.config["stop_offset"]
        stop_from_atr = current_price + (atr * 1.5)
        stop = min(stop_from_resistance, stop_from_atr)
        
        # Target above support
        target = support_level + self.config["target_offset"]
        
        # Ensure positive R:R
        risk = stop - entry
        reward = entry - target
        r_ratio = reward / risk if risk > 0 else 0
        
        return {
            "direction": "SHORT",
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
            "risk": round(risk, 2),
            "reward": round(reward, 2),
            "r_ratio": round(r_ratio, 2),
            "valid": r_ratio >= 1.5
        }
    
    def calculate_from_analysis(self, direction, analysis_1h):
        """Calculate levels from 1h analysis data"""
        if not analysis_1h:
            return None
        
        close = analysis_1h.get('metadata', {}).get('close_price', 0)
        atr = analysis_1h.get('indicator_values', {}).get('volatility', {}).get('atr_14', 10)
        
        # Get key levels from analysis
        key_levels = analysis_1h.get('interpretations', {}).get('key_levels', {})
        resistance = key_levels.get('nearest_resistance', close * 1.02)
        support = key_levels.get('nearest_support', close * 0.98)
        
        if direction == "LONG":
            return self.calculate_long_levels(close, support, resistance, atr)
        else:
            return self.calculate_short_levels(close, resistance, support, atr)

class PositionSizingCalculator:
    """Calculate position size based on risk parameters"""
    
    @staticmethod
    def calculate_position_size(account_balance, risk_percent, entry_price, stop_price, direction):
        """
        Calculate position size based on risk
        
        Example:
        - Account: $10,000
        - Risk: 2% ($200)
        - Entry: $2,000
        - Stop: $1,990 (LONG)
        - Risk per unit: $10
        - Position size: $200 / $10 = 20 units
        """
        risk_amount = account_balance * (risk_percent / 100)
        
        if direction == "LONG":
            risk_per_unit = entry_price - stop_price
        else:
            risk_per_unit = stop_price - entry_price
        
        if risk_per_unit <= 0:
            return 0
        
        position_size_units = risk_amount / risk_per_unit
        position_size_dollars = position_size_units * entry_price
        
        return {
            "account_balance": account_balance,
            "risk_percent": risk_percent,
            "risk_amount": round(risk_amount, 2),
            "risk_per_unit": round(risk_per_unit, 2),
            "position_size_units": round(position_size_units, 4),
            "position_size_dollars": round(position_size_dollars, 2),
            "leverage_required": round(position_size_dollars / account_balance, 2)
        }
    
    @staticmethod
    def calculate_scaled_entry(account_balance, risk_percent, entry_price, stop_price, direction, scale_count=2):
        """
        Calculate scaled entry (e.g., 50% + 50%)
        Reduces risk on first entry, adds on confirmation
        """
        base_size = PositionSizingCalculator.calculate_position_size(
            account_balance, risk_percent, entry_price, stop_price, direction
        )
        
        scale_1_percent = 60  # First entry 60%
        scale_2_percent = 40  # Second entry 40%
        
        scale_1 = {
            "percent": scale_1_percent,
            "units": round(base_size["position_size_units"] * (scale_1_percent / 100), 4),
            "dollars": round(base_size["position_size_dollars"] * (scale_1_percent / 100), 2)
        }
        
        scale_2 = {
            "percent": scale_2_percent,
            "units": round(base_size["position_size_units"] * (scale_2_percent / 100), 4),
            "dollars": round(base_size["position_size_dollars"] * (scale_2_percent / 100), 2)
        }
        
        return {
            "total": base_size,
            "scale_1": scale_1,
            "scale_2": scale_2,
            "scale_2_trigger": "On confirmation (volume spike or pattern)"
        }

def main():
    """Test buffer calculations"""
    print("="*70)
    print("ETHUSDT Entry Buffer System - Test")
    print("="*70)
    
    # Load 1h analysis
    analysis_file = ANALYSIS_DIR / "1h_current.json"
    if analysis_file.exists():
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
        
        close = analysis.get('metadata', {}).get('close_price', 2000)
        print(f"\nCurrent Price: ${close:.2f}")
        
        # Test LONG levels
        print("\n--- LONG LEVELS ---")
        for aggression in ["conservative", "moderate", "aggressive"]:
            calc = EntryBufferCalculator(aggression)
            levels = calc.calculate_from_analysis("LONG", analysis)
            if levels:
                print(f"\n{aggression.upper()}:")
                print(f"  Entry: ${levels['entry']:.2f}")
                print(f"  Stop: ${levels['stop']:.2f}")
                print(f"  Target: ${levels['target']:.2f}")
                print(f"  R:R = {levels['r_ratio']:.2f}:1")
                print(f"  Valid: {levels['valid']}")
        
        # Test position sizing
        print("\n--- POSITION SIZING ---")
        sizer = PositionSizingCalculator()
        
        # Example: $10,000 account, 2% risk
        account = 10000
        risk = 2.0
        
        calc = EntryBufferCalculator("moderate")
        long_levels = calc.calculate_from_analysis("LONG", analysis)
        
        if long_levels and long_levels['valid']:
            sizing = sizer.calculate_scaled_entry(
                account, risk, 
                long_levels['entry'], long_levels['stop'], 
                "LONG"
            )
            
            print(f"\nAccount: ${account:,.2f} | Risk: {risk}% (${sizing['total']['risk_amount']:,.2f})")
            print(f"\nScale 1 ({sizing['scale_1']['percent']}%): {sizing['scale_1']['units']:.4f} units (${sizing['scale_1']['dollars']:,.2f})")
            print(f"Scale 2 ({sizing['scale_2']['percent']}%): {sizing['scale_2']['units']:.4f} units (${sizing['scale_2']['dollars']:,.2f})")
            print(f"Total: {sizing['total']['position_size_units']:.4f} units (${sizing['total']['position_size_dollars']:,.2f})")
            print(f"Leverage: {sizing['total']['leverage_required']:.2f}x")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
