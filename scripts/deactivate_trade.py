#!/usr/bin/env python3
"""Deactivate trade spotlight"""
import json
from datetime import datetime
from pathlib import Path

state_file = Path("/root/.openclaw/workspace/data/.trade_spotlight_state.json")

if state_file.exists():
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    if state.get('status') == 'ACTIVE':
        trade_id = state.get('trade_id', 'N/A')
        state['status'] = 'INACTIVE'
        state['deactivation_reason'] = 'Manual deactivation'
        state['deactivated_at'] = datetime.now().isoformat()
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"✅ Trade spotlight DEACTIVATED (Trade: {trade_id})")
    else:
        print("ℹ️ No active trade to deactivate")
else:
    print("ℹ️ No state file found")
