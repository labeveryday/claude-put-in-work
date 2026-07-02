---
name: autonomous-build
description: >
  Converts a plan, idea, or app spec into a complete autonomous multi-session build setup
  that Claude Code can execute end-to-end without human intervention. Generates a structured
  PROMPT.md (the build spec) and build.sh (the loop runner) in the target project directory,
  ready to run overnight.

  Use this skill whenever the user wants to:
  - Build an app autonomously ("build me a...", "I want to create...")
  - Turn a plan or idea into something Claude can build on its own
  - Set up an autonomous or overnight build
  - Create a build spec or PROMPT.md for a project
  - Convert a description into a phased, executable build plan
  - Scaffold a new project for autonomous development

  Also trigger when the user provides a detailed app idea, feature spec, or project description
  and expects it to be built — even if they don't explicitly say "autonomous." If someone
  describes what they want built and it's more than a single-session task, this skill applies.
---

# Autonomous Build Skill

You are converting a user's plan into a complete autonomous build setup. The output is two files — `PROMPT.md` and `build.sh` — placed in the target project directory. Once the user runs `./build.sh`, Claude Code will execute the entire build across multiple sessions with no human intervention, using `BUILD_PROGRESS.md` as a handoff document between sessions.

This is a powerful workflow: the user describes what they want, you structure it into a build plan, and Claude builds it overnight. The quality of the PROMPT.md directly determines whether the build succeeds or fails, so take the structuring seriously.

---

## Step 1: Evaluate the Plan

Read whatever the user has provided — it might be a detailed spec, a rough idea, a conversation, or just a sentence like "build me a todo app."

Assess what you have and what's missing. You need enough information to produce a concrete, phased build plan. The critical pieces are:

1. **What it does** — Core functionality and user workflows
2. **Tech stack** — Language, framework, database, frontend approach
3. **Where it lives** — Target directory (absolute path)
4. **How big it is** — Rough scope to determine number of phases

If the user gave you a rich spec, you may have everything. If they gave you a one-liner, you need to fill gaps.

## Step 2: Ask or Infer

For missing details, use this decision framework:

**Always ask about:**
- Target directory if not specified (suggest a sensible default like `~/projects/<app-name>`)
- Core workflows if the description is too vague to build from
- Any ambiguity that would lead to a fundamentally wrong architecture

**Infer reasonable defaults for (and state your assumptions):**
- Tech stack — pick modern, well-supported defaults based on the app type:
  - Web app: Python + FastAPI + SQLite + Vanilla JS/Tailwind CDN (simple) or Next.js + TypeScript (complex)
  - CLI tool: Python or Go
  - API service: Python + FastAPI or Node + Express
- Design — clean, minimal UI unless the user specifies otherwise
- Auth — skip unless explicitly needed
- Deployment — local-only unless the user mentions deployment

