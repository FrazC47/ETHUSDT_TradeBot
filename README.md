# ETHUSDT TradeBot

Dedicated trading system for Ethereum (ETHUSDT) on Binance Futures.

## Overview

This repository contains a complete, self-improving trading system specifically designed and optimized for ETHUSDT. The system uses a 5-agent architecture with dynamic data granularity and automatic optimization.

## Architecture

### 5-Agent System

```
┌─────────────────────────────────────────────────────────────────┐
│  1. TRADING AGENT (Every 15 min)                                │
│     File: agents/ethusdt_agent.py                               │
│     Purpose: Find setups, execute trades                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. DYNAMIC PULLER (Every 1 min)                                │
│     File: agents/dynamic_data_puller.py                         │
│     Purpose: Smart 5m/1m switching for precision                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. IMPROVER (Daily 6:00 AM)                                    │
│     File: agents/improver/ethusdt_improver.py                   │
│     Purpose: Analyze performance, suggest improvements          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. AUTO-IMPLEMENTER (Daily 6:30 AM)                            │
│     File: agents/auto_implementer/auto_implementer.py           │
│     Purpose: Test & implement validated changes                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. SELF-IMPROVEMENT (Continuous)                               │
│     File: .learnings/LEARNINGS.md                               │
│     Purpose: Track errors and improvements                      │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Multi-Timeframe Analysis
- **7 Timeframes**: 1M, 1w, 1d, 4h, 1h, 15m, 5m
- **Top-down approach**: Macro → Execution
- **Primary**: 1h for entry decisions
- **Execution**: 5m (normal) / 1m (setup active)

### Dynamic Data Granularity
- **Normal Mode**: 5m data (saves API calls)
- **Granular Mode**: 1m data (precision entry/exit)
- **Auto-switch**: Based on setup identification
- **Timeout**: 30 minutes auto-revert

### Self-Improvement
- **Daily Analysis**: Win/loss patterns
- **Missed Opportunities**: Track filtered setups
- **Auto-Implementation**: Test & deploy improvements
- **Version Control**: Full rollback capability

### Risk Management
- **Position Sizing**: 3% risk per trade
- **Leverage**: 5x (isolated)
- **Stop Loss**: 1.5x ATR
- **Take Profit**: 3x ATR (2:1 R:R minimum)

## Directory Structure

```
ETHUSDT_TradeBot/
├── agents/
│   ├── ethusdt_agent.py              # Main trading agent
│   ├── dynamic_data_puller.py        # Smart data puller
│   ├── improver/
│   │   ├── ethusdt_improver.py       # Performance analyzer
│   │   └── README.md
│   ├── auto_implementer/
│   │   ├── auto_implementer.py       # Auto-implementation
│   │   └── README.md
│   ├── scripts/
│   │   ├── run_agent.sh              # Trading agent wrapper
│   │   ├── run_dynamic_puller.sh     # Dynamic puller wrapper
│   │   └── run_improver.sh           # Improver wrapper
│   ├── config/
│   │   └── agent.conf                # Configuration
│   ├── logs/
│   │   ├── agent.log                 # Trading logs
│   │   └── dynamic_puller.log        # Data puller logs
│   ├── state/
│   │   └── agent_state.json          # Agent memory
│   ├── analysis/
│   │   └── improvement_report_*.md   # Generated reports
│   └── versions/
│       └── change_history.json       # All changes tracked
├── data/
│   ├── 1M.csv                        # Monthly data
│   ├── 1w.csv                        # Weekly data
│   ├── 1d.csv                        # Daily data
│   ├── 4h.csv                        # 4-hour data
│   ├── 1h.csv                        # 1-hour data (primary)
│   ├── 15m.csv                       # 15-minute data
│   ├── 5m.csv                        # 5-minute data
│   └── ETHUSDT_indicators.json       # Calculated indicators
├── backtests/
│   └── ETHUSDT_trade_history.csv     # Historical trades
└── README.md                         # This file
```

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/FrazC47/ETHUSDT_TradeBot.git
cd ETHUSDT_TradeBot
```

### 2. Install Dependencies
```bash
pip install requests pandas numpy
```

### 3. Setup Cron Jobs
```bash
# Edit crontab
crontab -e

# Add these lines:
# Trading Agent (every 15 minutes)
*/15 * * * * /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/scripts/run_agent.sh

# Dynamic Puller (every minute)
* * * * * /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/scripts/run_dynamic_puller.sh

# Improver (daily 6 AM)
0 6 * * * /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/improver/scripts/run_improver.sh

# Auto-Implementer (daily 6:30 AM)
30 6 * * * /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/auto_implementer/scripts/run_auto_implementer.sh
```

## Usage

### Manual Run
```bash
# Trading Agent
cd /root/.openclaw/workspace/ETHUSDT_TradeBot/agents
python3 ethusdt_agent.py

# Dynamic Puller
python3 dynamic_data_puller.py

# Improver
python3 improver/ethusdt_improver.py

# Auto-Implementer
python3 auto_implementer/auto_implementer.py
```

### View Logs
```bash
# Real-time trading logs
tail -f /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/logs/agent.log

# Dynamic puller logs
tail -f /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/logs/dynamic_puller.log

# Check agent state
cat /root/.openclaw/workspace/ETHUSDT_TradeBot/agents/state/agent_state.json
```

## Configuration

Edit `agents/config/agent.conf` to customize:
- Risk parameters
- Entry criteria
- Filter thresholds
- Notification settings

## Performance

### Backtest Results (Jan-Mar 2026)
- **Total Trades**: 10
- **Win Rate**: 70%
- **Total P&L**: +$1,205.87
- **Return**: +120.59%
- **Profit Factor**: 5.72
- **Max Drawdown**: 8.7%

### Current Status
Check the latest logs and state files for real-time performance.

## Safety Features

- ✅ Version backups before every change
- ✅ Auto-rollback if performance degrades
- ✅ Maximum 3 changes per week
- ✅ Profit-first optimization
- ✅ Full audit trail

## License

Private - For personal trading use only

## Disclaimer

This is an automated trading system. Use at your own risk. Past performance does not guarantee future results.
