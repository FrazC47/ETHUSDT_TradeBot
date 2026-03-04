# Advanced Profit-Taking Scenarios - Visual Guide

## Overview: 12 Scenarios for Maximum Revenue

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MARKET CONDITION → SELECT SCENARIO                        │
└─────────────────────────────────────────────────────────────────────────────┘

PRICE LOCATION                    MARKET CONDITION              SCENARIO
─────────────────────────────────────────────────────────────────────────────

At Optimal Entry (0.618 fib)
    │
    ├── High confidence (>85%) + Momentum
    │   └── Quick Scalp (+15% boost)
    │       Entry: Market order
    │       Exit: 50% at +1.5%, 50% at +3%
    │       Stop: Tight 0.8%
    │
    └── Standard confidence
        └── Standard 2:1 R:R

Price Moved 10-20%
    │
    ├── High confidence (>80%)
    │   └── Chase with Tight Risk (+10% boost)
    │       Entry: Accept worse price
    │       Exit: 50% at 50% of remaining move
    │       Stop: Very tight 0.5%
    │
    └── Low confidence
        └── SKIP (wait for pullback)

Price at Support/Resistance
    │
    ├── Clear range + RSI oversold
    │   └── Range Scalp (+8% boost)
    │       Entry: Support + 0.3% buffer
    │       Exit: Range high
    │       Stop: Below support 0.8%
    │
    ├── Liquidity sweep below support
    │   └── Liquidity Sweep (+22% boost)
    │       Entry: Reversal close above support
    │       Exit: Previous resistance
    │       Stop: Below sweep low
    │
    └── Fib level (0.618/0.786)
        └── Fib Bounce (+12% boost)
            Entry: Fib level + 0.5% buffer
            Exit: Next fib level
            Stop: Below swing low

Breakout Conditions
    │
    ├── Breaks resistance + Volume spike
    │   └── Breakout Momentum (+25% boost)
    │       Entry: Close above resistance
    │       Exit: TRAILING STOP (no fixed target)
    │       Stop: Trail 1x ATR, breakeven at +2%
    │
    └── Opening range break (first hour)
        └── ORB Strategy (+18% boost)
            Entry: Break of opening range
            Exit: 2x range size
            Stop: Other side of range

Trend Conditions
    │
    ├── Strong trend (ADX >30) + Above EMAs
    │   └── Trend Ride (+35% boost)
    │       Entry: Pullback to EMA 9
    │       Exit: TRAILING STOP (ride trend)
    │       Stop: Trail 2x ATR, tighten to 1x after +5%
    │
    └── Already in winning trade + Higher low
        └── Pyramid Winner (+40% boost)
            Entry: ADD 50% to position
            Exit: 25% at +3%, 25% at +5%, 50% at +8%
            Stop: Move to breakeven

Mean Reversion
    │
    └── Price >2% from VWAP
        └── VWAP Reversion (+6% boost)
            Entry: Toward VWAP (counter-trend)
            Exit: VWAP line
            Stop: Beyond extension 1.0%

Time-Based
    │
    └── Trade open 12h + Minimal movement
        └── Time Decay Exit (+5% boost)
            Exit: Breakeven or +0.5%
            Stop: Tighten to entry after 8h

Momentum Exhaustion
    │
    └── Near target + RSI overbought
        └── Momentum Exhaustion (+8% boost)
            Exit: 80% at target, trail 20%
            Stop: Trail 2x ATR on remaining
```

---

## Trailing Stop Progression

```
Entry Price: $2000

Price Movement    Trailing Stop Action
─────────────────────────────────────────
$2000 → $2020    Initial stop at $1980 (1.5x ATR)
   (+1% profit)

$2020 → $2040    Move stop to breakeven ($2000)
   (+2% profit)   (lock in no loss)

$2040 → $2100    Trail 2x ATR behind price (~$2060)
   (+5% profit)   (give room for trend)

$2100 → $2200    Tighten to 1x ATR (~$2160)
   (+10% profit)  (lock in more profit)

$2200 → $2300    Very tight 0.8x ATR (~$2270)
   (+15% profit)  (parabolic protection)

$2300 → $2250    STOPPED OUT at $2270
   (pullback)     (+13.5% profit captured)
