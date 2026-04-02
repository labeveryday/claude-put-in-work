#!/bin/bash
# Autonomous multi-session build runner
# Usage: ./build.sh [--yes]
#   --yes    Skip confirmation prompt

set -euo pipefail

cd "$(dirname "$0")"

MAX_RUNS=10
RUN=0
LOG_DIR="build-logs"

# --- Pre-flight checks ---
if [ ! -f "PROMPT.md" ]; then
    echo "ERROR: PROMPT.md not found in $(pwd)"
    echo ""
    echo "Create a PROMPT.md with your build spec before running."
    echo "Options:"
    echo "  1. Use the /autonomous-build skill in Claude Code"
    echo "  2. Copy and fill in SAMPLE_PROMPT.md manually"
    exit 1
fi

mkdir -p "$LOG_DIR"

echo "============================================"
echo "  Autonomous Build Runner"
echo "============================================"
echo "Max sessions: $MAX_RUNS"
echo "Prompt:       PROMPT.md ($(wc -l < PROMPT.md | tr -d ' ') lines)"
echo "Logs:         $LOG_DIR/"
echo "Started:      $(date)"
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

while [ $RUN -lt $MAX_RUNS ]; do
    RUN=$((RUN + 1))
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOG_DIR/run_${RUN}_${TIMESTAMP}.log"

    echo ">>> Session $RUN/$MAX_RUNS - $(date)"
    echo ">>> Log: $LOG_FILE"
    echo ""

    cat PROMPT.md | claude --dangerously-skip-permissions 2>&1 | tee "$LOG_FILE"

    EXIT_CODE=${PIPESTATUS[1]}
    echo ""
    echo ">>> Session $RUN finished (exit $EXIT_CODE) at $(date)"
    echo ""

    # Check if BUILD_PROGRESS.md indicates completion
    if [ -f "BUILD_PROGRESS.md" ]; then
        if grep -qi "all phases complete\|build complete\|all.*done" BUILD_PROGRESS.md 2>/dev/null; then
            echo ">>> BUILD_PROGRESS.md indicates build is complete. Stopping early."
            break
        fi
    fi

    # Pause between sessions
    if [ $RUN -lt $MAX_RUNS ]; then
        sleep 5
    fi
done

echo ""
echo "============================================"
echo "  Build finished — $RUN session(s) ran"
echo "  $(date)"
echo "============================================"
if [ -f "BUILD_PROGRESS.md" ]; then
    echo ""
    echo "Progress summary:"
    head -30 BUILD_PROGRESS.md
fi
