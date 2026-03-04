#!/usr/bin/env python3
"""
ETHUSDT Buffer System - Anti-Manipulation Exits & Stops
Adds/subtracts buffer from calculated levels to avoid market maker traps
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

class BufferType(Enum):
    """Types of buffer adjustments"""
    CONSERVATIVE = "conservative"  # Safer, wider buffers
    MODERATE = "moderate"          # Balanced
    AGGRESSIVE = "aggressive"      # Tighter, more profit

@dataclass
class BufferedLevels:
    """Price levels with anti-manipulation buffers"""
    original_entry: float
    buffered_entry: float
    original_stop: float
    buffered_stop: float
    original_target: float
    buffered_target: float
    partial_exit_1: float  # First scale-out
    partial_exit_2: float  # Second scale-out
    trailing_activation: float  # When to start trailing
    
    # Buffer metadata
    entry_buffer_pips: float
    stop_buffer_pips: float
    target_buffer_pips: float
    buffer_type: BufferType

class BufferCalculator:
    """
    Calculates buffered price levels to avoid market maker manipulation
    
    Market makers often:
    - Push price to exact stops to liquidate positions
    - Front-run targets by a few pips
    - Manipulate around key levels (00s, 50s, fibs)
    
    Solution: Add/subtract buffer from calculated levels
    """
    
    def __init__(self, buffer_type: BufferType = BufferType.MODERATE):
        self.buffer_type = buffer_type
        self.pip_size = 0.01  # For ETH (1 pip = $0.01)
        
        # Buffer configurations (in pips)
        self.buffers = {
            BufferType.CONSERVATIVE: {
                'entry': 15,      # 15 pips buffer on entry
                'stop': 20,       # 20 pips beyond calculated stop
                'target': 15,     # 15 pips before target
                'partial_1': 25,  # First partial 25 pips before target
                'partial_2': 10,  # Second partial 10 pips before target
                'trailing': 30,   # Start trailing 30 pips before target
            },
            BufferType.MODERATE: {
                'entry': 10,
                'stop': 15,
                'target': 10,
                'partial_1': 20,
                'partial_2': 8,
                'trailing': 20,
            },
            BufferType.AGGRESSIVE: {
                'entry': 5,
                'stop': 10,
                'target': 5,
                'partial_1': 15,
                'partial_2': 5,
                'trailing': 15,
            }
        }
    
    def calculate_long_buffers(
        self,
        entry: float,
        stop: float,
        target: float
    ) -> BufferedLevels:
        """
        Calculate buffered levels for LONG position
        
        For LONGS:
        - Entry: Add buffer (enter slightly higher, avoid false breakdown)
        - Stop: Subtract buffer (stop slightly lower, avoid wick stop-out)
        - Target: Subtract buffer (exit slightly before target, front-run MMs)
        """
        b = self.buffers[self.buffer_type]
        
        # Convert pips to price
        entry_buffer = b['entry'] * self.pip_size
        stop_buffer = b['stop'] * self.pip_size
        target_buffer = b['target'] * self.pip_size
        partial_1_buffer = b['partial_1'] * self.pip_size
        partial_2_buffer = b['partial_2'] * self.pip_size
        trailing_buffer = b['trailing'] * self.pip_size
        
        # Calculate buffered levels
        buffered_entry = entry + entry_buffer  # Enter higher
        buffered_stop = stop - stop_buffer     # Stop lower
        buffered_target = target - target_buffer  # Exit before target
        
        # Partial exits (before target)
        distance_to_target = target - entry
        partial_1 = target - partial_1_buffer  # First scale-out
        partial_2 = target - partial_2_buffer  # Second scale-out
        
        # Trailing activation
        trailing_activation = target - trailing_buffer
        
        return BufferedLevels(
            original_entry=entry,
            buffered_entry=buffered_entry,
            original_stop=stop,
            buffered_stop=buffered_stop,
            original_target=target,
            buffered_target=buffered_target,
            partial_exit_1=partial_1,
            partial_exit_2=partial_2,
            trailing_activation=trailing_activation,
            entry_buffer_pips=b['entry'],
            stop_buffer_pips=b['stop'],
            target_buffer_pips=b['target'],
            buffer_type=self.buffer_type
        )
    
    def calculate_short_buffers(
        self,
        entry: float,
        stop: float,
        target: float
    ) -> BufferedLevels:
        """
        Calculate buffered levels for SHORT position
        
        For SHORTS:
        - Entry: Subtract buffer (enter slightly lower)
        - Stop: Add buffer (stop slightly higher)
        - Target: Add buffer (exit slightly before target)
        """
        b = self.buffers[self.buffer_type]
        
        entry_buffer = b['entry'] * self.pip_size
        stop_buffer = b['stop'] * self.pip_size
        target_buffer = b['target'] * self.pip_size
        partial_1_buffer = b['partial_1'] * self.pip_size
        partial_2_buffer = b['partial_2'] * self.pip_size
        trailing_buffer = b['trailing'] * self.pip_size
        
        # Calculate buffered levels (opposite for shorts)
        buffered_entry = entry - entry_buffer  # Enter lower
        buffered_stop = stop + stop_buffer     # Stop higher
        buffered_target = target + target_buffer  # Exit before target (higher for shorts)
        
        # Partial exits
        partial_1 = target + partial_1_buffer  # First scale-out
        partial_2 = target + partial_2_buffer  # Second scale-out
        
        # Trailing activation
        trailing_activation = target + trailing_buffer
        
        return BufferedLevels(
            original_entry=entry,
            buffered_entry=buffered_entry,
            original_stop=stop,
            buffered_stop=buffered_stop,
            original_target=target,
            buffered_target=buffered_target,
            partial_exit_1=partial_1,
            partial_exit_2=partial_2,
            trailing_activation=trailing_activation,
            entry_buffer_pips=b['entry'],
            stop_buffer_pips=b['stop'],
            target_buffer_pips=b['target'],
            buffer_type=self.buffer_type
        )
    
    def explain_buffers(self, levels: BufferedLevels, direction: str = "LONG"):
        """Print explanation of buffer logic"""
        
        print("="*70)
        print(f"BUFFER EXPLANATION - {direction} POSITION ({levels.buffer_type.value.upper()})")
        print("="*70)
        
        print(f"\n📍 ENTRY:")
        print(f"   Calculated:  ${levels.original_entry:.2f}")
        print(f"   Buffered:    ${levels.buffered_entry:.2f}")
        if direction == "LONG":
            print(f"   Logic:       Enter ${levels.entry_buffer_pips} pips HIGHER")
            print(f"   Reason:      Avoid false breakdown below support")
        else:
            print(f"   Logic:       Enter ${levels.entry_buffer_pips} pips LOWER")
            print(f"   Reason:      Avoid false breakout above resistance")
        
        print(f"\n🛑 STOP LOSS:")
        print(f"   Calculated:  ${levels.original_stop:.2f}")
        print(f"   Buffered:    ${levels.buffered_stop:.2f}")
        if direction == "LONG":
            print(f"   Logic:       Stop ${levels.stop_buffer_pips} pips LOWER")
            print(f"   Reason:      Avoid wick stop-out, give price room")
        else:
            print(f"   Logic:       Stop ${levels.stop_buffer_pips} pips HIGHER")
            print(f"   Reason:      Avoid wick stop-out, give price room")
        
        print(f"\n🎯 TARGET:")
        print(f"   Calculated:  ${levels.original_target:.2f}")
        print(f"   Buffered:    ${levels.buffered_target:.2f}")
        if direction == "LONG":
            print(f"   Logic:       Exit ${levels.target_buffer_pips} pips BEFORE target")
            print(f"   Reason:      Front-run market makers, capture profit")
        else:
            print(f"   Logic:       Exit ${levels.target_buffer_pips} pips BEFORE target")
            print(f"   Reason:      Front-run market makers, capture profit")
        
        print(f"\n📊 PARTIAL EXITS:")
        print(f"   First 25%:   ${levels.partial_exit_1:.2f}")
        print(f"   Second 25%:  ${levels.partial_exit_2:.2f}")
        print(f"   Final 50%:   ${levels.buffered_target:.2f}")
        print(f"   Reason:      Scale out before MM front-run")
        
        print(f"\n🔄 TRAILING ACTIVATION:")
        print(f"   Start at:    ${levels.trailing_activation:.2f}")
        print(f"   Reason:      Begin trailing before target hit")
        
        # Calculate R:R impact
        if direction == "LONG":
            original_risk = levels.original_entry - levels.original_stop
            original_reward = levels.original_target - levels.original_entry
            buffered_risk = levels.buffered_entry - levels.buffered_stop
            buffered_reward = levels.buffered_target - levels.buffered_entry
        else:
            original_risk = levels.original_stop - levels.original_entry
            original_reward = levels.original_entry - levels.original_target
            buffered_risk = levels.buffered_stop - levels.buffered_entry
            buffered_reward = levels.buffered_entry - levels.buffered_target
        
        original_rr = original_reward / original_risk if original_risk > 0 else 0
        buffered_rr = buffered_reward / buffered_risk if buffered_risk > 0 else 0
        
        print(f"\n📈 R:R IMPACT:")
        print(f"   Original R:R:  1:{original_rr:.2f}")
        print(f"   Buffered R:R:  1:{buffered_rr:.2f}")
        print(f"   Change:        {((buffered_rr/original_rr-1)*100):+.1f}%")
        print(f"   Trade-off:     Slightly worse R:R for higher probability of profit")
        
        print("\n" + "="*70)

# Example usage
if __name__ == '__main__':
    # Example LONG setup
    entry = 2200.00
    stop = 2150.00
    target = 2300.00
    
    print("\n" + "="*70)
    print("ETHUSDT BUFFER SYSTEM - EXAMPLE")
    print("="*70)
    print(f"\nOriginal Setup:")
    print(f"  Entry:  ${entry:.2f}")
    print(f"  Stop:   ${stop:.2f}")
    print(f"  Target: ${target:.2f}")
    print(f"  R:R:    1:{((target-entry)/(entry-stop)):.1f}")
    
    # Conservative buffers
    calc_conservative = BufferCalculator(BufferType.CONSERVATIVE)
    levels_conservative = calc_conservative.calculate_long_buffers(entry, stop, target)
    calc_conservative.explain_buffers(levels_conservative, "LONG")
    
    # Moderate buffers
    calc_moderate = BufferCalculator(BufferType.MODERATE)
    levels_moderate = calc_moderate.calculate_long_buffers(entry, stop, target)
    calc_moderate.explain_buffers(levels_moderate, "LONG")
    
    # Aggressive buffers
    calc_aggressive = BufferCalculator(BufferType.AGGRESSIVE)
    levels_aggressive = calc_aggressive.calculate_long_buffers(entry, stop, target)
    calc_aggressive.explain_buffers(levels_aggressive, "LONG")
