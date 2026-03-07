---
name: indicator-calculator
description: |
  Calculate comprehensive technical indicators for cryptocurrency trading data.
  Takes raw OHLCV candlestick data and calculates 100+ indicators including:
  - Moving averages (EMA, SMA, VWAP)
  - Momentum indicators (RSI, MACD, Stochastic)
  - Volatility indicators (ATR, Bollinger Bands, Keltner Channels)
  - Trend indicators (ADX, DMI, Parabolic SAR)
  - Fibonacci retracements and extensions
  - Market structure analysis (higher highs, lower lows)
  - Support and resistance levels
  - Trend line detection
  Use when calculating technical indicators for any timeframe of crypto trading data.
---

# Technical Indicator Calculator

## Usage

Calculate indicators for a specific timeframe:

```bash
python3 scripts/calculate_indicators.py <timeframe> <input_file> <output_file>
```

## Parameters

- `timeframe`: One of 1M, 1w, 1d, 4h, 1h, 15m, 5m
- `input_file`: Path to raw OHLCV CSV file
- `output_file`: Path to save calculated indicators CSV

## Example

```bash
python3 scripts/calculate_indicators.py 1w \
  /data/ETHUSDT_1w.csv \
  /data/ETHUSDT_1w_indicators.csv
```

## Output Columns (106 total)

### Price Data (12 columns)
open_time, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_volume, taker_buy_quote_volume, ignore

### Trend Indicators
ema_9, ema_21, ema_50, ema_200, sma_20, sma_50, trend_bullish, trend_strong

### Momentum Indicators
rsi, rsi_sma, macd_line, macd_signal, macd_hist

### Volatility Indicators
atr, atr_pct, bb_middle, bb_upper, bb_lower, bb_width, bb_position

### Volume Indicators
volume_sma_20, volume_ratio, typical_price, tp_volume, vwap, vwap_distance

### Trend Strength (DMI)
plus_dm, minus_dm, plus_di, minus_di, dx, adx, adx_trending

### Fibonacci (13 levels)
fib_0, fib_236, fib_382, fib_500, fib_618, fib_786, fib_100, fib_1272, fib_1382, fib_1618, fib_200, fib_2618, fib_4236, fib_position

### Market Structure
hh, lh, hl, ll, structure_score, structure_bullish, structure_bearish

### Price Action
body_size, upper_wick, lower_wick, range, range_pct, is_bullish, is_bearish, consecutive_bullish, swing_high, swing_low, range_location

### Support/Resistance (4 levels each)
resistance_1-4, support_1-4, dist_to_resistance_1, dist_to_support_1, sr_zone_size, position_in_sr_zone

### Trend Lines
bull_trend_line, bull_trend_touches, bull_trend_valid, bull_trend_angle, bull_trend_slope_pct, dist_to_bull_trend, bear_trend_line, bear_trend_touches, bear_trend_valid, bear_trend_angle, bear_trend_slope_pct, dist_to_bear_trend, above_bull_trend, below_bear_trend, between_trend_lines, broke_bull_trend, broke_bear_trend
