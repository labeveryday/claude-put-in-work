#!/bin/bash
# reviewer.sh — manage the Discord build reviewer for this project.
#
# Usage:  ./reviewer.sh start|stop|status
#
# start is idempotent (safe for build.sh to call every run) and exits 0 as a
# no-op when the reviewer isn't configured, so the build never breaks on it.
# The reviewer outlives the build — stop it with ./reviewer.sh stop or the
# /shutdown slash command in Discord.

set -euo pipefail
cd "$(dirname "$0")"

PIDFILE=".review/pid"
LOGFILE="build-logs/reviewer.log"

running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

# Set in the environment, or present in .env (agent.py loads .env itself)
have() { [ -n "${!1:-}" ] || grep -q "^$1=" .env 2>/dev/null; }

case "${1:-status}" in
    start)
        if running; then
            echo "Reviewer already running (PID $(cat "$PIDFILE"))"
            exit 0
        fi
        for var in DISCORD_BOT_TOKEN DISCORD_CHANNEL_ID ANTHROPIC_API_KEY; do
            if ! have "$var"; then
                echo "Reviewer disabled — $var not set (in environment or .env)"
                exit 0
            fi
        done
        PY="python3"; [ -x ".venv/bin/python" ] && PY=".venv/bin/python"
        mkdir -p .review build-logs
        nohup "$PY" reviewer/agent.py >> "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
        echo "Reviewer started (PID $(cat "$PIDFILE")) — log: $LOGFILE"
        ;;
    stop)
        if running; then
            kill "$(cat "$PIDFILE")" && rm -f "$PIDFILE"
            echo "Reviewer stopped"
        else
            rm -f "$PIDFILE"
            echo "Reviewer not running"
        fi
        ;;
    status)
        if running; then
            echo "Reviewer running (PID $(cat "$PIDFILE")) — log: $LOGFILE"
        else
            echo "Reviewer not running"
        fi
        ;;
    *)
        echo "Usage: ./reviewer.sh start|stop|status"
        exit 1
        ;;
esac
