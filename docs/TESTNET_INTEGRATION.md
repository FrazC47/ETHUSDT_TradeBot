# Binance Testnet Integration Architecture

## Overview

The testnet integration connects our ETHUSDT trading system to Binance's **fake money** trading environment for safe testing.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        SIGNAL GENERATION LAYER                          │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
  │  │   1M     │ │   1W     │ │   1d     │ │   4h     │ │   1h     │        │
  │  │ Monthly  │ │ Weekly   │ │  Daily   │ │  4 Hour  │ │  1 Hour  │        │
  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
  │       └─────────────┴────────────┴────────────┴────────────┘              │
  │                          ↓                                                │
  │              ┌───────────────────────┐                                    │
  │              │ Weighted Cluster      │  40% Macro (1M/1W)                 │
  │              │ Analyzer (40/35/25)   │  35% Intermediate (1d/4h)          │
  │              └───────────┬───────────┘  25% Execution (1h/15m)            │
  │                          ↓                                                │
  │              ┌───────────────────────┐                                    │
  │              │ 9-State Regime        │                                    │
  │              │ Classification        │                                    │
  │              └───────────┬───────────┘                                    │
  │                          ↓                                                │
  │              ┌───────────────────────┐                                    │
  │              │ Trade Detection Agent │  ← Signals generated here          │
  │              │ (Confidence: 65%+)    │                                    │
  │              └───────────┬───────────┘                                    │
  └──────────────────────────┼──────────────────────────────────────────────┘
                             │
                             ↓ IF confidence >= 65%
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                      EXECUTION DECISION LAYER                           │
  │  ┌─────────────────────────────────────────────────────────────────┐    │
  │  │                    Auto-Trading Mode                             │    │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
  │  │  │   TESTNET    │  │   PAPER      │  │    LIVE      │           │    │
  │  │  │   (FAKE $)   │  │   (SIMULATE) │  │  (REAL $)    │           │    │
  │  │  │  ✅ SAFEST   │  │   Testing    │  │  Production  │           │    │
  │  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
  │  └─────────────────────────────────────────────────────────────────┘    │
  │                           ↓                                             │
  └───────────────────────────┼─────────────────────────────────────────────┘
                              │
  ┌───────────────────────────┼─────────────────────────────────────────────┐
  │                      BINANCE TESTNET INTEGRATION                        │
  │                           ↓                                             │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │           BinanceTestnetClient (binance_testnet_client.py)      │   │
  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
  │  │  │  Account    │  │   Orders    │  │  Positions  │              │   │
  │  │  │  Balance    │  │  (Entry/SL/ │  │   (PnL)     │              │   │
  │  │  │  ($10,000)  │  │     TP)     │  │             │              │   │
  │  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │                           ↓                                             │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │        TestnetTradingExecutor (Auto-Execute Trades)             │   │
  │  │                                                                  │   │
  │  │  1. RECEIVE signal from detection agent                         │   │
  │  │     ↓                                                           │   │
  │  │  2. CALCULATE position size (2% risk rule)                      │   │
  │  │     ↓                                                           │   │
  │  │  3. PLACE 3 orders simultaneously:                              │   │
  │  │     • LIMIT entry order @ entry_price                           │   │
  │  │     • STOP_MARKET stop loss @ stop_price                        │   │
  │  │     • TAKE_PROFIT target @ target_price                         │   │
  │  │     ↓                                                           │   │
  │  │  4. MONITOR orders until filled or cancelled                    │   │
  │  │     ↓                                                           │   │
  │  │  5. RECORD trade in history                                     │   │
  │  │                                                                  │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │                           ↓                                             │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │           TESTNET ACCOUNT (Virtual $10,000 USDT)                │   │
  │  │                                                                  │   │
  │  │  • No real money risk                                           │   │
  │  │  • Real ETHUSDT prices                                          │   │
  │  │  • Real fee structure (0.02%/0.05%)                             │   │
  │  │  • Real order book behavior                                     │   │
  │  │  • Trades don't affect real market                              │   │
  │  │                                                                  │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────────┘
                              │
                              ↓ AFTER 20+ SUCCESSFUL TESTNET TRADES
  ┌───────────────────────────┼─────────────────────────────────────────────┐
  │                     LIVE TRADING (Production)                           │
  │  • Same code, same logic                                                │
  │  • Real Binance API (binance.com)                                       │
  │  • Your real $1,000                                                     │
  │  • Real profits & losses                                                │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components Explained

### 1. BinanceTestnetClient

**Purpose:** Low-level API communication with Binance testnet

