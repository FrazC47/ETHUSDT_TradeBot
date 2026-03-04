#!/usr/bin/env python3
"""
ETHUSDT Dynamic R:R Module
Adjusts risk/reward based on price location and confidence
"""

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class DynamicRRSetup:
    """Setup with dynamically calculated R:R"""
    entry_price: float
    stop_loss: float
    target_price: float
    original_rr: float
    adjusted_rr: float
    confidence: float
    reason: str
    should_trade: bool

class DynamicRRCalculator:
    """
    Calculates dynamic R:R based on:
    - Price location in the move
    - Confidence level
    - Remaining profit potential
    """
    
    def __init__(self):
        self.min_confidence = 0.75  # 75% minimum for dynamic entry
        self.min_acceptable_rr = 1.5  # Minimum 1.5:1 even for high confidence
        
    def calculate_setup(
        self,
        current_price: float,
        optimal_entry: float,
        stop_loss: float,
        target_price: float,
        confidence: float,
        price_moved_pct: float  # How much price has moved toward target
    ) -> DynamicRRSetup:
        """
        Calculate dynamic R:R setup
        
        Args:
            current_price: Current market price
            optimal_entry: Ideal entry price (e.g., 0.618 fib)
            stop_loss: Stop loss level
            target_price: Target level
            confidence: 0-1 confidence score
            price_moved_pct: % of move already completed (0-100)
        """
        
        # Calculate original R:R (from optimal entry)
        original_risk = abs(optimal_entry - stop_loss)
        original_reward = abs(target_price - optimal_entry)
        original_rr = original_reward / original_risk if original_risk > 0 else 0
        
        # Calculate current R:R (from current price)
        current_risk = abs(current_price - stop_loss)
        current_reward = abs(target_price - current_price)
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # Decision logic
        should_trade = False
        adjusted_rr = current_rr
        reason = ""
        
        # Scenario 1: Price at or near optimal entry
        if price_moved_pct < 10:
            # Normal entry - use original R:R
            should_trade = True
            adjusted_rr = original_rr
            reason = "Price at optimal entry - standard R:R"
            
        # Scenario 2: Price moved toward target (10-40%)
        elif 10 <= price_moved_pct < 40:
            if confidence >= self.min_confidence and current_rr >= self.min_acceptable_rr:
                # High confidence, acceptable R:R - take the trade
                should_trade = True
                adjusted_rr = current_rr
                reason = f"Price moved {price_moved_pct:.0f}% but high confidence ({confidence:.0%}) and acceptable R:R ({current_rr:.1f}:1)"
            elif confidence >= 0.80 and current_rr >= 1.0:
                # High confidence, 1:1 R:R - acceptable for chase
                should_trade = True
                adjusted_rr = current_rr
                reason = f"High confidence ({confidence:.0%}) allows chase with 1:1 R:R ({current_rr:.1f}:1)"
            elif confidence >= 0.90 and current_rr >= 0.8:
                # Very high confidence, marginal R:R - chase with reduced size
                should_trade = True
                adjusted_rr = current_rr
                reason = f"Very high confidence ({confidence:.0%}) compensates for lower R:R ({current_rr:.1f}:1) - reduce position size"
            else:
                should_trade = False
                reason = f"Price moved {price_moved_pct:.0f}% and R:R too low ({current_rr:.1f}:1) with insufficient confidence ({confidence:.0%})"
                
        # Scenario 3: Price moved significantly (40-70%)
        elif 40 <= price_moved_pct < 70:
            if confidence >= 0.90 and current_rr >= 1.2:
                # Exceptional confidence, marginal R:R - chase if very confident
                should_trade = True
                adjusted_rr = current_rr
                reason = f"Price moved {price_moved_pct:.0f}% but exceptional confidence ({confidence:.0%}) - chasing with tight risk"
            else:
                should_trade = False
                reason = f"Price moved {price_moved_pct:.0f}% - too late, missed opportunity"
                
        # Scenario 4: Price moved too far (>70%)
        else:
            should_trade = False
            reason = f"Price moved {price_moved_pct:.0f}% - move mostly complete, too late"
            adjusted_rr = current_rr
        
        return DynamicRRSetup(
            entry_price=current_price,
            stop_loss=stop_loss,
            target_price=target_price,
            original_rr=original_rr,
            adjusted_rr=adjusted_rr,
            confidence=confidence,
            reason=reason,
            should_trade=should_trade
        )
    
    def get_position_size_adjustment(
        self,
        adjusted_rr: float,
        original_rr: float,
        confidence: float
    ) -> float:
        """
        Adjust position size based on R:R and confidence
        
        Returns: Position size multiplier (0.5 = half size, 1.0 = full, 1.5 = 1.5x)
        """
        base_size = 1.0
        
        # Reduce size if R:R is worse than original
        if adjusted_rr < original_rr:
            rr_penalty = adjusted_rr / original_rr  # e.g., 1.5/2.0 = 0.75
            base_size *= rr_penalty
        
        # Increase size if very high confidence
        if confidence >= 0.90:
            base_size *= 1.2  # 20% boost for high confidence
        elif confidence >= 0.80:
            base_size *= 1.1  # 10% boost for good confidence
            
        # Cap at 1.5x and floor at 0.5x
        return max(0.5, min(1.5, base_size))

