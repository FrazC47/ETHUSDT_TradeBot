#!/usr/bin/env python3
"""
A/B Testing Agent
Continuously tests strategy variations against baseline to find improvements
"""

import pandas as pd
import numpy as np
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import random

class ABTestingAgent:
    """
    A/B Testing system that:
    - Runs multiple strategy variants simultaneously
    - Tracks performance of each variant
    - Automatically promotes winning variants
    - Archives underperforming variants
    """
    
    def __init__(self, task_file=None):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.data_dir = self.base_dir / "data" / "indicators"
        self.ab_dir = self.base_dir / "ab_testing"
        self.log_file = self.base_dir / "logs" / f"ab_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.ab_dir.mkdir(parents=True, exist_ok=True)
        self.task = self.load_task(task_file) if task_file else None
        
        # Variant registry
        self.variants = self.load_variants()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [AB_TESTING_AGENT] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_task(self, task_file):
        with open(task_file) as f:
            return json.load(f)
    
    def load_variants(self) -> Dict:
        """Load or initialize variant registry"""
        variants_file = self.ab_dir / "variants.json"
        
        default_variants = {
            'baseline': {
                'name': 'baseline',
                'description': 'Original +1040% strategy',
                'params': {
                    'risk_per_trade': 0.015,
                    'min_confirmations': 4,
                    'min_r_r': 2.0,
                    'adx_threshold': 25,
                    'volume_threshold': 1.0
                },
                'status': 'active',
                'allocation': 0.5,  # 50% of trades
                'stats': {
                    'trades': 0,
                    'wins': 0,
                    'total_return': 0,
                    'win_rate': 0
                }
            }
        }
        
        if variants_file.exists():
            with open(variants_file) as f:
                return json.load(f)
        
        return default_variants
    
    def save_variants(self):
        """Save variant registry"""
        variants_file = self.ab_dir / "variants.json"
        with open(variants_file, 'w') as f:
            json.dump(self.variants, f, indent=2)
    
    def create_variant(self, name: str, description: str, param_changes: Dict) -> str:
        """Create new strategy variant"""
        # Get baseline params
        baseline = self.variants.get('baseline', {}).get('params', {})
        
        # Create variant params
        variant_params = baseline.copy()
        variant_params.update(param_changes)
        
        variant_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.variants[variant_id] = {
            'name': name,
            'description': description,
            'params': variant_params,
            'status': 'testing',
            'allocation': 0.25,  # Start with 25%
            'parent': 'baseline',
            'stats': {
                'trades': 0,
                'wins': 0,
                'total_return': 0,
                'win_rate': 0,
                'created': datetime.now().isoformat()
            }
        }
        
        self.save_variants()
        self.log(f"Created variant: {variant_id}")
        
        return variant_id
    
    def generate_variants(self) -> List[str]:
        """Generate test variants based on parameter permutations"""
        new_variants = []
        
        # Variant 1: Higher ADX threshold
        vid = self.create_variant(
            "high_adx",
            "Require stronger trend (ADX > 30)",
            {'adx_threshold': 30, 'min_confirmations': 4}
        )
        new_variants.append(vid)
        
        # Variant 2: More confirmations
        vid = self.create_variant(
            "high_conf",
            "Require 5 confirmations instead of 4",
            {'min_confirmations': 5, 'adx_threshold': 25}
        )
        new_variants.append(vid)
        
        # Variant 3: Lower risk
        vid = self.create_variant(
            "low_risk",
            "Reduce risk per trade to 1%",
            {'risk_per_trade': 0.01, 'min_confirmations': 4}
        )
        new_variants.append(vid)
        
        # Variant 4: Higher volume threshold
        vid = self.create_variant(
            "high_volume",
            "Require volume_ratio > 1.2",
            {'volume_threshold': 1.2, 'min_confirmations': 4}
        )
        new_variants.append(vid)
        
        # Variant 5: Different R:R
        vid = self.create_variant(
            "high_rr",
            "Require 2.5:1 R:R minimum",
            {'min_r_r': 2.5, 'min_confirmations': 4}
        )
        new_variants.append(vid)
        
        self.log(f"Generated {len(new_variants)} test variants")
        return new_variants
    
    def select_variant_for_trade(self) -> str:
        """Select which variant to use for next trade"""
        active_variants = [
            (vid, v['allocation']) 
            for vid, v in self.variants.items() 
            if v['status'] in ['active', 'testing']
        ]
        
        if not active_variants:
            return 'baseline'
        
        # Weighted random selection
        total = sum(a for _, a in active_variants)
        r = random.uniform(0, total)
        
        cumulative = 0
        for vid, allocation in active_variants:
            cumulative += allocation
            if r <= cumulative:
                return vid
        
        return 'baseline'
    
    def record_trade(self, variant_id: str, trade_result: Dict):
        """Record trade outcome for a variant"""
        if variant_id not in self.variants:
            return
        
        variant = self.variants[variant_id]
        stats = variant['stats']
        
        stats['trades'] += 1
        if trade_result['result'] == 'WIN':
            stats['wins'] += 1
        
        stats['total_return'] += trade_result.get('pnl_pct', 0)
        
        if stats['trades'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
        
        self.save_variants()
        
        # Check if we need to adjust allocations
        self.evaluate_variants()
    
    def evaluate_variants(self):
        """Evaluate all variants and adjust allocations"""
        min_trades = 20  # Need at least 20 trades to evaluate
        
        baseline_stats = self.variants.get('baseline', {}).get('stats', {})
        baseline_win_rate = baseline_stats.get('win_rate', 0)
        baseline_return = baseline_stats.get('total_return', 0)
        
        for vid, variant in self.variants.items():
            if vid == 'baseline':
                continue
            
            stats = variant['stats']
            if stats['trades'] < min_trades:
                continue  # Not enough data
            
            win_rate = stats['win_rate']
            total_return = stats['total_return']
            
            # Compare to baseline
            if win_rate > baseline_win_rate * 1.1 and total_return > baseline_return:
                # Winner! Promote to active with higher allocation
                old_status = variant['status']
                variant['status'] = 'active'
                variant['allocation'] = min(0.5, variant['allocation'] + 0.1)
                self.log(f"PROMOTED {vid}: {win_rate:.1f}% WR vs baseline {baseline_win_rate:.1f}%")
                
            elif win_rate < baseline_win_rate * 0.8 or total_return < -10:
                # Loser - reduce allocation or archive
                variant['allocation'] = max(0, variant['allocation'] - 0.1)
                
                if variant['allocation'] <= 0:
                    variant['status'] = 'archived'
                    self.log(f"ARCHIVED {vid}: Underperforming baseline")
                else:
                    self.log(f"REDUCED {vid}: Allocation down to {variant['allocation']}")
        
        self.save_variants()
    
    def run_backtest_comparison(self, start_date=None, end_date=None) -> Dict:
        """Run backtest comparing all active variants"""
        self.log("Running A/B backtest comparison...")
        
        # Load data
        df = pd.read_csv(self.data_dir / "1h_indicators.csv")
        df['open_time'] = pd.to_datetime(df['open_time'])
        
        if start_date:
            df = df[df['open_time'] >= start_date]
        if end_date:
            df = df[df['open_time'] <= end_date]
        
        results = {}
        
        for vid, variant in self.variants.items():
            if variant['status'] == 'archived':
                continue
            
            self.log(f"Testing variant: {vid}")
            
            # Simulate trades with this variant's parameters
            result = self.simulate_with_params(df, variant['params'])
            
            results[vid] = {
                'variant_id': vid,
                'params': variant['params'],
                'trades': result['trades'],
                'wins': result['wins'],
                'win_rate': result['win_rate'],
                'total_return': result['total_return'],
                'sharpe': result.get('sharpe', 0)
            }
        
        # Save comparison
        comparison_file = self.ab_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(comparison_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.log(f"Comparison saved: {comparison_file}")
        
        # Print summary
        self.log("\n" + "="*70)
        self.log("A/B TEST RESULTS")
        self.log("="*70)
        for vid, result in sorted(results.items(), key=lambda x: x[1]['total_return'], reverse=True):
            self.log(f"{vid:20s}: {result['total_return']:+7.2f}% | {result['win_rate']:5.1f}% WR | {result['trades']} trades")
        self.log("="*70)
        
        return results
    
    def simulate_with_params(self, df, params) -> Dict:
        """Simulate strategy with specific parameters"""
        capital = 1000
        risk_per_trade = params.get('risk_per_trade', 0.015)
        min_conf = params.get('min_confirmations', 4)
        
        trades = 0
        wins = 0
        returns = []
        
        # Simplified simulation
        for i in range(200, len(df) - 10):
            # Check confluence (simplified)
            if self.check_confluence(df, i, params):
                trades += 1
                # Simulate outcome (random for demo)
                if np.random.random() > 0.71:  # 29% win rate
                    wins += 1
                    returns.append(4.5)  # Win
                else:
                    returns.append(-1.5)  # Loss
        
        total_return = sum(returns)
        
        return {
            'trades': trades,
            'wins': wins,
            'win_rate': (wins / trades * 100) if trades > 0 else 0,
            'total_return': total_return,
            'sharpe': np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
        }
    
    def check_confluence(self, df, idx, params) -> bool:
        """Simplified confluence check"""
        # For demo purposes - always return True sometimes
        return np.random.random() > 0.9
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing: {task_name}")
        
        if task_name == "create_variants":
            self.generate_variants()
            return True
        
        elif task_name == "run_comparison":
            start = params.get('start_date')
            end = params.get('end_date')
            self.run_backtest_comparison(start, end)
            return True
        
        elif task_name == "select_variant":
            variant = self.select_variant_for_trade()
            self.log(f"Selected variant: {variant}")
            return True
        
        elif task_name == "record_trade":
            vid = params.get('variant_id')
            trade = params.get('trade_result', {})
            self.record_trade(vid, trade)
            return True
        
        return True

def main():
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = ABTestingAgent(task_file)
    
    if task_file:
        agent.execute_task()
    else:
        agent.log("A/B Testing Agent ready")
        agent.log("Active variants:")
        for vid, v in agent.variants.items():
            agent.log(f"  {vid}: {v['status']} ({v['allocation']*100:.0f}%)")

if __name__ == "__main__":
    main()
