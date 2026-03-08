# Self-Improving Trading System

## Overview

A complete multi-agent trading system that **learns from every trade** and continuously improves strategy parameters.

## The Learning Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LEARNING CYCLE                               │
└─────────────────────────────────────────────────────────────────────┘

Trade Executed → Trade Completes (Win/Loss)
       │
       ▼
┌─────────────────┐
│ Forensics Agent │  ← Analyzes WHY trade won or lost
│                 │     • Market conditions at entry
│                 │     • Price action during trade
│                 │     • Root cause determination
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ Learning Agent   │  ← Updates strategy parameters
│                  │     • Reinforces winning patterns
│                  │     • Penalizes losing patterns
│                  │     • Adjusts global parameters
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ A/B Testing      │  ← Tests parameter variations
│                  │     • Runs multiple variants
│                  │     • Compares performance
│                  │     • Promotes winners
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Updated Strategy │  ← Improved parameters deployed
└──────────────────┘
         │
         └──────────────────────────────────────→ Next Trade
```

## Agent Architecture

### Core Agents

| Agent | File | Purpose |
|-------|------|---------|
| **Orchestrator** | `orchestrator.py` | Central controller |
| **Forensics** | `forensics_agent.py` | Trade analysis |
| **Learning System** | `learning_system.py` | Parameter optimization |
| **A/B Testing** | `ab_testing.py` | Variant testing |
| **Self-Improving** | `self_improving_system.py` | Learning loop coordinator |

### Support Agents

| Agent | File | Purpose |
|-------|------|---------|
| **Data Engineering** | `data_engineering.py` | Data management |
| **Backtesting** | `backtesting.py` | Strategy testing |
| **Reporting** | `reporting.py` | Report generation |

## How It Works

### 1. Trade Forensics

Every completed trade gets analyzed:

```python
forensics_report = {
    'trade_summary': {
        'direction': 'LONG',
        'result': 'WIN',
        'pnl_pct': 4.5
    },
    'entry_conditions': {
        '1h': {'adx': 32, 'volume_ratio': 1.8, 'trend': 'STRONG_UPTREND'},
        '1d': {'adx': 28, 'trend': 'UPTREND'}
    },
    'root_cause': {
        'primary_reason': 'STRONG_TREND',
        'confidence': 85,
        'replication_suggestion': 'Only trade when ADX > 30'
    },
    'signal_quality_score': 78
}
```

### 2. Learning System

Updates parameters based on trade outcomes:

**From Losses:**
```python
# Choppy market → Increase ADX threshold
if reason == "CHOPPY_MARKET":
    params['adx_threshold'] += 1

# Low volume → Increase volume requirement
if reason == "LOW_VOLUME":
    params['volume_threshold'] += 0.1
```

**From Wins:**
```python
# Strong trend → Slightly lower ADX (don't miss trends)
if reason == "STRONG_TREND":
    params['adx_threshold'] -= 0.5

# Multi-TF confluence → Increase higher TF weights
if reason == "MULTI_TF_CONFLUENCE":
    params['tf_weights']['1d'] += 0.5
```

### 3. Feature Tracking

Tracks which features predict success:

```json
{
  "1h_adx_STRONG_UPTREND": {
    "appearances": 45,
    "wins_when_present": 18,
    "losses_when_present": 27,
    "win_rate": 40.0,
    "avg_return": 1.2,
    "confidence": 95
  }
}
```

### 4. A/B Testing

Multiple strategy variants run simultaneously:

| Variant | Allocation | Status |
|---------|------------|--------|
| baseline | 50% | active |
| high_adx | 25% | testing |
| high_conf | 25% | testing |

Winners promoted, losers archived.

## Usage

### Initialize System

```bash
python3 agents/self_improving_system.py
```

### Process a Trade

```python
from agents.self_improving_system import SelfImprovingSystem

system = SelfImprovingSystem()

