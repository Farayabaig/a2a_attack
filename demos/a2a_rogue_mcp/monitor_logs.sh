#!/bin/bash
# Log monitoring script for Rogue MCP Attack Lab

CONTAINER_NAME="a2a-rogue-mcp-lab"
ATTACK_LOG="attack_logs/rogue_mcp_attack.log"

echo "=== Rogue MCP Attack Lab - Log Monitor ==="
echo ""
echo "Choose monitoring method:"
echo "1) Follow Docker logs (real-time)"
echo "2) View last 50 Docker log lines"
echo "3) Filter for ROGUE MCP messages"
echo "4) Filter for ATTACK messages"
echo "5) Filter for SENSITIVE paths"
echo "6) View attack log file (exfiltrated data)"
echo "7) Follow attack log file (real-time)"
echo "8) View formatted attack logs (JSON)"
echo "9) Combined view (Docker + Attack logs)"
echo ""
read -p "Enter choice (1-9): " choice

case $choice in
    1)
        echo "Following Docker logs (Ctrl+C to exit)..."
        docker logs -f $CONTAINER_NAME
        ;;
    2)
        echo "Last 50 Docker log lines:"
        docker logs --tail=50 $CONTAINER_NAME
        ;;
    3)
        echo "ROGUE MCP messages:"
        docker logs $CONTAINER_NAME | grep "ROGUE MCP"
        ;;
    4)
        echo "ATTACK messages:"
        docker logs $CONTAINER_NAME | grep "ATTACK"
        ;;
    5)
        echo "SENSITIVE path warnings:"
        docker logs $CONTAINER_NAME | grep "SENSITIVE"
        ;;
    6)
        if [ -f "$ATTACK_LOG" ]; then
            echo "Attack log file (exfiltrated data):"
            cat $ATTACK_LOG
        else
            echo "Attack log file not found. Run a task in rogue mode first."
        fi
        ;;
    7)
        if [ -f "$ATTACK_LOG" ]; then
            echo "Following attack log file (Ctrl+C to exit)..."
            tail -f $ATTACK_LOG
        else
            echo "Attack log file not found. Run a task in rogue mode first."
        fi
        ;;
    8)
        if command -v jq &> /dev/null; then
            if [ -f "$ATTACK_LOG" ]; then
                echo "Formatted attack logs (JSON):"
                cat $ATTACK_LOG | jq .
            else
                echo "Attack log file not found. Run a task in rogue mode first."
            fi
        else
            echo "jq not installed. Install with: sudo apt-get install jq"
            echo "Raw attack logs:"
            cat $ATTACK_LOG 2>/dev/null || echo "Attack log file not found."
        fi
        ;;
    9)
        echo "=== Docker Logs (last 20 lines) ==="
        docker logs --tail=20 $CONTAINER_NAME
        echo ""
        echo "=== Attack Log File ==="
        if [ -f "$ATTACK_LOG" ]; then
            tail -10 $ATTACK_LOG
        else
            echo "No attack log file yet. Run a task in rogue mode first."
        fi
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
