# ETHUSDT Indicator Calculation Formulas

## 1. EMA (Exponential Moving Average)
```
EMA = Close.ewm(span=N, adjust=False).mean()
```
- EMA9: span=9
- EMA21: span=21
- EMA50: span=50
- EMA200: span=200

## 2. RSI (Relative Strength Index)
```
Delta = Close - Close.shift(1)
Gain = Average of positive Deltas over 14 periods
Loss = Average of negative Deltas over 14 periods
RS = Gain / Loss
RSI = 100 - (100 / (1 + RS))
```
Period: 14

## 3. MACD
```
EMA12 = Close.ewm(span=12).mean()
EMA26 = Close.ewm(span=26).mean()
MACD Line = EMA12 - EMA26
Signal Line = MACD Line.ewm(span=9).mean()
Histogram = MACD Line - Signal Line
```

## 4. ATR (Average True Range)
```
TR1 = High - Low
TR2 = |High - Close.shift(1)|
TR3 = |Low - Close.shift(1)|
True Range = Max(TR1, TR2, TR3)
ATR = Average of True Range over 14 periods
ATR% = (ATR / Close) * 100
```

## 5. VWAP (Volume Weighted Average Price)
```
Typical Price = (High + Low + Close) / 3
TP Volume = Typical Price * Volume
VWAP = Sum(TP Volume over 20 periods) / Sum(Volume over 20 periods)
VWAP Distance = ((Close - VWAP) / VWAP) * 100
```

## 6. ADX (Average Directional Index)
```
+DM = Max(High - High.shift(1), 0) if (High - High.shift(1)) > (Low.shift(1) - Low)
-DM = Max(Low.shift(1) - Low, 0) if (Low.shift(1) - Low) > (High - High.shift(1))

+DI = 100 * (Average +DM over 14 periods / ATR)
-DI = 100 * (Average -DM over 14 periods / ATR)
DX = 100 * |+DI - -DI| / (+DI + -DI)
ADX = Average of DX over 14 periods
```
Trending = ADX > 25

## 7. Bollinger Bands
```
Middle Band = SMA20 (20-period simple moving average of Close)
Standard Deviation = StdDev of Close over 20 periods
Upper Band = Middle Band + (2 * Standard Deviation)
Lower Band = Middle Band - (2 * Standard Deviation)
BB Width = (Upper - Lower) / Middle
BB Position = (Close - Lower) / (Upper - Lower)
```

## 8. Fibonacci Levels (20-period lookback)
```
Recent High = Max(High over 20 periods)
Recent Low = Min(Low over 20 periods)
Range = Recent High - Recent Low

Fib 0%   = Recent High
Fib 23.6% = Recent High - (Range * 0.236)
Fib 38.2% = Recent High - (Range * 0.382)
Fib 50%   = Recent High - (Range * 0.500)
Fib 61.8% = Recent High - (Range * 0.618)
Fib 78.6% = Recent High - (Range * 0.786)
Fib 100%  = Recent Low

Fib Position = (Recent High - Close) / Range
```

## 9. Structure Score (HH/HL/LH/LL)
```
Swing High = (High > High.shift(1)) AND (High > High.shift(-1))
Swing Low = (Low < Low.shift(1)) AND (Low < Low.shift(-1))

Higher High (HH) = Swing High AND (High > previous Swing High)
Lower High (LH) = Swing High AND (High < previous Swing High)
Higher Low (HL) = Swing Low AND (Low > previous Swing Low)
Lower Low (LL) = Swing Low AND (Low < previous Swing Low)

Structure Score = (HH + HL - LH - LL) / (HH + HL + LH + LL)
```
Rolling window: 10 periods

## 10. Volume Indicators
```
Volume SMA20 = Average Volume over 20 periods
Volume Ratio = Volume / Volume SMA20
Volume Trend = SMA5(Volume) / SMA20(Volume)
```

## 11. Candle Metrics
```
Body Size = |Close - Open|
Upper Wick = High - Max(Open, Close)
Lower Wick = Min(Open, Close) - Low
Range = High - Low
Range % = (Range / Close) * 100
Is Bullish = Close > Open
Consecutive Bullish = Count of consecutive bullish candles
```