trade = {
    'id': 'trade_001',
    'direction': 'LONG',
    'entry_price': 2000.0,
    'exit_price': 2080.0,
    'entry_time': '2024-03-08T10:00:00',
    'exit_time': '2024-03-08T14:00:00',
    'result': 'WIN',
    'pnl_pct': 4.0,
    'stop_loss': 1940.0,
    'take_profit': 2120.0,
    'confirmations': ['1h_STRONG_BULL', '1d_FIB_382']
}

system.process_trade(trade)
```

### Get Current Parameters

```python
params = system.get_current_strategy_params()
print(params)
# {
#   'risk_per_trade': 0.015,
#   'min_confirmations': 4,
#   'adx_threshold': 26.5,  ← Updated!
#   'volume_threshold': 1.1  ← Updated!
# }
```

### Generate Improvement Report

```python
system.generate_learning_report()
```

## Learning Outcomes

The system learns:

1. **Which market conditions work best**
   - ADX levels that predict wins
   - Volume requirements for valid setups
   - RSI zones to avoid

2. **Which entry criteria are most important**
   - Relative weight of each timeframe
   - Minimum confirmation count
   - Optimal entry aggression

3. **When NOT to trade**
   - Choppy market conditions
   - Low volume periods
   - Late entry points

## Configuration

### Learning Rate

Control how aggressively parameters change:

```python
# Conservative - small changes
learning_rate = 0.05

# Moderate - balanced
learning_rate = 0.10

# Aggressive - larger changes
learning_rate = 0.20
```

### Batch Size

Number of trades before updating:

```python
# Update after every trade
batch_size = 1

# Update after 10 trades (recommended)
batch_size = 10

# Update after 50 trades
batch_size = 50
```

### Minimum Samples

Required samples before trusting statistics:

```python
# Require 10 trades per feature
min_samples = 10

# Require 20 trades (more reliable)
min_samples = 20
```

## Safety Mechanisms

1. **Bounds Checking:** Parameters can't go outside safe ranges
2. **Gradual Changes:** Maximum change per trade limited
3. **Win Rate Monitoring:** Reverts if performance degrades
4. **Manual Override:** Can lock parameters if needed

## File Structure

```
/root/.openclaw/workspace/
├── agents/
│   ├── self_improving_system.py    # Main coordinator
│   ├── forensics_agent.py          # Trade analysis
│   ├── learning_system.py          # Parameter learning
│   ├── ab_testing.py               # Variant testing
│   └── ...                         # Other agents
├── forensics/
│   ├── forensics_trade_001.json    # Individual trade analysis
│   └── ...
├── learning/
│   ├── current_params.json         # Current strategy params
│   ├── learning_state.json         # Feature statistics
│   └── improvement_report_*.json   # Periodic reports
├── ab_testing/
│   ├── variants.json               # Active variants
│   └── comparison_*.json           # A/B test results
└── logs/
    ├── self_improving_*.log        # System logs
    └── task_*.json                 # Agent tasks
```

## Example Output

```
[2024-03-08 14:30:22] [SELF_IMPROVING] Processing trade trade_001
[2024-03-08 14:30:23] [FORENSICS_AGENT] Analyzing LONG WIN trade
[2024-03-08 14:30:25] [FORENSICS_AGENT] Root cause: STRONG_TREND (confidence: 85%)
[2024-03-08 14:30:26] [LEARNING_AGENT] REINFORCED: adx_threshold 25.0 → 24.5
[2024-03-08 14:30:27] [LEARNING_AGENT] Total improvements: 1
[2024-03-08 14:30:28] [AB_TESTING_AGENT] Recorded for variant: baseline
[2024-03-08 14:30:29] [SELF_IMPROVING] ✓ Trade processed through learning loop
```

## Next Steps

1. **Run Initial Backtest:** Populate learning database
2. **Start Paper Trading:** Test with live data
3. **Monitor Learning:** Review improvement reports
4. **Go Live:** Deploy self-improving system

---

**This system learns from every trade and continuously improves.**
