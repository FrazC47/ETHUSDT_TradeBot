# Binance Testnet Setup Guide

## Quick Start (5 Minutes)

### Step 1: Get API Keys (2 minutes)

1. **Go to:** https://testnet.binancefuture.com

2. **Register:**
   - Click "Register"
   - Use any email (test email is fine)
   - Create password
   - No KYC required!

3. **Create API Key:**
   - Login → Profile → "API Management"
   - Click "Create API"
   - Name: `ETHUSDT_Trading_Bot`
   - Enable permissions:
     - ✅ Enable Reading
     - ✅ Enable Trading
     - ✅ Enable Futures
   - Click "Create"

4. **Save Keys:**
   ```
   API Key:     xxxxxxxxxx (copy this)
   Secret Key:  xxxxxxxxxx (copy this - shown ONCE only!)
   ```

5. **Get Free Funds:**
   - Look for "Faucet" button
   - Click "Get Test Funds"
   - Receive 10,000 USDT (free, virtual)

---

### Step 2: Configure Bot (1 minute)

Run setup command:
```bash
python3 scripts/binance_testnet_client.py setup
```

Enter your API keys when prompted:
```
API Key: [paste your key]
Secret Key: [paste your secret]
```

---

### Step 3: Verify Connection (30 seconds)

```bash
python3 scripts/binance_testnet_client.py balance
```

Expected output:
```json
[
  {
    "asset": "USDT",
    "balance": "10000.00000000",
    "availableBalance": "10000.00000000"
  }
]
```

✅ **If you see $10,000 USDT, you're ready!**

---

### Step 4: Execute First Test Trade (1 minute)

```bash
python3 scripts/binance_testnet_client.py trade
```

This will place:
- LONG entry at $2,000
- Stop loss at $1,980
- Take profit at $2,040
- Size: 0.1 ETH (small test)

Check status:
```bash
python3 scripts/binance_testnet_client.py status
```

---

## What Happens Next

### Option A: Manual Testing (Recommended First)

Use these commands to practice:
```bash
# Check balance anytime
python3 scripts/binance_testnet_client.py balance

# Check active trades
python3 scripts/binance_testnet_client.py status

# Close a trade manually
python3 scripts/binance_testnet_client.py close TRADE_ID
```

Run 5-10 manual trades to verify system works correctly.

---

### Option B: Auto-Detection (After Manual Testing)

Connect detection system to auto-execute:

```bash
# Start auto-trading on testnet
./scripts/trade_system.sh start

# Check system status
./scripts/trade_system.sh status

# Stop auto-trading
./scripts/trade_system.sh stop
```

The system will:
1. Monitor all 8 timeframes
2. Generate signals when confidence ≥ 65%
3. Auto-execute on testnet
4. Record all trades to `testnet_trade_history.json`
5. Send you Telegram alerts

---

## Troubleshooting

### "Connection failed" Error

**Cause:** API keys wrong or permissions not enabled

**Fix:**
1. Go back to testnet.binancefuture.com
2. Check API key permissions
3. Ensure "Enable Futures" is checked
4. Recreate keys if needed

---

### "Insufficient balance" Error

**Cause:** No testnet USDT received

**Fix:**
1. Go to testnet.binancefuture.com
2. Find "Faucet" or "Get Test Funds"
3. Click to receive 10,000 USDT

---

### "Invalid API key" Error

**Cause:** Using mainnet keys instead of testnet keys

**Fix:**
- Testnet keys start with different format
- Must get keys from testnet.binancefuture.com (NOT binance.com)

---

## Security Notes

| What | Protection |
|------|------------|
| API Keys | Stored in `data/` folder (gitignored) |
| Testnet vs Live | Completely separate environments |
| Real Money | Zero risk - all fake funds |
| Key Regeneration | Can create new keys anytime |

**Your testnet keys CANNOT access your real Binance account.**

---

## Next Steps After Testnet

| Phase | Timeline | Action |
|-------|----------|--------|
| **Testnet Practice** | Week 1-2 | Run 20+ trades, verify system |
| **Micro Live** | Week 3-4 | $100 real trades |
| **Full Live** | Month 2+ | $1,000 full deployment |

---

## Quick Reference

```bash
# Setup
python3 scripts/binance_testnet_client.py setup

# Balance
python3 scripts/binance_testnet_client.py balance

# Test trade
python3 scripts/binance_testnet_client.py trade

# Status
python3 scripts/binance_testnet_client.py status

# Auto-trading
./scripts/trade_system.sh start
./scripts/trade_system.sh stop
./scripts/trade_system.sh status

# Learning system
python3 scripts/learning_system.py
python3 scripts/auto_learning.py status
```

---

## Support

If you get stuck:
1. Check this guide again
2. Review error messages carefully
3. Verify you're on testnet (not mainnet)
4. Confirm API permissions are correct

**Ready to start? Go to https://testnet.binancefuture.com now!**
