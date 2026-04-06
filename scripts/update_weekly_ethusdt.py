#!/usr/bin/env python3
"""
ETHUSDT Weekly Data and Indicators Update Script
获取 ETHUSDT 周线K线数据并计算技术指标
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
import requests

# 配置
DATA_DIR = Path("/root/.openclaw/workspace/data/ethusdt")
LOG_FILE = DATA_DIR / "update_weekly.log"
DATA_FILE = DATA_DIR / "ethusdt_weekly.csv"
METRICS_FILE = DATA_DIR / "ethusdt_weekly_metrics.json"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Binance API 配置
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "ETHUSDT"
INTERVAL = "1w"  # 周线
LIMIT = 500  # 获取最近500条周线数据（约10年）

def log_message(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def fetch_klines():
    """从 Binance 获取 K 线数据"""
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": LIMIT
    }
    
    try:
        response = requests.get(BINANCE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 转换为 DataFrame
        # Binance K线数据格式: [open_time, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_volume, taker_buy_quote_volume, ignore]
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        
        # 转换数据类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 转换时间戳
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # 删除不需要的列
        df = df.drop(columns=['ignore'])
        
        return df
    
    except Exception as e:
        log_message(f"Error fetching klines: {e}")
        return None

def calculate_ema(series, period):
    """计算指数移动平均线"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_sma(series, period):
    """计算简单移动平均线"""
    return series.rolling(window=period).mean()

def calculate_rsi(series, period=14):
    """计算 RSI 指标"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, fast=12, slow=26, signal=9):
    """计算 MACD 指标"""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(series, period=20, std_dev=2):
    """计算布林带"""
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_atr(df, period=14):
    """计算 ATR (Average True Range)"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_indicators(df):
    """计算所有技术指标"""
    # EMA - 周线使用更长的周期
    df['ema_10'] = calculate_ema(df['close'], 10)   # 10周
    df['ema_20'] = calculate_ema(df['close'], 20)   # 20周（约5个月）
    df['ema_50'] = calculate_ema(df['close'], 50)   # 50周（约1年）
    
    # SMA - 周线常用
    df['sma_30'] = calculate_sma(df['close'], 30)   # 30周
    df['sma_52'] = calculate_sma(df['close'], 52)   # 52周（1年）
    
    # RSI
    df['rsi_14'] = calculate_rsi(df['close'], 14)
    
    # MACD - 周线使用标准参数
    df['macd'], df['macd_signal'], df['macd_hist'] = calculate_macd(df['close'])
    
    # 布林带
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # ATR
    df['atr_14'] = calculate_atr(df, 14)
    
    # 成交量指标
    df['volume_sma_10'] = df['volume'].rolling(window=10).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_10']
    
    # 价格变化率 - 周线版本
    df['price_change_1w'] = df['close'].pct_change(1) * 100
    df['price_change_4w'] = df['close'].pct_change(4) * 100  # 月度
    df['price_change_12w'] = df['close'].pct_change(12) * 100  # 季度
    df['price_change_52w'] = df['close'].pct_change(52) * 100  # 年度
    
    return df

def calculate_signals(df):
    """计算交易信号"""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    signals = {
        # EMA 趋势信号
        'ema_trend': 'bullish' if latest['close'] > latest['ema_20'] > latest['ema_50'] else 
                     'bearish' if latest['close'] < latest['ema_20'] < latest['ema_50'] else 'neutral',
        
        # 长期趋势（50周EMA）
        'long_term_trend': 'bullish' if latest['close'] > latest['ema_50'] else 'bearish',
        
        # RSI 信号
        'rsi_signal': 'overbought' if latest['rsi_14'] > 70 else 
                      'oversold' if latest['rsi_14'] < 30 else 'neutral',
        
        # MACD 信号
        'macd_signal': 'bullish_cross' if prev['macd'] < prev['macd_signal'] and latest['macd'] > latest['macd_signal'] else
                       'bearish_cross' if prev['macd'] > prev['macd_signal'] and latest['macd'] < latest['macd_signal'] else
                       'bullish' if latest['macd'] > latest['macd_signal'] else 'bearish',
        
        # 布林带信号
        'bb_signal': 'upper_touch' if latest['close'] >= latest['bb_upper'] else
                     'lower_touch' if latest['close'] <= latest['bb_lower'] else 'middle',
        
        # 成交量信号
        'volume_signal': 'high' if latest['volume_ratio'] > 2 else
                         'low' if latest['volume_ratio'] < 0.5 else 'normal'
    }
    
    return signals

