# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
