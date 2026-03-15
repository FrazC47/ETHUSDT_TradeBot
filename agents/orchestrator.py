#!/usr/bin/env python3
"""
OpenClaw Trading System - Orchestrator
Main controller that coordinates all sub-agents
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
try:
    from path_utils import get_project_root
except ModuleNotFoundError:
    from agents.path_utils import get_project_root
from typing import Dict, List, Optional
import subprocess
import time

class TradingOrchestrator:
    """
    Central orchestrator for the ETHUSDT trading system.
    Coordinates all sub-agents to achieve trading objectives.
    """
    
    def __init__(self):
        self.base_dir = get_project_root()
        self.agents_dir = self.base_dir / "agents"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.state_file = self.base_dir / "orchestrator_state.json"
        
        # Create directories
        for d in [self.agents_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.state = self.load_state()
        self.active_agents = {}
        
    def load_state(self) -> Dict:
        """Load orchestrator state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "initialized": datetime.now().isoformat(),
            "last_run": None,
            "active_agents": [],
            "completed_tasks": [],
            "system_status": "idle"
        }
    
    def save_state(self):
        """Save orchestrator state"""
        self.state["last_run"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def log(self, message: str, agent: str = "ORCHESTRATOR"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{agent}] {message}"
        print(log_entry)
        
        # Write to log file
        log_file = self.logs_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def spawn_agent(self, agent_name: str, task: str, **kwargs) -> str:
        """Spawn a sub-agent to perform a task"""
        self.log(f"Spawning {agent_name} for task: {task}")
        
        agent_script = self.agents_dir / f"{agent_name.lower().replace(' ', '_')}.py"
        
        if not agent_script.exists():
            self.log(f"ERROR: Agent script not found: {agent_script}")
            return None
        
        # Create task file for agent
        task_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_file = self.logs_dir / f"task_{task_id}.json"
        
        task_data = {
            "task_id": task_id,
            "agent": agent_name,
            "task": task,
            "params": kwargs,
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        # Execute agent (in background for long tasks)
        try:
            result = subprocess.run(
                [sys.executable, str(agent_script), str(task_file)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log(f"Agent {agent_name} completed successfully")
                return task_id
            else:
                self.log(f"Agent {agent_name} failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.log(f"Agent {agent_name} timed out (running in background)")
            return task_id
        except Exception as e:
            self.log(f"Error spawning agent: {e}")
            return None
    
    def check_agent_status(self, task_id: str) -> str:
        """Check status of a spawned agent"""
        task_file = self.logs_dir / f"task_{task_id}.json"
        
        if not task_file.exists():
            return "unknown"
        
        with open(task_file) as f:
            task_data = json.load(f)
        
        return task_data.get("status", "unknown")
    
    def run_full_backtest(self, years: List[int] = None):
        """Command: Run comprehensive backtest"""
        self.log("="*70)
        self.log("INITIATING FULL BACKTEST SEQUENCE")
        self.log("="*70)
        
        # Step 1: Data Engineering - Ensure all data is available
        self.log("\n[STEP 1] Data Engineering - Verifying data completeness")
        task = self.spawn_agent(
            "data_engineering",
            "verify_and_download",
            timeframes=['1M', '1w', '1d', '4h', '1h', '15m', '5m', '1m'],
            years=years or [2022, 2023, 2024, 2025, 2026]
        )
        
        if not task:
            self.log("ERROR: Data engineering failed")
            return False
        
        # Step 2: Backtesting - Run strategy tests
        self.log("\n[STEP 2] Backtesting - Running strategy analysis")
        for year in (years or [2022, 2023, 2024, 2025]):
            task = self.spawn_agent(
                "backtesting",
                f"backtest_year_{year}",
                year=year,
                strategy="atrade_multi_tf"
            )
            self.log(f"  Queued backtest for {year}")
        
        # Step 3: Reporting - Generate analysis
        self.log("\n[STEP 3] Reporting - Generating month-by-month breakdown")
        task = self.spawn_agent(
            "reporting",
            "generate_monthly_report",
            include_charts=True,
            metrics=['trades', 'profit', 'win_rate', 'drawdown']
        )
        
        self.log("\nFull backtest sequence initiated")
        self.log("Check individual agent logs for progress")
        return True
    
    def deploy_live_trading(self, mode: str = "paper"):
        """Command: Deploy to live trading"""
        self.log("="*70)
        self.log(f"INITIATING LIVE TRADING DEPLOYMENT - Mode: {mode.upper()}")
        self.log("="*70)
        
        # Step 1: Risk Management - Calculate position sizes
        self.log("\n[STEP 1] Risk Management - Calculating risk parameters")
        task = self.spawn_agent(
            "risk_management",
            "calculate_position_sizes",
            capital=1000,
            risk_per_trade=0.015,
            max_drawdown=0.30
        )
        
        # Step 2: Live Execution - Connect to exchange
        self.log("\n[STEP 2] Live Execution - Connecting to exchange")
        task = self.spawn_agent(
            "live_execution",
            "connect_and_initialize",
            exchange="binance",
            mode=mode,  # paper or live
            symbol="ETHUSDT"
        )
        
        # Step 3: Monitoring - Start 24/7 monitoring
        self.log("\n[STEP 3] Monitoring - Starting continuous monitoring")
        task = self.spawn_agent(
            "monitoring",
            "start_monitoring",
            alerts=['trade_executed', 'error', 'drawdown_20pct']
        )
        
        self.log(f"\n{mode.upper()} trading deployment initiated")
        return True
    
    def optimize_strategy(self):
        """Command: Run strategy optimization"""
        self.log("="*70)
        self.log("INITIATING STRATEGY OPTIMIZATION")
        self.log("="*70)
        
        # Step 1: Strategy Development - Research improvements
        self.log("\n[STEP 1] Strategy Development - Analyzing current strategy")
        task = self.spawn_agent(
            "strategy_development",
            "analyze_current_strategy",
            focus=['entry_timing', 'exit_rules', 'filter_conditions']
        )
        
        # Step 2: Backtesting - Test variations
        self.log("\n[STEP 2] Backtesting - Testing parameter variations")
        task = self.spawn_agent(
            "backtesting",
            "parameter_optimization",
            param_ranges={
                'risk_per_trade': [0.01, 0.015, 0.02],
                'min_confirmations': [3, 4, 5],
                'r_r_min': [2.0, 2.5, 3.0]
            }
        )
        
        # Step 3: Reporting - Compare results
        self.log("\n[STEP 3] Reporting - Comparing optimization results")
        task = self.spawn_agent(
            "reporting",
            "optimization_report",
            baseline_return=1040
        )
        
        self.log("\nStrategy optimization initiated")
        return True
    
    def get_status(self):
        """Command: Get system status"""
        self.log("="*70)
        self.log("SYSTEM STATUS REPORT")
        self.log("="*70)
        
        status = {
            "orchestrator_status": self.state.get("system_status", "idle"),
            "last_run": self.state.get("last_run", "never"),
            "active_agents": len(self.state.get("active_agents", [])),
            "completed_tasks": len(self.state.get("completed_tasks", [])),
            "data_status": self._check_data_status(),
            "available_agents": self._list_available_agents()
        }
        
        for key, value in status.items():
            self.log(f"  {key}: {value}")
        
        return status
    
    def _check_data_status(self) -> Dict:
        """Check status of all data files"""
        status = {}
        for tf in ['1M', '1w', '1d', '4h', '1h', '15m', '5m', '1m']:
            file_path = self.data_dir / "indicators" / f"{tf}_indicators.csv"
            if file_path.exists():
                import pandas as pd
                df = pd.read_csv(file_path, nrows=1)
                status[tf] = "available"
            else:
                status[tf] = "missing"
        return status
    
    def _list_available_agents(self) -> List[str]:
        """List all available agent scripts"""
        agents = []
        if self.agents_dir.exists():
            for f in self.agents_dir.glob("*.py"):
                agents.append(f.stem)
        return agents
    
    def run(self):
        """Main orchestrator loop"""
        self.log("="*70)
        self.log("TRADING SYSTEM ORCHESTRATOR INITIALIZED")
        self.log("="*70)
        self.log(f"Base Directory: {self.base_dir}")
        self.log(f"Agents Directory: {self.agents_dir}")
        self.log(f"Available Commands:")
        self.log("  1. run_full_backtest(years=[...])")
        self.log("  2. deploy_live_trading(mode='paper'|'live')")
        self.log("  3. optimize_strategy()")
        self.log("  4. get_status()")
        self.log("="*70)
        
        self.save_state()
        
        return True

def main():
    """Initialize orchestrator"""
    orchestrator = TradingOrchestrator()
    orchestrator.run()
    
    # Example commands
    print("\nExample usage:")
    print("  orchestrator.run_full_backtest(years=[2022, 2023])")
    print("  orchestrator.deploy_live_trading(mode='paper')")
    print("  orchestrator.get_status()")

if __name__ == "__main__":
    main()
