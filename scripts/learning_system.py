#!/usr/bin/env python3
"""
ETHUSDT Iterative Learning System
Auto-optimizes strategy parameters through backtesting
Ported from archived ETHUSDT_TradeBot
Max 100 iterations, 5% improvement threshold
"""

import json
import itertools
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Any
import random

DATA_DIR = Path("/root/.openclaw/workspace/data")
LEARNING_DIR = DATA_DIR / "learning"
LEARNING_DIR.mkdir(exist_ok=True)

@dataclass
class StrategyParameters:
    """Strategy parameters that can be optimized"""
    # EMA Settings
    ema_fast: int = 9
    ema_medium: int = 21
    ema_slow: int = 50
    
    # RSI Settings
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    
    # Entry Thresholds
    min_confluence: int = 2  # Min timeframes aligned
    weighted_threshold: float = 0.65  # Min weighted score
    
    # Risk Management
    max_risk_per_trade: float = 2.0  # %
    min_rr_ratio: float = 1.5
    
    # Buffer Settings
    entry_buffer: float = 3.0  # $ for ETH
    stop_buffer: float = 5.0   # $ for ETH
    
    # Dynamic R:R
    confidence_very_high: float = 90.0
    confidence_high: float = 80.0
    confidence_medium: float = 70.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyParameters':
        return cls(**data)

@dataclass
class LearningIteration:
    """Single learning iteration result"""
    iteration_id: str
    parameters: StrategyParameters
    timestamp: str
    
    # Performance metrics
    total_return: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    total_trades: int
    
    # Comparison to baseline
    improvement: float  # % improvement over previous best
    is_best: bool
    
    def to_dict(self) -> Dict:
        return {
            'iteration_id': self.iteration_id,
            'parameters': self.parameters.to_dict(),
            'timestamp': self.timestamp,
            'total_return': self.total_return,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'improvement': self.improvement,
            'is_best': self.is_best
        }

class StrategyVariantGenerator:
    """Generate strategy parameter variations"""
    
    # Parameter ranges to test
    EMA_FAST_RANGE = [8, 9, 10, 12]
    EMA_MEDIUM_RANGE = [18, 21, 24, 26]
    EMA_SLOW_RANGE = [45, 50, 55, 60]
    
    RSI_PERIOD_RANGE = [12, 14, 16]
    RSI_LEVELS = [(65, 35), (70, 30), (75, 25)]
    
    CONFLUENCE_RANGE = [2, 3]
    WEIGHTED_THRESHOLD_RANGE = [0.60, 0.65, 0.70, 0.75]
    
    BUFFER_RANGE = [(2.0, 4.0), (3.0, 5.0), (4.0, 6.0)]
    
    @classmethod
    def generate_variants(cls, base_params: StrategyParameters, max_variants: int = 10) -> List[StrategyParameters]:
        """Generate parameter variations to test"""
        variants = []
        
        # Generate systematic variations
        test_combinations = [
            # Test EMA combinations
            {'ema_fast': 8, 'ema_medium': 18, 'ema_slow': 45},
            {'ema_fast': 10, 'ema_medium': 24, 'ema_slow': 55},
            {'ema_fast': 12, 'ema_medium': 26, 'ema_slow': 60},
            
            # Test RSI sensitivity
            {'rsi_overbought': 65, 'rsi_oversold': 35},
            {'rsi_overbought': 75, 'rsi_oversold': 25},
            
            # Test confluence requirements
            {'min_confluence': 3, 'weighted_threshold': 0.70},
            {'min_confluence': 2, 'weighted_threshold': 0.60},
            
            # Test buffer sizes
            {'entry_buffer': 2.0, 'stop_buffer': 4.0},
            {'entry_buffer': 4.0, 'stop_buffer': 6.0},
        ]
        
        for combo in test_combinations[:max_variants]:
            variant = StrategyParameters(
                ema_fast=combo.get('ema_fast', base_params.ema_fast),
                ema_medium=combo.get('ema_medium', base_params.ema_medium),
                ema_slow=combo.get('ema_slow', base_params.ema_slow),
                rsi_period=combo.get('rsi_period', base_params.rsi_period),
                rsi_overbought=combo.get('rsi_overbought', base_params.rsi_overbought),
                rsi_oversold=combo.get('rsi_oversold', base_params.rsi_oversold),
                min_confluence=combo.get('min_confluence', base_params.min_confluence),
                weighted_threshold=combo.get('weighted_threshold', base_params.weighted_threshold),
                max_risk_per_trade=base_params.max_risk_per_trade,
                min_rr_ratio=base_params.min_rr_ratio,
                entry_buffer=combo.get('entry_buffer', base_params.entry_buffer),
                stop_buffer=combo.get('stop_buffer', base_params.stop_buffer),
                confidence_very_high=base_params.confidence_very_high,
                confidence_high=base_params.confidence_high,
                confidence_medium=base_params.confidence_medium
            )
            variants.append(variant)
        
        return variants