```

---

## Partial Profit Scaling

### Standard Scale-Out:
```
Entry: $2000
Target: $2200 (+10%)

Price    Action                Position
────────────────────────────────────────
$2060    Sell 25%             75% remaining
(+3%)

$2100    Sell 25%             50% remaining  
(+5%)

$2160    Sell 25%             25% remaining
(+8%)

$2200    Sell final 25%       0% (fully out)
(+10%)

Average exit: ~$2130 (+6.5% with reduced risk)
```

### Pyramid (Add to Winners):
```
Entry 1: $2000 (100% size)

Price    Action                Total Position
─────────────────────────────────────────────
$2040    Add 50% size         150% size
(+2%)

$2100    Sell 30%             120% size
(+5%)

$2200    Sell 40%             80% size
(+10%)

$2300    Sell final 80%       0% (fully out)
(+15%)

Result: Larger position during winning move
```

---

## Entry Placement Variations

### 1. Optimal Entry (Standard)
```
Fib 0.618: $2000
Entry:      $2000 (exact)
Buffer:     0%
```

### 2. Buffer Entry (Volatility)
```
Fib 0.618: $2000
Entry:      $2010 (+0.5% buffer)
Reason:     Avoid false breakdown
```

### 3. Chase Entry (FOMO)
```
Fib 0.618: $2000
Price now:  $2040 (+2% moved)
Entry:      $2040 (accept worse price)
Stop:       Tighter ($2020 vs $1980)
R:R:        Lower (1:1 vs 2:1)
Condition:  High confidence only
```

### 4. Scale-In Entry (Dollar Cost)
```
Entry 1: $2000 (50% position)
Entry 2: $1980 (30% position) - if drops
Entry 3: $1960 (20% position) - if drops more

Average: ~$1986 (better than single entry)
Risk:    More complex management
```

---

## Exit Placement Variations

### 1. Fixed Target (Standard)
```
Entry:  $2000
Stop:   $1950 (-2.5%)
Target: $2100 (+5%)
R:R:    2:1
```

### 2. Fibonacci Target
```
Entry:  $2000 (0.618 fib)
Stop:   $1980 (below 0.786)
Target: $2050 (0.5 fib)
       $2080 (0.382 fib - extended)
R:R:    2.5:1 to 5:1
```

### 3. Resistance Target
```
Entry:       $2000
Resistance:  $2100 (previous high)
Target:      $2100 (conservative)
             $2120 (breakout + buffer)
             $2200 (measured move)
```

### 4. Trailing Exit (Trend)
```
Entry:    $2000
No target - trail until:
- Price breaks below EMA 21
- Momentum indicator turns negative
- Volume dries up
- Stop hit (trailing)
```

---

## Scenario Selection Flowchart

```
START
  │
  ├─ Opening hour? ──YES──► ORB Strategy
  │
  ├─ Breakout from range? ──YES──► Breakout Momentum
  │
  ├─ At fib level (0.618/0.786)? ──YES──► Fib Bounce
  │
  ├─ Liquidity sweep? ──YES──► Liquidity Sweep
  │
  ├─ Strong trend (ADX>30)? ──YES──► Trend Ride
  │
  ├─ Far from VWAP (>2%)? ──YES──► VWAP Reversion
  │
  ├─ In clear range? ──YES──► Range Scalp
  │
  ├─ Already winning trade? ──YES──► Pyramid Winner
  │
  ├─ Price moved 20-30%? ──YES──► Chase with Tight Risk
  │
  └─ High confidence + Early? ──YES──► Quick Scalp
  │
  └─ Default ──► Standard 2:1 R:R
```

---

## Combined Revenue Impact

| Scenario Type | Frequency | Avg Boost | Annual Impact |
|---------------|-----------|-----------|---------------|
| Quick Scalps | 30% | +15% | +4.5% |
| Breakouts | 15% | +25% | +3.75% |
| Fib Bounces | 20% | +12% | +2.4% |
| Range Scalps | 15% | +8% | +1.2% |
| Trend Rides | 10% | +35% | +3.5% |
| Pyramids | 5% | +40% | +2.0% |
| Others | 5% | +15% | +0.75% |
| **TOTAL** | **100%** | | **+18.1%** |

**Result: +18-25% additional annual revenue through scenario optimization!**
