# ETHUSDT Data Schema and Indicator Calculations

This document describes the data structure and calculations used in the ETHUSDT trading system.

---

## 1. Raw Candlestick Data

### File Location
`/data/raw/[TIMEFRAME].csv`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `open_time` | datetime | Candle open timestamp (UTC) |
| `open` | float | Opening price |
| `high` | float | Highest price during candle |
| `low` | float | Lowest price during candle |
| `close` | float | Closing price |
| `volume` | float | Trading volume in base asset (ETH) |
| `close_time` | datetime | Candle close timestamp (UTC) |
| `quote_volume` | float | Trading volume in quote asset (USDT) |
| `count` | int | Number of trades in candle |
| `taker_buy_volume` | float | Volume of market buy orders |
| `taker_buy_quote_volume` | float | Quote volume of market buy orders |
| `ignore` | bool | Ignore flag (usually false) |

### Example
```csv
open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore
2025-01-01 00:00:00,2450.50,2460.00,2445.20,2455.80,1250.5,2025-01-01 01:00:00,3065000.5,850,623.2,1528000.2,false
```

---

## 2. Indicator Data

### File Location
`/data/indicators/[TIMEFRAME]_indicators.csv`

### Base Columns (from raw data)
- `open_time`
- `open`
- `high`
- `low`
- `close`
- `volume`

---

## 3. Indicator Calculations

### 3.1 EMA (Exponential Moving Average)

#### Formula
```
EMA_today = (Close_today × multiplier) + (EMA_yesterday × (1 - multiplier))
multiplier = 2 / (period + 1)
```

#### Python Implementation
```python
df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
```

#### Columns
- `ema_9` - 9-period EMA (short-term)
- `ema_21` - 21-period EMA (medium-term)
- `ema_50` - 50-period EMA (long-term)
- `ema_200` - 200-period EMA (very long-term)

---

### 3.2 RSI (Relative Strength Index)

#### Formula
```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss

Average Gain = (Previous Average Gain × 13 + Current Gain) / 14
Average Loss = (Previous Average Loss × 13 + Current Loss) / 14
```

#### Python Implementation
```python
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['rsi_14'] = 100 - (100 / (1 + rs))
```

#### Columns
- `rsi_14` - 14-period RSI (0-100 scale)

---

### 3.3 MACD (Moving Average Convergence Divergence)

#### Formula
```
MACD Line = EMA_12(Close) - EMA_26(Close)
Signal Line = EMA_9(MACD Line)
Histogram = MACD Line - Signal Line
```

#### Python Implementation
```python
exp1 = df['close'].ewm(span=12, adjust=False).mean()
exp2 = df['close'].ewm(span=26, adjust=False).mean()
df['macd_line'] = exp1 - exp2
df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
df['macd_hist'] = df['macd_line'] - df['macd_signal']
```

#### Columns
- `macd_line_12_26` - MACD line
- `macd_signal_12_26` - Signal line
- `macd_hist_12_26` - MACD histogram

---

### 3.4 Bollinger Bands

#### Formula
```
Middle Band = SMA_20(Close)
Upper Band = Middle Band + (Standard Deviation × 2)
Lower Band = Middle Band - (Standard Deviation × 2)
Band Position = (Close - Lower Band) / (Upper Band - Lower Band)
```

#### Python Implementation
```python
df['bb_middle'] = df['close'].rolling(window=20).mean()
bb_std = df['close'].rolling(window=20).std()
df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
```

#### Columns
- `bb_middle` - Middle band (20 SMA)
- `bb_upper` - Upper band (+2 std dev)
- `bb_lower` - Lower band (-2 std dev)
- `bb_position` - Position within bands (0-1)

---

### 3.5 ATR (Average True Range)

#### Formula
```
True Range = max(High - Low, |High - Previous Close|, |Low - Previous Close|)
ATR = SMA_14(True Range)
```

#### Python Implementation
```python
high_low = df['high'] - df['low']
high_close = np.abs(df['high'] - df['close'].shift())
low_close = np.abs(df['low'] - df['close'].shift())
ranges = pd.concat([high_low, high_close, low_close], axis=1)
true_range = np.max(ranges, axis=1)
df['atr_14'] = true_range.rolling(14).mean()
```

#### Columns
- `atr_14` - 14-period Average True Range

---

### 3.6 ADX (Average Directional Index)

#### Formula
```
+DM = Current High - Previous High (if positive and > -DM)
-DM = Previous Low - Current Low (if positive and > +DM)
+DI = 100 × EMA_14(+DM) / ATR_14
-DI = 100 × EMA_14(-DM) / ATR_14
DX = 100 × |+DI - -DI| / (+DI + -DI)
ADX = EMA_14(DX)
```

#### Python Implementation
```python
plus_dm = df['high'].diff()
minus_dm = df['low'].diff(-1).abs()
plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

atr = true_range.rolling(14).mean()
plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
df['adx'] = dx.rolling(14).mean()
df['plus_di'] = plus_di
df['minus_di'] = minus_di
```

#### Columns
- `adx` - Average Directional Index (0-100)
- `plus_di` - Positive Directional Indicator
- `minus_di` - Negative Directional Indicator

---

### 3.7 Volume Indicators

