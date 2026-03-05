# ETHUSDT TradeBot - Complete Process Flow

## Overview
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ETHUSDT TRADEBOT SYSTEM                          │
│                     (All 7 Timeframes | 60 Indicators)                  │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DATA LAYER  │────▶│ ANALYSIS LAYER│────▶│ DECISION LAYER│────▶│ EXECUTION LAYER│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │                     │
       ▼                     ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  RAW DATA    │     │ INDICATORS   │     │  FILTERS     │     │   TRADES     │
│  (7 TFs)     │     │  (60 each)   │     │  (8 checks)  │     │  (If passed) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 1. DATA LAYER - Every 1 Minute

### Cron Job
```
Schedule: * * * * *
Script: agents/scripts/run_dynamic_puller.sh
Python: agents/dynamic_data_puller.py
```

### Process Flow
```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Fetch from Binance API                               │
├─────────────────────────────────────────────────────────────┤
│ Input:  None (API call)                                     │
│ Output: 100 x 5m candles for ETHUSDT                        │
│ File:   agents/dynamic_data_puller.py                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Update Raw Data File                                │
├─────────────────────────────────────────────────────────────┤
│ Read:   data/raw/5m.csv                                     │
│ Append: New candles                                         │
│ Save:   data/raw/5m.csv                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Log Success                                         │
├─────────────────────────────────────────────────────────────┤
│ File:   agents/logs/dynamic_puller_YYYYMMDD.log            │
│ Format: [HH:MM:SS] Successfully pulled 100 5m candles      │
└─────────────────────────────────────────────────────────────┘
```

### Files Used
| File | Purpose | Updated |
|------|---------|---------|
| `agents/scripts/run_dynamic_puller.sh` | Shell wrapper | No |
| `agents/dynamic_data_puller.py` | Python fetcher | No |
| `data/raw/5m.csv` | Stores 5m OHLCV | **Yes (every minute)** |
| `agents/logs/dynamic_puller_YYYYMMDD.log` | Execution log | **Yes** |

---

## 2. ANALYSIS LAYER - Every 15 Minutes

### Cron Job
```
Schedule: */15 * * * *
Script: agents/scripts/run_agent.sh
Python: agents/ethusdt_agent.py
```

### Process Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Load Configuration                                   │
├─────────────────────────────────────────────────────────────┤
│ File:   config/agent.conf                                   │
│ Contains: Risk settings (3%), Leverage (5x), Filters        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Load All 7 Timeframe Data                           │
├─────────────────────────────────────────────────────────────┤
│ 1M:   data/raw/1M.csv   (Monthly - Macro trend)            │
│ 1w:   data/raw/1w.csv   (Weekly - Major trend)             │
│ 1d:   data/raw/1d.csv   (Daily - Intermediate)             │
│ 4h:   data/raw/4h.csv   (4 Hour - Short-term)              │
│ 1h:   data/raw/1h.csv   (1 Hour - PRIMARY)                 │
│ 15m:  data/raw/15m.csv  (15 Min - Confirmation)            │
│ 5m:   data/raw/5m.csv   (5 Min - Execution)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Load Pre-Calculated Indicators                      │
├─────────────────────────────────────────────────────────────┤
│ For each timeframe:                                         │
│   data/indicators/{TF}_indicators.csv                       │
│                                                             │
│ 60 indicators per TF including:                            │
│   - Trend: EMA 9/21/50/200, SMA 20/50                      │
│   - Momentum: RSI, RSI_SMA, MACD                           │
│   - Volatility: ATR, ATR%, BBands                          │
│   - Volume: VWAP, ratio, trend                             │
│   - Trend Strength: ADX, +DI, -DI                          │
│   - Fibonacci: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100% │
│   - Structure: HH/HL/LH/LL score                           │
│   - Price Action: body, wicks, range, etc.                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Top-Down Analysis (MTF Engine)                      │
├─────────────────────────────────────────────────────────────┤
│ Module: agents/modules/mtf_engine_v34.py                   │
│                                                             │
│ 1. MACRO (1M + 1w): Check major trend direction            │
│ 2. INTERMEDIATE (1d + 4h): Check daily/4h alignment        │
│ 3. PRIMARY (1h): Main analysis timeframe                   │
│ 4. EXECUTION (15m + 5m): Entry precision                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Fundamental Analysis (Optional)                     │
├─────────────────────────────────────────────────────────────┤
│ Module: agents/modules/fundamental_analyzer.py             │
│                                                             │
│ Daily check of:                                             │
│   - Exchange flows (inflow/outflow)                        │
│   - ETH staked amount                                      │
│   - Net issuance (burn vs mint)                            │
│   - Whale transactions                                     │
│   - Social sentiment                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Regime Detection                                    │
├─────────────────────────────────────────────────────────────┤
│ Module: agents/modules/regime_detector.py                  │
│                                                             │
│ Detects:                                                    │
│   - Strong Bull (trending up, high momentum)               │
│   - Bull (trending up, normal)                             │
│   - Range (sideways)                                       │
│   - Bear (trending down)                                   │
│   - Strong Bear (avoid trading)                            │
│   - High Volatility                                        │
│   - Low Volatility                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
```

---

## 3. DECISION LAYER - Filter Checks

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Run 8 Entry Filters                                 │
├─────────────────────────────────────────────────────────────┤
│ Module: ethusdt_agent.py (within analyze() method)         │
│                                                             │
│ 1. htf_aligned       - Monthly/Weekly/Daily/4h bullish     │
│ 2. trend_bullish     - EMA9 > EMA21 on 1h                  │
│ 3. rsi_ok            - RSI between 40-75                   │
│ 4. volume_ok         - Volume ratio >= 0.6x                │
│ 5. atr_ok            - ATR% > 0.5 (sufficient volatility)  │
│ 6. range_ok          - Range location < 70%                │
│ 7. consecutive_ok    - At least 2 bullish candles          │
│ 8. breakout          - Price broke above resistance        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌────────────────┐    ┌────────────────────┐
│ >= 5/8 PASSED  │    │ < 5/8 PASSED       │
│ Continue to    │    │ Log failure        │
│ entry calc     │    │ reasons, skip      │
└───────┬────────┘    └────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Calculate Entry Levels                              │
├─────────────────────────────────────────────────────────────┤
│ Module: agents/modules/buffer_system.py                    │
│                                                             │
│ Entry Price:   5m close + buffer (10 pips)                 │
│ Stop Loss:     Entry - (ATR × 1.5) - buffer (15 pips)      │
│ Take Profit:   Entry + (ATR × 3.0) - buffer (10 pips)      │
│                                                             │
│ Position Size: Account × 3% / (Entry - Stop)               │
│ Max Leverage:  5x (isolated margin)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
```

