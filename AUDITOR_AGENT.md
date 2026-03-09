# AUDITOR AGENT - System Honesty & Truth

## Overview

The **Auditor Agent** is the watchdog of the ETHUSDT trading system. Its sole purpose is to ensure that all other agents stay honest, grounded in truth, and never hallucinate or make up results.

---

## Core Principles

### 1. TRUST BUT VERIFY
- Question everything
- No agent is above audit
- All claims must be proven

### 2. SOURCE OF TRUTH
- All data must be traceable
- Only validated locations accepted
- Unknown sources flagged immediately

### 3. IMMUTABLE LOGS
- Once recorded, never altered
- Complete audit trail
- Tamper-evident records

### 4. GROUNDED IN FACTS
- No hallucinations allowed
- Real data only
- Verifiable results only

---

## What the Auditor Does

### 1. Verifies Data Sources
```python
# Validates:
✓ File exists in approved locations (/data/raw/, /data/indicators/)
✓ File is not empty
✓ OHLC data is valid (high >= low, close in range)
✓ No negative prices or volumes
✓ Sample data passes sanity checks
```

### 2. Audits Agent Operations
For every operation, the auditor records:
- **Who**: Which agent performed the operation
- **What**: What operation was performed
- **Inputs**: What data/parameters were used
- **Outputs**: What results were produced
- **Data Sources**: Where the data came from
- **Verification**: Whether everything checks out

### 3. Questions Suspicious Claims
The auditor flags:
- Returns > 1000% ("likely fake")
- Win rates > 90% ("too perfect")
- Data from unverified sources
- Missing evidence for claims

### 4. Maintains Audit Logs
Three types of logs:
- **Daily logs**: Human-readable text
- **Master JSONL**: Machine-readable structured data
- **Individual audits**: Per-operation detailed records

---

## Audit Trail Example

### Valid Operation (PASSED)
```json
{
  "timestamp": "2026-03-09T11:54:22",
  "agent": "backtesting_agent",
  "operation": "6_month_backtest",
  "inputs": {
    "start_date": "2025-09-01",
    "end_date": "2026-03-07",
    "initial_capital": 1000
  },
  "outputs": {
    "total_return": 2.43,
    "win_rate": 34.9,
    "total_trades": 344
  },
  "data_sources": [
    {
      "source": "/data/indicators/1h_indicators.csv",
      "verified": true,
      "checks": {
        "valid_location": true,
        "file_exists": true,
        "file_size": 4523456,
        "sample_valid": true
      }
    }
  ],
  "verification_status": "passed"
}
```

### Suspicious Operation (FAILED)
```json
{
  "timestamp": "2026-03-09T11:54:35",
  "agent": "fake_strategy_agent",
  "operation": "claim_1040_percent_return",
  "outputs": {
    "total_return": 1040,
    "win_rate": 95.5
  },
  "data_sources": [
    {
      "source": "/simulated/data/fake_prices.csv",
      "verified": false,
      "error": "Data source not in validated locations"
    }
  ],
  "suspicious_findings": [
    "Suspicious return: 1040% (too high)",
    "Suspicious win rate: 95.5% (too perfect)"
  ],
  "verification_status": "failed"
}
```

---

## Usage

### Audit an Operation
```python
# Create task file
{
  "task": "audit_operation",
  "params": {
    "agent_name": "backtesting_agent",
    "operation": "6_month_backtest",
    "inputs": {...},
    "outputs": {...},
    "data_sources": [...]
  }
}

# Run auditor
python3 agents/auditor_agent.py task.json
```

### Verify Data Source
```python
{
  "task": "verify_data_source",
  "params": {
    "source": "/data/indicators/1h_indicators.csv",
    "agent": "backtesting_agent"
  }
}
```

### Question an Agent's Claim
```python
{
  "task": "question_agent",
  "params": {
    "agent_name": "strategy_agent",
    "claim": "1040% return over 6 months",
    "evidence_required": [
      "/backtest_results/validated_results.json",
      "/data/indicators/1h_indicators.csv"
    ]
  }
}
```

### Generate Audit Report
```python
{
  "task": "generate_report"
}
```

---

## Integration with Other Agents

### Every Agent Should:
1. **Report their data sources** to the auditor
2. **Accept audits** of their operations
3. **Provide evidence** for claims
4. **Acknowledge failures** honestly

### Example Integration in Backtesting Agent:
```python
# After running backtest
audit_record = auditor.audit_agent_operation(
    agent_name="backtesting_agent",
    operation="monthly_backtest",
    inputs={"start_date": "2025-09-01", "end_date": "2026-03-07"},
    outputs={"total_return": 2.43, "win_rate": 34.9},
    data_sources=[
        "/data/indicators/1h_indicators.csv",
        "/data/indicators/4h_indicators.csv"
    ]
)

if audit_record["verification_status"] != "passed":
    log.error("Audit failed - results rejected")
    return None
```

---

## Audit Log Locations

| Log Type | Location | Purpose |
|----------|----------|---------|
| Daily Log | `audit_logs/audit_YYYYMMDD.log` | Human-readable daily summary |
| Master Log | `audit_logs/master_audit_log.jsonl` | Complete structured history |
| Individual | `audit_logs/[agent]_[timestamp].json` | Per-operation details |
| Reports | `audit_logs/audit_report_[timestamp].json` | Summary reports |

---

## Red Flags the Auditor Catches

### 🚩 CRITICAL (Automatic Rejection)
- Data from `/simulated/` or `/fake/` paths
- Returns > 1000%
- Win rates > 90%
- Empty or missing data files
- Invalid OHLC relationships

### ⚠️ WARNING (Requires Verification)
- Returns > 100%
- Win rates > 70%
- Data sources outside validated locations
- Unusual file sizes
- Missing evidence

### ℹ️ INFO (Logged for Review)
- Normal operations
- Successful verifications
- Routine audits

---

## Statistics Tracked

```python
{
  "total_audits": 147,
  "warnings_issued": 23,
  "errors_found": 5,
  "verifications_passed": 120,
  "verifications_failed": 8
}
```

---

## Validated Data Sources

Only these locations are trusted:
- `/data/raw/` - Raw candlestick downloads
- `/data/indicators/` - Calculated indicators
- `https://fapi.binance.com` - Binance API (direct)

Any data from other locations is **flagged as suspicious**.

---

## Summary

The Auditor Agent ensures:
- ✅ No fake data can enter the system
- ✅ No inflated results go unchallenged
- ✅ Every operation is traceable
- ✅ Every claim is verifiable
- ✅ Complete honesty is maintained

**Without the auditor, agents can hallucinate.**  
**With the auditor, only truth survives.**

---

*"Trust but verify."* - Ronald Reagan
