#!/usr/bin/env python3
"""
Learning System Agent
Self-improving trading system that updates strategy parameters based on trade outcomes
"""

import pandas as pd
import numpy as np
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

class LearningSystemAgent:
    """
    Continuous learning system that:
    - Tracks feature importance over time
    - Updates strategy weights based on performance
    - Detects regime changes
    - Optimizes parameters incrementally
    """
    
    def __init__(self, task_file=None):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.data_dir = self.base_dir / "data" / "indicators"
        self.learning_dir = self.base_dir / "learning"
        self.forensics_dir = self.base_dir / "forensics"
        self.log_file = self.base_dir / "logs" / f"learning_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        self.task = self.load_task(task_file) if task_file else None
        
        # Current strategy parameters (mutable)
        self.current_params = self.load_current_params()
        
        # Feature importance tracking
        self.feature_stats = defaultdict(lambda: {
            'appearances': 0,
            'wins_when_present': 0,
            'losses_when_present': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'confidence': 0.0
        })
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [LEARNING_AGENT] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_task(self, task_file):
        with open(task_file) as f:
            return json.load(f)
    
    def load_current_params(self) -> Dict:
        """Load current strategy parameters"""
        params_file = self.learning_dir / "current_params.json"
        
        default_params = {
            'risk_per_trade': 0.015,
            'min_confirmations': 4,
            'min_r_r': 2.0,
            'adx_threshold': 25,
            'volume_threshold': 1.0,
            'rsi_overbought': 75,
            'rsi_oversold': 25,
            'tf_weights': {
                '1M': 5, '1w': 4, '1d': 3, '4h': 2, '1h': 1, '15m': 1
            },
            'entry_aggression': 0.5,  # 0=conservative, 1=aggressive
            'learning_rate': 0.1,
            'last_updated': datetime.now().isoformat()
        }
        
        if params_file.exists():
            with open(params_file) as f:
                saved = json.load(f)
                default_params.update(saved)
        
        return default_params
    
    def save_params(self):
        """Save updated parameters"""
        params_file = self.learning_dir / "current_params.json"
        self.current_params['last_updated'] = datetime.now().isoformat()
        
        with open(params_file, 'w') as f:
            json.dump(self.current_params, f, indent=2)
        
        self.log(f"Parameters saved to {params_file}")
    
    def process_trade_outcome(self, forensics_report: Dict):
        """
        Process a completed trade and update learning
        """
        trade = forensics_report['trade_summary']
        root_cause = forensics_report['root_cause']
        entry_conditions = forensics_report['entry_conditions']
        
        # Update feature statistics
        self.update_feature_stats(entry_conditions, trade)
        
        # Learn from root cause
        if trade['result'] == 'LOSS':
            self.learn_from_loss(root_cause, entry_conditions, trade)
        else:
            self.learn_from_win(root_cause, entry_conditions, trade)
        
        # Update global parameters periodically
        self.update_global_params()
        
        # Save learning state
        self.save_learning_state()
    
    def update_feature_stats(self, entry_conditions: Dict, trade: Dict):
        """Update statistics for each feature"""
        for tf, conditions in entry_conditions.items():
            for feature, value in conditions.items():
                if feature == 'price':
                    continue
                
                key = f"{tf}_{feature}_{value}"
                
                self.feature_stats[key]['appearances'] += 1
                
                if trade['result'] == 'WIN':
                    self.feature_stats[key]['wins_when_present'] += 1
                else:
                    self.feature_stats[key]['losses_when_present'] += 1
                
                # Update win rate
                total = self.feature_stats[key]['wins_when_present'] + self.feature_stats[key]['losses_when_present']
                if total > 0:
                    self.feature_stats[key]['win_rate'] = (
                        self.feature_stats[key]['wins_when_present'] / total * 100
                    )
                
                # Update average return
                pnl = trade.get('pnl_pct', 0)
                old_avg = self.feature_stats[key]['avg_return']
                n = self.feature_stats[key]['appearances']
                self.feature_stats[key]['avg_return'] = old_avg + (pnl - old_avg) / n
                
                # Update confidence (more appearances = more confident)
                self.feature_stats[key]['confidence'] = min(100, n * 5)
    
    def learn_from_loss(self, root_cause: Dict, entry_conditions: Dict, trade: Dict):
        """Adjust parameters based on loss analysis"""
        reason = root_cause.get('primary_reason', 'UNKNOWN')
        
        adjustments = {}
        
        if reason == "CHOPPY_MARKET":
            # Increase ADX threshold
            old_adx = self.current_params['adx_threshold']
            self.current_params['adx_threshold'] = min(35, old_adx + 1)
            adjustments['adx_threshold'] = f"{old_adx} → {self.current_params['adx_threshold']}"
            
        elif reason == "LOW_VOLUME":
            # Increase volume threshold
            old_vol = self.current_params['volume_threshold']
            self.current_params['volume_threshold'] = min(1.5, old_vol + 0.1)
            adjustments['volume_threshold'] = f"{old_vol:.1f} → {self.current_params['volume_threshold']:.1f}"
            
        elif reason == "LATE_ENTRY":
            # Make entry more conservative
            old_aggression = self.current_params['entry_aggression']
            self.current_params['entry_aggression'] = max(0, old_aggression - 0.05)
            adjustments['entry_aggression'] = f"{old_aggression:.2f} → {self.current_params['entry_aggression']:.2f}"
            
        elif reason == "FALSE_BREAKOUT":
            # Require more confirmations
            old_conf = self.current_params['min_confirmations']
            self.current_params['min_confirmations'] = min(6, old_conf + 1)
            adjustments['min_confirmations'] = f"{old_conf} → {self.current_params['min_confirmations']}"
        
        if adjustments:
            self.log(f"LEARNED from loss ({reason}): {adjustments}")
    
    def learn_from_win(self, root_cause: Dict, entry_conditions: Dict, trade: Dict):
        """Reinforce successful parameters"""
        reason = root_cause.get('primary_reason', 'UNKNOWN')
        
        adjustments = {}
        
        if reason == "STRONG_TREND":
            # Slightly reduce ADX threshold (don't miss strong trends)
            old_adx = self.current_params['adx_threshold']
            self.current_params['adx_threshold'] = max(20, old_adx - 0.5)
            adjustments['adx_threshold'] = f"{old_adx} → {self.current_params['adx_threshold']}"
            
        elif reason == "VOLUME_CONFIRMATION":
            # Keep volume threshold where it is (it's working)
            pass
            
        elif reason == "PERFECT_ENTRY":
            # Current aggression level is good
            pass
            
        elif reason == "MULTI_TF_CONFLUENCE":
            # Increase weight on higher timeframes
            for tf in ['1d', '1w']:
                if tf in self.current_params['tf_weights']:
                    old_weight = self.current_params['tf_weights'][tf]
                    self.current_params['tf_weights'][tf] = min(10, old_weight + 0.5)
                    adjustments[f'{tf}_weight'] = f"{old_weight} → {self.current_params['tf_weights'][tf]}"
        
        if adjustments:
            self.log(f"REINFORCED from win ({reason}): {adjustments}")
    
    def update_global_params(self):
        """Update parameters based on aggregate statistics"""
        # Analyze recent performance
        recent_trades = self.get_recent_trades(50)  # Last 50 trades
        
        if len(recent_trades) < 20:
            return  # Not enough data
        
        wins = sum(1 for t in recent_trades if t['result'] == 'WIN')
        win_rate = wins / len(recent_trades)
        
        self.log(f"Recent performance: {wins}/{len(recent_trades)} wins ({win_rate*100:.1f}%)")
        
        # Adjust based on win rate
        if win_rate < 0.25:
            # Too many losses - be more selective
            self.current_params['min_confirmations'] = min(6, self.current_params.get('min_confirmations', 4) + 1)
            self.current_params['entry_aggression'] = max(0, self.current_params.get('entry_aggression', 0.5) - 0.1)
            self.log("Performance declining - becoming more conservative")
            
        elif win_rate > 0.35:
            # Doing well - can be slightly more aggressive
            self.current_params['min_confirmations'] = max(3, self.current_params.get('min_confirmations', 4) - 1)
            self.current_params['entry_aggression'] = min(1, self.current_params.get('entry_aggression', 0.5) + 0.05)
            self.log("Performance strong - increasing trade frequency slightly")
    
    def get_recent_trades(self, n: int) -> List[Dict]:
        """Load recent trades from forensics reports"""
        trades = []
        
        # Get all forensics files
        if not self.forensics_dir.exists():
            return trades
        
        files = sorted(self.forensics_dir.glob("forensics_*.json"), reverse=True)
        
        for file in files[:n]:
            try:
                with open(file) as f:
                    report = json.load(f)
                    trades.append(report['trade_summary'])
            except:
                pass
        
        return trades
    
    def save_learning_state(self):
        """Save current learning state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'current_params': self.current_params,
            'feature_stats': dict(self.feature_stats),
            'total_trades_analyzed': sum(
                s['appearances'] for s in self.feature_stats.values()
            ) // len(self.feature_stats) if self.feature_stats else 0
        }
        
        state_file = self.learning_dir / "learning_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def generate_improvement_report(self) -> Dict:
        """Generate report on what the system has learned"""
        report = {
            'generated': datetime.now().isoformat(),
            'current_parameters': self.current_params,
            'top_performing_features': self.get_top_features(min_win_rate=60),
            'underperforming_features': self.get_bottom_features(max_win_rate=30),
            'parameter_changes': self.get_parameter_history(),
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        report_file = self.learning_dir / f"improvement_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Improvement report saved: {report_file}")
        return report
    
    def get_top_features(self, min_win_rate=60, min_samples=10) -> List[Dict]:
        """Get features with high win rates"""
        top = []
        
        for feature, stats in self.feature_stats.items():
            if stats['appearances'] >= min_samples and stats['win_rate'] >= min_win_rate:
                top.append({
                    'feature': feature,
                    'win_rate': stats['win_rate'],
                    'avg_return': stats['avg_return'],
                    'sample_size': stats['appearances']
                })
        
        return sorted(top, key=lambda x: x['win_rate'], reverse=True)[:10]
    
    def get_bottom_features(self, max_win_rate=30, min_samples=10) -> List[Dict]:
        """Get features with low win rates"""
        bottom = []
        
        for feature, stats in self.feature_stats.items():
            if stats['appearances'] >= min_samples and stats['win_rate'] <= max_win_rate:
                bottom.append({
                    'feature': feature,
                    'win_rate': stats['win_rate'],
                    'avg_return': stats['avg_return'],
                    'sample_size': stats['appearances']
                })
        
        return sorted(bottom, key=lambda x: x['win_rate'])[:10]
    
    def get_parameter_history(self) -> List[Dict]:
        """Get history of parameter changes"""
        history = []
        # Load from learning state files if available
        # For now, return current as baseline
        history.append({
            'timestamp': self.current_params.get('last_updated'),
            'params': self.current_params
        })
        return history
    
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Analyze feature performance
        top_features = self.get_top_features()
        bottom_features = self.get_bottom_features()
        
        if top_features:
            recommendations.append(f"Emphasize features with >60% win rate: {[f['feature'] for f in top_features[:3]]}")
        
        if bottom_features:
            recommendations.append(f"Avoid features with <30% win rate: {[f['feature'] for f in bottom_features[:3]]}")
        
        # Parameter-based recommendations
        if self.current_params.get('adx_threshold', 25) > 30:
            recommendations.append("ADX threshold very high - may miss valid setups")
        
        if self.current_params.get('min_confirmations', 4) > 5:
            recommendations.append("High confirmation requirement - reducing trade frequency")
        
        return recommendations
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing: {task_name}")
        
        if task_name == "learn_from_trade":
            forensics_file = params.get('forensics_file')
            if forensics_file:
                with open(forensics_file) as f:
                    report = json.load(f)
                self.process_trade_outcome(report)
                self.save_params()
            return True
        
        elif task_name == "batch_learn":
            forensics_files = params.get('forensics_files', [])
            self.log(f"Batch learning from {len(forensics_files)} trades")
            
            for file in forensics_files:
                with open(file) as f:
                    report = json.load(f)
                self.process_trade_outcome(report)
            
            self.save_params()
            return True
        
        elif task_name == "generate_report":
            report = self.generate_improvement_report()
            return True
        
        return True

def main():
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = LearningSystemAgent(task_file)
    
    if task_file:
        agent.execute_task()
    else:
        agent.log("Learning System Agent ready")
        agent.log("Current parameters:")
        for k, v in agent.current_params.items():
            agent.log(f"  {k}: {v}")

if __name__ == "__main__":
    main()
