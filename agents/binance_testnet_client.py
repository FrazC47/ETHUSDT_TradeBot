#!/usr/bin/env python3
"""
Binance Futures Testnet Client
Execute paper trades on Binance testnet (NO REAL MONEY)
"""

import requests
import hmac
import hashlib
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import os

class BinanceTestnetClient:
    """
    Client for Binance Futures Testnet (paper trading)
    
    ⚠️  THIS IS TESTNET ONLY - NO REAL MONEY
    Uses fake funds for practice trading
    """
    
    def __init__(self):
        self.base_url = "https://testnet.binancefuture.com"
        self.api_key = os.getenv('BINANCE_TESTNET_API_KEY')
        self.api_secret = os.getenv('BINANCE_TESTNET_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Missing testnet API credentials.\n"
                "Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_SECRET\n"
                "Get them from: https://testnet.binancefuture.com"
            )
        
        self.symbol = "ETHUSDT"
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key
        })
        
        # Logging
        self.trade_log = Path("/root/.openclaw/workspace/logs/testnet_trades.log")
        self.trade_log.parent.mkdir(parents=True, exist_ok=True)
        
        self._verify_connection()
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC signature for API request"""
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make API request to testnet"""
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, data=params)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self._log_error(f"API request failed: {e}")
            raise
    
    def _verify_connection(self):
        """Verify connection to testnet"""
        try:
            account = self.get_account_info()
            print(f"✅ Connected to Binance Testnet")
            print(f"   Account Type: {account.get('accountType', 'Unknown')}")
            print(f"   Can Trade: {account.get('canTrade', False)}")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    def _log_trade(self, message: str):
        """Log trade to file"""
        timestamp = datetime.now().isoformat()
        with open(self.trade_log, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[TESTNET] {message}")
    
    def _log_error(self, message: str):
        """Log error"""
        self._log_trade(f"ERROR: {message}")
    
    # ============== ACCOUNT INFO ==============
    
    def get_account_info(self) -> Dict:
        """Get testnet account information"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_balance(self, asset: str = "USDT") -> float:
        """Get balance for specific asset"""
        account = self.get_account_info()
        for balance in account.get('assets', []):
            if balance['asset'] == asset:
                return float(balance['availableBalance'])
        return 0.0
    
    def get_position(self, symbol: str = None) -> Optional[Dict]:
        """Get current position"""
        symbol = symbol or self.symbol
        params = {'symbol': symbol}
        positions = self._make_request('GET', '/fapi/v2/positionRisk', params, signed=True)
        
        for pos in positions:
            if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                return pos
        return None
    
    # ============== MARKET DATA ==============
    
    def get_symbol_price(self, symbol: str = None) -> float:
        """Get current mark price"""
        symbol = symbol or self.symbol
        params = {'symbol': symbol}
        response = self._make_request('GET', '/fapi/v1/premiumIndex', params)
        return float(response['markPrice'])
    
    def get_klines(self, symbol: str = None, interval: str = '1h', limit: int = 100) -> List:
        """Get candlestick data"""
        symbol = symbol or self.symbol
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/klines', params)
    
    # ============== ORDER EXECUTION ==============
    
    def place_market_order(self, side: str, quantity: float, 
                          stop_loss: float = None, 
                          take_profit: float = None) -> Dict:
        """
        Place market order on testnet
        
        Args:
            side: 'BUY' (long) or 'SELL' (short)
            quantity: Position size in ETH
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
        """
        params = {
            'symbol': self.symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity,
        }
        
        # Add stop loss
        if stop_loss:
            params['stopPrice'] = stop_loss
            params['type'] = 'STOP_MARKET'
        
        response = self._make_request('POST', '/fapi/v1/order', params, signed=True)
        
        self._log_trade(
            f"MARKET ORDER: {side} {quantity} ETH @ Market | "
            f"Order ID: {response.get('orderId')} | "
            f"Status: {response.get('status')}"
        )
        
        # Place take profit if specified
        if take_profit:
            self._place_take_profit(side, quantity, take_profit)
        
        return response
    
    def _place_take_profit(self, side: str, quantity: float, price: float):
        """Place take profit order"""
        tp_side = 'SELL' if side == 'BUY' else 'BUY'
        params = {
            'symbol': self.symbol,
            'side': tp_side,
            'type': 'TAKE_PROFIT_MARKET',
            'stopPrice': price,
            'quantity': quantity,
            'reduceOnly': 'true'
        }
        
        response = self._make_request('POST', '/fapi/v1/order', params, signed=True)
        
        self._log_trade(
            f"TAKE PROFIT: {tp_side} @ {price} | Order ID: {response.get('orderId')}"
        )
        
        return response
    
    def place_stop_loss(self, side: str, quantity: float, stop_price: float) -> Dict:
        """Place stop loss order"""
        sl_side = 'SELL' if side == 'BUY' else 'BUY'
        params = {
            'symbol': self.symbol,
            'side': sl_side,
            'type': 'STOP_MARKET',
            'stopPrice': stop_price,
            'quantity': quantity,
            'reduceOnly': 'true'
        }
        
        response = self._make_request('POST', '/fapi/v1/order', params, signed=True)
        
        self._log_trade(
            f"STOP LOSS: {sl_side} @ {stop_price} | Order ID: {response.get('orderId')}"
        )
        
        return response
    
    def close_position(self, symbol: str = None) -> Dict:
        """Close all positions for symbol"""
        symbol = symbol or self.symbol
        position = self.get_position(symbol)
        
        if not position:
            self._log_trade("No position to close")
            return None
        
        position_amt = float(position['positionAmt'])
        if position_amt == 0:
            self._log_trade("Position size is 0")
            return None
        
        side = 'SELL' if position_amt > 0 else 'BUY'
        quantity = abs(position_amt)
        
        return self.place_market_order(side, quantity)
    
    # ============== ORDER MANAGEMENT ==============
    
    def get_open_orders(self, symbol: str = None) -> List:
        """Get all open orders"""
        symbol = symbol or self.symbol
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
    
    def cancel_order(self, order_id: str, symbol: str = None) -> Dict:
        """Cancel specific order"""
        symbol = symbol or self.symbol
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        response = self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
        self._log_trade(f"CANCELLED: Order {order_id}")
        return response
    
    def cancel_all_orders(self, symbol: str = None):
        """Cancel all open orders"""
        symbol = symbol or self.symbol
        params = {'symbol': symbol}
        response = self._make_request('DELETE', '/fapi/v1/allOpenOrders', params, signed=True)
        self._log_trade(f"CANCELLED ALL: {symbol}")
        return response
    
    # ============== TRADE HISTORY ==============
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> List:
        """Get recent trades"""
        symbol = symbol or self.symbol
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/userTrades', params, signed=True)


# ============== EXECUTION AGENT ==============

class TestnetExecutionAgent:
    """
    High-level execution agent for testnet trading
    Implements the strategy logic on testnet
    """
    
    def __init__(self, capital: float = 1000, risk_per_trade: float = 0.015):
        self.client = BinanceTestnetClient()
        self.initial_capital = capital
        self.risk_per_trade = risk_per_trade
        self.active_trade = None
        
    def get_account_summary(self) -> Dict:
        """Get account summary"""
        balance = self.client.get_balance('USDT')
        position = self.client.get_position()
        price = self.client.get_symbol_price()
        
        return {
            'balance_usdt': balance,
            'position': position,
            'current_price': price,
            'unrealized_pnl': float(position['unRealizedProfit']) if position else 0,
        }
    
    def execute_long(self, entry_price: float, stop_loss: float, take_profit: float) -> Dict:
        """
        Execute LONG trade on testnet
        
        Args:
            entry_price: Entry price (for position sizing calc)
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        # Calculate position size
        risk_amount = self.initial_capital * self.risk_per_trade
        risk_per_unit = entry_price - stop_loss
        
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be below entry for LONG")
        
        quantity = risk_amount / risk_per_unit
        quantity = round(quantity, 3)  # Round to 3 decimals
        
        print(f"🟢 TESTNET LONG: {quantity} ETH")
        print(f"   Entry: ~${entry_price}")
        print(f"   Stop: ${stop_loss}")
        print(f"   Target: ${take_profit}")
        print(f"   Risk: ${risk_amount:.2f}")
        
        # Execute
        order = self.client.place_market_order(
            side='BUY',
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.active_trade = {
            'direction': 'LONG',
            'quantity': quantity,
            'entry': entry_price,
            'stop': stop_loss,
            'target': take_profit,
            'order_id': order.get('orderId')
        }
        
        return order
    
    def execute_short(self, entry_price: float, stop_loss: float, take_profit: float) -> Dict:
        """Execute SHORT trade on testnet"""
        risk_amount = self.initial_capital * self.risk_per_trade
        risk_per_unit = stop_loss - entry_price
        
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be above entry for SHORT")
        
        quantity = risk_amount / risk_per_unit
        quantity = round(quantity, 3)
        
        print(f"🔴 TESTNET SHORT: {quantity} ETH")
        print(f"   Entry: ~${entry_price}")
        print(f"   Stop: ${stop_loss}")
        print(f"   Target: ${take_profit}")
        print(f"   Risk: ${risk_amount:.2f}")
        
        order = self.client.place_market_order(
            side='SELL',
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.active_trade = {
            'direction': 'SHORT',
            'quantity': quantity,
            'entry': entry_price,
            'stop': stop_loss,
            'target': take_profit,
            'order_id': order.get('orderId')
        }
        
        return order
    
    def close_active_trade(self):
        """Close the active trade"""
        if not self.active_trade:
            print("No active trade to close")
            return None
        
        result = self.client.close_position()
        self.active_trade = None
        return result


# ============== MAIN ==============

if __name__ == "__main__":
    print("="*70)
    print("BINANCE FUTURES TESTNET CLIENT")
    print("="*70)
    print("⚠️  PAPER TRADING ONLY - NO REAL MONEY")
    print("="*70)
    
    try:
        # Initialize client
        client = BinanceTestnetClient()
        
        # Get account info
        print("\n📊 Account Summary:")
        balance = client.get_balance('USDT')
        print(f"   USDT Balance: ${balance:.2f}")
        
        price = client.get_symbol_price()
        print(f"   ETH Price: ${price:.2f}")
        
        position = client.get_position()
        if position:
            print(f"   Position: {position['positionAmt']} ETH")
            print(f"   Unrealized PnL: ${float(position['unRealizedProfit']):.2f}")
        else:
            print("   Position: None (flat)")
        
        # Show open orders
        open_orders = client.get_open_orders()
        print(f"\n📋 Open Orders: {len(open_orders)}")
        for order in open_orders:
            print(f"   {order['side']} {order['type']} @ {order.get('stopPrice', 'Market')}")
        
        print("\n✅ Testnet client ready!")
        print("   Use: agent.execute_long() or agent.execute_short()")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTo use testnet:")
        print("1. Get API keys from https://testnet.binancefuture.com")
        print("2. Set environment variables:")
        print("   export BINANCE_TESTNET_API_KEY='your_key'")
        print("   export BINANCE_TESTNET_SECRET='your_secret'")
