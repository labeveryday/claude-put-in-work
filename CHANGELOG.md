# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [3.0.0] - 2026-07-05

v3: the build gets a supervisor. A Strands-powered reviewer agent runs alongside the build loop, reviews every phase, and holds the final phase to an approval gate — all from a Discord channel you can talk to.

### Added
- `reviewer/` — Strands agent (Discord bot) with two roles sharing one toolset:
  - Phase reviews: when the builder appends `phase: N` to `.review/queue`, the reviewer checks the phase against its `PROMPT.md` checklist, runs the test suite, screenshots the app with Playwright on a dedicated review port, posts the report + images to Discord, and records `APPROVED` / `CHANGES_REQUESTED` in `.review/verdicts.md`
  - Chat: plain channel messages hit a persistent agent with sliding-window memory that reads the repo, runs tests, and screenshots on demand; requested changes are filed as directives that outrank the spec
- Final-phase approval gate — the build cannot write `ALL PHASES COMPLETE` until the last phase has an `APPROVED` verdict; a heartbeat check keeps an offline reviewer from ever blocking a build
- Slash commands: `/status` (phase plan + remaining tasks + verdicts + open feedback), `/review`, `/pending`, `/approve` (human gate override), `/shutdown`
- `NEW_FEEDBACK.md` feedback ledger — numbered entries with PENDING/ADDRESSED/DEFERRED status; build sessions address open entries before new work
- `reviewer.sh` — `start | stop | status` with a pidfile; `start` is idempotent and no-ops when unconfigured
- Safety-net review when commits land with no review for `SAFETY_REVIEW_MINUTES` (default 60)
- `.review/config.json` — per-project test command, app start command, review port, and screenshot paths; the reviewer degrades to read-only when values are omitted
- Hub observability — per-project agent registry, per-run sessions, and metrics in `.agent_hub/` (S3 optional via `USE_S3`)
- `reviewer/.env.example` documenting all reviewer configuration
- Reviewer Feedback Loop & Phase Reviews section in `SAMPLE_PROMPT.md` defining the builder↔reviewer file contract
- Multi-build support — one reviewer process and one Discord channel per project on a shared bot token

### Changed
- `build.sh` now starts the reviewer via `./reviewer.sh start` and reports reviewer status in the pre-flight header; the reviewer deliberately outlives the build so you can discuss results after it finishes
- `/autonomous-build` skill generates the reviewer, `reviewer.sh`, and `.review/config.json` alongside `PROMPT.md` and `build.sh`
- `.gitignore` covers the new runtime state (`.review/`, `.agent_hub/`, `NEW_FEEDBACK.md`) while keeping placeholder `.env.example` files tracked
- README restructured around the plan → build → review flow

### Security
- The reviewer's file-reading tool blocks `.env*`, `secrets/`, and `.git`, and its only write paths are two append-only ledgers — repo contents can't leak into Discord and the reviewer can't modify code

## [0.3.0] - 2026-04-02

### Added
- `/autonomous-build` skill — interactive conversation that gathers requirements and generates `PROMPT.md` + `build.sh` for any target project
- Pre-flight check in `build.sh` — fails fast with a helpful message if `PROMPT.md` is missing
- Confirmation prompt before running (skip with `--yes` flag)
- Early completion detection — build runner stops when `BUILD_PROGRESS.md` indicates all phases are done
- Graceful Ctrl+C handling with clean exit message
- Progress summary output at the end of a build (prints first 30 lines of `BUILD_PROGRESS.md`)
- "Security & Commit Rules" section in `SAMPLE_PROMPT.md` covering secret protection and filesystem safety
- "ALL PHASES COMPLETE" convention for signaling build completion in `BUILD_PROGRESS.md`
- Prerequisites section in README

### Changed
- Renamed skill from `build-prompt` to `autonomous-build` to match the slash command name
- Hardened `build.sh` with `set -euo pipefail` instead of just `set -e`
- README now features the `/autonomous-build` skill as the primary getting-started path
- Made all files generic — removed hardcoded paths so anyone can clone and use the repo
- Reorganized commit rules in `SAMPLE_PROMPT.md` into a broader "Security & Commit Rules" section with git safety, secret protection, and filesystem safety subsections

### Removed
- Old `build-prompt` skill directory (replaced by `autonomous-build`)

## [0.2.0] - 2026-02-25

### Added
- Minimal concrete example (todo app) in `SAMPLE_PROMPT.md` showing the simplest possible `PROMPT.md`
- Security and risk documentation for `--dangerously-skip-permissions` in README
- `.gitignore` entries for session-specific files (`PROMPT.md`, `BUILD_PROGRESS.md`, `build-logs/`, `CLAUDE.md`, `.claude/`)

### Changed
- Expanded CHANGELOG to capture project intent and philosophy, not just file listings
- Improved README `build.sh` configuration section with detailed permission flag explanation

## [0.1.0] - 2026-02-25

Initial release. A framework for turning a detailed spec into a working app through autonomous, multi-session builds.

### Added
- `SAMPLE_PROMPT.md` — Annotated template that teaches users how to write a `PROMPT.md`. Covers all sections (continuity, mission, tech stack, architecture, build phases, commit rules) with `[PLACEHOLDER]` values and `<!-- GUIDANCE -->` comments explaining each decision.
- `build.sh` — Loop runner that pipes `PROMPT.md` into Claude Code up to N times. Each session runs autonomously, picks up where the last left off via `BUILD_PROGRESS.md`, and logs output to `build-logs/`.
- `README.md` — Project documentation covering the core concept, quick start, file reference, and tips.
- `.gitignore` — Python-focused gitignore
- MIT License

### Core Concept
The framework solves the problem of context limits in long builds. Instead of one massive session that runs out of context, `build.sh` runs many shorter sessions. `BUILD_PROGRESS.md` acts as a handoff document — each session reads it to understand what's done, builds the next phase, then updates it for the next session. The result is a build that can run overnight and produce a working app by morning.
