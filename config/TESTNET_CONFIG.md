# Binance Testnet Trading Configuration

## ⚠️ IMPORTANT: TESTNET ONLY - NO REAL MONEY

This configuration is for **Binance Testnet** (paper trading) only.
No real funds are at risk.

---

## Testnet Details

**Binance Futures Testnet:**
- Base URL: `https://testnet.binancefuture.com`
- WebSocket: `wss://stream.binancefuture.com`
- Symbol: `ETHUSDT` (same as mainnet)

**Purpose:**
- Paper trading with fake money
- Test strategy execution
- Verify order placement
- Practice risk management
- No real funds involved

---

## Getting Testnet API Keys

### Step 1: Create Testnet Account
1. Go to: https://testnet.binancefuture.com
2. Click "Generate API Key"
3. Login with GitHub or register
4. API keys will be generated automatically

### Step 2: Fund Testnet Account
1. Go to: https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key"
3. Copy API Key and Secret
4. Fund your testnet account (fake USDT)

### Step 3: Configure Environment
```bash
# Add to your environment variables
export BINANCE_TESTNET_API_KEY="your_testnet_api_key"
export BINANCE_TESTNET_SECRET="your_testnet_secret"
```

---

## API Configuration

```python
TESTNET_CONFIG = {
    'base_url': 'https://testnet.binancefuture.com',
    'api_key': os.getenv('BINANCE_TESTNET_API_KEY'),
    'api_secret': os.getenv('BINANCE_TESTNET_SECRET'),
    'symbol': 'ETHUSDT',
    'recv_window': 5000,
}
```

---

## Testnet vs Mainnet Differences

| Feature | Testnet | Mainnet |
|---------|---------|---------|
| Money | Fake/Test funds | Real money |
| Prices | May differ slightly | Real market prices |
| Liquidity | Lower | High |
| Orders | Execute slower | Real-time |
| API Rate Limits | Same | Same |

---

## Testing Checklist

Before live trading, verify on testnet:
- [ ] Orders placed correctly
- [ ] Stop losses trigger properly
- [ ] Position sizing works
- [ ] Risk limits enforced
- [ ] P&L calculations accurate
- [ ] API error handling works
- [ ] Reconnection logic works

---

## Safety Rules

1. **Never use mainnet API keys in testnet code**
2. **Always verify you're on testnet before trading**
3. **Test all scenarios: win, loss, stop hit, target hit**
4. **Verify fees match expected amounts**

---

## Connection Test

```python
from binance_testnet_client import BinanceTestnetClient

client = BinanceTestnetClient()
print(f"Connected to: {client.get_account_info()}")
print(f"Balance: {client.get_balance('USDT')}")
print(f"Position: {client.get_position('ETHUSDT')}")
```

Expected output should show testnet balance (fake money).

---

## Links

- Testnet Trading: https://testnet.binancefuture.com
- API Docs: https://binance-docs.github.io/apidocs/futures/en/#testnet
- Testnet Funds: https://testnet.binance.vision/

---

**Remember: This is practice money only. Learn here, earn on mainnet.**