def save_data(df):
    """保存数据到 CSV"""
    try:
        df.to_csv(DATA_FILE, index=False)
        log_message(f"Data saved to {DATA_FILE}")
        return True
    except Exception as e:
        log_message(f"Error saving data: {e}")
        return False

def save_metrics(df, signals):
    """保存指标摘要"""
    try:
        latest = df.iloc[-1]
        
        # 计算年度高点/低点（52周）
        yearly_data = df.tail(52)
        yearly_high = yearly_data['high'].max()
        yearly_low = yearly_data['low'].min()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'symbol': SYMBOL,
            'interval': INTERVAL,
            'current_price': round(float(latest['close']), 2),
            'weekly_change': round(float(latest['price_change_1w']), 4) if not pd.isna(latest['price_change_1w']) else None,
            'monthly_change': round(float(latest['price_change_4w']), 4) if not pd.isna(latest['price_change_4w']) else None,
            'quarterly_change': round(float(latest['price_change_12w']), 4) if not pd.isna(latest['price_change_12w']) else None,
            'yearly_change': round(float(latest['price_change_52w']), 4) if not pd.isna(latest['price_change_52w']) else None,
            'yearly_high': round(float(yearly_high), 2),
            'yearly_low': round(float(yearly_low), 2),
            'indicators': {
                'ema_10': round(float(latest['ema_10']), 2) if not pd.isna(latest['ema_10']) else None,
                'ema_20': round(float(latest['ema_20']), 2) if not pd.isna(latest['ema_20']) else None,
                'ema_50': round(float(latest['ema_50']), 2) if not pd.isna(latest['ema_50']) else None,
                'sma_30': round(float(latest['sma_30']), 2) if not pd.isna(latest['sma_30']) else None,
                'sma_52': round(float(latest['sma_52']), 2) if not pd.isna(latest['sma_52']) else None,
                'rsi_14': round(float(latest['rsi_14']), 2) if not pd.isna(latest['rsi_14']) else None,
                'macd': round(float(latest['macd']), 4) if not pd.isna(latest['macd']) else None,
                'macd_signal': round(float(latest['macd_signal']), 4) if not pd.isna(latest['macd_signal']) else None,
                'macd_hist': round(float(latest['macd_hist']), 4) if not pd.isna(latest['macd_hist']) else None,
                'bb_upper': round(float(latest['bb_upper']), 2) if not pd.isna(latest['bb_upper']) else None,
                'bb_lower': round(float(latest['bb_lower']), 2) if not pd.isna(latest['bb_lower']) else None,
                'bb_position': round(float(latest['bb_position']), 4) if not pd.isna(latest['bb_position']) else None,
                'atr_14': round(float(latest['atr_14']), 2) if not pd.isna(latest['atr_14']) else None,
            },
            'signals': signals,
            'volume': {
                'current': round(float(latest['volume']), 4),
                'sma_10': round(float(latest['volume_sma_10']), 4) if not pd.isna(latest['volume_sma_10']) else None,
                'ratio': round(float(latest['volume_ratio']), 2) if not pd.isna(latest['volume_ratio']) else None
            },
            'data_points': len(df)
        }
        
        with open(METRICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        log_message(f"Metrics saved to {METRICS_FILE}")
        return metrics
    
    except Exception as e:
        log_message(f"Error saving metrics: {e}")
        return None

def main():
    """主函数"""
    log_message("=" * 50)
    log_message("Starting ETHUSDT Weekly Data Update")
    log_message("=" * 50)
    
    # 1. 获取数据
    log_message("Fetching weekly K-line data from Binance...")
    df = fetch_klines()
    
    if df is None or df.empty:
        log_message("ERROR: Failed to fetch data")
        sys.exit(1)
    
    log_message(f"Fetched {len(df)} weekly data points")
    
    # 2. 计算指标
    log_message("Calculating technical indicators...")
    df = calculate_indicators(df)
    
    # 3. 计算信号
    log_message("Generating trading signals...")
    signals = calculate_signals(df)
    
    # 4. 保存数据
    if not save_data(df):
        sys.exit(1)
    
    # 5. 保存指标摘要
    metrics = save_metrics(df, signals)
    
    if metrics:
        log_message("-" * 50)
        log_message(f"Current Price: ${metrics['current_price']}")
        log_message(f"Weekly Change: {metrics['weekly_change']}%")
        log_message(f"Yearly Change: {metrics['yearly_change']}%")
        log_message(f"RSI(14): {metrics['indicators']['rsi_14']}")
        log_message(f"MACD Hist: {metrics['indicators']['macd_hist']}")
        log_message(f"Signals: {signals}")
        log_message("-" * 50)
    
    log_message("Weekly update completed successfully!")
    log_message("")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
