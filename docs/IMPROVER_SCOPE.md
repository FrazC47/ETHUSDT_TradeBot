# Improver Scope: What Changes vs What Stays Fixed

## Philosophy

**Change:** Parameters, thresholds, filters (tactics)  
**Keep Fixed:** Core strategy principles (strategy)

The improver optimizes **HOW** to trade, not **WHAT** to trade.

---

## ✅ WHAT WILL CHANGE (Variable)

### 1. Filter Thresholds
**Why change:** Find optimal strictness

| Parameter | Current | Range to Test | Purpose |
|-----------|---------|---------------|---------|
| `volume_threshold` | 1.0x | 0.6 - 1.2x | Balance opportunity vs quality |
| `max_range_location` | 70% | 50 - 80% | Avoid chasing late entries |
| `rsi_min` | 40 | 30 - 45 | Avoid oversold bounces |
| `rsi_max` | 75 | 70 - 85 | Capture momentum trades |
| `consecutive_bullish` | 2 | 1 - 4 | Confirm trend strength |

**Example Change:**
```
Volume 1.0 → 0.8 = Capture 40% more setups
Result: +$238 profit ✅
```

---

### 2. Risk Management Parameters
**Why change:** Optimize risk/reward balance

| Parameter | Current | Range to Test | Purpose |
|-----------|---------|---------------|---------|
| `atr_multiplier_stop` | 1.5x | 1.0 - 2.5x | Avoid stop-outs vs give room |
| `atr_multiplier_target` | 3.0x | 2.0 - 4.0x | R:R ratio optimization |
| `position_scale` | 50%+50% | Test 100% vs scaling | Entry timing precision |

**Example Change:**
```
Stop 1.5x ATR → 2.0x ATR = Fewer stop-outs
Result: +3% win rate ✅
```

---

### 3. Timeframe Weightings
**Why change:** Optimize which timeframes matter most

| Aspect | Current | Possible Changes |
|--------|---------|------------------|
| Primary TF | 1h | Could test 30m or 2h |
| Execution TF | 5m/1m dynamic | Could test 15m for less noise |
| HTF Check | 4h trend | Could add 1d weighting |

**BUT:** Will NOT remove 1M→5m MTF structure

---

### 4. Indicator Periods
**Why change:** Optimize for ETH's volatility

| Indicator | Current | Range to Test |
|-----------|---------|---------------|
| EMA Fast | 9 | 7, 8, 9, 10, 12 |
| EMA Slow | 21 | 18, 21, 25, 30 |
| RSI Period | 14 | 10, 14, 20 |
| ATR Period | 14 | 10, 14, 20 |

---

## ❌ WHAT STAYS FIXED (Constant)

### 1. Core Strategy Type
**Fixed:** Long-only trend following on ETHUSDT

**Why fixed:**
- Strategy has proven edge (+120% backtest)
- Changing strategy type = new system entirely
- Would require complete re-validation

**Won't change to:**
- ❌ Short selling (different skill set)
- ❌ Scalping (different time commitment)
- ❌ Mean reversion (opposite philosophy)
- ❌ Different asset (BTC, SOL, etc.)

---

### 2. Multi-Timeframe Structure
**Fixed:** 1M → 1w → 1d → 4h → 1h → 15m → 5m

**Why fixed:**
- Top-down analysis is core principle
- Removes 90% of bad trades
- Proven in backtests

**Won't change to:**
- ❌ Single timeframe (loses context)
- ❌ Different TF hierarchy
- ❌ Remove monthly/weekly (macro context)

---

### 3. Minimum Risk/Reward
**Fixed:** Minimum 2:1 R:R ratio

**Why fixed:**
- Mathematical requirement for profitability
- Lower R:R = losing strategy long-term
- Non-negotiable risk management

**Won't accept:**
- ❌ 1.5:1 R:R (not profitable)
- ❌ 1:1 R:R (guaranteed losses)
- ❌ Negative R:R (insanity)

---

### 4. Risk Per Trade
**Fixed:** Maximum 3% risk per trade

**Why fixed:**
- Capital preservation priority
- Allows 33 consecutive losses before ruin
- Industry standard for safety

