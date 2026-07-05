# claude-put-in-work

A framework for autonomous, multi-session app building with Claude Code. Describe what you want built, run `build.sh`, and let Claude build it end-to-end — overnight if you want. In v3, a Strands-powered reviewer agent watches the build from Discord: it reviews every phase, runs the tests, screenshots the app, and holds the final phase to an approval gate — while you steer the build from your phone.

## How It Works

```
 1. PLAN                2. BUILD                        3. REVIEW

 Your idea/plan          ./build.sh ──────┬────────> ./reviewer.sh (auto)
       │                        │         │                  │
       v                        v         │                  v
/autonomous-build     ┌───────────────────┐       ┌──────────────────────┐
       │              │ Claude Code loop   │       │ Reviewer agent        │
       v              │ session 1 -> 2 ... │       │ (Discord + Strands)   │
┌─────────────┐       └────────┬──────────┘       └──────────┬───────────┘
│  PROMPT.md   │               │                              │
│  build.sh   │        after each phase:              reviews the phase:
│  reviewer/  │        appends "phase: N"             checklist + tests +
└─────────────┘        to .review/queue ────────────> screenshots, then
                               │                      posts a verdict
                               │                              │
                               v                              v
                     ┌──────────────────┐          ┌────────────────────┐
                     │ BUILD_PROGRESS.md │<─────────│ NEW_FEEDBACK.md     │
                     │ (session handoff) │ feedback │ .review/verdicts.md │
                     └──────────────────┘          └────────────────────┘
                     "ALL PHASES COMPLETE"          final phase requires
                      only after APPROVAL <───────── an APPROVED verdict
```

1. **Plan** — Describe your idea and run `/autonomous-build`. The skill generates a `PROMPT.md` spec, the `build.sh` runner, and the reviewer agent in your target project. Review the spec before running — it's your last checkpoint before autonomous execution.
2. **Build** — Run `./build.sh`. Claude Code runs in a loop, reading `BUILD_PROGRESS.md` each session to pick up where it left off. No human intervention needed until it's done.
3. **Review** — If Discord is configured, `build.sh` also starts the reviewer. Every completed phase gets reviewed with a verdict posted to your channel, you can chat with the reviewer about the build anytime, and the final phase can't complete without approval.

Two ideas make this work: `BUILD_PROGRESS.md` gives Claude continuity across sessions, and the `.review/` file contract lets a second agent supervise the first without either one blocking.

## Quick Start

### 1. Plan

```
/autonomous-build a task management app with categories and due dates
```

The skill asks clarifying questions, then generates `PROMPT.md`, `build.sh`, `notify.sh`, `reviewer.sh`, and `reviewer/` in your target project directory.

**Or manually:** Copy `SAMPLE_PROMPT.md` to `PROMPT.md` in your project and fill in the placeholders, then copy `build.sh`, `notify.sh`, `reviewer.sh`, and `reviewer/` alongside it.

### 2. Build

```bash
chmod +x build.sh notify.sh reviewer.sh
./build.sh
```

