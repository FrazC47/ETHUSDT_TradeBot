#!/usr/bin/env python3
"""
ETHUSDT Auto-Learning Scheduler
Runs learning system periodically and deploys improvements
Integrates with trade detection system
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from learning_system import LearningEngine, StrategyParameters

DATA_DIR = Path("/root/.openclaw/workspace/data")
LEARNING_DIR = DATA_DIR / "learning"
LOG_FILE = DATA_DIR / "auto_learning.log"

def log(message):
    """Log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')

def should_run_learning() -> bool:
    """Check if learning should run (weekly)"""
    last_run_file = LEARNING_DIR / ".last_learning_run"
    
    if not last_run_file.exists():
        return True
    
    with open(last_run_file, 'r') as f:
        last_run = datetime.fromisoformat(f.read().strip())
    
    # Run if it's been more than 7 days
    return datetime.now() - last_run > timedelta(days=7)

def update_trading_params(params: StrategyParameters):
    """Update trading system with new parameters"""
    log("Updating trading system parameters...")
    
    # Write to config file that trading system reads
    config_file = DATA_DIR / "optimized_params.json"
    with open(config_file, 'w') as f:
        json.dump(params.to_dict(), f, indent=2)
    
    log(f"Parameters saved to: {config_file}")
    
    # Create deployment notice
    deploy_notice = DATA_DIR / ".params_updated"
    with open(deploy_notice, 'w') as f:
        f.write(f"Updated at: {datetime.now().isoformat()}\n")
        f.write(f"New EMA: {params.ema_fast}/{params.ema_medium}/{params.ema_slow}\n")
        f.write(f"New Confluence: {params.min_confluence} timeframes\n")
    
    log("Trading system will use new parameters on next restart")

def run_weekly_learning():
    """Run weekly learning cycle"""
    log("="*70)
    log("AUTO-LEARNING: Weekly Optimization Cycle")
    log("="*70)
    
    if not should_run_learning():
        log("Learning ran recently, skipping...")
        return
    
    # Run learning
    engine = LearningEngine(max_iterations=50)  # 50 iterations per week
    engine.run_learning()
    
    # Deploy best parameters if significant improvement
    if engine.best_iteration and engine.best_iteration.improvement >= 5.0:
        log(f"Significant improvement found: {engine.best_iteration.improvement:+.2f}%")
        update_trading_params(engine.best_iteration.parameters)
        
        # Create alert for user
        alert_file = DATA_DIR / ".learning_alert"
        with open(alert_file, 'w') as f:
            f.write(f"NEW OPTIMIZED PARAMETERS DEPLOYED\n")
            f.write(f"Improvement: {engine.best_iteration.improvement:+.2f}%\n")
            f.write(f"Expected Return: {engine.best_iteration.total_return:+.2f}%\n")
            f.write(f"Deployed: {datetime.now().isoformat()}\n")
    else:
        log("No significant improvements found this cycle")
    
    # Update last run timestamp
    last_run_file = LEARNING_DIR / ".last_learning_run"
    with open(last_run_file, 'w') as f:
        f.write(datetime.now().isoformat())
    
    log("="*70)

def get_performance_projection():
    """Get projected performance based on learning history"""
    history_file = LEARNING_DIR / "learning_history.json"
    
    if not history_file.exists():
        return {
            'status': 'No learning history yet',
            'current_return': 0,
            'projected_annual': 0
        }
    
    with open(history_file) as f:
        data = json.load(f)
    
    iterations = data.get('iterations', [])
    if not iterations:
        return {'status': 'No iterations completed'}
    
    best = max(iterations, key=lambda x: x['total_return'])
    
    # Simple projection (would be more sophisticated in production)
    monthly_return = best['total_return'] / 12  # Assuming 12-month backtest
    annual_projection = monthly_return * 12
    
    return {
        'status': 'Learning active',
        'best_iteration': best['iteration_id'],
        'best_return': best['total_return'],
        'win_rate': best['win_rate'],
        'monthly_projection': monthly_return,
        'annual_projection': annual_projection,
        'total_iterations': len(iterations),
        'last_updated': data.get('last_updated')
    }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Learning System')
    parser.add_argument('command', choices=['run', 'status', 'force'], 
                       help='Run learning, check status, or force run')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_weekly_learning()
    elif args.command == 'force':
        log("Forcing learning cycle...")
        engine = LearningEngine(max_iterations=20)
        engine.run_learning()
    elif args.command == 'status':
        projection = get_performance_projection()
        print(json.dumps(projection, indent=2))

if __name__ == "__main__":
    main()
