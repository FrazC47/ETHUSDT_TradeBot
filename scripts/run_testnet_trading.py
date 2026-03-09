#!/usr/bin/env python3
"""
Testnet Trading Script - Execute Strategy on Binance Testnet
Paper trading with fake money for practice
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/agents')

from binance_testnet_client import TestnetExecutionAgent
import json
from datetime import datetime

def run_testnet_trading():
    """Run strategy execution on testnet"""
    
    print("="*70)
    print("ETHUSDT TESTNET TRADING - PAPER MODE")
    print("="*70)
    print("⚠️  NO REAL MONEY - PRACTICE ONLY")
    print("="*70)
    
    try:
        # Initialize execution agent
        agent = TestnetExecutionAgent(
            capital=1000,  # Fake money
            risk_per_trade=0.015  # 1.5% risk
        )
        
        # Get current market data
        summary = agent.get_account_summary()
        
        print("\n📊 Current Status:")
        print(f"   Balance: ${summary['balance_usdt']:.2f} (TESTNET FUNDS)")
        print(f"   ETH Price: ${summary['current_price']:.2f}")
        
        if summary['position']:
            print(f"   Position: {summary['position']['positionAmt']} ETH")
            print(f"   Unrealized PnL: ${summary['unrealized_pnl']:.2f}")
        else:
            print("   Position: FLAT")
        
        # Example: Execute a test trade
        print("\n" + "="*70)
        print("SAMPLE TRADE EXECUTION")
        print("="*70)
        
        current_price = summary['current_price']
        
        # Example LONG setup
        entry = current_price
        stop = entry * 0.97  # 3% stop
        target = entry * 1.06  # 6% target
        
        print(f"\n📝 Example LONG Setup:")
        print(f"   Entry: ${entry:.2f}")
        print(f"   Stop: ${stop:.2f}")
        print(f"   Target: ${target:.2f}")
        print(f"   R:R = 1:{(target-entry)/(entry-stop):.1f}")
        
        response = input("\nExecute this test trade? (y/n): ")
        
        if response.lower() == 'y':
            print("\n🚀 Executing on TESTNET...")
            
            try:
                order = agent.execute_long(entry, stop, target)
                
                print("\n✅ Order Executed!")
                print(f"   Order ID: {order.get('orderId')}")
                print(f"   Status: {order.get('status')}")
                print(f"   Executed Qty: {order.get('executedQty', 0)} ETH")
                print(f"   Avg Price: ${float(order.get('avgPrice', 0)):.2f}")
                
                # Save trade record
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'TESTNET_TRADE',
                    'direction': 'LONG',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'order': order
                }
                
                with open('/root/.openclaw/workspace/logs/testnet_trade.json', 'a') as f:
                    f.write(json.dumps(trade_record) + '\n')
                
                print("\n📋 Trade logged to: logs/testnet_trade.json")
                
            except Exception as e:
                print(f"\n❌ Trade failed: {e}")
        else:
            print("\n⏭️  Trade skipped")
        
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        print("1. Monitor trade in Binance Testnet UI:")
        print("   https://testnet.binancefuture.com")
        print("\n2. Check logs:")
        print("   tail -f /root/.openclaw/workspace/logs/testnet_trades.log")
        print("\n3. Close position when done testing:")
        print("   agent.close_active_trade()")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Testnet API keys from https://testnet.binancefuture.com")
        print("2. Environment variables set:")
        print("   export BINANCE_TESTNET_API_KEY='your_key'")
        print("   export BINANCE_TESTNET_SECRET='your_secret'")
        return False
    
    return True

if __name__ == "__main__":
    success = run_testnet_trading()
    sys.exit(0 if success else 1)