---

## 4. EXECUTION LAYER (If Setup Valid)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: Place Trade (If paper/live trading enabled)        │
├─────────────────────────────────────────────────────────────┤
│ Currently: Paper trading / Analysis only                   │
│                                                             │
│ Would place order on Binance via API:                      │
│   - Market or limit entry                                  │
│   - Stop-loss order                                        │
│   - Take-profit order                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: Update State & Log                                 │
├─────────────────────────────────────────────────────────────┤
│ State File:   agents/state/agent_state.json                │
│ Log File:     agents/logs/cron_YYYYMMDD.log                │
│                                                             │
│ Records:                                                    │
│   - Analysis results                                       │
│   - Filter pass/fail status                                │
│   - Entry/exit levels (if setup found)                     │
│   - Timestamp                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. IMPROVEMENT LAYER - Daily 6:00 AM

### Cron Job
```
Schedule: 0 6 * * *
Script: agents/improver/scripts/run_improver.sh
Python: agents/improver/ethusdt_improver_v2.py
```

### Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Load Trade History                                  │
├─────────────────────────────────────────────────────────────┤
│ File:   backtests/ETHUSDT_trade_history.csv                │
│ Format: entry_time, exit_time, entry_price, exit_price,    │
│         pnl, exit_reason, etc.                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Analyze Performance                                 │
├─────────────────────────────────────────────────────────────┤
│ Metrics calculated:                                         │
│   - Win rate                                               │
│   - Average win/loss                                       │
│   - Profit factor                                          │
│   - Max drawdown                                           │
│   - Consecutive losses                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Generate Hypotheses (up to 100)                     │
├─────────────────────────────────────────────────────────────┤
│ Examples:                                                   │
│   H1: "What if volume_threshold = 0.5 instead of 0.6?"    │
│   H2: "What if RSI range is 35-70 instead of 40-75?"      │
│   H3: "What if ATR multiplier = 1.3 instead of 1.5?"      │
│   H4: "What if we add ADX > 25 filter?"                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Backtest Each Hypothesis                            │
├─────────────────────────────────────────────────────────────┤
│ For each hypothesis:                                        │
│   - Modify parameters temporarily                          │
│   - Run backtest on historical data                        │
│   - Calculate new performance metrics                      │
│   - If improvement >= 5% AND confidence >= 70%:           │
│       → Save to validated_suggestion.json                  │
│       → STOP (early exit)                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Save Results                                        │
├─────────────────────────────────────────────────────────────┤
│ If valid improvement found:                                 │
│   File: agents/improver/validated_suggestion.json          │
│   Contains: Parameter change, expected improvement %       │
│                                                            │
│ Log: agents/improver/logs/cron_YYYYMMDD.log                │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. AUTO-IMPLEMENTATION LAYER - Daily 6:30 AM

