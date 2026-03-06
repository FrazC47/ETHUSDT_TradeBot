#!/usr/bin/env python3
"""
Binance Futures Testnet Integration
Connects ETHUSDT trading system to Binance testnet API
"""

import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from urllib.parse import urlencode

# Binance Testnet Configuration
TESTNET_BASE_URL = "https://testnet.binancefuture.com"
TESTNET_WS_URL = "wss://stream.binancefuture.com/ws"

DATA_DIR = Path("/root/.openclaw/workspace/data")
CONFIG_FILE = DATA_DIR / "binance_testnet_config.json"

@dataclass
class TestnetPosition:
    """Represents a position on testnet"""
    symbol: str
    side: str  # LONG or SHORT
    size: float  # Position size in ETH
    entry_price: float
    leverage: int
    margin: float
    unrealized_pnl: float
    realized_pnl: float
    
@dataclass
class TestnetOrder:
    """Represents an order on testnet"""
    order_id: str
    symbol: str
    side: str  # BUY or SELL
    order_type: str  # LIMIT, MARKET, STOP
    quantity: float
    price: float
    stop_price: float
    status: str  # NEW, FILLED, CANCELED
    created_time: datetime

class BinanceTestnetClient:
    """Client for Binance Futures Testnet API"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = TESTNET_BASE_URL
        
        # Load config if not provided
        if not self.api_key or not self.api_secret:
            self._load_config()
    
    def _load_config(self):
        """Load API credentials from config file"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.api_key = config.get('api_key')
                self.api_secret = config.get('api_secret')
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _headers(self) -> Dict:
        """Get request headers"""
        return {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make API request to testnet"""
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self._headers(), params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self._headers(), params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self._headers(), params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    # ============ ACCOUNT ENDPOINTS ============
    
    def get_account_balance(self) -> Dict:
        """Get testnet account balance"""
        return self._make_request('GET', '/fapi/v2/balance', signed=True)
    
    def get_account_info(self) -> Dict:
        """Get testnet account information"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_position_risk(self, symbol: str = None) -> List[Dict]:
        """Get position risk/PNL"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v2/positionRisk', params, signed=True)
    
    # ============ TRADING ENDPOINTS ============
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """Set leverage for a symbol"""
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
    
    def set_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """Set margin type (ISOLATED or CROSSED)"""
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: float = None, 
                   stop_price: float = None, time_in_force: str = 'GTC') -> Dict:
        """Place an order"""
        params = {
            'symbol': symbol,
            'side': side,  # BUY or SELL
            'type': order_type,  # LIMIT, MARKET, STOP, STOP_MARKET, TAKE_PROFIT
            'quantity': quantity,
            'timeInForce': time_in_force
        }
        
        if price:
            params['price'] = price
        if stop_price:
            params['stopPrice'] = stop_price
        
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def get_order(self, symbol: str, order_id: str) -> Dict:
        """Get order status"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('GET', '/fapi/v1/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an order"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
    
    # ============ MARKET DATA ============
    
    def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price"""
        return self._make_request('GET', '/fapi/v1/ticker/price', {'symbol': symbol})
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book"""
        return self._make_request('GET', '/fapi/v1/depth', {'symbol': symbol, 'limit': limit})
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List[List]:
        """Get candlestick data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/klines', params)

class TestnetTradingExecutor:
    """Executes trades on testnet based on signals"""
    
    def __init__(self, client: BinanceTestnetClient = None):
        self.client = client or BinanceTestnetClient()
        self.active_trades: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
    
    def execute_trade_setup(self, setup: Dict) -> Dict:
        """
        Execute a complete trade setup on testnet
        
        Args:
            setup: Trade setup from detection system
                {
                    'direction': 'LONG' or 'SHORT',
                    'entry_price': float,
                    'stop_price': float,
                    'target_price': float,
                    'position_size': float,  # in ETH
                    'confidence': float
                }
        """
        symbol = 'ETHUSDT'
        direction = setup['direction']
        entry_price = setup['entry_price']
        stop_price = setup['stop_price']
        target_price = setup['target_price']
        position_size = setup['position_size']
        
        print(f"\n{'='*60}")
        print(f"EXECUTING TESTNET TRADE")
        print(f"{'='*60}")
        print(f"Direction: {direction}")
        print(f"Entry: ${entry_price:.2f}")
        print(f"Stop: ${stop_price:.2f}")
        print(f"Target: ${target_price:.2f}")
        print(f"Size: {position_size:.4f} ETH")
        print(f"{'='*60}\n")
        
        # Check account balance
        balance = self.client.get_account_balance()
        usdt_balance = next((b for b in balance if b['asset'] == 'USDT'), None)
        
        if usdt_balance:
            available = float(usdt_balance['availableBalance'])
            print(f"Account Balance: ${available:,.2f} USDT")
            
            required_margin = position_size * entry_price / 10  # Assuming 10x leverage
            if available < required_margin:
                return {'error': f'Insufficient balance. Need ${required_margin:.2f}, have ${available:.2f}'}
        
        # Set leverage
        leverage = 10  # 10x for ETH
        self.client.set_leverage(symbol, leverage)
        print(f"Leverage set: {leverage}x")
        
        # Calculate order side
        order_side = 'BUY' if direction == 'LONG' else 'SELL'
        
        # 1. Place entry order (LIMIT)
        entry_order = self.client.place_order(
            symbol=symbol,
            side=order_side,
            order_type='LIMIT',
            quantity=position_size,
            price=entry_price,
            time_in_force='GTC'
        )
        
        if 'orderId' not in entry_order:
            return {'error': f'Failed to place entry order: {entry_order}'}
        
        entry_order_id = entry_order['orderId']
        print(f"✅ Entry order placed: {entry_order_id}")
        
        # 2. Place stop loss (STOP_MARKET)
        stop_side = 'SELL' if direction == 'LONG' else 'BUY'
        stop_order = self.client.place_order(
            symbol=symbol,
            side=stop_side,
            order_type='STOP_MARKET',
            quantity=position_size,
            stop_price=stop_price
        )
        
        stop_order_id = stop_order.get('orderId', 'N/A')
        print(f"✅ Stop loss placed: {stop_order_id}")
        
        # 3. Place take profit (TAKE_PROFIT_MARKET)
        tp_order = self.client.place_order(
            symbol=symbol,
            side=stop_side,
            order_type='TAKE_PROFIT_MARKET',
            quantity=position_size,
            stop_price=target_price
        )
        
        tp_order_id = tp_order.get('orderId', 'N/A')
        print(f"✅ Take profit placed: {tp_order_id}")
        
        # Record trade
        trade_record = {
            'trade_id': f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'position_size': position_size,
            'leverage': leverage,
            'orders': {
                'entry': entry_order_id,
                'stop': stop_order_id,
                'take_profit': tp_order_id
            },
            'status': 'ACTIVE',
            'created_at': datetime.now().isoformat()
        }
        
        self.active_trades[trade_record['trade_id']] = trade_record
        self.trade_history.append(trade_record)
        
        # Save to file
        self._save_trade_history()
        
        print(f"\n✅ Trade executed on testnet: {trade_record['trade_id']}")
        
        return trade_record
    
    def check_active_trades(self):
        """Check status of active trades"""
        print(f"\n{'='*60}")
        print(f"ACTIVE TRADES STATUS ({len(self.active_trades)})")
        print(f"{'='*60}\n")
        
        for trade_id, trade in list(self.active_trades.items()):
            symbol = trade['symbol']
            
            # Check entry order status
            entry_status = self.client.get_order(symbol, trade['orders']['entry'])
            
            if entry_status.get('status') == 'FILLED':
                # Get position info
                positions = self.client.get_position_risk(symbol)
                position = next((p for p in positions if p['symbol'] == symbol), None)
                
                if position:
                    pnl = float(position.get('unRealizedProfit', 0))
                    print(f"{trade_id}: Entry filled | PnL: ${pnl:+.2f}")
                else:
                    print(f"{trade_id}: Entry filled | No position data")
            else:
                print(f"{trade_id}: Entry pending ({entry_status.get('status')})")
    
    def close_trade(self, trade_id: str, reason: str = 'manual'):
        """Close an active trade"""
        if trade_id not in self.active_trades:
            return {'error': f'Trade {trade_id} not found'}
        
        trade = self.active_trades[trade_id]
        symbol = trade['symbol']
        
        # Cancel stop and TP orders
        self.client.cancel_order(symbol, trade['orders']['stop'])
        self.client.cancel_order(symbol, trade['orders']['take_profit'])
        
        # Close position
        close_side = 'SELL' if trade['direction'] == 'LONG' else 'BUY'
        close_order = self.client.place_order(
            symbol=symbol,
            side=close_side,
            order_type='MARKET',
            quantity=trade['position_size']
        )
        
        trade['status'] = 'CLOSED'
        trade['closed_at'] = datetime.now().isoformat()
        trade['close_reason'] = reason
        
        del self.active_trades[trade_id]
        self._save_trade_history()
        
        print(f"✅ Trade {trade_id} closed: {reason}")
        return trade
    
    def _save_trade_history(self):
        """Save trade history to file"""
        history_file = DATA_DIR / "testnet_trade_history.json"
        with open(history_file, 'w') as f:
            json.dump({
                'active_trades': self.active_trades,
                'trade_history': self.trade_history
            }, f, indent=2, default=str)

def setup_testnet_config():
    """Interactive setup for testnet API keys"""
    print("="*60)
    print("BINANCE TESTNET SETUP")
    print("="*60)
    print("\n1. Go to: https://testnet.binancefuture.com")
    print("2. Register/login to testnet")
    print("3. Go to API Management")
    print("4. Create new API key")
    print("5. Enable Futures trading")
    print()
    
    api_key = input("Enter Testnet API Key: ").strip()
    api_secret = input("Enter Testnet API Secret: ").strip()
    
    config = {
        'api_key': api_key,
        'api_secret': api_secret,
        'base_url': TESTNET_BASE_URL,
        'setup_date': datetime.now().isoformat()
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to: {CONFIG_FILE}")
    
    # Test connection
    print("\nTesting connection...")
    client = BinanceTestnetClient(api_key, api_secret)
    balance = client.get_account_balance()
    
    if 'error' not in balance:
        usdt = next((b for b in balance if b['asset'] == 'USDT'), None)
        if usdt:
            print(f"✅ Connection successful!")
            print(f"   Balance: ${float(usdt['balance']):,.2f} USDT")
        else:
            print("⚠️ Connected but no USDT balance found")
            print("   Get testnet funds from: https://testnet.binancefuture.com")
    else:
        print(f"❌ Connection failed: {balance.get('error')}")

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 binance_testnet_client.py [setup|balance|trade|status|close]")
        return
    
    command = sys.argv[1]
    
    if command == 'setup':
        setup_testnet_config()
    
    elif command == 'balance':
        client = BinanceTestnetClient()
        balance = client.get_account_balance()
        print(json.dumps(balance, indent=2))
    
    elif command == 'trade':
        # Test trade execution
        executor = TestnetTradingExecutor()
        test_setup = {
            'direction': 'LONG',
            'entry_price': 2000.0,
            'stop_price': 1980.0,
            'target_price': 2040.0,
            'position_size': 0.1,
            'confidence': 85.0
        }
        result = executor.execute_trade_setup(test_setup)
        print(json.dumps(result, indent=2))
    
    elif command == 'status':
        executor = TestnetTradingExecutor()
        executor.check_active_trades()
    
    elif command == 'close':
        if len(sys.argv) < 3:
            print("Usage: close <trade_id>")
            return
        executor = TestnetTradingExecutor()
        executor.close_trade(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
