"""
Repo tools for the build reviewer - read access to the project plus two write
paths: appending feedback to NEW_FEEDBACK.md and verdicts to .review/verdicts.md.

Also holds the .review/ state layout shared by the queue watcher and slash
commands: queue (phase-review requests from the builder), verdicts.md,
heartbeat, screenshots/, and last_review.json.
"""

import datetime
import pathlib
import re
import subprocess

from strands import tool

# reviewer/tools/repo_tools.py -> project root
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FEEDBACK_FILE = REPO_ROOT / "NEW_FEEDBACK.md"

REVIEW_DIR = REPO_ROOT / ".review"
QUEUE_FILE = REVIEW_DIR / "queue"
QUEUE_DONE_FILE = REVIEW_DIR / "queue.done"
VERDICTS_FILE = REVIEW_DIR / "verdicts.md"
HEARTBEAT_FILE = REVIEW_DIR / "heartbeat"
SCREENSHOT_DIR = REVIEW_DIR / "screenshots"
LAST_REVIEW_FILE = REVIEW_DIR / "last_review.json"

BLOCKED = re.compile(r"(^|/)(\.env[^/]*|secrets|\.git|node_modules|\.venv|__pycache__)(/|$)")

FEEDBACK_HEADER = """# New Feedback

Entries are appended here by the reviewer agent and by humans on Discord.
The build agent marks each entry ADDRESSED or DEFERRED - entries are never deleted.
"""


def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    return out.stdout.strip() or out.stderr.strip()


def git_head() -> str:
    return _git("rev-parse", "HEAD")


def file_feedback_entry(source: str, text: str) -> str:
    """Append one PENDING feedback entry and return its id (e.g. F-003)."""
    count = 0
    if FEEDBACK_FILE.exists():
        count = len(re.findall(r"^## \[F-\d+\]", FEEDBACK_FILE.read_text(), re.M))
    else:
        FEEDBACK_FILE.write_text(FEEDBACK_HEADER)

    fid = f"F-{count + 1:03d}"
    with FEEDBACK_FILE.open("a") as f:
        f.write(f"\n## [{fid}] {_stamp()} — {source}\n**Status: PENDING**\n\n{text.strip()}\n")
    return fid


def feedback_count() -> int:
    if not FEEDBACK_FILE.exists():
        return 0
    return len(re.findall(r"^## \[F-\d+\]", FEEDBACK_FILE.read_text(), re.M))


def pending_feedback() -> list[tuple[str, str, str]]:
    """Return (id, source, first line) for every PENDING entry."""
    if not FEEDBACK_FILE.exists():
        return []
    entries = []
    blocks = re.split(r"^## ", FEEDBACK_FILE.read_text(), flags=re.M)[1:]
    for block in blocks:
        m = re.match(r"\[(F-\d+)\][^—]*—\s*(.+)", block)
        if not m or "**Status: PENDING**" not in block:
            continue
        body = block.split("**Status: PENDING**", 1)[1].strip().splitlines()
        first = body[0].strip() if body else ""
        entries.append((m.group(1), m.group(2).strip(), first))
    return entries


def record_verdict_line(line: str) -> None:
    REVIEW_DIR.mkdir(exist_ok=True)
    with VERDICTS_FILE.open("a") as f:
        f.write(line.rstrip() + "\n")


def queued_phases() -> list[int]:
    """Phase numbers the builder has requested reviews for, in order."""
    if not QUEUE_FILE.exists():
        return []
    phases = []
    for line in QUEUE_FILE.read_text().splitlines():
        m = re.search(r"phase\s*:?\s*(\d+)", line, re.I)
        if m:
            phases.append(int(m.group(1)))
    return phases


