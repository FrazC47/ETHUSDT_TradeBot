#!/usr/bin/env python3
"""
ETHUSDT Testnet Setup Wizard
Guides user through testnet API setup and first trade
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/data")
CONFIG_FILE = DATA_DIR / "binance_testnet_config.json"

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(number, title):
    """Print step header"""
    print(f"\n{'─'*70}")
    print(f"  STEP {number}: {title}")
    print(f"{'─'*70}\n")

def check_config():
    """Check if config already exists"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        return config.get('api_key') and config.get('api_secret')
    return False

def step_1_get_keys():
    """Step 1: Guide to get API keys"""
    print_step(1, "Get Testnet API Keys")
    
    print("You need to create a Binance testnet account and get API keys.")
    print()
    print("📋 Instructions:")
    print()
    print("  1. Open your browser and go to:")
    print("     https://testnet.binancefuture.com")
    print()
    print("  2. Click 'Register' (or login if you have an account)")
    print("     • Use any email (can be a test email)")
    print("     • No KYC/verification required for testnet")
    print()
    print("  3. After login, click on your profile → 'API Management'")
    print()
    print("  4. Click 'Create API Key'")
    print("     • Give it a name: 'ETHUSDT_Trading_Bot'")
    print("     • Enable 'Enable Futures' permission")
    print("     • Enable 'Enable Reading' permission")
    print("     • Enable 'Enable Trading' permission")
    print()
    print("  5. Save your keys securely:")
    print("     • API Key (starts with letters/numbers)")
    print("     • Secret Key (long string, only shown once!)")
    print()
    print("  6. Get free testnet funds:")
    print("     • Look for 'Faucet' or 'Get Test Funds'")
    print("     • Request 10,000 USDT (free)")
    print()
    
    input("Press Enter when you have your API keys ready...")

def step_2_enter_keys():
    """Step 2: Enter API keys"""
    print_step(2, "Enter Your API Keys")
    
    print("Enter your testnet API credentials:")
    print()
    
    api_key = input("  API Key: ").strip()
    api_secret = input("  Secret Key: ").strip()
    
    if not api_key or not api_secret:
        print("\n❌ Error: Both keys are required")
        return None
    
    # Save config
    config = {
        'api_key': api_key,
        'api_secret': api_secret,
        'base_url': 'https://testnet.binancefuture.com',
        'setup_date': datetime.now().isoformat(),
        'status': 'configured'
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to: {CONFIG_FILE}")
    
    return config

def step_3_verify_connection():
    """Step 3: Verify connection works"""
    print_step(3, "Verify Connection")
    
    print("Testing connection to Binance testnet...")
    print()
    
    try:
        # Import and test
        sys.path.insert(0, str(Path(__file__).parent))
        from binance_testnet_client import BinanceTestnetClient
        
        client = BinanceTestnetClient()
        balance = client.get_account_balance()
        
        if 'error' in balance:
            print(f"❌ Connection failed: {balance['error']}")
            return False
        
        # Find USDT balance
        usdt_balance = None
        for asset in balance:
            if asset.get('asset') == 'USDT':
                usdt_balance = asset
                break
        
        if usdt_balance:
            available = float(usdt_balance.get('availableBalance', 0))
            total = float(usdt_balance.get('balance', 0))
            
            print("✅ Connection successful!")
            print()
            print(f"  Account Status: Active")
            print(f"  Total Balance: ${total:,.2f} USDT")
            print(f"  Available: ${available:,.2f} USDT")
            print()
            
            if available < 1000:
                print("⚠️  Warning: Low balance")
                print("   Get more testnet funds from:")
                print("   https://testnet.binancefuture.com")
            else:
                print("✅ Sufficient balance for trading")
            
            return True
        else:
            print("⚠️  Connected but no USDT balance found")
            print("   Get testnet funds from the website")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def step_4_execute_test_trade():
    """Step 4: Execute first test trade"""
    print_step(4, "Execute First Test Trade")
    
    print("This will execute a test LONG trade on ETHUSDT:")
    print()
    print("  Symbol: ETHUSDT")
    print("  Direction: LONG")
    print("  Entry: $2,000")
    print("  Stop: $1,980")
    print("  Target: $2,040")
    print("  Size: 0.1 ETH (small test)")
    print()
    
    confirm = input("Execute test trade? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\nSkipping test trade. You can run it later with:")
        print("  python3 scripts/binance_testnet_client.py trade")
        return False
    
    print("\nExecuting trade...")
    print()
    
    try:
        from binance_testnet_client import TestnetTradingExecutor
        
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
        
        if 'error' in result:
            print(f"❌ Trade failed: {result['error']}")
            return False
        
        print("\n✅ Test trade executed successfully!")
        print(f"   Trade ID: {result['trade_id']}")
        print(f"   Orders placed: Entry, Stop Loss, Take Profit")
        print()
        print("You can check status anytime with:")
        print("  python3 scripts/binance_testnet_client.py status")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def step_5_connect_detection():
    """Step 5: Connect to auto-detection"""
    print_step(5, "Connect Auto-Detection System")
    
    print("Your testnet is now configured and tested!")
    print()
    print("Next: Connect the trade detection system for fully automated trading.")
    print()
    print("This will:")
    print("  • Monitor detection signals 24/7")
    print("  • Auto-execute trades on testnet")
    print("  • Record all results for learning")
    print("  • Send you alerts on Telegram")
    print()
    
    print("To enable auto-trading, run:")
    print("  python3 scripts/trade_system.sh start")
    print()
    print("To check detection status:")
    print("  python3 scripts/trade_system.sh status")

def main():
    """Main setup wizard"""
    import sys
    
    print_header("ETHUSDT TESTNET SETUP WIZARD")
    print("This will guide you through connecting to Binance testnet")
    print("for automated paper trading with $10,000 virtual balance.")
    
    # Check existing config
    if check_config():
        print("\n⚠️  Existing configuration found!")
        overwrite = input("Reconfigure? (yes/no): ").strip().lower()
        if overwrite != 'yes':
            print("\nUsing existing configuration.")
            print("You can test connection with:")
            print("  python3 scripts/binance_testnet_client.py balance")
            return
    
    # Step 1: Get keys
    step_1_get_keys()
    
    # Step 2: Enter keys
    config = step_2_enter_keys()
    if not config:
        print("\n❌ Setup failed. Please try again.")
        return
    
    # Step 3: Verify
    if not step_3_verify_connection():
        print("\n⚠️  Connection verification failed.")
        print("Please check your API keys and try again.")
        return
    
    # Step 4: Test trade
    step_4_execute_test_trade()
    
    # Step 5: Next steps
    step_5_connect_detection()
    
    print_header("SETUP COMPLETE!")
    print("Your testnet trading environment is ready.")
    print()
    print("Quick Commands:")
    print("  Check balance:  python3 scripts/binance_testnet_client.py balance")
    print("  Check trades:   python3 scripts/binance_testnet_client.py status")
    print("  Start system:   ./scripts/trade_system.sh start")
    print("  Stop system:    ./scripts/trade_system.sh stop")
    print()

if __name__ == "__main__":
    import sys  # Need to import here for the function
    main()