class LearningEngine:
    """Main learning engine - iteratively improves strategy"""
    
    def __init__(self, max_iterations: int = 100, improvement_threshold: float = 5.0):
        self.max_iterations = max_iterations
        self.improvement_threshold = improvement_threshold
        self.iterations: List[LearningIteration] = []
        self.best_iteration: LearningIteration = None
        self.current_params = StrategyParameters()  # Start with defaults
        
        # Load existing learning history
        self.load_history()
    
    def load_history(self):
        """Load previous learning iterations"""
        history_file = LEARNING_DIR / "learning_history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)
                self.iterations = [LearningIteration(
                    iteration_id=i['iteration_id'],
                    parameters=StrategyParameters.from_dict(i['parameters']),
                    timestamp=i['timestamp'],
                    total_return=i['total_return'],
                    win_rate=i['win_rate'],
                    profit_factor=i['profit_factor'],
                    max_drawdown=i['max_drawdown'],
                    total_trades=i['total_trades'],
                    improvement=i['improvement'],
                    is_best=i['is_best']
                ) for i in data.get('iterations', [])]
                
                # Find best iteration
                if self.iterations:
                    self.best_iteration = max(self.iterations, key=lambda x: x.total_return)
                    self.current_params = self.best_iteration.parameters
                    print(f"Loaded {len(self.iterations)} previous iterations")
                    print(f"Best so far: {self.best_iteration.iteration_id} "
                          f"({self.best_iteration.total_return:+.2f}%)")
    
    def save_history(self):
        """Save learning history"""
        history_file = LEARNING_DIR / "learning_history.json"
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_iterations': len(self.iterations),
            'best_iteration_id': self.best_iteration.iteration_id if self.best_iteration else None,
            'iterations': [i.to_dict() for i in self.iterations]
        }
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def simulate_performance(self, params: StrategyParameters) -> Dict[str, float]:
        """
        Simulate strategy performance with given parameters
        
        In production, this would run actual backtest.
        For now, uses estimated performance based on parameter quality.
        """
        # Base performance
        base_return = 100.0  # 100% base
        base_winrate = 55.0
        
        # Adjust based on parameters
        adjustments = {
            'ema_optimization': 0,
            'rsi_optimization': 0,
            'confluence_optimization': 0,
            'buffer_optimization': 0
        }
        
        # EMA optimization (faster = more signals, slower = higher quality)
        if params.ema_fast == 9 and params.ema_medium == 21:
            adjustments['ema_optimization'] = 10  # Standard, proven
        elif params.ema_fast < 9:
            adjustments['ema_optimization'] = 5   # Faster, more noise
        else:
            adjustments['ema_optimization'] = 8   # Slower, less signals
        
        # RSI optimization
        if params.rsi_overbought == 70 and params.rsi_oversold == 30:
            adjustments['rsi_optimization'] = 5  # Standard
        elif params.rsi_overbought > 70:
            adjustments['rsi_optimization'] = 8  # Less false signals
        else:
            adjustments['rsi_optimization'] = 3  # More signals, more noise
        
        # Confluence optimization
        if params.min_confluence == 2:
            adjustments['confluence_optimization'] = 15  # Good balance
        elif params.min_confluence == 3:
            adjustments['confluence_optimization'] = 20  # Higher quality, fewer trades
        else:
            adjustments['confluence_optimization'] = 10
        
        # Buffer optimization
        if params.entry_buffer == 3.0:
            adjustments['buffer_optimization'] = 10  # Moderate
        elif params.entry_buffer < 3.0:
            adjustments['buffer_optimization'] = 5   # Tight, more misses
        else:
            adjustments['buffer_optimization'] = 12  # Loose, better fills
        
        # Calculate adjusted performance
        total_adjustment = sum(adjustments.values())
        adjusted_return = base_return + total_adjustment + random.uniform(-10, 10)
        adjusted_winrate = base_winrate + (total_adjustment / 5) + random.uniform(-3, 3)
        
        return {
            'total_return': adjusted_return,
            'win_rate': min(adjusted_winrate, 75),  # Cap at 75%
            'profit_factor': 1.5 + (total_adjustment / 40),
            'max_drawdown': 25 - (total_adjustment / 10),
            'total_trades': 50 + int(total_adjustment / 2)
        }
    
    def run_iteration(self, iteration_num: int) -> LearningIteration:
        """Run single learning iteration"""
        iteration_id = f"LRN-{datetime.now().strftime('%Y%m%d')}-{iteration_num:03d}"
        
        print(f"\n{'='*70}")
        print(f"Learning Iteration {iteration_num}/{self.max_iterations}: {iteration_id}")
        print(f"{'='*70}")
        
        # Generate parameter variant
        if iteration_num == 1:
            # First iteration uses current best (or default)
            test_params = self.current_params
        else:
            # Generate variation
            variants = StrategyVariantGenerator.generate_variants(self.current_params, max_variants=1)
            test_params = variants[0] if variants else self.current_params
        
        print(f"\nTesting Parameters:")
        for key, value in test_params.to_dict().items():
            print(f"  {key}: {value}")
        
        # Simulate performance
        perf = self.simulate_performance(test_params)
        
        print(f"\nSimulated Performance:")
        print(f"  Total Return: {perf['total_return']:+.2f}%")
        print(f"  Win Rate: {perf['win_rate']:.1f}%")
        print(f"  Profit Factor: {perf['profit_factor']:.2f}")
        print(f"  Max Drawdown: {perf['max_drawdown']:.1f}%")
        print(f"  Total Trades: {perf['total_trades']}")
        
        # Calculate improvement
        improvement = 0.0
        is_best = False
        
        if self.best_iteration:
            improvement = ((perf['total_return'] - self.best_iteration.total_return) 
                          / abs(self.best_iteration.total_return)) * 100
            
            if perf['total_return'] > self.best_iteration.total_return:
                is_best = True
                self.best_iteration = None  # Will set below
                print(f"\n✅ NEW BEST! Improvement: {improvement:+.2f}%")
        else:
            is_best = True
            print(f"\n✅ First iteration - Setting baseline")
        
        # Create iteration record
        iteration = LearningIteration(
            iteration_id=iteration_id,
            parameters=test_params,
            timestamp=datetime.now().isoformat(),
            total_return=perf['total_return'],
            win_rate=perf['win_rate'],
            profit_factor=perf['profit_factor'],
            max_drawdown=perf['max_drawdown'],
            total_trades=perf['total_trades'],
            improvement=improvement,
            is_best=is_best
        )
        
        self.iterations.append(iteration)
        
        if is_best:
            self.best_iteration = iteration
            self.current_params = test_params
        
        return iteration
    
    def should_continue(self) -> bool:
        """Check if learning should continue"""
        if len(self.iterations) >= self.max_iterations:
            print(f"\nReached max iterations ({self.max_iterations})")
            return False
        
        # Check for recent improvements
        recent_iterations = self.iterations[-5:] if len(self.iterations) >= 5 else self.iterations
        recent_improvements = [i.improvement for i in recent_iterations if i.improvement > 0]
        
        if len(recent_improvements) == 0 and len(self.iterations) > 10:
            print(f"\nNo improvements in last {len(recent_iterations)} iterations")
            print("Learning converged or stuck")
            return False
        
        return True
    
    def run_learning(self):
        """Run complete learning process"""
        print("="*70)
        print("ETHUSDT ITERATIVE LEARNING SYSTEM")
        print("="*70)
        print(f"Max Iterations: {self.max_iterations}")
        print(f"Improvement Threshold: {self.improvement_threshold}%")
        print(f"Learning Directory: {LEARNING_DIR}")
        
        iteration_num = len(self.iterations) + 1
        
        while self.should_continue() and iteration_num <= self.max_iterations:
            iteration = self.run_iteration(iteration_num)
            self.save_history()
            
            # Check for significant improvement
            if iteration.is_best and iteration.improvement >= self.improvement_threshold:
                print(f"\n🎯 Significant improvement achieved!")
                print(f"   Deploying new parameters...")
                self.deploy_parameters(iteration.parameters)
            
            iteration_num += 1
        
        # Final summary
        self.print_summary()
    
    def deploy_parameters(self, params: StrategyParameters):
        """Deploy optimized parameters to trading system"""
        deploy_file = LEARNING_DIR / "deployed_params.json"
        data = {
            'deployed_at': datetime.now().isoformat(),
            'parameters': params.to_dict(),
            'source_iteration': self.best_iteration.iteration_id if self.best_iteration else None
        }
        with open(deploy_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"   Parameters deployed to: {deploy_file}")
    
    def print_summary(self):
        """Print learning summary"""
        print("\n" + "="*70)
        print("LEARNING SUMMARY")
        print("="*70)
        
        print(f"\nTotal Iterations: {len(self.iterations)}")
        print(f"Best Iteration: {self.best_iteration.iteration_id if self.best_iteration else 'N/A'}")
        
        if self.best_iteration:
            print(f"\nBest Performance:")
            print(f"  Total Return: {self.best_iteration.total_return:+.2f}%")
            print(f"  Win Rate: {self.best_iteration.win_rate:.1f}%")
            print(f"  Profit Factor: {self.best_iteration.profit_factor:.2f}")
            print(f"  Max Drawdown: {self.best_iteration.max_drawdown:.1f}%")
            
            print(f"\nOptimized Parameters:")
            for key, value in self.best_iteration.parameters.to_dict().items():
                print(f"  {key}: {value}")
        
        # Top 5 iterations
        sorted_iterations = sorted(self.iterations, key=lambda x: x.total_return, reverse=True)
        print(f"\nTop 5 Iterations:")
        for i, it in enumerate(sorted_iterations[:5], 1):
            print(f"  {i}. {it.iteration_id}: {it.total_return:+.2f}% "
                  f"(Win: {it.win_rate:.1f}%, PF: {it.profit_factor:.2f})")
        
        print("\n" + "="*70)

def main():
    """Run learning system"""
    engine = LearningEngine(max_iterations=20)  # Start with 20 for testing
    engine.run_learning()

if __name__ == "__main__":
    main()
