#!/usr/bin/env python3
"""
ETHUSDT Backtesting System
Simulates trading performance on historical data
Starting capital: $1000
Binance Futures fees: 0.02% maker, 0.05% taker
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))

DATA_DIR = Path("/root/.openclaw/workspace/data")
ANALYSIS_DIR = DATA_DIR / "analysis"

@dataclass
class Trade:
    """Represents a single trade"""
    trade_id: str
    direction: str  # LONG or SHORT
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    stop_price: float = 0.0
    target_price: float = 0.0
    position_size: float = 0.0  # in ETH
    position_value: float = 0.0  # in USD
    risk_amount: float = 0.0
    exit_reason: str = ""
    pnl: float = 0.0
    pnl_percent: float = 0.0
    fees: float = 0.0
    r_multiple: float = 0.0

@dataclass
class BacktestConfig:
    """Backtest configuration"""
    initial_capital: float = 1000.0
    maker_fee: float = 0.0002  # 0.02%
    taker_fee: float = 0.0005  # 0.05%
    max_risk_per_trade: float = 2.0  # 2% of account
    min_risk_reward: float = 1.5
    max_concurrent_trades: int = 2
    use_weighted_detection: bool = True
    use_dynamic_rr: bool = True
    use_entry_buffer: bool = True

@dataclass
class BacktestResults:
    """Backtest results summary"""
    config: BacktestConfig = field(default_factory=BacktestConfig)
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    final_capital: float = 0.0
    total_return: float = 0.0
    total_return_percent: float = 0.0
    total_fees: float = 0.0
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)

class BacktestEngine:
    """Main backtesting engine"""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.capital = self.config.initial_capital
        self.peak_capital = self.capital
        self.max_drawdown = 0.0
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.current_trades: Dict[str, Trade] = {}

        # Load all timeframe data
        self.data = self.load_all_data()

    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load historical data for all timeframes"""
        data = {}
        timeframes = ['1M', '1w', '1d', '4h', '1h', '15m', '5m', '1m']

        for tf in timeframes:
            file = DATA_DIR / f"ETHUSDT_{tf}_indicators.csv"
            if file.exists():
                try:
                    df = pd.read_csv(file)
                    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                    data[tf] = df.sort_values('open_time')
                    print(f"  Loaded {tf}: {len(df)} candles")
                except Exception as e:
                    print(f"  Warning: Could not load {tf}: {e}")

        return data

    def calculate_weighted_score(self, timestamp: datetime) -> Dict:
        """Calculate weighted cluster score at specific timestamp"""
        scores = {'macro': 0, 'intermediate': 0, 'execution': 0}

        # Define timeframe to cluster mapping
        clusters = {
            'macro': ['1M', '1w'],
            'intermediate': ['1d', '4h'],
            'execution': ['1h', '15m']
        }

        for cluster_name, tfs in clusters.items():
            cluster_score = 0
            for tf in tfs:
                if tf in self.data:
                    df = self.data[tf]
                    # Find closest candle to timestamp
                    mask = df['open_time'] <= timestamp
                    if mask.any():
                        idx = df[mask].index[-1]
                        row = df.loc[idx]

                        # Simple regime detection
                        ema_bullish = row.get('ema_9', 0) > row.get('ema_21', 0) > row.get('ema_50', 0)
                        if ema_bullish:
                            cluster_score += 1
                        elif row.get('ema_9', 0) < row.get('ema_21', 0) < row.get('ema_50', 0):
                            cluster_score -= 1

            scores[cluster_name] = cluster_score / len(tfs) if tfs else 0

        # Weighted average
        total_score = (scores['macro'] * 0.4 +
                      scores['intermediate'] * 0.35 +
                      scores['execution'] * 0.25)

        direction = 'LONG' if total_score > 0.2 else 'SHORT' if total_score < -0.2 else 'NEUTRAL'

        return {
            'score': total_score,
            'direction': direction,
            'macro': scores['macro'],
            'intermediate': scores['intermediate'],
            'execution': scores['execution']
        }

    def check_entry_signal(self, timestamp: datetime, direction: str) -> Optional[Dict]:
        """Check for entry signal at timestamp"""
        # Use 1h data for entry check
        if '1h' not in self.data:
            return None

        df = self.data['1h']
        mask = df['open_time'] <= timestamp
        if not mask.any():
            return None

        idx = df[mask].index[-1]
        row = df.loc[idx]

        # Basic entry conditions
        if direction == 'LONG':
            # Check for bullish conditions
            if (row.get('rsi', 50) < 70 and
                row.get('ema_9', 0) > row.get('ema_21', 0) and
                row.get('close', 0) > row.get('vwap', row.get('close', 0))):
                return {
                    'price': row['close'],
                    'stop': row.get('support_1', row['close'] * 0.98),
                    'target': row.get('resistance_1', row['close'] * 1.02),
                    'atr': row.get('atr_14', row['close'] * 0.02)
                }
        else:  # SHORT
            if (row.get('rsi', 50) > 30 and
                row.get('ema_9', 0) < row.get('ema_21', 0) and
                row.get('close', 0) < row.get('vwap', row.get('close', 0))):
                return {
                    'price': row['close'],
                    'stop': row.get('resistance_1', row['close'] * 1.02),
                    'target': row.get('support_1', row['close'] * 0.98),
                    'atr': row.get('atr_14', row['close'] * 0.02)
                }

        return None

    def calculate_position_size(self, entry: float, stop: float, direction: str) -> float:
        """Calculate position size based on risk"""
        risk_amount = self.capital * (self.config.max_risk_per_trade / 100)

        if direction == 'LONG':
            risk_per_unit = entry - stop
        else:
            risk_per_unit = stop - entry

        if risk_per_unit <= 0:
            return 0

        units = risk_amount / risk_per_unit
        return units

    def simulate_trade(self, timestamp: datetime, direction: str, setup: Dict) -> Optional[Trade]:
        """Simulate a complete trade"""
        entry_price = setup['price']
        stop_price = setup['stop']
        target_price = setup['target']

        # Check R:R
        if direction == 'LONG':
            risk = entry_price - stop_price
            reward = target_price - entry_price
        else:
            risk = stop_price - entry_price
            reward = entry_price - target_price

        rr_ratio = reward / risk if risk > 0 else 0

        if rr_ratio < self.config.min_risk_reward:
            return None

        # Calculate position size
        position_size = self.calculate_position_size(entry_price, stop_price, direction)
        position_value = position_size * entry_price

        # Entry fee
        entry_fee = position_value * self.config.taker_fee

        # Find exit using 5m or 1h data for detailed simulation
        exit_price = None
        exit_time = None
        exit_reason = ""

        # Simulate forward to find exit
        if '5m' in self.data:
            df = self.data['5m']
            future_mask = df['open_time'] > timestamp
            future_data = df[future_mask].head(288)  # 24 hours of 5m data

            for idx, row in future_data.iterrows():
                high = row['high']
                low = row['low']
                close = row['close']

                if direction == 'LONG':
                    # Check stop loss
                    if low <= stop_price:
                        exit_price = stop_price
                        exit_time = row['open_time']
                        exit_reason = "Stop Loss"
                        break
                    # Check target
                    elif high >= target_price:
                        exit_price = target_price
                        exit_time = row['open_time']
                        exit_reason = "Target"
                        break
                    # Time-based exit (24 hours)
                    elif idx == future_data.index[-1]:
                        exit_price = close
                        exit_time = row['open_time']
                        exit_reason = "Time Exit"
                        break
                else:  # SHORT
                    if high >= stop_price:
                        exit_price = stop_price
                        exit_time = row['open_time']
                        exit_reason = "Stop Loss"
                        break
                    elif low <= target_price:
                        exit_price = target_price
                        exit_time = row['open_time']
                        exit_reason = "Target"
                        break
                    elif idx == future_data.index[-1]:
                        exit_price = close
                        exit_time = row['open_time']
                        exit_reason = "Time Exit"
                        break

        if exit_price is None or exit_time is None:
            return None

        # Calculate PnL
        if direction == 'LONG':
            pnl = (exit_price - entry_price) * position_size
        else:
            pnl = (entry_price - exit_price) * position_size

        # Calculate fees
        exit_value = position_size * exit_price
        exit_fee = exit_value * self.config.taker_fee
        total_fees = entry_fee + exit_fee

        # Net PnL
        net_pnl = pnl - total_fees
        pnl_percent = (net_pnl / position_value) * 100 if position_value > 0 else 0

        # R multiple
        r_multiple = pnl / (position_size * risk) if risk > 0 and position_size > 0 else 0

        trade = Trade(
            trade_id=f"BT_{timestamp.strftime('%Y%m%d_%H%M')}",
            direction=direction,
            entry_time=timestamp,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            stop_price=stop_price,
            target_price=target_price,
            position_size=position_size,
            position_value=position_value,
            risk_amount=self.capital * (self.config.max_risk_per_trade / 100),
            exit_reason=exit_reason,
            pnl=net_pnl,
            pnl_percent=pnl_percent,
            fees=total_fees,
            r_multiple=r_multiple
        )

        # Update capital
        self.capital += net_pnl

        # Update max drawdown
        if self.capital > self.peak_capital:
            self.peak_capital = self.capital
        else:
            drawdown = self.peak_capital - self.capital
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown

        return trade

    def run_backtest(self, start_date: datetime = None, end_date: datetime = None) -> BacktestResults:
        """Run complete backtest"""
        print("="*70)
        print("ETHUSDT BACKTEST - Starting")
        print("="*70)
        print(f"Initial Capital: ${self.config.initial_capital:,.2f}")
        print(f"Maker Fee: {self.config.maker_fee*100:.3f}%")
        print(f"Taker Fee: {self.config.taker_fee*100:.3f}%")
        print(f"Max Risk/Trade: {self.config.max_risk_per_trade}%")
        print("="*70)

        # Determine date range from data
        if '1h' in self.data:
            df = self.data['1h']
            if start_date is None:
                start_date = df['open_time'].min()
            if end_date is None:
                end_date = df['open_time'].max()

        print(f"\nBacktest Period: {start_date} to {end_date}")

        # Iterate through 1h candles
        if '1h' not in self.data:
            print("Error: No 1h data available")
            return None

        df_1h = self.data['1h']
        date_mask = (df_1h['open_time'] >= start_date) & (df_1h['open_time'] <= end_date)
        df_period = df_1h[date_mask]

        print(f"Processing {len(df_period)} hours...")

        # Check for signals every 4 hours (to avoid over-trading)
        check_interval = 4
        last_check_idx = -check_interval

        for idx, row in df_period.iterrows():
            timestamp = row['open_time']

            # Record equity
            self.equity_curve.append((timestamp, self.capital))

            # Check for new signal every 4 hours
            if len(self.equity_curve) - last_check_idx >= check_interval:
                last_check_idx = len(self.equity_curve)

                # Calculate weighted score
                score_data = self.calculate_weighted_score(timestamp)

                # Check if we have a valid setup
                if score_data['direction'] != 'NEUTRAL' and len(self.current_trades) < self.config.max_concurrent_trades:
                    # Check for entry
                    entry_setup = self.check_entry_signal(timestamp, score_data['direction'])

                    if entry_setup:
                        # Simulate trade
                        trade = self.simulate_trade(timestamp, score_data['direction'], entry_setup)

                        if trade:
                            self.trades.append(trade)
                            print(f"\n  Trade: {trade.trade_id}")
                            print(f"    Direction: {trade.direction}")
                            print(f"    Entry: ${trade.entry_price:.2f}")
                            print(f"    Exit: ${trade.exit_price:.2f} ({trade.exit_reason})")
                            print(f"    PnL: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%) | R: {trade.r_multiple:.2f}")
                            print(f"    Capital: ${self.capital:.2f}")

        # Calculate results
        return self.calculate_results(start_date, end_date)

    def calculate_results(self, start_date: datetime, end_date: datetime) -> BacktestResults:
        """Calculate final backtest results"""
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        losing_trades = total_trades - winning_trades

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        total_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        total_loss = sum(abs(t.pnl) for t in self.trades if t.pnl < 0)
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')

        avg_profit = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = total_loss / losing_trades if losing_trades > 0 else 0

        total_fees = sum(t.fees for t in self.trades)

        total_return = self.capital - self.config.initial_capital
        total_return_percent = (total_return / self.config.initial_capital) * 100

        max_drawdown_percent = (self.max_drawdown / self.peak_capital) * 100 if self.peak_capital > 0 else 0

        return BacktestResults(
            config=self.config,
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=self.max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            final_capital=self.capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            total_fees=total_fees,
            trades=self.trades,
            equity_curve=self.equity_curve
        )

