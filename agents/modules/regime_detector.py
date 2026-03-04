#!/usr/bin/env python3
"""
Market Regime Detector for ETHUSDT
Detects market conditions and adapts strategy parameters
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np

class MarketRegime(Enum):
    """Market regime classifications"""
    STRONG_BULL = "strong_bull"      # Trending up, high momentum
    BULL = "bull"                     # Trending up, normal momentum
    RANGE_BOUND = "range_bound"       # Sideways, no clear trend
    BEAR = "bear"                     # Trending down, normal momentum
    STRONG_BEAR = "strong_bear"       # Trending down, high momentum
    HIGH_VOLATILITY = "high_vol"      # Choppy, large moves
    LOW_VOLATILITY = "low_vol"        # Compressed, small moves

@dataclass
class RegimeParameters:
    """Strategy parameters optimized for specific regime"""
    # Entry filters
    volume_threshold: float
    rsi_min: int
    rsi_max: int
    consecutive_bullish: int
    
    # Risk management
    atr_multiplier_stop: float
    atr_multiplier_target: float
    position_scale: float
    
    # Position sizing
    risk_per_trade: float  # % of account
    max_concurrent_trades: int
    
    # Profit taking
    partial_exit_1: float  # % of position at first target
    partial_exit_2: float  # % of position at second target
    trailing_activation: float  # % profit to activate trailing
    
    # Description
    description: str

class RegimeAdaptiveStrategy:
    """
    Adapts strategy parameters based on detected market regime
    """
    
    # Regime-specific parameter sets
    REGIME_PARAMS = {
        MarketRegime.STRONG_BULL: RegimeParameters(
            volume_threshold=0.8,    # Lower threshold (more opportunities)
            rsi_min=45,              # Higher RSI floor (strong trend)
            rsi_max=85,              # Allow higher RSI (momentum)
            consecutive_bullish=2,   # Normal confirmation
            atr_multiplier_stop=2.0, # Wider stops (volatility)
            atr_multiplier_target=4.0, # Higher targets (trend)
            position_scale=1.0,      # Full size
            risk_per_trade=0.03,     # 3% risk
            max_concurrent_trades=2, # Can hold multiple
            partial_exit_1=0.25,     # Scale out gradually
            partial_exit_2=0.25,
            trailing_activation=0.02, # Trail early
            description="Aggressive trend following, wider stops, larger targets"
        ),
        
        MarketRegime.BULL: RegimeParameters(
            volume_threshold=1.0,
            rsi_min=40,
            rsi_max=75,
            consecutive_bullish=2,
            atr_multiplier_stop=1.5,
            atr_multiplier_target=3.0,
            position_scale=1.0,
            risk_per_trade=0.03,
            max_concurrent_trades=1,
            partial_exit_1=0.25,
            partial_exit_2=0.25,
            trailing_activation=0.03,
            description="Standard trend following parameters"
        ),
        
        MarketRegime.RANGE_BOUND: RegimeParameters(
            volume_threshold=1.2,    # Higher threshold (quality only)
            rsi_min=35,              # Lower RSI (buy dips)
            rsi_max=70,              # Lower RSI max (sell rips)
            consecutive_bullish=3,   # More confirmation needed
            atr_multiplier_stop=1.0, # Tighter stops
            atr_multiplier_target=2.0, # Lower targets (range)
            position_scale=0.7,      # Smaller size
            risk_per_trade=0.02,     # 2% risk (choppy)
            max_concurrent_trades=1,
            partial_exit_1=0.5,      # Take profit faster
            partial_exit_2=0.3,
            trailing_activation=0.05, # Trail later
            description="Conservative, tighter stops, faster profit taking"
        ),
        
        MarketRegime.BEAR: RegimeParameters(
            volume_threshold=1.5,    # Very high threshold (rare opportunities)
            rsi_min=25,              # Deep oversold only
            rsi_max=60,              # Lower ceiling
            consecutive_bullish=4,   # Strong confirmation needed
            atr_multiplier_stop=1.0, # Tight stops
            atr_multiplier_target=2.5, # Lower targets
            position_scale=0.5,      # Half size
            risk_per_trade=0.02,     # 2% risk
            max_concurrent_trades=1,
            partial_exit_1=0.5,      # Take profit quickly
            partial_exit_2=0.3,
            trailing_activation=0.04,
            description="Very selective, small size, quick profits"
        ),
        
        MarketRegime.STRONG_BEAR: RegimeParameters(
            volume_threshold=999,    # Essentially no trades
            rsi_min=20,
            rsi_max=50,
            consecutive_bullish=5,
            atr_multiplier_stop=0.8,
            atr_multiplier_target=2.0,
            position_scale=0.0,      # NO TRADES
            risk_per_trade=0.0,
            max_concurrent_trades=0,
            partial_exit_1=0.0,
            partial_exit_2=0.0,
            trailing_activation=0.0,
            description="STAND ASIDE - No long positions in strong bear"
        ),
        
        MarketRegime.HIGH_VOLATILITY: RegimeParameters(
            volume_threshold=1.3,
            rsi_min=30,
            rsi_max=80,
            consecutive_bullish=3,
            atr_multiplier_stop=2.5, # Very wide stops
            atr_multiplier_target=5.0, # Very high targets
            position_scale=0.6,      # Smaller size
            risk_per_trade=0.025,
            max_concurrent_trades=1,
            partial_exit_1=0.3,
            partial_exit_2=0.3,
            trailing_activation=0.02,
            description="Wide stops, smaller size, capture big moves"
        ),
        
        MarketRegime.LOW_VOLATILITY: RegimeParameters(
            volume_threshold=0.9,    # Lower threshold (more signals)
            rsi_min=40,
            rsi_max=70,
            consecutive_bullish=2,
            atr_multiplier_stop=1.2, # Tighter stops (low vol)
            atr_multiplier_target=2.5,
            position_scale=1.0,      # Full size (low risk)
            risk_per_trade=0.03,
            max_concurrent_trades=2,
            partial_exit_1=0.25,
            partial_exit_2=0.25,
            trailing_activation=0.04,
            description="Normal size, tighter stops, wait for expansion"
        )
    }
    
    def detect_regime(self, price_data: Dict) -> MarketRegime:
        """
        Detect current market regime from price data
        
        Args:
            price_data: Dict with 'prices', 'volumes', 'highs', 'lows' arrays
        
        Returns:
            MarketRegime classification
        """
        prices = price_data['prices']
        volumes = price_data.get('volumes', [])
        
        # Calculate key metrics
        returns = np.diff(prices) / prices[:-1]
        
        # Trend detection (using 20-period slope)
        if len(prices) >= 20:
            x = np.arange(20)
            y = prices[-20:]
            slope = np.polyfit(x, y, 1)[0]
            slope_pct = slope / prices[-20] * 100  # Normalized slope
        else:
            slope_pct = 0
        
        # Volatility detection
        volatility = np.std(returns) * np.sqrt(365)  # Annualized
        
        # Volume trend
        if len(volumes) >= 10:
            vol_trend = np.mean(volumes[-5:]) / np.mean(volumes[-10:-5])
        else:
            vol_trend = 1.0
        
        # ADX for trend strength (simplified)
        if len(prices) >= 14:
            highs = price_data.get('highs', prices)
            lows = price_data.get('lows', prices)
            adx = self._calculate_adx(highs, lows, prices)
        else:
            adx = 25
        
        # Regime classification logic
        if volatility > 0.8:  # Very high volatility
            return MarketRegime.HIGH_VOLATILITY
        
        if volatility < 0.3:  # Very low volatility
            return MarketRegime.LOW_VOLATILITY
        
        if slope_pct > 0.5 and adx > 30:  # Strong uptrend
            return MarketRegime.STRONG_BULL
        
        if slope_pct > 0.2 and adx > 25:  # Moderate uptrend
            return MarketRegime.BULL
        
        if slope_pct < -0.5 and adx > 30:  # Strong downtrend
            return MarketRegime.STRONG_BEAR
        
        if slope_pct < -0.2 and adx > 25:  # Moderate downtrend
            return MarketRegime.BEAR
        
        return MarketRegime.RANGE_BOUND  # Default
    
    def _calculate_adx(self, highs, lows, closes, period=14):
        """Simplified ADX calculation"""
        # This is a simplified version - real implementation would be more robust
        tr1 = np.array(highs[1:]) - np.array(lows[1:])
        tr2 = np.abs(np.array(highs[1:]) - np.array(closes[:-1]))
        tr3 = np.abs(np.array(lows[1:]) - np.array(closes[:-1]))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        
        # Simplified - return average of recent true ranges as proxy
        return np.mean(tr[-period:]) / np.mean(closes[-period:]) * 100
    
    def get_parameters(self, regime: MarketRegime) -> RegimeParameters:
        """Get strategy parameters for detected regime"""
        return self.REGIME_PARAMS.get(regime, self.REGIME_PARAMS[MarketRegime.BULL])
    
    def should_trade(self, regime: MarketRegime) -> Tuple[bool, str]:
        """Determine if trading is allowed in current regime"""
        params = self.get_parameters(regime)
        
        if params.position_scale <= 0:
            return False, f"STAND ASIDE - {regime.value} regime"
        
        if params.risk_per_trade < 0.02:
            return True, f"CAUTIOUS - {regime.value} regime (reduced size)"
        
        return True, f"ACTIVE - {regime.value} regime"

# Example usage
if __name__ == '__main__':
    detector = RegimeAdaptiveStrategy()
    
    # Example price data (would come from actual market data)
    example_data = {
        'prices': [2200, 2210, 2205, 2220, 2230, 2225, 2240, 2250, 2245, 2260,
                   2270, 2265, 2280, 2290, 2285, 2300, 2310, 2305, 2320, 2330],
        'volumes': [1000] * 20,
        'highs': [2205, 2215, 2210, 2225, 2235, 2230, 2245, 2255, 2250, 2265,
                  2275, 2270, 2285, 2295, 2290, 2305, 2315, 2310, 2325, 2335],
        'lows': [2195, 2205, 2200, 2215, 2225, 2220, 2235, 2245, 2240, 2255,
                 2265, 2260, 2275, 2285, 2280, 2295, 2305, 2300, 2315, 2325]
    }
    
    regime = detector.detect_regime(example_data)
    params = detector.get_parameters(regime)
    should_trade, reason = detector.should_trade(regime)
    
    print("="*70)
    print("MARKET REGIME DETECTION")
    print("="*70)
    print(f"Detected Regime: {regime.value.upper()}")
    print(f"Trading Status: {'✅ ' if should_trade else '❌ '}{reason}")
    print()
    print("ADAPTED PARAMETERS:")
    print("-"*70)
    print(f"Volume Threshold:     {params.volume_threshold}x")
    print(f"RSI Range:            {params.rsi_min} - {params.rsi_max}")
    print(f"ATR Stop Multiplier:  {params.atr_multiplier_stop}x")
    print(f"ATR Target Multiplier:{params.atr_multiplier_target}x")
    print(f"Position Scale:       {params.position_scale*100:.0f}%")
    print(f"Risk Per Trade:       {params.risk_per_trade*100:.1f}%")
    print(f"Description:          {params.description}")
    print("="*70)
