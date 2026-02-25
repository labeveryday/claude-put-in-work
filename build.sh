#!/bin/bash
# Autonomous multi-session build runner
# Usage: ./build.sh

set -e

cd "$(dirname "$0")"

MAX_RUNS=10
RUN=0
LOG_DIR="build-logs"
mkdir -p "$LOG_DIR"

echo "============================================"
echo "  Autonomous Build Runner"
echo "============================================"
echo "Max runs: $MAX_RUNS"
echo "Logs: $LOG_DIR/"
echo "Started: $(date)"
echo "============================================"
echo ""

while [ $RUN -lt $MAX_RUNS ]; do
    RUN=$((RUN + 1))
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOG_DIR/run_${RUN}_${TIMESTAMP}.log"

    echo ">>> Run $RUN/$MAX_RUNS - $(date)"
    echo ">>> Log: $LOG_FILE"
    echo ""

    cat PROMPT.md | claude --dangerously-skip-permissions 2>&1 | tee "$LOG_FILE"

    EXIT_CODE=${PIPESTATUS[1]}
    echo ""
    echo ">>> Run $RUN finished with exit code $EXIT_CODE at $(date)"
    echo ""

    # Short pause between runs so it doesn't hammer immediately
    sleep 5
done

echo "============================================"
echo "  Build complete - $RUN runs finished"
echo "  $(date)"
echo "============================================"