def print_results(results: BacktestResults):
    """Print backtest results"""
    print("\n" + "="*70)
    print("BACKTEST RESULTS")
    print("="*70)
    print(f"\nPeriod: {results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}")
    print(f"\nCapital:")
    print(f"  Initial: ${results.config.initial_capital:,.2f}")
    print(f"  Final: ${results.final_capital:,.2f}")
    print(f"  Total Return: ${results.total_return:,.2f} ({results.total_return_percent:+.2f}%)")

    print(f"\nTrades:")
    print(f"  Total: {results.total_trades}")
    print(f"  Winners: {results.winning_trades} ({results.win_rate:.1f}%)")
    print(f"  Losers: {results.losing_trades}")
    print(f"  Avg Profit: ${results.avg_profit:.2f}")
    print(f"  Avg Loss: ${results.avg_loss:.2f}")
    print(f"  Profit Factor: {results.profit_factor:.2f}")

    print(f"\nRisk Metrics:")
    print(f"  Max Drawdown: ${results.max_drawdown:.2f} ({results.max_drawdown_percent:.2f}%)")
    print(f"  Total Fees: ${results.total_fees:.2f}")

    # Show top 5 trades
    if results.trades:
        print(f"\nTop 5 Winning Trades:")
        sorted_trades = sorted(results.trades, key=lambda x: x.pnl, reverse=True)
        for i, trade in enumerate(sorted_trades[:5], 1):
            print(f"  {i}. {trade.trade_id}: ${trade.pnl:+.2f} ({trade.pnl_percent:+.2f}%)")

        print(f"\nWorst 5 Losing Trades:")
        for i, trade in enumerate(sorted_trades[-5:], 1):
            print(f"  {i}. {trade.trade_id}: ${trade.pnl:+.2f} ({trade.pnl_percent:+.2f}%)")

    print("\n" + "="*70)

