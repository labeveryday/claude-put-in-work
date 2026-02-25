# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