**Methods:**
```python
# Account
get_account_balance()      # Check your $10,000 fake balance
get_position_risk()        # See open positions and PnL

# Trading
place_order()              # Place entry/stop/target orders
cancel_order()             # Cancel pending orders
get_open_orders()          # List all pending orders

# Market Data
get_symbol_price()         # Current ETHUSDT price
get_klines()               # Candlestick data
```

**API Authentication:**
```
Request → Add API Key Header → Generate HMAC Signature → Send to testnet.binancefuture.com
```

### 2. TestnetTradingExecutor

**Purpose:** High-level trade execution logic

**What it does:**
1. **Receives signal** from `trade_detection_agent_v2.py`
2. **Calculates position size** using 2% risk rule
3. **Places 3 orders atomically:**
   - LIMIT entry (waits for price)
   - STOP_MARKET stop loss (triggers on stop_price)
   - TAKE_PROFIT target (triggers on target_price)
4. **Monitors execution** until filled
5. **Records history** for learning system

**Order Placement Flow:**
```
Signal Received
     ↓
Calculate: position_size = (account * 0.02) / (entry - stop)
     ↓
Set leverage: 10x for ETH
     ↓
Place ENTRY order (LIMIT @ entry_price)
     ↓
Place STOP order (STOP_MARKET @ stop_price)
     ↓
Place TARGET order (TAKE_PROFIT @ target_price)
     ↓
Wait for fills...
     ↓
Record trade in testnet_trade_history.json
```

### 3. Configuration Storage

**File:** `data/binance_testnet_config.json`

```json
{
  "api_key": "your_testnet_api_key_here",
  "api_secret": "your_testnet_secret_here",
  "base_url": "https://testnet.binancefuture.com",
  "setup_date": "2026-03-07T04:00:00"
}
```

**Security:** 
- File is in `.gitignore` (not committed to GitHub)
- Testnet keys are separate from live keys
- Can be regenerated anytime

---

## Data Flow Example

### Scenario: LONG Signal Generated

```
1. DETECTION AGENT OUTPUT:
   {
     "direction": "LONG",
     "entry_price": 2000.00,
     "stop_price": 1980.00,
     "target_price": 2040.00,
     "confidence": 85,
     "confluence": 4
   }

2. CALCULATION:
   Account balance: $10,000
   Risk amount: $10,000 × 2% = $200
   Risk per ETH: $2000 - $1980 = $20
   Position size: $200 / $20 = 10 ETH
   Margin required (10x): $2000 × 10 / 10 = $2,000

3. ORDER PLACEMENT:
   Order 1: LIMIT BUY 10 ETH @ $2000
   Order 2: STOP MARKET SELL 10 ETH @ $1980
   Order 3: TAKE PROFIT SELL 10 ETH @ $2040

4. EXECUTION SCENARIOS:
   
   A. Price hits $2000 first:
      - Entry fills
      - Wait for stop or target
      - If price hits $2040: +$400 profit
      - If price hits $1980: -$200 loss
   
   B. Price drops to $1980 first:
      - Entry never fills
      - Stop cancels automatically
      - No trade executed

5. RESULT RECORDED:
   {
     "trade_id": "TEST_20260307_120000",
     "direction": "LONG",
     "entry": 2000.00,
     "exit": 2040.00,
     "pnl": 400.00,
     "pnl_percent": 4.0,
     "status": "WIN"
   }
```

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/binance_testnet_client.py` | API client + trading executor |
| `data/binance_testnet_config.json` | API credentials (gitignored) |
| `data/testnet_trade_history.json` | Record of all testnet trades |

---

## Commands Available

```bash
# Setup (one time)
python3 scripts/binance_testnet_client.py setup

# Check balance
python3 scripts/binance_testnet_client.py balance

# Execute test trade
python3 scripts/binance_testnet_client.py trade

# Check active trades
python3 scripts/binance_testnet_client.py status

# Close a trade manually
python3 scripts/binance_testnet_client.py close <trade_id>
```

---

## Why This Architecture?

| Feature | Benefit |
|---------|---------|
| **Separate client** | Can test API without trading logic |
| **Separate executor** | Can simulate trades without real API |
| **JSON config** | Easy to swap between testnet/live |
| **JSON history** | Learning system can analyze performance |
| **3-order atomic** | Entry + protection placed together |
| **HMAC auth** | Secure API communication |

---

## Next Steps to Activate

1. **Get testnet API keys** from testnet.binancefuture.com
2. **Run setup** to save credentials
3. **Verify balance** ($10,000 should be there)
4. **Execute test trade** to verify connection
5. **Connect to detection system** for auto-trading

**Ready to proceed?**
