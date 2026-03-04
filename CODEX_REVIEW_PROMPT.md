# OpenAI Codex Review Prompt - ETHUSDT TradeBot

## Repository
https://github.com/FrazC47/ETHUSDT_TradeBot

## Your Task
Review the entire ETHUSDT TradeBot codebase and make it more robust, reliable, and production-ready. This is a real trading system that will manage real money.

---

## System Overview

**What this is:**
- Automated trading bot for ETHUSDT on Binance Futures
- Multi-timeframe technical analysis (1M → 5M)
- Fundamental analysis (on-chain data, sentiment)
- Self-improving system with hypothesis testing
- Risk management and drawdown protection

**Current Performance:**
- Backtest: +662% profit, 58.6% win rate
- Live: Just deployed, monitoring

---

## Code Review Checklist

### 1. ERROR HANDLING & ROBUSTNESS
```
□ Wrap all API calls in try-except blocks
□ Implement retry logic with exponential backoff
□ Handle network timeouts gracefully
□ Validate all inputs before processing
□ Log errors with context for debugging
□ Fail safely (don't trade if data is bad)
```

### 2. RISK MANAGEMENT
```
□ Verify position sizing calculations
□ Check stop-loss is always set before entry
□ Ensure max 3% risk per trade is enforced
□ Validate leverage doesn't exceed 5x
□ Confirm drawdown limits trigger correctly
□ Test emergency stop functionality
```

### 3. DATA VALIDITY
```
□ Check for NaN/None values in price data
□ Validate OHLC data makes sense (high >= low, etc.)
□ Verify timestamp continuity (no gaps)
□ Check for stale data (prices not updating)
□ Validate API responses before parsing
```

### 4. CONCURRENCY & TIMING
```
□ Ensure no race conditions in shared state
□ Handle overlapping cron jobs gracefully
□ Implement proper locking if needed
□ Check for timing issues (candle close vs tick)
□ Verify async operations complete before next cycle
```

### 5. LOGGING & MONITORING
```
□ Add comprehensive logging (entry/exit/errors)
□ Log all trading decisions with reasoning
□ Implement structured logging (JSON format)
□ Add performance metrics tracking
□ Create alerts for critical errors
```

### 6. CONFIGURATION & SECURITY
```
□ Move sensitive config to environment variables
□ Validate all configuration values on startup
□ Add config schema validation
□ Remove any hardcoded credentials
□ Implement API key rotation capability
```

### 7. TESTING
```
□ Add unit tests for critical functions
□ Create integration tests for full pipeline
□ Add mock data for testing without API calls
□ Test edge cases (zero volume, extreme prices)
□ Validate backtest engine accuracy
```

### 8. PERFORMANCE
```
□ Optimize data fetching (caching, batching)
□ Reduce unnecessary API calls
□ Profile slow functions
□ Check memory leaks in long-running processes
□ Optimize pandas/numpy operations
```

---

## Specific Files to Review

### Critical Path (Must be bulletproof)
1. `agents/ethusdt_agent.py` - Main trading logic
2. `agents/modules/mtf_engine_v34.py` - Signal generation
3. `agents/modules/signal_engine.py` - State machine
4. `agents/modules/fundamental_analyzer.py` - Entry filtering

### Risk Management (Safety critical)
5. `agents/modules/drawdown_recovery.py` - Capital protection
6. `agents/modules/buffer_system.py` - Execution safety
7. `agents/modules/dynamic_rr.py` - Risk/reward calculation

### Infrastructure (Reliability)
8. `agents/modules/regime_detector.py` - Market adaptation
9. `agents/improver/ethusdt_improver_v2.py` - Self-improvement
10. `agents/auto_implementer/auto_implementer_v2.py` - Deployment

---

## Common Issues to Fix

### Python Specific
- Unhandled exceptions
- Mutable default arguments
- Resource leaks (files, connections)
- Circular imports
- Type mismatches

### Trading Specific
- Division by zero in calculations
- Integer overflow in position sizing
- Floating point precision issues
- Timezone handling
- Candle close assumption errors

### API Specific
- Rate limiting not handled
- Authentication failures
- Partial fills not handled
- Order status polling issues
- WebSocket reconnection

---

## Improvements to Add

### 1. Health Checks
```python
def health_check() -> Dict:
    """Verify all systems operational before trading"""
    return {
        'api_connection': test_binance_connection(),
        'data_freshness': check_last_candle_time(),
        'balance_sufficient': check_min_balance(),
        'strategy_loaded': validate_strategy_config(),
        'all_systems_go': all(checks_passed)
    }
```

### 2. Circuit Breaker
```python
class CircuitBreaker:
    """Stop trading if too many errors"""
    - Count errors in time window
    - Open circuit if threshold exceeded
    - Require manual reset or time delay
```

### 3. Position Reconciliation
```python
def reconcile_positions():
    """Verify local state matches exchange"""
    - Query exchange for open positions
    - Compare to local position tracking
    - Alert if mismatch detected
```

### 4. Order Idempotency
```python
def place_order_safe(params) -> Order:
    """Ensure order placed exactly once"""
    - Generate unique client order ID
    - Check if order already exists
    - Handle "already filled" responses
```

---

## Output Requirements

For each file reviewed, provide:

1. **Issues Found** (critical, high, medium, low priority)
2. **Fixes Applied** (with code snippets)
3. **Improvements Made** (enhancements)
4. **Tests Added** (if applicable)

Create a summary report:
```markdown
# Codex Review Report - ETHUSDT TradeBot

## Executive Summary
- Total files reviewed: X
- Critical issues fixed: X
- High priority fixes: X
- Improvements added: X
- Tests added: X

## Critical Fixes
1. [Description and fix]

## Improvements
1. [Description and implementation]

## Testing
- How to run tests
- Coverage report

## Deployment Notes
- Any breaking changes
- Migration steps
- Rollback procedure
```

---

## Constraints

**DO NOT:**
- Change core strategy logic (trend following, MTF analysis)
- Modify risk limits (3% max risk, 5x leverage)
- Remove existing safety checks
- Add new external dependencies without justification
- Change file structure significantly

**DO:**
- Fix bugs and edge cases
- Add error handling
- Improve logging
- Add tests
- Optimize performance
- Enhance reliability

---

## Success Criteria

The code is production-ready when:
- [ ] No unhandled exceptions possible
- [ ] All API calls have retry logic
- [ ] Risk limits are hard-enforced
- [ ] Comprehensive logging in place
- [ ] Tests cover critical paths
- [ ] Health checks verify system state
- [ ] Circuit breaker prevents runaway errors
- [ ] Documentation is complete

---

## Questions?

If you find something unclear:
1. Check the docs/ folder for context
2. Look at comments in the code
3. Make reasonable assumptions
4. Document your assumptions in the review

---

**Start with the critical path files first, then move to risk management and infrastructure.**

**This is real money - be thorough, be careful, be excellent.**
