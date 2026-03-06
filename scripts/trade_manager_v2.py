#!/usr/bin/env python3
"""
ETHUSDT Integrated Trade Manager v2.0
Combines ported features:
- 9-state regime classification
- Weighted cluster analysis  
- Signal state machine
- Entry buffer system
- Position sizing
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Import the ported modules
sys.path.insert(0, str(Path(__file__).parent))
from trade_detection_agent_v2 import (
    RegimeClassifier, 
    WeightedClusterAnalyzer,
    SignalStateMachine,
    EnhancedTradeDetectionAgent
)
from entry_buffer_system import EntryBufferCalculator, PositionSizingCalculator

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"

def generate_trade_plan(trade_id=None):
    """Generate complete trade plan with all ported features"""
    
    print("="*70)
    print("ETHUSDT Integrated Trade Manager v2.0")
    print("="*70)
    
    # Step 1: Load state
    state_file = DATA_DIR / ".trade_spotlight_state_v2.json"
    state_machine = SignalStateMachine(state_file)
    
    # Get pending or active signal
    pending = state_machine.get_pending_signals()
    active = state_machine.get_active_signals()
    
    if not pending and not active:
        print("\n❌ No trade signals available")
        print("Run: python3 trade_detection_agent_v2.py")
        return None
    
    # Use first available signal
    if pending:
        signal_id = list(pending.keys())[0]
        signal = pending[signal_id]
        print(f"\n📋 Processing PENDING signal: {signal_id}")
    else:
        signal_id = list(active.keys())[0]
        signal = active[signal_id]
        print(f"\n📋 Processing ACTIVE signal: {signal_id}")
    
    setup = signal['setup']
    direction = setup['direction']
    
    print(f"\n🎯 SETUP: {direction}")
    print(f"   Weighted Score: {setup['weighted_score']:.2f}")
    print(f"   Macro Cluster: {setup['macro_score']:.2f}")
    print(f"   Intermediate: {setup['intermediate_score']:.2f}")
    print(f"   Execution: {setup['execution_score']:.2f}")
    
    # Step 2: Regime Summary
    print("\n📊 9-STATE REGIME SUMMARY:")
    for tf, regime in setup['regime_summary'].items():
        print(f"   {tf}: {regime}")
    
    # Step 3: Calculate buffered entry levels
    print("\n" + "-"*70)
    print("🎯 ENTRY BUFFER CALCULATION")
    print("-"*70)
    
    # Load 1h analysis for levels
    analysis_1h = None
    analysis_file = ANALYSIS_DIR / "1h_current.json"
    if analysis_file.exists():
        with open(analysis_file, 'r') as f:
            analysis_1h = json.load(f)
    
    if not analysis_1h:
        print("❌ No 1h analysis available")
        return None
    
    # Calculate for all aggression levels
    levels_summary = {}
    for aggression in ["conservative", "moderate", "aggressive"]:
        calc = EntryBufferCalculator(aggression)
        levels = calc.calculate_from_analysis(direction, analysis_1h)
        if levels:
            levels_summary[aggression] = levels
            
            print(f"\n{aggression.upper()}:")
            print(f"  Entry: ${levels['entry']:.2f}")
            print(f"  Stop: ${levels['stop']:.2f} (Risk: ${levels['risk']:.2f})")
            print(f"  Target: ${levels['target']:.2f} (Reward: ${levels['reward']:.2f})")
            print(f"  R:R = {levels['r_ratio']:.2f}:1 {'✅' if levels['valid'] else '❌'}")
    
    # Use moderate as default
    selected_levels = levels_summary.get("moderate")
    if not selected_levels or not selected_levels['valid']:
        print("\n❌ No valid entry levels (R:R < 1.5)")
        return None
    
    # Step 4: Position Sizing
    print("\n" + "-"*70)
    print("📊 POSITION SIZING (Scaled Entry: 60% + 40%)")
    print("-"*70)
    
    sizer = PositionSizingCalculator()
    
    # Example accounts
    accounts = [
        {"balance": 5000, "risk": 2.0},
        {"balance": 10000, "risk": 2.0},
        {"balance": 25000, "risk": 1.5}
    ]
    
    for account in accounts:
        sizing = sizer.calculate_scaled_entry(
            account['balance'], 
            account['risk'],
            selected_levels['entry'],
            selected_levels['stop'],
            direction
        )
        
        print(f"\nAccount: ${account['balance']:,.0f} | Risk: {account['risk']}%")
        print(f"  Scale 1 (60%): {sizing['scale_1']['units']:.3f} ETH (${sizing['scale_1']['dollars']:,.2f})")
        print(f"  Scale 2 (40%): {sizing['scale_2']['units']:.3f} ETH (${sizing['scale_2']['dollars']:,.2f})")
        print(f"  Total: {sizing['total']['position_size_units']:.3f} ETH")
        print(f"  Leverage: {sizing['total']['leverage_required']:.2f}x")
    
    # Step 5: Generate Trade Plan
    print("\n" + "="*70)
    print("📋 COMPLETE TRADE PLAN")
    print("="*70)
    
    trade_plan = {
        "trade_id": signal_id,
        "timestamp": datetime.now().isoformat(),
        "direction": direction,
        "setup_quality": {
            "weighted_score": setup['weighted_score'],
            "macro_score": setup['macro_score'],
            "intermediate_score": setup['intermediate_score'],
            "execution_score": setup['execution_score'],
            "regime_summary": setup['regime_summary']
        },
        "entry_strategy": {
            "type": "scaled_entry",
            "scale_1_percent": 60,
            "scale_2_percent": 40,
            "scale_2_trigger": "Confirmation (volume spike or pattern)",
            "levels": {
                "entry": selected_levels['entry'],
                "stop": selected_levels['stop'],
                "target": selected_levels['target'],
                "risk": selected_levels['risk'],
                "reward": selected_levels['reward'],
                "r_ratio": selected_levels['r_ratio']
            }
        },
        "risk_management": {
            "position_sizing_example": sizer.calculate_scaled_entry(
                10000, 2.0,
                selected_levels['entry'],
                selected_levels['stop'],
                direction
            ),
            "max_loss_percent": 2.0,
            "trailing_stop": "Activate at 1R profit",
            "breakeven": "Move stop to entry at 0.5R profit"
        },
        "exit_strategy": {
            "target_1": selected_levels['target'],
            "target_2": "Scale 50% at 2R, trail remainder",
            "time_stop": "Exit if no progress in 4 hours"
        },
        "state_machine": {
            "current_state": signal['state'],
            "pending_timeout": signal.get('pending_timeout'),
            "entry_confirmed": signal.get('entry_confirmed', False)
        }
    }
    
    print(f"\nTrade ID: {trade_plan['trade_id']}")
    print(f"Direction: {trade_plan['direction']}")
    print(f"\nEntry: ${trade_plan['entry_strategy']['levels']['entry']:.2f}")
    print(f"Stop: ${trade_plan['entry_strategy']['levels']['stop']:.2f}")
    print(f"Target: ${trade_plan['entry_strategy']['levels']['target']:.2f}")
    print(f"R:R = {trade_plan['entry_strategy']['levels']['r_ratio']:.2f}:1")
    print(f"\nEntry Strategy: {trade_plan['entry_strategy']['scale_1_percent']}% + {trade_plan['entry_strategy']['scale_2_percent']}%")
    print(f"State: {trade_plan['state_machine']['current_state']}")
    
    # Save trade plan
    plan_file = DATA_DIR / f"trade_plan_{signal_id}.json"
    with open(plan_file, 'w') as f:
        json.dump(trade_plan, f, indent=2)
    
    print(f"\n✅ Trade plan saved: {plan_file}")
    print("="*70)
    
    return trade_plan

def confirm_entry(trade_id, actual_entry_price):
    """Confirm entry and move signal to ACTIVE state"""
    state_file = DATA_DIR / ".trade_spotlight_state_v2.json"
    state_machine = SignalStateMachine(state_file)
    
    if state_machine.activate_signal(trade_id, actual_entry_price):
        print(f"✅ Entry confirmed: {trade_id} at ${actual_entry_price:.2f}")
        print(f"   Signal state: ACTIVE")
        print(f"   Cooldown until: {datetime.now() + timedelta(minutes=120)}")
        return True
    else:
        print(f"❌ Failed to activate signal: {trade_id}")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETHUSDT Integrated Trade Manager')
    parser.add_argument('command', choices=['plan', 'confirm', 'status'], help='Command to run')
    parser.add_argument('--trade-id', help='Trade ID for confirm command')
    parser.add_argument('--price', type=float, help='Actual entry price for confirm command')
    
    args = parser.parse_args()
    
    if args.command == 'plan':
        generate_trade_plan()
    elif args.command == 'confirm':
        if not args.trade_id or not args.price:
            print("Usage: --trade-id ID --price PRICE")
            sys.exit(1)
        confirm_entry(args.trade_id, args.price)
    elif args.command == 'status':
        state_file = DATA_DIR / ".trade_spotlight_state_v2.json"
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            print(json.dumps(state, indent=2))
        else:
            print("No state file found")

if __name__ == "__main__":
    main()