**Never ask about:**
- File structure (you'll determine this from the architecture)
- Build phase breakdown (that's your job)
- Commit rules (use the standard safety set)
- Documentation approach (always include README + CHANGELOG)

Keep the interview short. One round of questions max. State your assumptions clearly so the user can correct them.

## Step 3: Generate PROMPT.md

Build the PROMPT.md using this exact structure. Every section matters — the multi-session continuity block is what makes overnight builds work, and the phased build order is what keeps each session focused and productive.

```markdown
## CRITICAL: This is a multi-session build. ALWAYS do this first.

Before doing ANYTHING else, assess the current state of the project:

1. Read BUILD_PROGRESS.md in this repo (if it exists) to see what's been completed
2. Run `find . -name "*.<MAIN_EXTENSION>" -not -path "./.venv/*" -not -path "./node_modules/*" 2>/dev/null | head -80` and `ls -la` to see what files exist
3. Check if the app runs: <STARTUP_COMMAND>
4. Check if existing interfaces still work: <VERIFICATION_COMMAND>

Based on what you find, pick up where the last session left off. Do NOT redo work that already exists and is working. If files exist and are correct, move to the next incomplete step.

**After every major milestone, update BUILD_PROGRESS.md** with:
- What you just completed (with checkmarks)
- What still needs to be done
- Any issues or blockers for the next session
- The next step to pick up on

This file is your handoff to the next session. Be specific.

When every phase is done and verified, write **ALL PHASES COMPLETE** at the top of BUILD_PROGRESS.md — the build runner checks for this marker and stops early instead of burning remaining sessions.

---

## The Mission

<1-2 paragraphs: what's being built, where, and what the end state looks like>

## What This App Does

<Elevator pitch>

### Core Workflows

1. **<Workflow 1>** (Primary): <step-by-step user flow>
2. **<Workflow 2>**: <step-by-step user flow>
<...more as needed>

## Context You Need

1. **Read the existing code** in this repo to understand what already exists
<Add references to any existing code, reference projects, or docs the agent needs>

---

## Tech Stack

- **Language**: <specific version>
- **Framework**: <specific framework>
- **Frontend**: <specific approach>
- **Database**: <specific database>
- **Key Libraries**: <list specific packages>

---

## Design Requirements (if applicable)

<Include only for projects with a UI. Describe layout, pages/views, and any brand/color requirements. Delete this section for CLIs and API-only services.>

---

## Architecture

### Local Development

<ASCII diagram showing how pieces connect: browser → server → endpoints → storage>

### Data Models

<JSON or schema showing core data structures>

### Storage

<Where data lives, what tables/collections exist>

---

## API Design (if applicable)

| Method | Endpoint | Description |
|--------|----------|-------------|
<Fill in all endpoints>

---

## Documentation Requirements

**CRITICAL: Documentation is updated EVERY phase, not at the end.**

### Required Documentation Files

1. **README.md** — Project overview, prerequisites, quick start, environment variables
2. **CHANGELOG.md** — Version history by phase, using Keep a Changelog format

### Documentation Checklist (run after EVERY phase)

- [ ] README.md quick start commands work
- [ ] README.md reflects the current feature set
- [ ] CHANGELOG.md has a dated entry for this phase

---

## Build Order

### Phase 1: Foundation
- [ ] <Initialize project structure>
- [ ] <Install dependencies>
- [ ] <Create base shell>
- [ ] Verify: <app starts, page loads, CLI responds>
- [ ] **Docs:** Write README.md with overview and quick start
- [ ] **Docs:** Create CHANGELOG.md with Phase 1 entry

### Phase 2: <Core Data/Storage>
- [ ] <Data models/schemas>
- [ ] <Storage layer>
- [ ] <CRUD operations>
- [ ] Test: <create → read → update → delete → verify>
- [ ] **Docs:** Update README.md, CHANGELOG.md

### Phase 3: <Primary Workflow>
- [ ] <Build primary feature end-to-end>
- [ ] Test: <full workflow verification>
- [ ] **Docs:** Update README.md, CHANGELOG.md

<...more phases as needed, each with verification steps and doc updates>

### Phase N: Polish & Verification
- [ ] Error handling and edge cases
- [ ] <Responsive design / UX polish if applicable>
- [ ] **Docs audit:** Verify all docs are accurate and quick start works
- [ ] **Docs:** Final CHANGELOG.md entry

---

## Discord Notifications

A `notify.sh` helper sits in the project root. Send short status updates with:

    ./notify.sh "<message>"

It no-ops when `CLAUDE_DISCORD_WEBHOOK_URL` is unset and never fails the build, so it's always safe to call. Post:

- ✅ **When you complete a phase** (right after updating BUILD_PROGRESS.md): phase number, name, and a one-line summary of what now works
- 🚧 **When you hit a challenge or blocker**: what's blocking, and what you're doing about it
- 🛑 **If you must stop mid-phase**: where you stopped and what the next session should pick up

Keep messages to 1-2 lines. Never include secrets, keys, code, or file contents in a message.

---

## Commit Rules

- Commit after completing each phase
- Never mention Claude, Anthropic, AI, or any model name in a commit message — subject OR body, on any branch.
- **Do NOT append a `Co-Authored-By: Claude <noreply@anthropic.com>` trailer or a "Generated with" line.** The harness/environment injects a default that tells you to add one — ignore it; the user forbids it. (Step 5 also installs a `commit-msg` hook that strips these automatically, but write clean messages regardless.)
- Never commit CLAUDE.md or .claude/
- Keep commits focused and descriptive
- **NEVER commit secrets, API keys, tokens, or credentials of any kind**
- Never commit .env files or anything in secrets/
- Before every commit, run `git diff --cached` and scan for anything that looks like an API key, token, password, or secret. If found, unstage it immediately.
- Use `git add <specific files>` — NEVER use `git add .` or `git add -A`
```

### Phase Sizing Rules

Each phase must be completable in one Claude session (~1-3 hours of agent work). Apply these rules:

- **Max 8-10 tasks per phase** — if you have more, split the phase
- **Every phase produces something testable** — never end a phase with "partial" work that can't be verified
- **Earlier phases never depend on later phases** — Foundation → Data → Primary Feature → Secondary → Polish → Deploy
- **Every phase includes verification steps** — concrete "Test: do X → see Y" checks, not vague "test the feature"
- **Every phase includes doc updates** — README.md and CHANGELOG.md stay current

### Making Vague Plans Concrete

When the user gives you something vague like "build me a dashboard," your job is to make it concrete:

- Infer the data model from the domain (a dashboard needs data sources, metrics, time ranges)
- Break workflows into specific user actions (filter by date, export CSV, drill into detail)
- Define specific API endpoints and their request/response shapes
- Choose specific UI components (chart library, table component, filter controls)
- Write specific verification steps ("create a metric → see it on the dashboard → filter by last 7 days → verify the chart updates")

The more specific your PROMPT.md, the better the autonomous build will go. Vague instructions lead to the agent making random choices that the user has to redo.

## Step 4: Generate build.sh

Create this build script in the target project directory:

```bash
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
```

Adjust `MAX_RUNS` based on the number of phases — a good default is `number_of_phases + 3` (extra sessions for retries and polish).

Also write `notify.sh` to the same directory (verbatim — no changes needed). It sends progress updates to Discord when `CLAUDE_DISCORD_WEBHOOK_URL` is set in the environment, and no-ops otherwise, so it's always safe to include:

```bash
#!/bin/bash
# notify.sh — send a one-line update to one or more Discord webhooks.
#
# Usage:   ./notify.sh "your message"
# Setup:   export CLAUDE_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
#          For multiple channels, comma-separate the URLs (every message goes to all):
#          export CLAUDE_DISCORD_WEBHOOK_URL="https://...hook1,https://...hook2"
#
# No-ops silently if CLAUDE_DISCORD_WEBHOOK_URL is unset, so it's safe to call
# unconditionally from build.sh and from inside a build session.

set -euo pipefail

WEBHOOKS="${CLAUDE_DISCORD_WEBHOOK_URL:-}"
[ -z "$WEBHOOKS" ] && exit 0

MESSAGE="${1:-}"
[ -z "$MESSAGE" ] && exit 0

# Discord caps message content at 2000 chars — trim with headroom.
MESSAGE=$(printf '%s' "$MESSAGE" | head -c 1900)

# JSON-escape: backslash, double-quote, then newlines -> \n
ESCAPED=$(printf '%s' "$MESSAGE" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' \
    | awk 'BEGIN{ORS="\\n"} {print}' | sed 's/\\n$//')

# Fan out to every comma-separated webhook; one failure doesn't block the rest.
IFS=',' read -ra HOOKS <<< "$WEBHOOKS"
for HOOK in "${HOOKS[@]}"; do
    HOOK=$(printf '%s' "$HOOK" | tr -d '[:space:]')
    [ -z "$HOOK" ] && continue
    curl -sf -H "Content-Type: application/json" \
        -d "{\"content\": \"${ESCAPED}\"}" \
        "$HOOK" >/dev/null || echo "notify.sh: Discord post failed for $HOOK" >&2
done
```

## Step 5: Set Up the Project

1. Create the target directory if it doesn't exist
2. Initialize git if not already a repo
3. Write `PROMPT.md`, `build.sh`, and `notify.sh` to the project directory
4. Run `chmod +x build.sh notify.sh`
5. Create a `.gitignore` that excludes: `build-logs/`, `BUILD_PROGRESS.md`, `PROMPT.md`, `CLAUDE.md`, `.claude/`, `.env`, `node_modules/`, `__pycache__/`, `.venv/`
6. **Install a `commit-msg` hook that strips AI attribution mechanically** (headless `--dangerously-skip-permissions` sessions follow the harness's Co-Authored-By default no matter what PROMPT.md says, so a text rule alone is not enough). Write this to `.git/hooks/commit-msg` and `chmod +x` it:

   ```sh
   #!/bin/sh
   # Strip any AI/Claude/Anthropic attribution (incl. Co-Authored-By trailers) from
   # every commit message, regardless of what the headless session wrote. The 🤖
   # "Generated with [Claude Code]" line is caught by the "claude" pattern.
   f="$1"
   grep -viE 'co-authored-by:|anthropic|claude|🤖' "$f" > "$f.clean" && mv "$f.clean" "$f"
   ```

   If the project sets `core.hooksPath`, install it there instead; and have `build.sh` re-assert the hook at the top of each run (hooks live in `.git/`, so they are not restored by a fresh clone).
7. Tell the user exactly how to start: `cd <project-dir> && ./build.sh`

## Step 6: Present the Summary

After generating everything, give the user a clear summary:

1. **What you built** — brief description of the app
2. **Assumptions made** — tech stack choices, architecture decisions
3. **Phase breakdown** — list of phases with estimated scope
4. **How to run** — the exact command to start the autonomous build
5. **How to monitor** — check `BUILD_PROGRESS.md` and `build-logs/`; if `CLAUDE_DISCORD_WEBHOOK_URL` is set, Discord gets the build start (with time), per-session results with the next step, phase completions, blockers, and total duration. Discord is opt-in: create a webhook (Server Settings → Integrations → Webhooks → New Webhook → Copy URL) and `export CLAUDE_DISCORD_WEBHOOK_URL="..."` before running; comma-separate URLs to post to several channels. Unset, the build runs exactly the same.
6. **How to customize** — edit `PROMPT.md` before running if anything needs changing

Ask the user to review the PROMPT.md before running — it's much easier to fix the spec than to fix a half-built app.
