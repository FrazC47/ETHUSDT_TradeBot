#!/usr/bin/env python3
"""
Self-Improving Trading System - Feedback Loop Orchestrator
Coordinates all agents for continuous learning and improvement
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class SelfImprovingSystem:
    """
    Central orchestrator for the self-improving trading system.
    
    The learning loop:
    1. Trade executed (Live Execution Agent)
    2. Trade completed (win/loss)
    3. Forensics Agent analyzes WHY
    4. Learning Agent updates parameters
    5. A/B Testing Agent tests variations
    6. Strategy updated with improvements
    7. Repeat
    """
    
    def __init__(self):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.agents_dir = self.base_dir / "agents"
        self.forensics_dir = self.base_dir / "forensics"
        self.learning_dir = self.base_dir / "learning"
        self.ab_dir = self.base_dir / "ab_testing"
        self.state_file = self.base_dir / "self_improving_state.json"
        
        # Create directories
        for d in [self.forensics_dir, self.learning_dir, self.ab_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.state = self.load_state()
        self.log_file = self.base_dir / "logs" / f"self_improving_{datetime.now().strftime('%Y%m%d')}.log"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [SELF_IMPROVING] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_state(self) -> Dict:
        """Load system state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        
        return {
            'initialized': datetime.now().isoformat(),
            'total_trades_processed': 0,
            'total_improvements': 0,
            'active_variants': ['baseline'],
            'learning_enabled': True,
            'last_update': None,
            'system_status': 'initialized'
        }
    
    def save_state(self):
        """Save system state"""
        self.state['last_update'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def spawn_agent(self, agent_name: str, task_data: Dict) -> bool:
        """Spawn an agent to perform a task"""
        agent_script = self.agents_dir / f"{agent_name}.py"
        
        if not agent_script.exists():
            self.log(f"Agent not found: {agent_script}", "ERROR")
            return False
        
        # Create task file
        task_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.base_dir / "logs" / f"task_{task_id}.json"
        
        task_data['task_id'] = task_id
        task_data['created'] = datetime.now().isoformat()
        
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        try:
            result = subprocess.run(
                [sys.executable, str(agent_script), str(task_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True
            else:
                self.log(f"Agent {agent_name} error: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error spawning agent {agent_name}: {e}", "ERROR")
            return False
    
    def process_trade(self, trade: Dict):
        """
        Process a completed trade through the learning loop:
        Trade → Forensics → Learning → Parameter Update
        """
        self.log("="*70)
        self.log("PROCESSING TRADE THROUGH LEARNING LOOP")
        self.log("="*70)
        
        trade_id = trade.get('id', f"trade_{datetime.now().timestamp()}")
        
        # Step 1: Forensics Analysis
        self.log(f"\n[STEP 1] Forensics Agent analyzing trade {trade_id}")
        forensics_task = {
            'task': 'analyze_trade',
            'params': {'trade': trade}
        }
        
        if not self.spawn_agent('forensics_agent', forensics_task):
            self.log("Forensics analysis failed", "ERROR")
            return False
        
        forensics_file = self.forensics_dir / f"forensics_{trade_id}.json"
        
        if not forensics_file.exists():
            self.log("Forensics report not generated", "ERROR")
            return False
        
        self.log(f"✓ Forensics complete: {forensics_file}")
        
        # Step 2: Learning Update
        self.log(f"\n[STEP 2] Learning Agent updating from forensics")
        learning_task = {
            'task': 'learn_from_trade',
            'params': {'forensics_file': str(forensics_file)}
        }
        
        if not self.spawn_agent('learning_system', learning_task):
            self.log("Learning update failed", "ERROR")
            return False
        
        self.log("✓ Learning parameters updated")
        
        # Step 3: Record for A/B Testing
        self.log(f"\n[STEP 3] A/B Testing Agent recording trade")
        variant_id = trade.get('variant_id', 'baseline')
        ab_task = {
            'task': 'record_trade',
            'params': {
                'variant_id': variant_id,
                'trade_result': trade
            }
        }
        
        self.spawn_agent('ab_testing', ab_task)
        
        # Step 4: Check for variant promotion/demotion
        self.log(f"\n[STEP 4] Evaluating variant performance")
        self.evaluate_variants()
        
        # Update state
        self.state['total_trades_processed'] += 1
        self.save_state()
        
        self.log(f"\n✓ Trade {trade_id} processed through learning loop")
        self.log("="*70)
        
        return True
    
    def evaluate_variants(self):
        """Check if any variants should be promoted or archived"""
        ab_file = self.ab_dir / "variants.json"
        
        if not ab_file.exists():
            return
        
        with open(ab_file) as f:
            variants = json.load(f)
        
        # Check for winners
        for vid, variant in variants.items():
            if vid == 'baseline':
                continue
            
            stats = variant.get('stats', {})
            if stats.get('trades', 0) < 20:
                continue
            
            win_rate = stats.get('win_rate', 0)
            
            # If variant significantly outperforms, promote
            baseline_wr = variants.get('baseline', {}).get('stats', {}).get('win_rate', 0)
            
            if win_rate > baseline_wr * 1.15:  # 15% better
                self.log(f"🎉 VARIANT PROMOTED: {vid} ({win_rate:.1f}% vs baseline {baseline_wr:.1f}%)")
                self.state['total_improvements'] += 1
                
                # Could update baseline here
    
    def run_batch_learning(self, trade_files: List[str]):
        """Process multiple trades in batch"""
        self.log(f"Running batch learning on {len(trade_files)} trades")
        
        # Load all trades
        trades = []
        for file in trade_files:
            with open(file) as f:
                trades.append(json.load(f))
        
        # Batch forensics
        forensics_files = []
        for trade in trades:
            trade_id = trade.get('id')
            forensics_file = self.forensics_dir / f"forensics_{trade_id}.json"
            
            if not forensics_file.exists():
                self.process_trade(trade)
            
            forensics_files.append(str(forensics_file))
        
        # Batch learning
        learning_task = {
            'task': 'batch_learn',
            'params': {'forensics_files': forensics_files}
        }
        
        self.spawn_agent('learning_system', learning_task)
        
        self.log("✓ Batch learning complete")
    
    def generate_learning_report(self):
        """Generate comprehensive learning report"""
        self.log("Generating learning report...")
        
        # Get learning system to generate report
        learning_task = {
            'task': 'generate_report',
            'params': {}
        }
        
        self.spawn_agent('learning_system', learning_task)
        
        # Get A/B testing comparison
        ab_task = {
            'task': 'run_comparison',
            'params': {}
        }
        
        self.spawn_agent('ab_testing', ab_task)
        
        self.log("✓ Learning report generated")
    
    def get_current_strategy_params(self) -> Dict:
        """Get the current optimized strategy parameters"""
        params_file = self.learning_dir / "current_params.json"
        
        if params_file.exists():
            with open(params_file) as f:
                return json.load(f)
        
        # Return defaults
        return {
            'risk_per_trade': 0.015,
            'min_confirmations': 4,
            'min_r_r': 2.0,
            'adx_threshold': 25,
            'volume_threshold': 1.0
        }
    
    def run(self):
        """Initialize the self-improving system"""
        self.log("="*70)
        self.log("SELF-IMPROVING TRADING SYSTEM INITIALIZED")
        self.log("="*70)
        
        # Check all agents exist
        required_agents = [
            'forensics_agent',
            'learning_system',
            'ab_testing'
        ]
        
        missing = []
        for agent in required_agents:
            agent_file = self.agents_dir / f"{agent}.py"
            if not agent_file.exists():
                missing.append(agent)
        
        if missing:
            self.log(f"Missing agents: {missing}", "ERROR")
            return False
        
        self.log("✓ All agents present")
        self.log(f"✓ System state: {self.state['system_status']}")
        self.log(f"✓ Trades processed: {self.state['total_trades_processed']}")
        self.log(f"✓ Total improvements: {self.state['total_improvements']}")
        
        # Show current parameters
        params = self.get_current_strategy_params()
        self.log("\nCurrent Strategy Parameters:")
        for k, v in params.items():
            if k != 'last_updated':
                self.log(f"  {k}: {v}")
        
        self.log("\n" + "="*70)
        self.log("System ready for continuous learning")
        self.log("="*70)
        
        self.save_state()
        return True
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing: {task_name}")
        
        if task_name == "process_trade":
            trade = params.get('trade', {})
            return self.process_trade(trade)
        
        elif task_name == "batch_process":
            files = params.get('trade_files', [])
            self.run_batch_learning(files)
            return True
        
        elif task_name == "generate_report":
            self.generate_learning_report()
            return True
        
        elif task_name == "get_params":
            params = self.get_current_strategy_params()
            self.log(f"Current params: {params}")
            return True
        
        return True

def main():
    system = SelfImprovingSystem()
    system.run()
    
    print("\n" + "="*70)
    print("SELF-IMPROVING SYSTEM READY")
    print("="*70)
    print("\nUsage:")
    print("  system.process_trade(trade_dict)  - Process a trade")
    print("  system.generate_learning_report() - Get improvement report")
    print("  system.get_current_strategy_params() - Get current params")
    print("\nLearning Loop:")
    print("  Trade → Forensics → Learning → Parameter Update")
    print("="*70)

if __name__ == "__main__":
    main()