The script will:
- Confirm before starting (pass `--yes` to skip)
- Start the reviewer if configured (see [The Reviewer Agent](#the-reviewer-agent))
- Run Claude Code up to N sessions (configurable in `build.sh`)
- Log each session to `build-logs/`
- Stop early once `BUILD_PROGRESS.md` says all phases are complete — which, with the reviewer running, requires an APPROVED verdict on the final phase
- Post progress to Discord if `CLAUDE_DISCORD_WEBHOOK_URL` is set (see [Discord Notifications](#discord-notifications-webhook))

Check `BUILD_PROGRESS.md` anytime, or just ask the reviewer in Discord.

## The Reviewer Agent

The reviewer is a [Strands Agents](https://strandsagents.com) app (`reviewer/`) that runs alongside the build and talks to you through a Discord bot. It's opt-in: without its env vars, `./reviewer.sh start` no-ops and builds run exactly as before.

### What it does

- **Phase reviews.** After committing each phase, the builder appends `phase: N` to `.review/queue`. The reviewer picks it up, checks the phase against its `PROMPT.md` checklist, runs the project's test suite, screenshots the app with Playwright (on a dedicated review port, so it never collides with the build), and posts a report — with images — to your channel.
- **Verdicts and the final gate.** Every phase review ends in `APPROVED` or `CHANGES_REQUESTED (F-xxx)` recorded in `.review/verdicts.md`. Mid-build verdicts are advisory; the **final phase cannot complete without approval**. A heartbeat check means an offline reviewer never deadlocks the build, and `/approve` lets you override the gate yourself.
- **Feedback loop.** Findings are filed as numbered entries in `NEW_FEEDBACK.md`. Each build session addresses PENDING entries before starting new work and marks them ADDRESSED or DEFERRED — nothing gets silently dropped.
- **Conversation.** Plain messages in the channel are a chat with a persistent agent that can read the repo, run the tests, and take screenshots on demand. Ask what's left, ask for proof, or ask for a change — when you request one, it files a directive that **outranks the spec**, so you can change requirements mid-build from your phone.
- **Safety-net reviews.** If commits pile up with no review for an hour (`SAFETY_REVIEW_MINUTES`), it reviews anyway.

### Slash commands

| Command | What it does |
|---------|--------------|
| `/status` | Current phase plan with remaining tasks, progress, recent verdicts, open feedback |
| `/review` | Run a checkpoint review right now |
| `/pending` | List feedback the builder hasn't addressed yet |
| `/approve` | Human override: approve the final phase so the build can complete |
| `/shutdown` | Stop the bot (exports run metrics first) |

### Setup

1. **Discord bot** (once): [Developer Portal](https://discord.com/developers/applications) → New Application → Bot → enable **Message Content Intent** → copy the token. Invite it to your server with the **bot and applications.commands scopes** and Send Messages / Read Message History / Add Reactions / Attach Files permissions.
2. **Channel**: create one channel per build and copy its ID (Settings → Advanced → Developer Mode, then right-click the channel → Copy Channel ID).
3. **Environment** (exported, or in the project's `.env` — see `reviewer/.env.example`):

```bash
export ANTHROPIC_API_KEY="..."      # reviewer model access
export DISCORD_BOT_TOKEN="..."      # the bot token
export DISCORD_CHANNEL_ID="..."     # this build's channel
```

4. **Dependencies** (the skill does this for you on generated projects):

```bash
python3 -m venv .venv
.venv/bin/pip install -r reviewer/requirements.txt
.venv/bin/playwright install chromium
```

The reviewer defaults to Haiku 4.5 to keep review costs at pennies per build — set `REVIEWER_MODEL_ID` to use a bigger model.

### Testing and screenshots

`.review/config.json` tells the reviewer how to exercise the project:

```json
{
  "test_cmd": ".venv/bin/pytest -q",
  "app_start_cmd": "PORT={port} .venv/bin/python app.py",
  "review_port": 5599,
  "app_ready_seconds": 30,
  "screenshot_paths": ["/", "/dashboard"]
}
```

Omit `test_cmd` or `app_start_cmd` and the reviewer degrades gracefully to read-only for that capability.

### Lifecycle and multiple builds

`build.sh` runs `./reviewer.sh start` (idempotent), and the reviewer **outlives the build** — so when you wake up, you can ask it how the night went. Stop it with `/shutdown` or `./reviewer.sh stop`; `./reviewer.sh status` tells you if it's running.

Running two builds at once? Each project runs its own reviewer process with its own state — reuse the same bot token, but give **each build its own channel**.

Sessions, metrics, and an agent registry are written to `.agent_hub/` per project (or S3 with `USE_S3=true`), so you can inspect what any reviewer did after the fact.

## File Reference

| File | Purpose |
|------|---------|
| `PROMPT.md` | **Your app spec** — the prompt Claude reads each session. You create this (or the skill generates it). |
| `SAMPLE_PROMPT.md` | Annotated template with `[PLACEHOLDERS]`, `<!-- GUIDANCE -->` comments, and a minimal todo app example. |
| `build.sh` | Loop runner that pipes `PROMPT.md` into Claude Code repeatedly and starts the reviewer. |
| `reviewer.sh` | Manage the reviewer: `start` \| `stop` \| `status`. Safe to run unconfigured (no-ops). |
| `reviewer/` | The Strands reviewer agent — `agent.py`, model factory, prompts, tools, hub integration. |
| `notify.sh` | Optional Discord webhook notifier. No-ops unless `CLAUDE_DISCORD_WEBHOOK_URL` is set. |
| `BUILD_PROGRESS.md` | Auto-generated during builds. Tracks completed/in-progress/next steps across sessions. |
| `NEW_FEEDBACK.md` | Auto-generated feedback ledger — reviewer findings and your Discord requests, each with a status. |
| `.review/` | Auto-generated reviewer state: review queue, verdicts, heartbeat, screenshots, app config. |
| `build-logs/` | Auto-generated. One log per build session plus `reviewer.log`. |

## Anatomy of a Good PROMPT.md

A well-structured prompt has these sections:

1. **Multi-session continuity block** — Instructions to read `BUILD_PROGRESS.md` and assess project state before doing anything
2. **Mission** — What you're building and why
3. **Core workflows** — What users can DO with the app
4. **Context** — Files, repos, and docs the agent needs to read
5. **Tech stack** — Explicit language, framework, database, and library choices
6. **Design requirements** — UI specs, colors, component patterns (if applicable)
7. **Architecture** — How pieces connect, data models, storage, API endpoints
8. **Documentation rules** — What docs to maintain and when to update them
9. **Build order** — Phased plan where each phase is testable and completable in one session
10. **Reviewer feedback loop** — How to request phase reviews, handle feedback, and clear the final approval gate
11. **Security & commit rules** — Safety rails for git operations and secret protection

See the [Tips section](SAMPLE_PROMPT.md#tips-for-writing-a-great-promptmd) in `SAMPLE_PROMPT.md` for detailed advice.

## Discord Notifications (webhook)

Separate from the reviewer bot: lightweight one-way pings from the build loop itself, useful even without the reviewer. Opt-in, and the build behaves identically without them.

**Setup:**

1. In Discord: Server Settings → Integrations → Webhooks → New Webhook → Copy Webhook URL
2. Export it before running the build:

```bash
export CLAUDE_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
./build.sh
```

To post to several channels at once, comma-separate the URLs.

**What you'll get:**

| When | Message |
|------|---------|
| Build starts | 🚀 Project name, start time, max sessions |
| Phase completes | ✅ Phase number + one-line summary (sent by the agent mid-session) |
| Agent hits a blocker | 🚧 What's blocking and what it's trying |
| Session ends | ✅/⚠️ Duration, exit code, and the next step from `BUILD_PROGRESS.md` |
| Build finishes | 🏁 Total sessions and total duration |

The webhook URL stays in your environment — never commit it to the repo or hardcode it in any file.

## Configuring build.sh

Edit `build.sh` to adjust:

```bash
MAX_RUNS=10          # Maximum number of Claude sessions
sleep 5              # Pause between sessions (seconds)
```

### Security Considerations

The script uses `--dangerously-skip-permissions` so Claude can execute shell commands, write files, and commit code without prompting for approval. This is what makes unattended builds possible — but it means Claude has full system access during the run.

**What this means:**
- Claude can run any shell command, read/write any file, and make git commits
- There are no interactive "allow this action?" prompts
- Your `PROMPT.md` security rules are the primary guardrails

**How to mitigate risk:**
- Always include the security & commit rules section in your `PROMPT.md` (the template includes these by default)
- Run builds in an isolated environment (container, VM, or dedicated machine) when possible
- Review `build-logs/` and `git log` after the build completes
- Keep sensitive files (`.env`, credentials) outside the project directory or in `.gitignore`
- Never store API keys, tokens, or passwords in files within the project — use environment variables

The reviewer is read-only by design outside of two append-only files (`NEW_FEEDBACK.md`, `.review/verdicts.md`) plus running your configured test command — and its file-reading tool blocks `.env`, `secrets/`, and `.git` so credentials can't leak into Discord.

**Running interactively:** Remove `--dangerously-skip-permissions` from `build.sh` if you'd rather approve each action — but each session will block waiting for your input.

## Tips

- **Phase sizing matters** — Each phase should be completable in one session (~1-3 hours of agent work). If a phase has 15+ tasks, split it.
- **Absolute paths** — Use full paths in your prompt so they work across sessions.
- **Verification steps** — Include concrete test steps in each phase ("Test: create X -> see Y"). This lets Claude confirm its own work.
- **Reference projects** — "Follow the architecture of /path/to/project" is more precise than pages of architecture description.
- **Security rules prevent disasters** — Without explicit rules, the agent may `git add .` and commit secrets or generated files.
- **Early completion** — When Claude writes "ALL PHASES COMPLETE" at the top of `BUILD_PROGRESS.md`, the runner stops — no wasted sessions.
- **Steer with feedback, not restarts** — Mid-build course corrections belong in the Discord channel. A message like "use cursor pagination instead" reaches the very next session; killing the build loses a session's context for nothing.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- A shell environment (bash/zsh)
- For the reviewer: Python 3.10+, an [Anthropic API key](https://console.anthropic.com/), and a Discord server you can add a bot to

## License

[MIT](LICENSE)
