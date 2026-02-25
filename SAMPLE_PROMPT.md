# SAMPLE_PROMPT.md — Template for Writing Your PROMPT.md

> **How to use this file:** Copy this file to `PROMPT.md`, replace all `[PLACEHOLDER]` values
> and `<!-- GUIDANCE -->` comments with your project-specific details, then delete any sections
> that don't apply. The structure below is battle-tested for multi-session autonomous builds.
> See the "Minimal Example: Todo App" section at the bottom for a concrete, filled-out version.

---

## CRITICAL: This is a multi-session build. ALWAYS do this first.

Before doing ANYTHING else, assess the current state of the project:

1. Read BUILD_PROGRESS.md in this repo (if it exists) to see what's been completed
2. Run `find . -name "*.[MAIN_EXTENSION]" -not -path "./.venv/*" 2>/dev/null | head -80` and `ls -la` to see what files exist
3. Check if the app runs: `[COMMAND_TO_VERIFY_APP_STARTS]`
4. Check if existing interfaces still work: `[COMMAND_TO_VERIFY_CLI_OR_TESTS]`

<!-- GUIDANCE: Replace the commands above with real commands for your project.
     Examples:
     - Python:  cd /path/to/project && source .venv/bin/activate && python -m uvicorn server:app --help
     - Node:    cd /path/to/project && npm start -- --help
     - Go:      cd /path/to/project && go build ./... && ./app --help
-->

Based on what you find, pick up where the last session left off. Do NOT redo work that already exists and is working. If files exist and are correct, move to the next incomplete step.

**After every major milestone, update BUILD_PROGRESS.md** with:
- What you just completed (with checkmarks)
- What still needs to be done
- Any issues or blockers for the next session
- The next step to pick up on

This file is your handoff to the next session. Be specific. Example:
```
## Completed
- [x] Server scaffolded with static file serving
- [x] Database schema created and migrated
- [x] User authentication working

## In Progress
- [ ] Dashboard page — API endpoint done, frontend rendering partially complete

## Not Started
- [ ] Settings page
- [ ] Export functionality

## Next Step
Finish the dashboard chart component in frontend/src/components/Dashboard.jsx — the data
fetching works but the chart library isn't rendering. Then move to Settings page.
```

---

## The Mission

<!-- GUIDANCE: 1-2 paragraphs. What are you building? Why? What's the end state?
     Be specific about the final deliverable so every session understands the goal. -->

You are building [APP_NAME] at [ABSOLUTE_PATH_TO_PROJECT]. [One sentence describing what exists today, if anything]. The goal is to [what the finished product looks like and does].

[Optional: Where will this deploy? What ecosystem does it belong to?]

## What This App Does

<!-- GUIDANCE: Describe the app from a user's perspective. What can someone DO with it?
     List the core workflows — these become your build phases. -->

[1-2 sentences: the elevator pitch.]

### Core Workflows

1. **[Workflow 1 Name]** (Primary): [Step-by-step user flow]
2. **[Workflow 2 Name]**: [Step-by-step user flow]
3. **[Workflow 3 Name]**: [Step-by-step user flow]

<!-- GUIDANCE: Every workflow you list here should map to a build phase below.
     If you can't describe the user flow, you're not ready to build it yet. -->

## Context You Need

<!-- GUIDANCE: This section tells the agent what to READ before coding.
     Reference repos, docs, files, or codebases the agent needs to understand.
     Use absolute paths so the agent can find them across sessions. -->

1. **Read the existing code** in this repo to understand what already exists:
   - `[path/to/file]` — [what it does]
   - `[path/to/directory/]` — [what it contains]

2. **[Optional] Read [REFERENCE_PROJECT]** at [ABSOLUTE_PATH] — this is the [architecture / design / pattern] to follow:
   - [What to take from it: architecture, UI patterns, deployment strategy, etc.]

3. **[Optional] Read [DOCS_OR_DISCUSSION_FILE]** — [what decisions it captures]

<!-- GUIDANCE: Be selective. Only reference what the agent NEEDS to read.
     Don't point to 10 repos — point to 1-2 and say what to take from each. -->

---

## Tech Stack

<!-- GUIDANCE: Declare your stack explicitly. The agent won't guess. -->

