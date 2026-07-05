#!/bin/bash
# Autonomous multi-session build runner
# Usage: ./build.sh [--yes]
#   --yes    Skip confirmation prompt

set -euo pipefail

cd "$(dirname "$0")"

MAX_RUNS=10
RUN=0
LOG_DIR="build-logs"

# Discord notifications go through notify.sh, which no-ops when
# CLAUDE_DISCORD_WEBHOOK_URL is unset or the script is missing.
notify() { [ -x "./notify.sh" ] && ./notify.sh "$1" || true; }

# --- Pre-flight checks ---
if [ ! -f "PROMPT.md" ]; then
    echo "ERROR: PROMPT.md not found in $(pwd)"
    echo "Create a PROMPT.md with your build spec before running."
    echo ""
    echo "Options:"
    echo "  1. Use the /autonomous-build skill to generate one"
    echo "  2. Copy and fill in SAMPLE_PROMPT.md manually"
    exit 1
fi

mkdir -p "$LOG_DIR"

PROJECT_NAME=$(basename "$PWD")
BUILD_START=$(date +%s)

echo "============================================"
echo "  Autonomous Build Runner"
echo "============================================"
echo "Max sessions: $MAX_RUNS"
echo "Prompt:       PROMPT.md ($(wc -l < PROMPT.md | tr -d ' ') lines)"
echo "Logs:         $LOG_DIR/"
echo "Started:      $(date)"
if [ -n "${CLAUDE_DISCORD_WEBHOOK_URL:-}" ]; then
    echo "Discord:      notifications enabled"
else
    echo "Discord:      disabled (export CLAUDE_DISCORD_WEBHOOK_URL to enable)"
fi
if [ -n "${DISCORD_BOT_TOKEN:-}" ] && [ -n "${DISCORD_CHANNEL_ID:-}" ] && [ -n "${ANTHROPIC_API_KEY:-}" ] && [ -f "reviewer/agent.py" ]; then
    echo "Reviewer:     enabled (phase reviews + final gate via Discord)"
else
    echo "Reviewer:     disabled (need DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, ANTHROPIC_API_KEY)"
fi
echo "============================================"
echo ""

# Confirm unless --yes flag is passed
if [ "${1:-}" != "--yes" ]; then
    echo "This will run Claude Code with --dangerously-skip-permissions."
    echo "Claude will have full system access during the build."
    echo ""
    read -r -p "Continue? [y/N] " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# Clean exit on Ctrl+C
trap 'echo ""; echo ">>> Build interrupted at session $RUN/$MAX_RUNS"; exit 130' INT

# Ensure the Discord reviewer is up (idempotent; no-ops unless configured).
# It deliberately outlives the build — stop it with ./reviewer.sh stop or /shutdown.
[ -x "./reviewer.sh" ] && ./reviewer.sh start || true

notify "🚀 **$PROJECT_NAME** build started — $(date '+%a %b %d, %I:%M %p') (up to $MAX_RUNS sessions)"

while [ $RUN -lt $MAX_RUNS ]; do
    RUN=$((RUN + 1))
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOG_DIR/run_${RUN}_${TIMESTAMP}.log"

    echo ">>> Session $RUN/$MAX_RUNS - $(date)"
    echo ">>> Log: $LOG_FILE"
    echo ""

    RUN_START=$(date +%s)
    EXIT_CODE=0
    # With pipefail, this captures claude's exit code without tripping set -e
    cat PROMPT.md | claude --dangerously-skip-permissions 2>&1 | tee "$LOG_FILE" || EXIT_CODE=$?
    RUN_MINS=$(( ($(date +%s) - RUN_START) / 60 ))

    echo ""
    echo ">>> Session $RUN finished (exit $EXIT_CODE) after ${RUN_MINS}m at $(date)"
    echo ""

    # Surface the latest "Next Step" from BUILD_PROGRESS.md in the Discord feed
    NEXT_STEP=""
    if [ -f "BUILD_PROGRESS.md" ]; then
        NEXT_STEP=$(awk '/[Nn]ext [Ss]tep/{flag=1; next} flag && NF{print; exit}' BUILD_PROGRESS.md)
    fi

    if [ "$EXIT_CODE" -eq 0 ]; then
        notify "✅ **$PROJECT_NAME** session $RUN/$MAX_RUNS finished in ${RUN_MINS}m. Next: ${NEXT_STEP:-see BUILD_PROGRESS.md}"
    else
        notify "⚠️ **$PROJECT_NAME** session $RUN/$MAX_RUNS exited with code $EXIT_CODE after ${RUN_MINS}m — check build-logs/"
    fi

    # Stop early once BUILD_PROGRESS.md declares the build done
    if [ -f "BUILD_PROGRESS.md" ] && grep -qi "all phases complete" BUILD_PROGRESS.md 2>/dev/null; then
        echo ">>> BUILD_PROGRESS.md indicates build is complete. Stopping early."
        break
    fi

    if [ $RUN -lt $MAX_RUNS ]; then
        sleep 5
    fi
done

TOTAL_MINS=$(( ($(date +%s) - BUILD_START) / 60 ))
notify "🏁 **$PROJECT_NAME** build complete — $RUN session(s) in $((TOTAL_MINS / 60))h $((TOTAL_MINS % 60))m"

echo ""
echo "============================================"
echo "  Build finished — $RUN session(s) ran"
echo "  Total time: $((TOTAL_MINS / 60))h $((TOTAL_MINS % 60))m"
echo "  $(date)"
echo "============================================"
if [ -f "BUILD_PROGRESS.md" ]; then
    echo ""
    echo "Progress summary:"
    head -30 BUILD_PROGRESS.md
fi
