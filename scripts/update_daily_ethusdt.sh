#!/bin/bash
# ETHUSDT Daily Data and Indicators Update Script
# This script runs both 1-hour and weekly data updates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="/root/.openclaw/workspace/data/ethusdt"
LOG_FILE="$DATA_DIR/update_daily.log"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Logging function
log_message() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

log_message "=========================================="
log_message "Starting ETHUSDT Daily Data Update"
log_message "=========================================="

# Run 1-hour data update
log_message "Running 1-hour data update..."
if bash "$SCRIPT_DIR/update_1h_ethusdt.sh" >> "$LOG_FILE" 2>&1; then
    log_message "1-hour update completed successfully"
else
    log_message "ERROR: 1-hour update failed"
    exit 1
fi

# Run weekly data update
log_message "Running weekly data update..."
if bash "$SCRIPT_DIR/update_weekly_ethusdt.sh" >> "$LOG_FILE" 2>&1; then
    log_message "Weekly update completed successfully"
else
    log_message "ERROR: Weekly update failed"
    exit 1
fi

log_message "=========================================="
log_message "Daily update completed successfully!"
log_message "=========================================="
