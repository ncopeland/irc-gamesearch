#!/bin/bash

# IRC Game Search Bot Control Script
# Usage: ./gamebot.sh {start|stop|status|restart}

BOT_NAME="irc_gamebot"
BOT_SCRIPT="irc_gamebot.py"
PID_FILE="/tmp/${BOT_NAME}.pid"
LOG_FILE="irc_gamebot.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if bot is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead
            rm -f "$PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# Function to start the bot
start_bot() {
    if is_running; then
        print_status $YELLOW "Bot is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    if [ ! -f "$BOT_SCRIPT" ]; then
        print_status $RED "Error: $BOT_SCRIPT not found!"
        return 1
    fi
    
    if [ ! -f "irc-gamebot.conf" ]; then
        print_status $RED "Error: irc-gamebot.conf not found!"
        print_status $YELLOW "Please copy irc-gamebot.conf.example to irc-gamebot.conf and configure it."
        return 1
    fi
    
    print_status $GREEN "Starting IRC Game Search Bot..."
    nohup python3 "$BOT_SCRIPT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    if is_running; then
        print_status $GREEN "Bot started successfully (PID: $pid)"
        print_status $YELLOW "Logs: tail -f $LOG_FILE"
    else
        print_status $RED "Failed to start bot. Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the bot
stop_bot() {
    if ! is_running; then
        print_status $YELLOW "Bot is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    print_status $YELLOW "Stopping bot (PID: $pid)..."
    
    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && is_running; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if is_running; then
        print_status $YELLOW "Force killing bot..."
        kill -KILL "$pid" 2>/dev/null
        sleep 1
    fi
    
    if is_running; then
        print_status $RED "Failed to stop bot"
        return 1
    else
        print_status $GREEN "Bot stopped successfully"
        rm -f "$PID_FILE"
    fi
}

# Function to show bot status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_status $GREEN "Bot is running (PID: $pid)"
        
        # Show some basic process info
        if command -v ps > /dev/null; then
            echo "Process info:"
            ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || true
        fi
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo ""
            print_status $YELLOW "Recent log entries:"
            tail -n 5 "$LOG_FILE" 2>/dev/null || true
        fi
    else
        print_status $RED "Bot is not running"
    fi
}

# Function to restart the bot
restart_bot() {
    print_status $YELLOW "Restarting bot..."
    stop_bot
    sleep 2
    start_bot
}

# Main script logic
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    status)
        show_status
        ;;
    restart)
        restart_bot
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the IRC Game Search Bot"
        echo "  stop    - Stop the running bot"
        echo "  status  - Show bot status and recent logs"
        echo "  restart - Stop and start the bot"
        echo ""
        echo "Logs: tail -f $LOG_FILE"
        exit 1
        ;;
esac