### Cron Job
```
Schedule: 30 6 * * *
Script: agents/auto_implementer/scripts/run_auto_implementer.sh
Python: agents/auto_implementer/auto_implementer_v2.py
```

### Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Check for Validated Suggestion                      │
├─────────────────────────────────────────────────────────────┤
│ File: agents/improver/validated_suggestion.json            │
│                                                            │
│ If NOT found:                                              │
│   → Log "No suggestions"                                   │
│   → Exit                                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Validate Suggestion                                 │
├─────────────────────────────────────────────────────────────┤
│ Checks:                                                     │
│   - Improvement >= 5% ?                                    │
│   - Confidence >= 70% ?                                    │
│   - Backtest result verified?                              │
│                                                            │
│ If FAILED:                                                 │
│   → Log rejection reason                                   │
│   → Delete suggestion file                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Deploy Improvement                                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Backup current config:                                  │
│    → versions/config_YYYYMMDD_HHMMSS.json                  │
│                                                            │
│ 2. Update config/agent.conf:                               │
│    → Apply new parameter value                             │
│                                                            │
│ 3. Log deployment:                                         │
│    → agents/auto_implementer/logs/cron_YYYYMMDD.log        │
│                                                            │
│ 4. Delete suggestion file                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. BACKTEST REVIEW LAYER - Every 6 Hours

### Cron Job
```
Schedule: 0 */6 * * * (00:00, 06:00, 12:00, 18:00)
Script: agents/backtest_reviews/scripts/run_6hour_review.sh
```

### Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Quick Performance Check                             │
├─────────────────────────────────────────────────────────────┤
│ Python: quick_performance_check.py                         │
│                                                            │
│ Analyzes last 6 hours of trading:                          │
│   - Recent win rate                                        │
│   - Recent P&L                                             │
│   - Average trade size                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Full System Backtest                                │
├─────────────────────────────────────────────────────────────┤
│ Python: full_system_backtest.py                            │
│                                                            │
│ Runs backtest on ALL historical data:                      │
│   - Uses all 7 timeframes                                  │
│   - All 60 indicators                                      │
│   - All 8 filters                                          │
│   - Calculates full metrics                                │
│                                                            │
│ Output: backtests/full_system_backtest_results.json        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Degradation Detection                               │
├─────────────────────────────────────────────────────────────┤
│ Python: degradation_detector.py                            │
│                                                            │
│ Compares first half vs second half:                        │
│   - Win rate drop > 20% ?                                  │
│   - Profit decline > $200 ?                                │
│   - Recent win rate < 40% ?                                │
│                                                            │
│ If degradation detected:                                   │
│   → Create emergency_adjustment.json                       │
│   → Reduce position size / tighten filters                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Log Results                                         │
├─────────────────────────────────────────────────────────────┤
│ File: agents/backtest_reviews/logs/review_YYYYMMDD_HH.log  │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. INDICATOR CALCULATION LAYER - Every Hour

### Cron Job
```
Schedule: 2 * * * * (at :02 past each hour)
Script: agents/scripts/calculate_indicators.py
```

### Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Check for Data Changes                              │
├─────────────────────────────────────────────────────────────┤
│ For each timeframe:                                        │
│   - Calculate file hash of data/raw/{TF}.csv               │
│   - Compare to stored hash in calculation_state.json       │
│                                                            │
│ If unchanged:                                              │
│   → Skip (use existing indicators)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Calculate New Indicators (Incremental)             │
├─────────────────────────────────────────────────────────────┤
│ For each timeframe:                                        │
│   - Load raw data                                          │
│   - Calculate all 60 indicators                            │
│   - Save to data/indicators/{TF}_indicators.csv            │
│   - Update metadata                                        │
│   - Update state file                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Verify Coverage                                     │
├─────────────────────────────────────────────────────────────┤
│ Check: Every candle has indicators                         │
│ Report: Any mismatches                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## File Reference Summary

### Core System Files
| File | Purpose | Modified By |
|------|---------|-------------|
| `agents/ethusdt_agent.py` | Main trading logic | Auto-implementer (rarely) |
| `agents/dynamic_data_puller.py` | Data fetching | Never |
| `agents/modules/*.py` | All strategy modules | Auto-implementer (rarely) |

### Configuration
| File | Purpose | Modified By |
|------|---------|-------------|
| `config/agent.conf` | Trading parameters | Auto-implementer (daily) |
| `config/crontab.txt` | Cron schedule | Manual only |
| `config/dynamic_frequency_state.json` | Frequency mode | Trading agent |

