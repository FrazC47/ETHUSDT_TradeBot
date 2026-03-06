#!/usr/bin/env python3
"""
ETHUSDT Dynamic Risk:Reward System
Adjusts R:R ratio based on confidence levels
Ported from archived ETHUSDT_TradeBot

Logic:
- Base R:R = 1.5:1 (minimum)
- Confidence 70-79% → R:R = 1.5:1
- Confidence 80-89% → R:R = 1.2:1 (tighter, more aggressive)
- Confidence 90%+ → R:R = 1:1 (very aggressive, extend targets)
- Confidence <70% → R:R = 2:1 (wider, more conservative)
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"

class DynamicRiskRewardCalculator:
    """Calculate dynamic R:R based on confidence"""
    
    # R:R adjustment table based on confidence
    RR_TABLE = {
        "very_high": {    # 90%+
            "rr_ratio": 1.0,
            "description": "Very aggressive - 1:1 R:R, extend targets",
            "target_multiplier": 1.5,  # Extend targets 50%
            "position_scale": 1.2      # Increase position 20%
        },
        "high": {         # 80-89%
            "rr_ratio": 1.2,
            "description": "Aggressive - 1.2:1 R:R",
            "target_multiplier": 1.2,
            "position_scale": 1.1
        },
        "medium": {       # 70-79%
            "rr_ratio": 1.5,
            "description": "Standard - 1.5:1 R:R",
            "target_multiplier": 1.0,
            "position_scale": 1.0
        },
        "low": {          # 60-69%
            "rr_ratio": 2.0,
            "description": "Conservative - 2:1 R:R",
            "target_multiplier": 0.9,
            "position_scale": 0.8
        },
        "very_low": {     # <60%
            "rr_ratio": 2.5,
            "description": "Very conservative - 2.5:1 R:R, reduce size",
            "target_multiplier": 0.8,
            "position_scale": 0.6
        }
    }
    
    @staticmethod
    def calculate_confidence_score(setup_data):
        """
        Calculate overall confidence score for trade setup
        
        Factors:
        - Weighted score alignment (0-40 points)
        - Timeframe confluence (0-30 points)
        - Regime clarity (0-20 points)
        - Volume confirmation (0-10 points)
        """
        score = 0
        
        # 1. Weighted score (0-40 points)
        weighted_score = abs(setup_data.get('weighted_score', 0))
        if weighted_score >= 0.8:
            score += 40
        elif weighted_score >= 0.65:
            score += 35
        elif weighted_score >= 0.5:
            score += 25
        elif weighted_score >= 0.3:
            score += 15
        else:
            score += 5
        
        # 2. Timeframe confluence (0-30 points)
        confluence = setup_data.get('confluence_count', 0)
        total_tf = setup_data.get('total_timeframes', 6)
        confluence_pct = confluence / total_tf if total_tf > 0 else 0
        
        if confluence_pct >= 0.8:  # 5/6 or 6/6
            score += 30
        elif confluence_pct >= 0.6:  # 4/6
            score += 25
        elif confluence_pct >= 0.5:  # 3/6
            score += 15
        else:
            score += 5
        
        # 3. Regime clarity (0-20 points)
        regime_summary = setup_data.get('regime_summary', {})
        strong_trends = sum(1 for r in regime_summary.values() 
                          if r in ['strong_uptrend', 'strong_downtrend'])
        
        if strong_trends >= 4:
            score += 20
        elif strong_trends >= 2:
            score += 15
        elif strong_trends >= 1:
            score += 10
        else:
            score += 5
        
        # 4. Volume confirmation (0-10 points) - from 5m analysis
        score += 10  # Assume good for now (would check 5m volume ratio)
        
        return min(score, 100)  # Cap at 100
    
    @staticmethod
    def get_rr_config(confidence_score):
        """Get R:R configuration based on confidence"""
        if confidence_score >= 90:
            return "very_high", DynamicRiskRewardCalculator.RR_TABLE["very_high"]
        elif confidence_score >= 80:
            return "high", DynamicRiskRewardCalculator.RR_TABLE["high"]
        elif confidence_score >= 70:
            return "medium", DynamicRiskRewardCalculator.RR_TABLE["medium"]
        elif confidence_score >= 60:
            return "low", DynamicRiskRewardCalculator.RR_TABLE["low"]
        else:
            return "very_low", DynamicRiskRewardCalculator.RR_TABLE["very_low"]
    
    @classmethod
    def calculate_adjusted_levels(cls, entry, stop, target, setup_data, direction):
        """
        Calculate adjusted levels based on dynamic R:R
        
        Returns adjusted target and position scale
        """
        confidence = cls.calculate_confidence_score(setup_data)
        level, config = cls.get_rr_config(confidence)
        
        # Calculate base risk
        if direction == "LONG":
            risk = entry - stop
            # Adjust target based on R:R
            adjusted_reward = risk * config["rr_ratio"]
            adjusted_target = entry + adjusted_reward
            
            # Apply target multiplier for very high confidence
            if level == "very_high":
                extended_target = target * config["target_multiplier"]
                adjusted_target = max(adjusted_target, extended_target)
        else:  # SHORT
            risk = stop - entry
            adjusted_reward = risk * config["rr_ratio"]
            adjusted_target = entry - adjusted_reward
            
            if level == "very_high":
                extended_target = target * (2 - config["target_multiplier"])  # Invert for short
                adjusted_target = min(adjusted_target, extended_target)
        
        return {
            "confidence_score": confidence,
            "confidence_level": level,
            "base_rr": 1.5,
            "adjusted_rr": config["rr_ratio"],
            "description": config["description"],
            "entry": entry,
            "stop": stop,
            "original_target": target,
            "adjusted_target": round(adjusted_target, 2),
            "position_scale": config["position_scale"],
            "risk_amount": round(risk, 2),
            "reward_amount": round(abs(adjusted_target - entry), 2)
        }

class ConfidenceAnalyzer:
    """Analyze and report confidence breakdown"""
    
    @staticmethod
    def generate_confidence_report(setup_data):
        """Generate detailed confidence report"""
        calc = DynamicRiskRewardCalculator()
        
        score = calc.calculate_confidence_score(setup_data)
        level, config = calc.get_rr_config(score)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": score,
            "level": level,
            "rr_config": config,
            "breakdown": {
                "weighted_score": {
                    "value": abs(setup_data.get('weighted_score', 0)),
                    "points": min(abs(setup_data.get('weighted_score', 0)) * 50, 40),
                    "max_points": 40
                },
                "confluence": {
                    "count": setup_data.get('confluence_count', 0),
                    "total": setup_data.get('total_timeframes', 6),
                    "points": (setup_data.get('confluence_count', 0) / setup_data.get('total_timeframes', 6)) * 30 if setup_data.get('total_timeframes', 6) > 0 else 0,
                    "max_points": 30
                },
                "regime_clarity": {
                    "strong_trends": sum(1 for r in setup_data.get('regime_summary', {}).values() 
                                        if r in ['strong_uptrend', 'strong_downtrend']),
                    "points": 15,  # Simplified
                    "max_points": 20
                },
                "volume_confirmation": {
                    "status": "assumed_good",
                    "points": 10,
                    "max_points": 10
                }
            },
            "recommendations": []
        }
        
        # Add recommendations
        if score < 60:
            report["recommendations"].append("⚠️ Low confidence - Consider skipping or reducing position size")
        elif score >= 90:
            report["recommendations"].append("✅ Very high confidence - Can be aggressive with sizing and targets")
        
        if setup_data.get('confluence_count', 0) < 3:
            report["recommendations"].append("⚠️ Low timeframe confluence - Wait for more alignment")
        
        return report

def main():
    """Test dynamic R:R system"""
    print("="*70)
    print("ETHUSDT Dynamic Risk:Reward System")
    print("="*70)
    
    # Example setup data
    test_setups = [
        {
            "name": "High Confidence Setup",
            "weighted_score": 0.85,
            "confluence_count": 5,
            "total_timeframes": 6,
            "regime_summary": {
                "1M": "strong_downtrend",
                "1W": "strong_downtrend",
                "1d": "bearish_distribution",
                "4h": "downtrend_with_bounce",
                "1h": "strong_downtrend",
                "15m": "bearish_distribution"
            }
        },
        {
            "name": "Medium Confidence Setup",
            "weighted_score": 0.60,
            "confluence_count": 4,
            "total_timeframes": 6,
            "regime_summary": {
                "1M": "bearish_distribution",
                "1W": "bearish_distribution",
                "1d": "transition",
                "4h": "transition",
                "1h": "bearish_distribution",
                "15m": "ranging"
            }
        },
        {
            "name": "Low Confidence Setup",
            "weighted_score": 0.30,
            "confluence_count": 2,
            "total_timeframes": 6,
            "regime_summary": {
                "1M": "ranging",
                "1W": "bearish_distribution",
                "1d": "transition",
                "4h": "volatile_chop",
                "1h": "transition",
                "15m": "ranging"
            }
        }
    ]
    
    calc = DynamicRiskRewardCalculator()
    
    for setup in test_setups:
        print(f"\n{setup['name']}:")
        print("-" * 50)
        
        score = calc.calculate_confidence_score(setup)
        level, config = calc.get_rr_config(score)
        
        print(f"Confidence Score: {score}/100 ({level})")
        print(f"R:R Ratio: {config['rr_ratio']}:1")
        print(f"Description: {config['description']}")
        print(f"Position Scale: {config['position_scale']}x")
        print(f"Target Multiplier: {config['target_multiplier']}x")
        
        # Example calculation
        entry = 2000
        stop = 1980 if "downtrend" in str(setup['regime_summary']) else 2020
        target = 2100
        direction = "SHORT" if "downtrend" in str(setup['regime_summary']) else "LONG"
        
        adjusted = calc.calculate_adjusted_levels(entry, stop, target, setup, direction)
        print(f"\nExample {direction}:")
        print(f"  Entry: ${entry:.2f}")
        print(f"  Stop: ${stop:.2f}")
        print(f"  Original Target: ${target:.2f}")
        print(f"  Adjusted Target: ${adjusted['adjusted_target']:.2f}")
        print(f"  Effective R:R: {adjusted['adjusted_rr']:.2f}:1")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
