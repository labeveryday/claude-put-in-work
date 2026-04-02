---
name: autonomous-build
description: Converts a plan, idea, or app spec into a complete autonomous multi-session build setup that Claude Code can execute end-to-end without human intervention. Generates a structured PROMPT.md (the build spec) and build.sh (the loop runner) in the target project directory, ready to run overnight.
argument-hint: "[project description or path to existing spec]"
---

# Autonomous Build Setup

You are generating the files a user needs to run an autonomous multi-session build: `PROMPT.md` and `build.sh`.

Use this skill whenever the user wants to:
- Build an app autonomously ("build me a...", "I want to create...")
- Turn a plan or idea into something Claude Code can build on its own
- Set up an autonomous or overnight build
- Create a build spec or PROMPT.md for a project
- Convert a description into a phased, executable build plan
- Scaffold a new project for autonomous development

Also trigger when the user provides a detailed app idea, feature spec, or project description and expects it to be built — even if they don't explicitly say "autonomous." If someone describes what they want built and it's more than a single-session task, this skill applies.

## Your Job

1. **Gather requirements** by asking the user about their project. Don't ask everything at once — have a conversation. Start with the big picture, then drill into specifics.
2. **Write `PROMPT.md`** in the user's target project directory
3. **Write `build.sh`** in the same directory
4. **Tell the user what to do next** — review, then run

## Step 1: Gather Requirements

If the user provided a description with `$ARGUMENTS`, use that as a starting point. Otherwise, ask.

Ask about these in order, skipping what's already clear:

1. **What are you building?** — App name, what it does, who it's for
2. **Where should it live?** — Absolute path for the project directory
3. **Tech stack** — Language, framework, frontend approach, database, key libraries. If the user is unsure, make a recommendation based on what they're building.
4. **Core workflows** — What can a user DO with this app? Walk through the primary flows.
5. **Architecture** — API endpoints, data models, how pieces connect. Sketch this out with the user.
6. **Design requirements** — Only if there's a UI. Colors, layout, component style. If the user doesn't care, skip this section entirely in the output.
7. **Number of sessions** — How many build.sh loops? Default is 10. More phases = more sessions needed.

Don't ask about:
- Commit rules (use the standard set)
- Multi-session continuity block (always include it)
- Documentation requirements (always include the standard set)
- BUILD_PROGRESS.md format (standardized)

## Step 2: Write PROMPT.md

Write `PROMPT.md` to the target project directory. Read `SAMPLE_PROMPT.md` from this repo first to follow its structure — but with ALL placeholders filled in and ALL guidance comments removed.

**To find the template:** Look for `SAMPLE_PROMPT.md` in the repo that contains this skill file (the `claude-put-in-work` repo). Read it before generating the output.

The output should be a clean, ready-to-run prompt with no template artifacts.

**Critical rules for the generated PROMPT.md:**

- Use ABSOLUTE paths everywhere (the user's project path, not relative)
- Every phase must have concrete verification steps ("Test: do X -> see Y")
- Each phase should be completable in one session (~1-3 hours of agent work)
- Phase 1 is always foundation (skeleton + "it starts")
- Final phase is always polish + verification
- Include the multi-session continuity block at the top (with real commands for the chosen stack)
- Include the standard commit rules and security rules
- Include documentation requirements with per-phase checklist
- Include the "ALL PHASES COMPLETE" instruction for BUILD_PROGRESS.md
- Do NOT include the "Minimal Example" or "Tips" sections — those are template-only

**Security rules to always include in the generated PROMPT.md:**

- Never commit secrets, API keys, tokens, or credentials
- Never commit .env files
- Before every commit, scan staged changes for secrets
- Use `git add <specific files>` — never `git add .` or `git add -A`
- Never use `--force` with git push
- Never run destructive commands outside the project directory
- If the project needs API keys, read them from environment variables, never hardcode them

**Phase sizing guidance:**
- Simple app (todo, blog, calculator): 3-4 phases
- Medium app (dashboard, CRUD with auth, API service): 5-7 phases
- Complex app (multi-service, real-time, deployment): 8-10 phases

## Step 3: Write build.sh

Write `build.sh` to the same directory. Use this exact script, only changing `MAX_RUNS` based on the number of phases (set it to number of phases + 2 to give buffer):

```bash
#!/bin/bash
# Autonomous multi-session build runner
# Usage: ./build.sh [--yes]
#   --yes    Skip confirmation prompt

set -euo pipefail

cd "$(dirname "$0")"

MAX_RUNS={{MAX_RUNS}}
RUN=0
LOG_DIR="build-logs"

# --- Pre-flight checks ---
if [ ! -f "PROMPT.md" ]; then
    echo "ERROR: PROMPT.md not found in $(pwd)"
    echo "Create a PROMPT.md with your build spec before running."
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
```

Replace `{{MAX_RUNS}}` with the actual number.

After writing both files, run `chmod +x build.sh` in the target directory.

## Step 4: Summary

After writing both files, tell the user:

1. Where the files were written
2. How many phases and sessions are configured
3. Suggest they review `PROMPT.md` — especially the tech stack, architecture, and phase breakdown
4. Tell them to run: `cd <project-path> && ./build.sh`
5. Remind them they can check progress in `BUILD_PROGRESS.md` and logs in `build-logs/`
6. Remind them to review `build-logs/` and `git log` after the build for any issues
