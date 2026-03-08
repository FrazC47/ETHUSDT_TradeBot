#!/usr/bin/env python3
"""
Trade Forensics Agent
Analyzes every trade to understand WHY it won or lost
"""

import pandas as pd
import numpy as np
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

class TradeForensicsAgent:
    """
    Analyzes individual trades to determine causality:
    - Why did this trade win?
    - Why did this trade lose?
    - What market conditions preceded the outcome?
    - Which indicators were predictive?
    """
    
    def __init__(self, task_file=None):
        self.base_dir = Path("/root/.openclaw/workspace")
        self.data_dir = self.base_dir / "data" / "indicators"
        self.forensics_dir = self.base_dir / "forensics"
        self.log_file = self.base_dir / "logs" / f"forensics_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.forensics_dir.mkdir(parents=True, exist_ok=True)
        self.task = self.load_task(task_file) if task_file else None
        
        # Forensics categories
        self.loss_reasons = [
            "EARLY_STOP_HIT",      # Stop triggered before setup matured
            "TREND_REVERSAL",      # Major trend changed direction
            "FALSE_BREAKOUT",      # Price broke level then reversed
            "LOW_VOLUME",          # Not enough volume for move
            "NEWS_EVENT",          # Unexpected news/volatility
            "CHOPPY_MARKET",       # No clear direction
            "LATE_ENTRY",          # Entered after optimal point
            "STRUCTURE_BREAK",     # Key support/resistance broke
        ]
        
        self.win_reasons = [
            "STRONG_TREND",        # Clear trend in trade direction
            "PERFECT_ENTRY",       # Entry at optimal Fib level
            "VOLUME_CONFIRMATION", # High volume supporting move
            "MULTI_TF_CONFLUENCE", # All timeframes aligned
            "MOMENTUM_CARRY",      # Strong momentum continuation
            "BREAKOUT_SUCCESS",    # Clean breakout and follow-through
        ]
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [FORENSICS_AGENT] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_task(self, task_file):
        with open(task_file) as f:
            return json.load(f)
    
    def analyze_trade(self, trade: Dict) -> Dict:
        """
        Deep analysis of a single trade
        trade = {
            'entry_time': timestamp,
            'exit_time': timestamp,
            'direction': 'LONG'/'SHORT',
            'entry_price': float,
            'exit_price': float,
            'result': 'WIN'/'LOSS',
            'timeframe': '1h',
            'confirmations': [...]
        }
        """
        self.log(f"Analyzing trade: {trade.get('direction')} {trade.get('result')}")
        
        entry_time = pd.to_datetime(trade['entry_time'])
        exit_time = pd.to_datetime(trade['exit_time'])
        
        # Load market conditions at entry
        entry_conditions = self.get_market_conditions(entry_time)
        
        # Load market conditions at exit
        exit_conditions = self.get_market_conditions(exit_time)
        
        # Analyze price action between entry and exit
        price_action = self.analyze_price_action(
            entry_time, exit_time, 
            trade['direction'], 
            trade['entry_price'],
            trade.get('stop_loss'),
            trade.get('take_profit')
        )
        
        # Determine root cause
        if trade['result'] == 'WIN':
            root_cause = self.determine_win_reason(
                entry_conditions, price_action, trade
            )
        else:
            root_cause = self.determine_loss_reason(
                entry_conditions, price_action, trade
            )
        
        forensics_report = {
            'trade_id': trade.get('id', f"trade_{datetime.now().timestamp()}"),
            'timestamp': datetime.now().isoformat(),
            'trade_summary': {
                'direction': trade['direction'],
                'result': trade['result'],
                'entry': trade['entry_price'],
                'exit': trade['exit_price'],
                'pnl_pct': trade.get('pnl_pct', 0),
                'duration_hours': (exit_time - entry_time).total_seconds() / 3600
            },
            'entry_conditions': entry_conditions,
            'exit_conditions': exit_conditions,
            'price_action': price_action,
            'root_cause': root_cause,
            'lessons_learned': self.extract_lessons(root_cause, trade),
            'signal_quality_score': self.calculate_signal_quality(entry_conditions, trade)
        }
        
        return forensics_report
    
    def get_market_conditions(self, timestamp) -> Dict:
        """Get comprehensive market conditions at specific time"""
        conditions = {}
        
        for tf in ['1d', '4h', '1h']:
            try:
                df = pd.read_csv(self.data_dir / f"{tf}_indicators.csv")
                df['open_time'] = pd.to_datetime(df['open_time'])
                
                # Find closest candle
                mask = df['open_time'] <= timestamp
                if mask.any():
                    row = df[mask].iloc[-1]
                    conditions[tf] = {
                        'trend': self.classify_trend(row),
                        'rsi': row.get('rsi_14', 50),
                        'macd_hist': row.get('macd_hist', 0),
                        'adx': row.get('adx', 25),
                        'volume_ratio': row.get('volume_ratio', 1.0),
                        'bb_position': row.get('bb_position', 0.5),
                        'atr': row.get('atr_14', 0),
                        'price': row['close']
                    }
            except Exception as e:
                self.log(f"Error loading {tf} data: {e}")
        
        return conditions
    
    def classify_trend(self, row) -> str:
        """Classify trend strength"""
        close = row['close']
        ema9 = row.get('ema_9', close)
        ema21 = row.get('ema_21', close)
        ema50 = row.get('ema_50', close)
        adx = row.get('adx', 25)
        
        if adx < 20:
            return "RANGING"
        
        if close > ema9 > ema21 > ema50:
            return "STRONG_UPTREND" if adx > 30 else "UPTREND"
        elif close < ema9 < ema21 < ema50:
            return "STRONG_DOWNTREND" if adx > 30 else "DOWNTREND"
        else:
            return "MIXED"
    
    def analyze_price_action(self, entry_time, exit_time, direction, entry, stop, target) -> Dict:
        """Analyze what price did during the trade"""
        try:
            df = pd.read_csv(self.data_dir / "1h_indicators.csv")
            df['open_time'] = pd.to_datetime(df['open_time'])
            
            # Filter to trade duration
            mask = (df['open_time'] >= entry_time) & (df['open_time'] <= exit_time)
            trade_data = df[mask]
            
            if len(trade_data) == 0:
                return {}
            
            analysis = {
                'max_favorable_excursion': 0,
                'max_adverse_excursion': 0,
                'candles_in_trade': len(trade_data),
                'volume_avg': trade_data['volume'].mean(),
                'volatility_avg': trade_data.get('atr_14', pd.Series([0])).mean()
            }
            
            if direction == "LONG":
                analysis['max_favorable_excursion'] = ((trade_data['high'].max() - entry) / entry) * 100
                analysis['max_adverse_excursion'] = ((entry - trade_data['low'].min()) / entry) * 100
            else:
                analysis['max_favorable_excursion'] = ((entry - trade_data['low'].min()) / entry) * 100
                analysis['max_adverse_excursion'] = ((trade_data['high'].max() - entry) / entry) * 100
            
            return analysis
            
        except Exception as e:
            self.log(f"Error in price action analysis: {e}")
            return {}
    
    def determine_loss_reason(self, entry_conditions, price_action, trade) -> Dict:
        """Determine why a trade lost"""
        reasons = []
        confidence = 0
        
        h1 = entry_conditions.get('1h', {})
        
        # Check ADX (trend strength)
        if h1.get('adx', 25) < 20:
            reasons.append("CHOPPY_MARKET")
            confidence += 25
        
        # Check if stop was hit quickly
        if price_action.get('candles_in_trade', 10) < 5:
            reasons.append("EARLY_STOP_HIT")
            confidence += 20
        
        # Check volume
        if h1.get('volume_ratio', 1.0) < 0.8:
            reasons.append("LOW_VOLUME")
            confidence += 15
        
        # Check if price went in favor first
        mfe = price_action.get('max_favorable_excursion', 0)
        mae = price_action.get('max_adverse_excursion', 0)
        
        if mfe > 0.5:  # Price went 0.5% in favor before stopping out
            reasons.append("FALSE_BREAKOUT")
            confidence += 20
        
        # RSI divergence check
        if h1.get('rsi', 50) > 70 and trade['direction'] == "LONG":
            reasons.append("LATE_ENTRY")
            confidence += 15
        elif h1.get('rsi', 50) < 30 and trade['direction'] == "SHORT":
            reasons.append("LATE_ENTRY")
            confidence += 15
        
        # Default reason if nothing else fits
        if not reasons:
            reasons.append("TREND_REVERSAL")
            confidence = 30
        
        return {
            'primary_reason': reasons[0] if reasons else "UNKNOWN",
            'all_reasons': reasons,
            'confidence': min(confidence, 100),
            'prevention_suggestion': self.get_prevention_suggestion(reasons[0]) if reasons else "Review setup criteria"
        }
    
    def determine_win_reason(self, entry_conditions, price_action, trade) -> Dict:
        """Determine why a trade won"""
        reasons = []
        confidence = 0
        
        h1 = entry_conditions.get('1h', {})
        d1 = entry_conditions.get('1d', {})
        
        # Strong trend alignment
        if h1.get('adx', 25) > 30:
            reasons.append("STRONG_TREND")
            confidence += 30
        
        # Volume confirmation
        if h1.get('volume_ratio', 1.0) > 1.5:
            reasons.append("VOLUME_CONFIRMATION")
            confidence += 20
        
        # Multi-timeframe confluence
        if d1 and h1:
            if d1.get('trend') in ['STRONG_UPTREND', 'UPTREND'] and trade['direction'] == "LONG":
                reasons.append("MULTI_TF_CONFLUENCE")
                confidence += 25
            elif d1.get('trend') in ['STRONG_DOWNTREND', 'DOWNTREND'] and trade['direction'] == "SHORT":
                reasons.append("MULTI_TF_CONFLUENCE")
                confidence += 25
        
        # Clean price action
        mae = price_action.get('max_adverse_excursion', 1)
        if mae < 0.5:  # Small drawdown
            reasons.append("PERFECT_ENTRY")
            confidence += 15
        
        # Default
        if not reasons:
            reasons.append("MOMENTUM_CARRY")
            confidence = 30
        
        return {
            'primary_reason': reasons[0] if reasons else "UNKNOWN",
            'all_reasons': reasons,
            'confidence': min(confidence, 100),
            'replication_suggestion': self.get_replication_suggestion(reasons[0]) if reasons else "Follow same criteria"
        }
    
    def get_prevention_suggestion(self, reason: str) -> str:
        """Get suggestion for preventing this loss type"""
        suggestions = {
            "EARLY_STOP_HIT": "Wait for 1-2 candle confirmation before entry",
            "TREND_REVERSAL": "Check higher timeframe trend alignment",
            "FALSE_BREAKOUT": "Require ADX > 25 for breakout entries",
            "LOW_VOLUME": "Skip trades with volume_ratio < 1.0",
            "CHOPPY_MARKET": "Avoid trading when ADX < 20",
            "LATE_ENTRY": "Enter on pullbacks, not extensions",
            "STRUCTURE_BREAK": "Monitor key S/R levels more closely"
        }
        return suggestions.get(reason, "Review setup criteria")
    
    def get_replication_suggestion(self, reason: str) -> str:
        """Get suggestion for replicating this win"""
        suggestions = {
            "STRONG_TREND": "Only trade when ADX > 30",
            "PERFECT_ENTRY": "Wait for price to touch key level",
            "VOLUME_CONFIRMATION": "Require volume_ratio > 1.5",
            "MULTI_TF_CONFLUENCE": "Ensure 3+ timeframes align",
            "MOMENTUM_CARRY": "Enter on momentum confirmation"
        }
        return suggestions.get(reason, "Follow same criteria")
    
    def extract_lessons(self, root_cause: Dict, trade: Dict) -> List[str]:
        """Extract actionable lessons from trade"""
        lessons = []
        
        if trade['result'] == 'LOSS':
            lessons.append(f"Avoid {root_cause['primary_reason']} setups")
            if root_cause.get('prevention_suggestion'):
                lessons.append(root_cause['prevention_suggestion'])
        else:
            lessons.append(f"Seek {root_cause['primary_reason']} setups")
            if root_cause.get('replication_suggestion'):
                lessons.append(root_cause['replication_suggestion'])
        
        return lessons
    
    def calculate_signal_quality(self, entry_conditions: Dict, trade: Dict) -> float:
        """Calculate quality score (0-100) for the signal"""
        score = 50  # Base score
        
        h1 = entry_conditions.get('1h', {})
        
        # Trend alignment
        if h1.get('adx', 25) > 30:
            score += 15
        elif h1.get('adx', 25) > 20:
            score += 5
        else:
            score -= 10
        
        # Volume
        if h1.get('volume_ratio', 1.0) > 1.5:
            score += 10
        elif h1.get('volume_ratio', 1.0) < 0.8:
            score -= 10
        
        # RSI (avoid extremes)
        rsi = h1.get('rsi', 50)
        if 40 < rsi < 60:
            score += 5
        elif rsi > 75 or rsi < 25:
            score -= 15
        
        # MACD
        if abs(h1.get('macd_hist', 0)) > 0.5:
            score += 5
        
        return max(0, min(100, score))
    
    def execute_task(self):
        """Execute assigned task"""
        if not self.task:
            self.log("No task assigned")
            return False
        
        task_name = self.task.get('task')
        params = self.task.get('params', {})
        
        self.log(f"Executing: {task_name}")
        
        if task_name == "analyze_trade":
            trade = params.get('trade', {})
            result = self.analyze_trade(trade)
            
            # Save forensics report
            report_file = self.forensics_dir / f"forensics_{trade.get('id', 'unknown')}.json"
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            self.log(f"Forensics report saved: {report_file}")
            return True
        
        elif task_name == "batch_analyze":
            trades = params.get('trades', [])
            self.log(f"Batch analyzing {len(trades)} trades")
            
            for trade in trades:
                result = self.analyze_trade(trade)
                report_file = self.forensics_dir / f"forensics_{trade.get('id', 'unknown')}.json"
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2)
            
            return True
        
        return True

def main():
    task_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = TradeForensicsAgent(task_file)
    
    if task_file:
        agent.execute_task()
    else:
        agent.log("Trade Forensics Agent ready")
        agent.log("Usage: python forensics_agent.py <task_file.json>")

if __name__ == "__main__":
    main()