- **Language**: [Python 3.12 / TypeScript / Go / etc.]
- **Framework**: [FastAPI / Next.js / Gin / etc.]
- **Frontend**: [React / Vanilla JS + Tailwind CDN / Vue / etc.]
- **Database**: [PostgreSQL / SQLite / DynamoDB / JSON files / etc.]
- **Auth**: [Cognito / Auth0 / None for local / etc.]
- **Deployment**: [AWS CDK / Vercel / Docker / etc.]
- **Key Libraries**: [List any specific packages the agent should use]

---

## Design Requirements

<!-- GUIDANCE: This section is optional but powerful. If you have UI requirements,
     design specs, or brand guidelines, put them here. If you're building a CLI
     or API-only service, delete this section entirely. -->

### UI Overview

<!-- GUIDANCE: Describe the layout. What pages/tabs/views exist?
     For each one, describe what the user sees and can do. -->

[Describe the overall layout: sidebar nav, tab nav, single page, multi-page, etc.]

#### [Page/Tab 1 Name]

[What's on this page. What inputs, outputs, and actions exist. Be specific enough
that someone could build it without asking questions.]

#### [Page/Tab 2 Name]

[Same level of detail.]

### Brand & UI Design

<!-- GUIDANCE: If you have specific colors, fonts, or component styles, list them.
     If you're following another project's design system, reference it.
     If you don't care about design specifics, delete this subsection. -->

**Color Palette:**
- Primary accent: `[HEX]`
- Background: `[HEX]`
- Text: `[HEX]`
- [Add more as needed]

**Typography:**
- Font family: `[font stack]`
- [Sizes, weights if important]

**Component Patterns:**
- Cards: [border radius, padding, hover behavior]
- Buttons: [primary/secondary styles]
- Inputs: [focus states, sizing]

---

## Architecture

<!-- GUIDANCE: Show how the pieces connect. This helps the agent make correct
     decisions about file structure, API design, and data flow. -->

### Local Development

```
[Draw your local architecture. Example:]

Browser → localhost:[PORT]
│
[Framework] Server
├── Static files ([frontend tech])
├── REST endpoints
│   ├── GET  /api/[resource]         → [description]
│   ├── POST /api/[resource]         → [description]
│   └── [more endpoints...]
└── [Backend services]
    ├── [Service 1]
    └── [Service 2]
```

### Data Models

<!-- GUIDANCE: Define your core data structures. The agent will reference these
     when building storage, APIs, and UI components. -->

```json
{
    "id": "uuid",
    "name": "string",
    "created_at": "ISO timestamp",
    "[field]": "[type and description]"
}
```

### Storage

<!-- GUIDANCE: Where does data live? Be explicit. -->