def main():
    """Run backtest"""
    # Configuration
    config = BacktestConfig(
        initial_capital=1000.0,
        maker_fee=0.0002,
        taker_fee=0.0005,
        max_risk_per_trade=2.0,
        min_risk_reward=1.5
    )

    # Create engine
    engine = BacktestEngine(config)

    # Run backtest
    results = engine.run_backtest()

    if results:
        print_results(results)

        # Save results
        results_file = DATA_DIR / f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

        # Convert to dict for JSON
        results_dict = {
            'config': {
                'initial_capital': results.config.initial_capital,
                'maker_fee': results.config.maker_fee,
                'taker_fee': results.config.taker_fee,
                'max_risk_per_trade': results.config.max_risk_per_trade
            },
            'start_date': results.start_date.isoformat(),
            'end_date': results.end_date.isoformat(),
            'total_trades': results.total_trades,
            'winning_trades': results.winning_trades,
            'losing_trades': results.losing_trades,
            'win_rate': results.win_rate,
            'avg_profit': results.avg_profit,
            'avg_loss': results.avg_loss,
            'profit_factor': results.profit_factor,
            'max_drawdown': results.max_drawdown,
            'max_drawdown_percent': results.max_drawdown_percent,
            'final_capital': results.final_capital,
            'total_return': results.total_return,
            'total_return_percent': results.total_return_percent,
            'total_fees': results.total_fees,
            'trades': [
                {
                    'trade_id': t.trade_id,
                    'direction': t.direction,
                    'entry_time': t.entry_time.isoformat() if t.entry_time else None,
                    'entry_price': t.entry_price,
                    'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                    'exit_price': t.exit_price,
                    'exit_reason': t.exit_reason,
                    'pnl': t.pnl,
                    'pnl_percent': t.pnl_percent,
                    'fees': t.fees,
                    'r_multiple': t.r_multiple
                }
                for t in results.trades
            ]
        }

        with open(results_file, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    main()
