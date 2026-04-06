#!/usr/bin/env python3
"""
ETHUSDT Comprehensive Trade Logger
Logs every trade with full detail for future analysis
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

DATA_DIR = Path("/root/.openclaw/workspace/data")
TRADE_LOG_CSV = DATA_DIR / "trade_log.csv"
TRADE_LOG_JSON = DATA_DIR / "trade_log.json"

@dataclass
class TradeRecord:
    """Complete trade record for analysis"""
    # Trade Identification
    trade_number: int
    trade_id: str
    timestamp: str
    
    # Trade Details
    symbol: str
    direction: str
    entry_date: str
    entry_time: str
    exit_date: str
    exit_time: str
    
    # Prices
    entry_price: float
    stop_price: float
    target_price: float
    exit_price: float
    
    # Position
    position_size: float
    position_value: float
    leverage: int
    
    # Risk
    risk_amount: float
    risk_percent: float
    
    # PnL
    gross_pnl: float
    fees: float
    net_pnl: float
    pnl_percent: float
    r_multiple: float
    
    # Exit
    exit_reason: str
    time_in_trade: str
    
    # Signal Context
    confluence_count: int
    confidence: float
    regime: str
    weighted_score: float
    
    # Market Context
    atr_14: float
    rsi: float
    trend: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_csv_row(self) -> List:
        return [
            self.trade_number,
            self.trade_id,
            self.timestamp,
            self.symbol,
            self.direction,
            self.entry_date,
            self.entry_time,
            self.exit_date,
            self.exit_time,
            self.entry_price,
            self.stop_price,
            self.target_price,
            self.exit_price,
            self.position_size,
            self.position_value,
            self.leverage,
            self.risk_amount,
            self.risk_percent,
            self.gross_pnl,
            self.fees,
            self.net_pnl,
            self.pnl_percent,
            self.r_multiple,
            self.exit_reason,
            self.time_in_trade,
            self.confluence_count,
            self.confidence,
            self.regime,
            self.weighted_score,
            self.atr_14,
            self.rsi,
            self.trend
        ]

class TradeLogger:
    """Logs all trades in multiple formats for analysis"""
    
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self.load_existing()
    
    def load_existing(self):
        """Load existing trades from log"""
        if TRADE_LOG_JSON.exists():
            with open(TRADE_LOG_JSON, 'r') as f:
                data = json.load(f)
                self.trades = [TradeRecord(**t) for t in data.get('trades', [])]
    
    def log_trade(self, trade: TradeRecord):
        """Log a new trade"""
        # Assign trade number
        trade.trade_number = len(self.trades) + 1
        trade.timestamp = datetime.now().isoformat()
        
        self.trades.append(trade)
        self._save_json()
        self._save_csv()
        
        print(f"✅ Trade #{trade.trade_number} logged: {trade.trade_id}")
    
    def _save_json(self):
        """Save to JSON"""
        with open(TRADE_LOG_JSON, 'w') as f:
            json.dump({
                'last_updated': datetime.now().isoformat(),
                'total_trades': len(self.trades),
                'trades': [t.to_dict() for t in self.trades]
            }, f, indent=2, default=str)
    
    def _save_csv(self):
        """Save to CSV"""
        headers = [
            'trade_number', 'trade_id', 'timestamp', 'symbol', 'direction',
            'entry_date', 'entry_time', 'exit_date', 'exit_time',
            'entry_price', 'stop_price', 'target_price', 'exit_price',
            'position_size', 'position_value', 'leverage',
            'risk_amount', 'risk_percent',
            'gross_pnl', 'fees', 'net_pnl', 'pnl_percent', 'r_multiple',
            'exit_reason', 'time_in_trade',
            'confluence_count', 'confidence', 'regime', 'weighted_score',
            'atr_14', 'rsi', 'trend'
        ]
        
        with open(TRADE_LOG_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for trade in self.trades:
                writer.writerow(trade.to_csv_row())
    
    def print_comparison_table(self, num_trades: int = 20):
        """Print formatted trade comparison table"""
        print("\n" + "="*120)
        print(f"  TRADE LOG - First {min(num_trades, len(self.trades))} Trades")
        print("="*120)
        print()
        
        print(f"{'#':<4} {'ID':<12} {'Date':<10} {'Time':<8} {'Dir':<5} {'Entry':<8} {'Stop':<8} {'Target':<8} {'Exit':<8} {'PnL':<10} {'R':<5} {'Exit Type':<12} {'Conf':<5}")
        print("-"*120)
        
        for trade in self.trades[:num_trades]:
            print(f"{trade.trade_number:<4} {trade.trade_id:<12} {trade.entry_date:<10} {trade.entry_time:<8} "
                  f"{trade.direction:<5} ${trade.entry_price:<7.0f} ${trade.stop_price:<7.0f} "
                  f"${trade.target_price:<7.0f} ${trade.exit_price:<7.0f} "
                  f"${trade.net_pnl:>+8.2f} {trade.r_multiple:<5.2f} "
                  f"{trade.exit_reason:<12} {trade.confidence:<5.0f}%")
        
        print()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive trade report"""
        if not self.trades:
            return {'error': 'No trades logged'}
        
        total_trades = len(self.trades)
        wins = len([t for t in self.trades if t.net_pnl > 0])
        losses = total_trades - wins
        
        total_pnl = sum(t.net_pnl for t in self.trades)
        total_fees = sum(t.fees for t in self.trades)
        
        win_trades = [t for t in self.trades if t.net_pnl > 0]
        loss_trades = [t for t in self.trades if t.net_pnl <= 0]
        
        avg_win = sum(t.net_pnl for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = sum(t.net_pnl for t in loss_trades) / len(loss_trades) if loss_trades else 0
        
        avg_r_win = sum(t.r_multiple for t in win_trades) / len(win_trades) if win_trades else 0
        avg_r_loss = sum(t.r_multiple for t in loss_trades) / len(loss_trades) if loss_trades else 0
        
        # Calculate max drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        for trade in self.trades:
            cumulative += trade.net_pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        return {
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': (wins / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'avg_winner': avg_win,
            'avg_loser': avg_loss,
            'avg_r_winner': avg_r_win,
            'avg_r_loser': avg_r_loss,
            'max_drawdown': max_dd,
            'profit_factor': abs(sum(t.net_pnl for t in win_trades) / sum(t.net_pnl for t in loss_trades)) if loss_trades else float('inf'),
            'avg_trade': total_pnl / total_trades if total_trades > 0 else 0,
            ' expectancy': total_pnl / total_trades if total_trades > 0 else 0
        }

def main():
    """Demo the trade logger"""
    logger = TradeLogger()
    
    print("="*70)
    print("  TRADE LOGGER DEMONSTRATION")
    print("="*70)
    print()
    print("This system will log every trade with:")
    print("  ✓ Trade number and ID")
    print("  ✓ Entry/exit dates and times")
    print("  ✓ Entry, stop, target, exit prices")
    print("  ✓ Position size and leverage")
    print("  ✓ Risk amount and percentage")
    print("  ✓ Gross PnL, fees, net PnL")
    print("  ✓ R-multiple achieved")
    print("  ✓ Exit reason")
    print("  ✓ Signal confidence and regime")
    print()
    
    if logger.trades:
        logger.print_comparison_table()
        report = logger.generate_report()
        print("\nREPORT:")
        for key, value in report.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
    else:
        print("No trades logged yet.")
        print("Trades will be logged automatically when system executes.")
    
    print()
    print("Files created:")
    print(f"  JSON: {TRADE_LOG_JSON}")
    print(f"  CSV:  {TRADE_LOG_CSV}")

if __name__ == "__main__":
    main()
