#!/usr/bin/env python3
"""
ETHUSDT 4-Hour Data and Indicators Update Script
获取 ETHUSDT 4小时K线数据并计算技术指标
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
LOG_FILE = DATA_DIR / "update_4h.log"
DATA_FILE = DATA_DIR / "ethusdt_4h.csv"
METRICS_FILE = DATA_DIR / "ethusdt_4h_metrics.json"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Binance API 配置
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "ETHUSDT"
INTERVAL = "4h"
LIMIT = 1000  # 获取最近1000条K线数据

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
    sma = calculate_sma(series, period)
    std = series.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_atr(df, period=14):
    """计算 ATR (Average True Range)"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def calculate_indicators(df):
    """计算所有技术指标"""
    log_message("Calculating technical indicators...")
    
    # EMA
    df['ema_12'] = calculate_ema(df['close'], 12)
    df['ema_26'] = calculate_ema(df['close'], 26)
    df['ema_50'] = calculate_ema(df['close'], 50)
    df['ema_200'] = calculate_ema(df['close'], 200)
    
    # SMA
    df['sma_20'] = calculate_sma(df['close'], 20)
    df['sma_50'] = calculate_sma(df['close'], 50)
    
    # RSI
    df['rsi_14'] = calculate_rsi(df['close'], 14)
    df['rsi_7'] = calculate_rsi(df['close'], 7)
    
    # MACD
    df['macd'], df['macd_signal'], df['macd_histogram'] = calculate_macd(df['close'])
    
    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
    
    # ATR
    df['atr_14'] = calculate_atr(df, 14)
    
    # Volume indicators
    df['volume_sma_20'] = calculate_sma(df['volume'], 20)
    
    log_message("Indicators calculated successfully")
    return df

def save_data(df):
    """保存数据到 CSV"""
    try:
        df.to_csv(DATA_FILE, index=False)
        log_message(f"Data saved to {DATA_FILE}")
        return True
    except Exception as e:
        log_message(f"Error saving data: {e}")
        return False

def calculate_metrics(df):
    """计算当前市场指标摘要"""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "latest_data": {
            "open_time": latest['open_time'].isoformat() if pd.notna(latest['open_time']) else None,
            "open": float(latest['open']) if pd.notna(latest['open']) else None,
            "high": float(latest['high']) if pd.notna(latest['high']) else None,
            "low": float(latest['low']) if pd.notna(latest['low']) else None,
            "close": float(latest['close']) if pd.notna(latest['close']) else None,
            "volume": float(latest['volume']) if pd.notna(latest['volume']) else None,
        },
        "indicators": {
            "rsi_14": float(latest['rsi_14']) if pd.notna(latest['rsi_14']) else None,
            "rsi_7": float(latest['rsi_7']) if pd.notna(latest['rsi_7']) else None,
            "ema_12": float(latest['ema_12']) if pd.notna(latest['ema_12']) else None,
            "ema_26": float(latest['ema_26']) if pd.notna(latest['ema_26']) else None,
            "ema_50": float(latest['ema_50']) if pd.notna(latest['ema_50']) else None,
            "ema_200": float(latest['ema_200']) if pd.notna(latest['ema_200']) else None,
            "sma_20": float(latest['sma_20']) if pd.notna(latest['sma_20']) else None,
            "sma_50": float(latest['sma_50']) if pd.notna(latest['sma_50']) else None,
            "macd": float(latest['macd']) if pd.notna(latest['macd']) else None,
            "macd_signal": float(latest['macd_signal']) if pd.notna(latest['macd_signal']) else None,
            "macd_histogram": float(latest['macd_histogram']) if pd.notna(latest['macd_histogram']) else None,
            "bb_upper": float(latest['bb_upper']) if pd.notna(latest['bb_upper']) else None,
            "bb_middle": float(latest['bb_middle']) if pd.notna(latest['bb_middle']) else None,
            "bb_lower": float(latest['bb_lower']) if pd.notna(latest['bb_lower']) else None,
            "atr_14": float(latest['atr_14']) if pd.notna(latest['atr_14']) else None,
        },
        "trend": {
            "price_change_4h": float(latest['close'] - prev['close']) if pd.notna(prev['close']) else None,
            "price_change_pct": float((latest['close'] - prev['close']) / prev['close'] * 100) if pd.notna(prev['close']) and prev['close'] != 0 else None,
            "above_ema_50": bool(latest['close'] > latest['ema_50']) if pd.notna(latest['ema_50']) else None,
            "above_ema_200": bool(latest['close'] > latest['ema_200']) if pd.notna(latest['ema_200']) else None,
            "macd_bullish": bool(latest['macd'] > latest['macd_signal']) if pd.notna(latest['macd']) and pd.notna(latest['macd_signal']) else None,
        }
    }
    
    return metrics

def save_metrics(metrics):
    """保存指标摘要到 JSON"""
    try:
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        log_message(f"Metrics saved to {METRICS_FILE}")
        return True
    except Exception as e:
        log_message(f"Error saving metrics: {e}")
        return False

def main():
    """主函数"""
    log_message("=" * 50)
    log_message("ETHUSDT 4-Hour Data Update Started")
    log_message("=" * 50)
    
    # 获取数据
    log_message("Fetching klines from Binance...")
    df = fetch_klines()
    
    if df is None or df.empty:
        log_message("ERROR: Failed to fetch data")
        sys.exit(1)
    
    log_message(f"Fetched {len(df)} candles")
    
    # 计算指标
    df = calculate_indicators(df)
    
    # 保存数据
    if not save_data(df):
        sys.exit(1)
    
    # 计算并保存指标摘要
    metrics = calculate_metrics(df)
    if not save_metrics(metrics):
        sys.exit(1)
    
    # 打印摘要
    log_message("-" * 50)
    log_message("Update Summary:")
    log_message(f"  Latest Close: {metrics['latest_data']['close']:.2f} USDT")
    log_message(f"  RSI(14): {metrics['indicators']['rsi_14']:.2f}")
    log_message(f"  MACD: {metrics['indicators']['macd']:.4f}")
    log_message(f"  EMA50: {metrics['indicators']['ema_50']:.2f}")
    log_message(f"  Trend: {'Bullish' if metrics['trend']['macd_bullish'] else 'Bearish'}")
    log_message("=" * 50)
    log_message("Update completed successfully!")
    log_message("=" * 50)

if __name__ == "__main__":
    main()