**Won't increase to:**
- ❌ 5% risk (too volatile)
- ❌ 10% risk (gambling)
- ❌ All-in (certain ruin)

---

### 5. Leverage
**Fixed:** 5x leverage (isolated)

**Why fixed:**
- Tested and optimized for ETH volatility
- Higher = liquidation risk
- Lower = capital inefficiency

**Won't change to:**
- ❌ 10x, 20x, 50x (liquidation risk)
- ❌ 1x, 2x (inefficient)
- ❌ Cross margin (uncontrolled risk)

---

### 6. Trading Hours
**Fixed:** 24/7 (crypto never sleeps)

**Why fixed:**
- Crypto markets always open
- Missing moves = missed profit
- Automated system doesn't sleep

**Won't restrict to:**
- ❌ Trading sessions (NY, London, Asia)
- ❌ Weekdays only (miss weekend moves)
- ❌ Specific hours (arbitrary)

---

## 🧪 EXPERIMENTAL (May Test, Probably Won't Change)

### 1. Scalping Elements
**Status:** Might test, unlikely to adopt

**Why probably not:**
- Current system is swing trading (hours to days)
- Scalping requires different infrastructure
- Higher fees, more stress
- Would need dedicated scalping agent

**Might test:**
- 1-minute entries for precision (already doing)
- Tighter stops for quick exits
- But NOT pure scalping strategy

---

### 2. Additional Indicators
**Status:** Might add if proven valuable

**Possible additions:**
- VWAP deviation bands
- Order flow imbalance
- Funding rate analysis
- Whales wallet tracking

**Requirements to add:**
- Must improve backtest results >5%
- Must not increase complexity >20%
- Must be data-available in real-time

---

### 3. Dynamic Position Sizing
**Status:** Already implemented, may refine

**Current:** Fixed 3% risk per trade

**Might test:**
- Kelly criterion sizing
- Volatility-adjusted sizing
- Confidence-based sizing (higher confidence = larger size)

---

## 📋 Summary Table

| Category | Examples | Status |
|----------|----------|--------|
| **Filter Thresholds** | Volume, RSI, Range | ✅ CHANGE |
| **Risk Parameters** | Stop distance, R:R | ✅ CHANGE |
| **Indicator Periods** | EMA 9/21, RSI 14 | ✅ CHANGE |
| **Timeframe Weights** | Primary TF emphasis | ⚠️ MAYBE |
| **Core Strategy** | Long trend following | ❌ FIXED |
| **MTF Structure** | 1M→5m hierarchy | ❌ FIXED |
| **Min R:R** | 2:1 minimum | ❌ FIXED |
| **Risk Per Trade** | 3% max | ❌ FIXED |
| **Leverage** | 5x isolated | ❌ FIXED |
| **Asset** | ETHUSDT only | ❌ FIXED |
| **Scalping** | 1m precision | ⚠️ PARTIAL |
| **New Indicators** | VWAP, Order flow | ⚠️ EXPERIMENTAL |

---

## 🎯 The Boundary

**Improver changes TACTICS, not STRATEGY:**

| Strategy (Fixed) | Tactics (Variable) |
|------------------|-------------------|
| Long trend following | Entry timing precision |
| 7 timeframe analysis | Which TF weights more |
| 2:1 minimum R:R | Exact stop/target placement |
| ETHUSDT only | Which filters to use |
| 3% risk per trade | How to scale entries |

**Analogy:**
- **Strategy** = Deciding to drive from NY to LA (fixed goal)
- **Tactics** = Which route, speed, stops (optimized path)

The improver finds the **best route**, not a **different destination**.

---

## 🚀 Bottom Line

**The improver will:**
✅ Optimize parameters within proven strategy  
✅ Fine-tune filters for ETH's behavior  
✅ Adapt to changing market conditions  
✅ Maximize profit while respecting risk limits  

**The improver won't:**
❌ Change to a different trading style  
❌ Remove core risk management rules  
❌ Trade different assets  
❌ Become a scalping system  
❌ Gamble with your capital  

**Result:** A better version of what already works! 🎯