#### Volume Ratio
```python
df['volume_sma_20'] = df['volume'].rolling(20).mean()
df['volume_ratio'] = df['volume'] / df['volume_sma_20']
```

#### Columns
- `volume_ratio` - Current volume / 20-period average

---

### 3.8 VWAP (Volume Weighted Average Price)

#### Formula
```
VWAP = Σ(Typical Price × Volume) / Σ(Volume)
Typical Price = (High + Low + Close) / 3
VWAP Distance = (Close - VWAP) / VWAP × 100
```

#### Python Implementation
```python
typical_price = (df['high'] + df['low'] + df['close']) / 3
vwap_cumsum = (typical_price * df['volume']).cumsum()
vol_cumsum = df['volume'].cumsum()
df['vwap'] = vwap_cumsum / vol_cumsum
df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100
```

#### Columns
- `vwap` - Volume Weighted Average Price
- `vwap_distance` - Distance from VWAP in percentage

---

### 3.9 Fibonacci Levels

#### Calculation
```python
# For each period, calculate based on recent swing high/low
period = 20  # Lookback period
high_20 = df['high'].rolling(period).max()
low_20 = df['low'].rolling(period).min()
diff = high_20 - low_20

df['fib_382'] = high_20 - (diff * 0.382)
df['fib_500'] = high_20 - (diff * 0.500)
df['fib_618'] = high_20 - (diff * 0.618)
```

#### Columns
- `fib_382` - 38.2% retracement level
- `fib_500` - 50% retracement level
- `fib_618` - 61.8% retracement level

---

### 3.10 Support/Resistance Levels

#### Calculation (Simplified)
```python
# Pivot points (simplified)
pivot = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
r1 = (2 * pivot) - df['low'].shift(1)
s1 = (2 * pivot) - df['high'].shift(1)

# Store as rolling max/min for dynamic levels
df['support_level'] = df['low'].rolling(20).min()
df['resistance_level'] = df['high'].rolling(20).max()
```

#### Columns
- `support_level` - Recent support level
- `resistance_level` - Recent resistance level

---

## 4. Complete Column List by Timeframe

### Higher Timeframes (1M, 1W, 1D)
- open_time, open, high, low, close, volume
- ema_9, ema_21, ema_50, ema_200
- rsi_14
- macd_line_12_26, macd_signal_12_26, macd_hist_12_26
- bb_middle, bb_upper, bb_lower, bb_position
- atr_14
- adx, plus_di, minus_di
- volume_ratio
- fib_382, fib_500, fib_618
- support_level, resistance_level

### Lower Timeframes (4H, 1H, 15M, 5M, 1M)
All columns from higher timeframes PLUS:
- vwap, vwap_distance
- Candlestick pattern indicators (if calculated)

---

## 5. Data Validation Checks

### OHLC Integrity
```python
# Check high >= low
assert (df['high'] >= df['low']).all()

# Check close within high/low
assert ((df['close'] >= df['low']) & (df['close'] <= df['high'])).all()

# Check open within high/low
assert ((df['open'] >= df['low']) & (df['open'] <= df['high'])).all()
```

### Volume Validation
```python
# No negative volumes
assert (df['volume'] >= 0).all()

# Volume not all identical (would suggest fake data)
assert df['volume'].nunique() > 100
```

### Timestamp Validation
```python
# No duplicate timestamps
assert df['open_time'].is_unique

# Chronological order
df = df.sort_values('open_time')
```

---

## 6. Recreating Indicators

### From Scratch
```python
import pandas as pd
import numpy as np

# Load raw data
df = pd.read_csv('/data/raw/1h.csv')
df['open_time'] = pd.to_datetime(df['open_time'])

# Calculate all indicators
# (Use formulas from sections 3.1 - 3.10 above)

# Save
df.to_csv('/data/indicators/1h_indicators.csv', index=False)
```

---

## 7. Notes

- All indicators use `adjust=False` for EMA calculations (standard for trading)
- RSI uses Wilder's smoothing method (rolling mean)
- MACD uses standard 12/26/9 periods
- Bollinger Bands use 2 standard deviations
- ATR and ADX use 14 periods (standard)
- Fibonacci levels recalculate on each candle based on rolling window

---

## 8. Indicator Count Summary

| Timeframe | Total Columns | Base | EMAs | Oscillators | Volatility | Volume | Patterns |
|-----------|--------------|------|------|-------------|------------|--------|----------|
| 1M | ~20 | 6 | 4 | 3 | 3 | 2 | 2 |
| 1W | ~25 | 6 | 4 | 3 | 3 | 2 | 7 |
| 1D | ~30 | 6 | 4 | 3 | 3 | 2 | 12 |
| 4H | ~35 | 6 | 4 | 3 | 3 | 3 | 16 |
| 1H | ~40 | 6 | 4 | 3 | 3 | 3 | 21 |
| 15M | ~45 | 6 | 4 | 3 | 3 | 3 | 26 |
| 5M | ~50 | 6 | 4 | 3 | 3 | 3 | 31 |
| 1M | ~55 | 6 | 4 | 3 | 3 | 3 | 36 |

---

**Last Updated:** 2026-03-09  
**Data Source:** Binance Futures ETHUSDT