def build_status_text() -> str:
    """Compose the /status report from PROMPT.md, BUILD_PROGRESS.md, and .review/ state."""
    parts = []

    phases = queued_phases()
    current = (phases[-1] + 1) if phases else 1
    parts.append(f"📋 **Build status** — phase {current} in progress"
                 f" ({len(phases)} phase(s) submitted for review)")

    prompt_md = REPO_ROOT / "PROMPT.md"
    if prompt_md.exists():
        m = re.search(rf"^### Phase {current}\b[^\n]*\n(.*?)(?=^### |\Z)",
                      prompt_md.read_text(), re.M | re.S)
        if m:
            checklist = "\n".join(m.group(0).strip().splitlines()[:14])
            parts.append(f"**Current phase plan:**\n{checklist}")

    progress = REPO_ROOT / "BUILD_PROGRESS.md"
    if progress.exists():
        head = "\n".join(progress.read_text().splitlines()[:12])
        parts.append(f"**BUILD_PROGRESS.md:**\n{head}")

    if VERDICTS_FILE.exists():
        tail = "\n".join(VERDICTS_FILE.read_text().splitlines()[-3:])
        parts.append(f"**Recent verdicts:**\n{tail}")

    pending = pending_feedback()
    parts.append(f"**Open feedback:** {len(pending)} PENDING" +
                 ("".join(f"\n- [{fid}] {src}: {first}" for fid, src, first in pending[:5])))

    return "\n\n".join(parts)


# --- Tools for the Strands agents ---

@tool
def list_repo() -> str:
    """List all git-tracked files in the repository.

    Returns:
        One file path per line
    """
    return _git("ls-files")


@tool
def read_repo_file(path: str) -> str:
    """Read a file from the repository. Env files, secrets, and .git are blocked.

    Args:
        path: Path relative to the repository root

    Returns:
        File contents (truncated to 30k characters)
    """
    p = (REPO_ROOT / path).resolve()
    if not str(p).startswith(str(REPO_ROOT)):
        return f"ERROR: access to {path} is not allowed"
    rel = str(p.relative_to(REPO_ROOT))
    if BLOCKED.search(rel):
        return f"ERROR: access to {path} is not allowed"
    if not p.is_file():
        return f"ERROR: {path} is not a file"
    return p.read_text(errors="replace")[:30000]


@tool
def recent_commits() -> str:
    """Show the last 10 commits and the file-level stat of the most recent one.

    Returns:
        git log --oneline output followed by git show --stat HEAD
    """
    return _git("log", "--oneline", "-10") + "\n\n" + _git("show", "--stat", "HEAD")


@tool
def latest_build_log(lines: int = 120) -> str:
    """Return the tail of the newest build session log.

    Args:
        lines: Number of lines from the end of the log (default: 120)

    Returns:
        Log tail, or a note if no logs exist yet
    """
    logs = sorted((REPO_ROOT / "build-logs").glob("run_*.log"))
    if not logs:
        return "No build logs yet."
    return "\n".join(logs[-1].read_text(errors="replace").splitlines()[-lines:])


@tool
def file_feedback(suggestion: str) -> str:
    """File one concrete, actionable suggestion for the build agent to address.

    Args:
        suggestion: The suggestion - specific enough to act on (file, problem, proposed fix)

    Returns:
        The id the entry was filed under
    """
    fid = file_feedback_entry("reviewer agent", suggestion)
    return f"Filed as {fid}"


@tool
def record_verdict(phase: int, verdict: str, summary: str, feedback_ids: str = "") -> str:
    """Record the review verdict for a completed phase. Call exactly once per phase review.

    Args:
        phase: The phase number that was reviewed
        verdict: APPROVED or CHANGES_REQUESTED
        summary: One line on why
        feedback_ids: Comma-separated feedback ids when requesting changes (e.g. "F-004, F-005")

    Returns:
        Confirmation of the recorded verdict
    """
    v = verdict.strip().upper()
    if v not in ("APPROVED", "CHANGES_REQUESTED"):
        return "ERROR: verdict must be APPROVED or CHANGES_REQUESTED"
    ids = f" ({feedback_ids.strip()})" if feedback_ids.strip() else ""
    line = f"phase {phase}: {v}{ids} — {_stamp()} — {summary.strip()}"
    record_verdict_line(line)
    return f"Recorded: {line}"