# Example usage scenarios
if __name__ == '__main__':
    calc = DynamicRRCalculator()
    
    print("="*70)
    print("DYNAMIC R:R CALCULATOR - EXAMPLE SCENARIOS")
    print("="*70)
    
    # Scenario 1: Optimal entry
    print("\n1. OPTIMAL ENTRY (Price at 0.618 fib)")
    result = calc.calculate_setup(
        current_price=2200,
        optimal_entry=2200,
        stop_loss=2150,
        target_price=2300,
        confidence=0.75,
        price_moved_pct=0
    )
    print(f"   Entry: ${result.entry_price}")
    print(f"   Original R:R: {result.original_rr:.1f}:1")
    print(f"   Trade: {'✅ YES' if result.should_trade else '❌ NO'}")
    print(f"   Reason: {result.reason}")
    
    # Scenario 2: Price moved 20%, high confidence
    print("\n2. PRICE MOVED 20%, HIGH CONFIDENCE")
    result = calc.calculate_setup(
        current_price=2220,
        optimal_entry=2200,
        stop_loss=2150,
        target_price=2300,
        confidence=0.85,
        price_moved_pct=20
    )
    print(f"   Entry: ${result.entry_price} (missed $20)")
    print(f"   Original R:R: {result.original_rr:.1f}:1")
    print(f"   Adjusted R:R: {result.adjusted_rr:.1f}:1")
    print(f"   Trade: {'✅ YES' if result.should_trade else '❌ NO'}")
    print(f"   Reason: {result.reason}")
    
    # Scenario 3: Price moved 50%, exceptional confidence
    print("\n3. PRICE MOVED 50%, EXCEPTIONAL CONFIDENCE")
    result = calc.calculate_setup(
        current_price=2250,
        optimal_entry=2200,
        stop_loss=2150,
        target_price=2300,
        confidence=0.92,
        price_moved_pct=50
    )
    print(f"   Entry: ${result.entry_price} (missed $50)")
    print(f"   Original R:R: {result.original_rr:.1f}:1")
    print(f"   Adjusted R:R: {result.adjusted_rr:.1f}:1")
    print(f"   Trade: {'✅ YES' if result.should_trade else '❌ NO'}")
    print(f"   Reason: {result.reason}")
    
    # Scenario 4: Price moved 80%, too late
    print("\n4. PRICE MOVED 80%, TOO LATE")
    result = calc.calculate_setup(
        current_price=2280,
        optimal_entry=2200,
        stop_loss=2150,
        target_price=2300,
        confidence=0.95,
        price_moved_pct=80
    )
    print(f"   Entry: ${result.entry_price} (missed $80)")
    print(f"   Original R:R: {result.original_rr:.1f}:1")
    print(f"   Adjusted R:R: {result.adjusted_rr:.1f}:1")
    print(f"   Trade: {'✅ YES' if result.should_trade else '❌ NO'}")
    print(f"   Reason: {result.reason}")
    
    print("\n" + "="*70)