- `[directory/]` — [what's stored here]
- `[database]` — [tables/collections and their purpose]

### Production (if applicable)

<!-- GUIDANCE: If you plan to deploy, describe the target architecture.
     If local-only, delete this subsection. -->

```
[Production architecture diagram]
```

---

## API Design

<!-- GUIDANCE: List your API endpoints. The agent will implement these exactly.
     If you're building a CLI instead of an API, replace this with CLI commands. -->

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/[resource]` | [List/search resources] |
| GET | `/api/[resource]/{id}` | [Get specific resource] |
| POST | `/api/[resource]` | [Create resource] |
| PUT | `/api/[resource]/{id}` | [Update resource] |
| DELETE | `/api/[resource]/{id}` | [Delete resource] |

<!-- GUIDANCE: For WebSocket endpoints, describe the message protocol:
     what the client sends, what the server streams back, message types. -->

---

## Documentation Requirements

<!-- GUIDANCE: Define what docs the agent must create and maintain.
     This prevents docs from becoming stale across sessions. -->

**CRITICAL: Documentation is updated EVERY phase, not at the end.** After completing each phase, update all affected docs before moving on.

### Required Documentation Files

1. **README.md** — Project overview, prerequisites, quick start, environment variables
2. **CHANGELOG.md** — Version history by phase, using Keep a Changelog format
3. **[Optional] docs/ARCHITECTURE.md** — Technical deep dive
4. **[Optional] docs/API.md** — API reference with request/response examples

### Documentation Checklist (run after EVERY phase)

Before marking a phase complete in BUILD_PROGRESS.md, verify:

- [ ] README.md quick start commands work (copy-paste test)
- [ ] README.md reflects the current feature set
- [ ] CHANGELOG.md has a dated entry for this phase
- [ ] [Add any project-specific doc checks]

---

## Build Order

<!-- GUIDANCE: This is the most important section. Break your build into phases
     that each produce a WORKING increment. Rules:
     - Each phase should be completable in one session (1-3 hours of agent work)
     - Each phase should produce something testable
     - Earlier phases should NOT depend on later phases
     - Include specific verification steps ("Test: do X → see Y")
     - Include doc updates in every phase

     A good phase has: implementation tasks, test/verification steps, doc updates.
     A bad phase is vague ("build the frontend") or too large (10+ tasks). -->

### Phase 1: Foundation

<!-- GUIDANCE: Phase 1 always sets up the skeleton: project structure, dependencies,
     basic server/app running, and initial documentation. The bar is: "it starts." -->

- [ ] Initialize project structure ([framework] scaffold, directory layout)
- [ ] Install dependencies ([list key packages])
- [ ] [Create base UI shell / CLI entry point / API skeleton]
- [ ] Verify: [app starts, base page loads, CLI responds to --help, etc.]
- [ ] **Docs:** Write README.md with overview, prerequisites, quick start
- [ ] **Docs:** Create CHANGELOG.md with Phase 1 entry

### Phase 2: [Core Data / Models / Storage]

<!-- GUIDANCE: Phase 2 usually establishes the data layer: schemas, storage,
     CRUD operations, seed data. The bar is: "data flows correctly." -->

- [ ] [Define data models / schemas]
- [ ] [Implement storage layer (database, file system, etc.)]
- [ ] [Write CRUD API endpoints or CLI commands]
- [ ] [Seed with initial/test data if needed]
- [ ] Test: [create a record → read it back → update → delete → verify]
- [ ] **Docs:** Update README.md, CHANGELOG.md

### Phase 3: [Primary Workflow]

<!-- GUIDANCE: Phase 3 builds the main thing users will DO with the app.
     The bar is: "the primary use case works end-to-end." -->

- [ ] [Build the primary UI / interface]
- [ ] [Implement the core business logic]
- [ ] [Wire up frontend to backend]
- [ ] Test: [full workflow: input → process → output → verify]
- [ ] **Docs:** Update README.md, CHANGELOG.md

### Phase 4: [Secondary Workflow]

- [ ] [Build secondary feature]
- [ ] Test: [workflow verification]
- [ ] **Docs:** Update README.md, CHANGELOG.md

### Phase 5: [Additional Features]

<!-- GUIDANCE: Add as many phases as needed. Common later phases:
     - Additional workflows / features
     - Integrations (external APIs, services)
     - Real-time features (WebSocket, SSE)
     - Polish (error handling, loading states, responsive design)
     - Deployment infrastructure
     - End-to-end verification -->

- [ ] [Feature work]
- [ ] Test: [verification]
- [ ] **Docs:** Update README.md, CHANGELOG.md

### Phase N: Polish & Verification

<!-- GUIDANCE: Always end with a polish + verification phase. -->

- [ ] Error handling and loading states
- [ ] Responsive design / edge cases
- [ ] **Docs audit:** Verify all docs are accurate and quick start works
- [ ] **Docs:** Final CHANGELOG.md entry

### Phase N+1: Deployment (if applicable)

<!-- GUIDANCE: Deployment is always the last phase. Don't mix deployment
     concerns into feature phases. -->

- [ ] [Infrastructure setup (CDK, Terraform, Docker, etc.)]
- [ ] [CI/CD pipeline]
- [ ] [Production verification]
- [ ] **Docs:** Deployment guide

---

## Commit Rules

<!-- GUIDANCE: These rules prevent common autonomous build mistakes.
     Customize for your project but keep the safety rules. -->

- Commit after completing each phase
- Never mention Claude, Anthropic, or AI in commit messages
- Never commit CLAUDE.md or .claude/
- Keep commits focused and descriptive
- **NEVER commit secrets, API keys, tokens, or credentials of any kind**
- Never commit .env files or anything in secrets/
- Before every commit, run `git diff --cached` and scan for anything that looks like an API key, token, password, or secret. If found, unstage it immediately.
- Use `git add <specific files>` — NEVER use `git add .` or `git add -A`

<!-- GUIDANCE: Add project-specific gitignore rules:
     - Generated files (media, build artifacts)
     - Database files
     - Upload directories
     - Large binary files -->

---

## Minimal Example: Todo App

<!-- DELETE THIS SECTION from your final PROMPT.md — it shows the simplest possible prompt. -->

> Below is the **minimum viable PROMPT.md** — just the essential sections, no optional extras.
> If your project is straightforward, this is all you need.

```markdown
## CRITICAL: This is a multi-session build. ALWAYS do this first.

Before doing ANYTHING else:
1. Read BUILD_PROGRESS.md (if it exists) to see what's been completed
2. Run `ls -la` and check what files exist
3. Check if the app runs: `cd /Users/me/projects/todo-app && python server.py`

Pick up where the last session left off. Do NOT redo existing work.
**After every milestone, update BUILD_PROGRESS.md.**

---

## The Mission

You are building a todo app at /Users/me/projects/todo-app. Nothing exists yet.
The goal is a web-based todo list with categories, due dates, and a clean UI.

## Tech Stack

- Python 3.12, FastAPI, Vanilla JS + Tailwind CDN, SQLite

## Architecture

Browser → localhost:8000
├── Static files (index.html)
├── GET  /api/todos         → list todos (filter by category, status)
├── POST /api/todos         → create todo
├── PUT  /api/todos/{id}    → update todo (toggle done, edit text)
├── DELETE /api/todos/{id}  → delete todo
└── SQLite database (todos.db)

## Build Order

### Phase 1: Foundation
- [ ] Scaffold FastAPI with static serving, SQLite schema (id, text, category, due_date, done, created_at)
- [ ] Serve base HTML with Tailwind CDN
- [ ] Verify: server starts, page loads at localhost:8000
- [ ] Docs: README.md with quick start, CHANGELOG.md

### Phase 2: CRUD
- [ ] Implement all API endpoints
- [ ] Build frontend: add todo form, todo list with checkboxes, delete buttons
- [ ] Test: create todo → see it in list → check it off → delete it
- [ ] Docs: Update README.md, CHANGELOG.md

### Phase 3: Categories & Filtering
- [ ] Add category selector (work, personal, errands) and due date picker
- [ ] Add filter bar (by category, by status, by due date)
- [ ] Test: create todos in different categories → filter → verify
- [ ] Docs: Update README.md, CHANGELOG.md

### Phase 4: Polish
- [ ] Error handling, empty states, loading indicators
- [ ] Responsive design (mobile-friendly)
- [ ] Docs audit: verify quick start works from scratch

## Commit Rules

- Commit after each phase
- Never mention Claude, Anthropic, or AI in commit messages
- Never commit .env, CLAUDE.md, or .claude/
- Use `git add <specific files>` — never `git add .`
```

---

## Tips for Writing a Great PROMPT.md

<!-- DELETE THIS SECTION from your final PROMPT.md — it's only here as guidance. -->

### What makes a prompt effective:

1. **Absolute paths** — The agent runs across sessions. Relative paths break. Use `/full/path/to/project`.

2. **Concrete verification steps** — "Test: create a user → log in → see dashboard" beats "test the auth system."

3. **Explicit tool/library choices** — Don't say "add a database." Say "use SQLite via `sqlite3` stdlib" or "use PostgreSQL via `asyncpg`."

4. **Phase sizing** — Each phase should be completable in one `build.sh` run (~1-3 hours of agent work). If a phase has 15+ tasks, split it.

5. **BUILD_PROGRESS.md is the bridge** — The multi-session continuity section at the top is what makes autonomous overnight builds work. Don't skip it.

6. **Design specs prevent rework** — If you care about how it looks, specify colors, spacing, and component styles. Otherwise the agent will pick something and you'll redo it.

7. **Reference projects over descriptions** — "Follow the architecture of /path/to/reference-project" is more precise than paragraphs of architecture description. Use both when possible.

8. **Commit rules prevent disasters** — The agent will `git add .` and commit secrets if you don't explicitly forbid it.

9. **Doc requirements prevent staleness** — Requiring doc updates in every phase means you always have accurate docs, not a "we'll document it later" mess.

10. **Order matters** — Foundation → Data → Primary Feature → Secondary Features → Polish → Deploy. Each phase should work independently. Never build Phase 5 features that depend on Phase 8.
