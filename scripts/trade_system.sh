#!/bin/bash
# ETHUSDT Trade Detection System - Master Control
# Usage: ./trade_system.sh [start|stop|status|detect|deactivate]

SCRIPT_DIR="/root/.openclaw/workspace/scripts"
DATA_DIR="/root/.openclaw/workspace/data"
STATE_FILE="$DATA_DIR/.trade_spotlight_state.json"
PID_FILE="$DATA_DIR/.trade_system.pid"
DAEMON_LOG="$DATA_DIR/spotlight_daemon.log"

color_green='\033[0;32m'
color_red='\033[0;31m'
color_yellow='\033[1;33m'
color_nc='\033[0m'

print_status() {
    echo -e "${color_green}[INFO]${color_nc} $1"
}

print_error() {
    echo -e "${color_red}[ERROR]${color_nc} $1"
}

print_warning() {
    echo -e "${color_yellow}[WARN]${color_nc} $1"
}

check_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    else
        echo '{"status": "INACTIVE"}'
    fi
}

cmd_start() {
    print_status "Starting Trade Detection System..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_warning "Trade system already running (PID: $PID)"
            return 1
        fi
    fi
    
    nohup python3 "$SCRIPT_DIR/spotlight_daemon.py" > /dev/null 2>&1 &
echo $! > "$PID_FILE"
    
    print_status "Trade Spotlight Daemon started (PID: $(cat $PID_FILE))"
    print_status "Logs: $DAEMON_LOG"
    sleep 1
    cmd_detect
}

cmd_stop() {
    print_status "Stopping Trade Detection System..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID" 2>/dev/null
            print_status "Daemon stopped (PID: $PID)"
        fi
        rm -f "$PID_FILE"
    fi
    
    python3 "$SCRIPT_DIR/deactivate_trade.py"
}

cmd_status() {
    echo "======================================"
    echo "ETHUSDT Trade Detection System Status"
    echo "======================================"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "Daemon: ${color_green}RUNNING${color_nc} (PID: $PID)"
        else
            echo -e "Daemon: ${color_red}STOPPED${color_nc} (stale PID file)"
        fi
    else
        echo -e "Daemon: ${color_red}STOPPED${color_nc}"
    fi
    
    echo ""
    echo "State:"
    check_state | python3 -m json.tool 2>/dev/null | head -20 || check_state
    
    echo ""
    echo "Recent Activity:"
    if [ -f "$DAEMON_LOG" ]; then
        tail -3 "$DAEMON_LOG" 2>/dev/null || echo "No recent activity"
    else
        echo "No log file yet"
    fi
}

cmd_detect() {
    print_status "Running trade detection cycle..."
    python3 "$SCRIPT_DIR/trade_detection_agent.py"
}

cmd_deactivate() {
    print_status "Deactivating trade spotlight..."
    python3 "$SCRIPT_DIR/deactivate_trade.py"
}

cmd_help() {
    echo "ETHUSDT Trade Detection System"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the trade detection daemon"
    echo "  stop        - Stop the daemon and deactivate trades"
    echo "  status      - Show system status and recent activity"
    echo "  detect      - Run one detection cycle manually"
    echo "  deactivate  - Manually deactivate current trade"
    echo "  help        - Show this help message"
}

COMMAND=${1:-help}

case "$COMMAND" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    status)
        cmd_status
        ;;
    detect)
        cmd_detect
        ;;
    deactivate)
        cmd_deactivate
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        cmd_help
        exit 1
        ;;
esac