### Data Files (Updated Regularly)
| File | Purpose | Updated By |
|------|---------|------------|
| `data/raw/1M.csv` | Monthly OHLCV | Manual (rare) |
| `data/raw/1w.csv` | Weekly OHLCV | Manual (rare) |
| `data/raw/1d.csv` | Daily OHLCV | Daily |
| `data/raw/4h.csv` | 4H OHLCV | Dynamic puller |
| `data/raw/1h.csv` | 1H OHLCV | Dynamic puller |
| `data/raw/15m.csv` | 15M OHLCV | Dynamic puller |
| `data/raw/5m.csv` | 5M OHLCV | **Dynamic puller (every minute)** |

### Indicator Files (Updated Hourly)
| File | Purpose | Updated By |
|------|---------|------------|
| `data/indicators/1M_indicators.csv` | Monthly indicators | calculate_indicators.py |
| `data/indicators/1w_indicators.csv` | Weekly indicators | calculate_indicators.py |
| `data/indicators/1d_indicators.csv` | Daily indicators | calculate_indicators.py |
| `data/indicators/4h_indicators.csv` | 4H indicators | calculate_indicators.py |
| `data/indicators/1h_indicators.csv` | 1H indicators | calculate_indicators.py |
| `data/indicators/15m_indicators.csv` | 15M indicators | calculate_indicators.py |
| `data/indicators/5m_indicators.csv` | 5M indicators | calculate_indicators.py |
| `data/indicators/calculation_state.json` | State tracking | calculate_indicators.py |

### State Files
| File | Purpose | Updated By |
|------|---------|------------|
| `agents/state/agent_state.json` | Agent state | Trading agent (every 15 min) |
| `agents/improver/state.json` | Improver state | Improver (daily) |
| `agents/improver/validated_suggestion.json` | Pending improvement | Improver (when found) |

### Backtest Files
| File | Purpose | Updated By |
|------|---------|------------|
| `backtests/ETHUSDT_trade_history.csv` | Trade history | Trading agent (when trades) |
| `backtests/ETHUSDT_strategy_config.csv` | Strategy settings | Manual |
| `backtests/full_system_backtest_results.json` | Backtest results | 6-hour review |
| `backtests/MISSED_OPPORTUNITIES.json` | Missed setups | Improver |

### Log Files (Created Daily)
| File | Purpose | Updated By |
|------|---------|------------|
| `agents/logs/cron_YYYYMMDD.log` | Trading agent logs | Trading agent (every 15 min) |
| `agents/logs/dynamic_puller_YYYYMMDD.log` | Data puller logs | Dynamic puller (every minute) |
| `agents/logs/indicator_calc.log` | Indicator logs | calculate_indicators.py (hourly) |
| `agents/improver/logs/cron_YYYYMMDD.log` | Improver logs | Improver (daily) |
| `agents/auto_implementer/logs/cron_YYYYMMDD.log` | Deploy logs | Auto-implementer (daily) |
| `agents/backtest_reviews/logs/review_YYYYMMDD_HH.log` | Review logs | 6-hour review |

---

## Execution Timeline (24 Hours)

```
TIME     EVENT                                            FILES ACCESSED
────────────────────────────────────────────────────────────────────────────
00:00    Backtest Review (00:00)                         
         └─> Runs full system backtest                    See section 7

00:01    Dynamic Puller                                   
         └─> Updates 5m data                              data/raw/5m.csv

00:02    Indicator Calculation                            
         └─> Updates all indicators                       data/indicators/*.csv

00:15    Trading Agent                                    
         └─> Analyzes for setups                          All data + indicators

00:30    Trading Agent                                    
         └─> Analyzes for setups                          All data + indicators

00:45    Trading Agent                                    
         └─> Analyzes for setups                          All data + indicators

... (repeats every 15 minutes) ...

06:00    IMPROVER (Daily)                                 
         └─> Analyzes trades, tests hypotheses            backtests/*, creates suggestion

06:01    Dynamic Puller (as usual)

06:02    Indicator Calc (as usual)

06:15    Trading Agent (as usual)

06:30    AUTO-IMPLEMENTER (Daily)                         
         └─> Deploys validated improvements               config/agent.conf, versions/*

... (continues through day) ...

12:00    Backtest Review (12:00)
18:00    Backtest Review (18:00)

... and so on ...
```

---

## Total Daily File Operations

| File Type | Writes/Day | Reads/Day |
|-----------|------------|-----------|
| Raw data (5m) | ~1,440 | ~96 |
| Indicators | ~168 | ~96 |
| Agent logs | ~96 | Manual |
| Puller logs | ~1,440 | Manual |
| State files | ~96 | ~96 |
| Backtest results | 4 | 4 |
| Improvement logs | 1 | 1 |
| Deploy logs | 1 | 1 |

**Total: ~2,800+ file operations per day**

---

This is the complete, exact flow of your ETHUSDT trading system!
