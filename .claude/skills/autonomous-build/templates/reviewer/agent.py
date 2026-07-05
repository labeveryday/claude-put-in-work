"""
Build Reviewer Agent - Strands + Discord

Watches an autonomous build while build.sh runs, and keeps running after it
so you can talk through the results. Two agents share one toolset:

- Review agent (fresh per review): triggered when the builder appends
  "phase: N" to .review/queue after committing a phase. Reviews the phase
  against its PROMPT.md checklist, runs the tests, screenshots the app, files
  feedback in NEW_FEEDBACK.md, and records APPROVED / CHANGES_REQUESTED in
  .review/verdicts.md. The final phase's verdict gates build completion.
  A safety-net review runs if commits pile up with no review for
  SAFETY_REVIEW_MINUTES (default 60).

- Chat agent (persistent, sliding-window memory): any plain message in the
  channel. Discuss the build, ask what's left, request proof (tests /
  screenshots). When you ask for a change, it files a directive in
  NEW_FEEDBACK.md that the next build session must address.

Slash commands: /status /review /pending /approve /shutdown

Env (in .env or exported):
  ANTHROPIC_API_KEY        required
  DISCORD_BOT_TOKEN        required
  DISCORD_CHANNEL_ID       required - one channel per build
  REVIEWER_MODEL_ID        default claude-haiku-4-5-20251001
  SAFETY_REVIEW_MINUTES    default 60

Run via ./reviewer.sh start (or: .venv/bin/python reviewer/agent.py)
"""

from dotenv import load_dotenv

# Load environment variables FIRST (before hub imports)
load_dotenv()

import asyncio  # noqa: E402
import datetime  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import pathlib  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import discord  # noqa: E402
from discord import app_commands  # noqa: E402
from strands import Agent  # noqa: E402
from strands.agent.conversation_manager import SlidingWindowConversationManager  # noqa: E402

from models import anthropic_model  # noqa: E402
from config import (  # noqa: E402
    CHAT_SYSTEM_PROMPT,
    GENERAL_REVIEW_PROMPT,
    PHASE_REVIEW_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
)
from hub import AgentRegistry, MetricsExporter, create_session_manager  # noqa: E402
from hub.session import generate_run_id  # noqa: E402
from tools import (  # noqa: E402
    file_feedback,
    latest_build_log,
    list_repo,
    read_repo_file,
    recent_commits,
    record_verdict,
    run_tests,
    screenshot_page,
)
from tools.repo_tools import (  # noqa: E402
    HEARTBEAT_FILE,
    LAST_REVIEW_FILE,
    REPO_ROOT,
    REVIEW_DIR,
    SCREENSHOT_DIR,
    VERDICTS_FILE,
    build_status_text,
    feedback_count,
    file_feedback_entry,
    git_head,
    pending_feedback,
    queued_phases,
)


# =============================================================================
# CONFIGURATION - Customize these for your reviewer
# =============================================================================

AGENT_ID = f"build-reviewer-{REPO_ROOT.name}"
AGENT_NAME = "Build Reviewer"
PROMPT_VERSION = "v2"

MODEL_ID = os.getenv("REVIEWER_MODEL_ID", "claude-haiku-4-5-20251001")
MODEL = anthropic_model(model_id=MODEL_ID)

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
QUEUE_POLL_SECONDS = 20
SAFETY_REVIEW_MINUTES = int(os.getenv("SAFETY_REVIEW_MINUTES", "60"))

REVIEW_TOOLS = [list_repo, read_repo_file, recent_commits, latest_build_log,
                run_tests, screenshot_page, file_feedback, record_verdict]
CHAT_TOOLS = [list_repo, read_repo_file, recent_commits, latest_build_log,
              run_tests, screenshot_page, file_feedback]


# =============================================================================
# HUB INTEGRATION - Registry, per-run session, metrics
# =============================================================================

run_id = generate_run_id(AGENT_ID)

registry = AgentRegistry()
registry.register(
    agent_id=AGENT_ID,
    description=f"Discord build reviewer for {REPO_ROOT.name}",
    tags=["build-reviewer", "discord"],
    owner=os.getenv("USER", "unknown"),
    environment="dev",
    model_id=MODEL_ID,
)

metrics = MetricsExporter(agent_id=AGENT_ID, run_id=run_id, prompt_version=PROMPT_VERSION)


# =============================================================================
# AGENTS - persistent chat agent; fresh review agent per review
# =============================================================================

chat_agent = Agent(
    model=MODEL,
    system_prompt=CHAT_SYSTEM_PROMPT,
    tools=CHAT_TOOLS,
    session_manager=create_session_manager(agent_id=AGENT_ID, run_id=run_id),
    conversation_manager=SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
    ),
    name=AGENT_NAME,
)
last_chat_result = None


def run_review(phase: int | None) -> str:
    """One stateless review pass. Phase reviews record a verdict; general ones don't."""
    agent = Agent(
        model=MODEL,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        tools=REVIEW_TOOLS,
        name=f"{AGENT_NAME} (review)",
    )
    prompt = PHASE_REVIEW_PROMPT.format(phase=phase) if phase else GENERAL_REVIEW_PROMPT
    return str(agent(prompt)).strip()


def new_screenshots(since: float) -> list[pathlib.Path]:
    if not SCREENSHOT_DIR.exists():
        return []
    return sorted(p for p in SCREENSHOT_DIR.glob("*.png") if p.stat().st_mtime >= since)[:4]


def mark_reviewed() -> None:
    REVIEW_DIR.mkdir(exist_ok=True)
    LAST_REVIEW_FILE.write_text(json.dumps({"sha": git_head(), "time": time.time()}))


def last_review() -> dict:
    try:
        return json.loads(LAST_REVIEW_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {"sha": "", "time": 0}


# =============================================================================
# DISCORD WIRING
# =============================================================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
review_lock = asyncio.Lock()
chat_lock = asyncio.Lock()
_started = False


def ours(interaction: discord.Interaction) -> bool:
    return interaction.channel_id == CHANNEL_ID


async def post(channel: discord.abc.Messageable, text: str,
               files: list[pathlib.Path] | None = None) -> None:
    """Send text (chunked under Discord's 2000-char cap) with optional images."""
    attachments = [discord.File(str(f)) for f in (files or [])]
    first = True
    for i in range(0, max(len(text), 1), 1900):
        await channel.send(text[i:i + 1900], files=attachments if first else None)
        first = False


async def do_review(channel: discord.abc.Messageable, phase: int | None, reason: str) -> None:
    if review_lock.locked():
        return
    async with review_lock:
        started = time.time()
        title = f"phase {phase} review" if phase else "checkpoint review"
        try:
            report = await asyncio.to_thread(run_review, phase)
            mark_reviewed()
            stamp = datetime.datetime.now().strftime("%I:%M %p")
            await post(channel, f"🔍 **{title.title()}** ({reason}) — {stamp}\n{report}",
                       files=new_screenshots(started))
        except Exception as e:
            await post(channel, f"⚠️ Reviewer error during {title}: {e}")


async def watch_queue(channel: discord.abc.Messageable) -> None:
    """Poll .review/queue for phase-complete signals; heartbeat every pass."""
    done_file = REVIEW_DIR / "queue.done"
    while not client.is_closed():
        REVIEW_DIR.mkdir(exist_ok=True)
        HEARTBEAT_FILE.touch()

        phases = queued_phases()
        done = int(done_file.read_text()) if done_file.exists() else 0
        if len(phases) > done:
            for i in range(done, len(phases)):
                await do_review(channel, phases[i], "builder finished the phase")
                done_file.write_text(str(i + 1))
        else:
            # Safety net: commits landed but nothing reviewed for a while
            last = last_review()
            stale = (time.time() - last["time"]) > SAFETY_REVIEW_MINUTES * 60
            head = git_head()
            if stale and head and not head.startswith("fatal") and head != last["sha"]:
                await do_review(channel, None, f"no review in {SAFETY_REVIEW_MINUTES}m with new commits")

        await asyncio.sleep(QUEUE_POLL_SECONDS)


@client.event
async def on_ready() -> None:
    global _started
    if _started:
        return
    _started = True

    channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
    if getattr(channel, "guild", None):
        tree.copy_global_to(guild=channel.guild)
        await tree.sync(guild=channel.guild)

    mark_reviewed()  # baseline: don't fire the safety net at boot
    await channel.send(
        f"👋 {AGENT_NAME} online for **{REPO_ROOT.name}** ({MODEL_ID}). "
        "Phase reviews run automatically; talk to me to discuss the build or request changes. "
        "Commands: /status /review /pending /approve /shutdown"
    )
    asyncio.create_task(watch_queue(channel))


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.channel.id != CHANNEL_ID:
        return
    text = message.content.strip()
    if not text or text.startswith(("/", "!")):
        return

    global last_chat_result
    async with chat_lock:
        started = time.time()
        fb_before = feedback_count()
        try:
            async with message.channel.typing():
                last_chat_result = await asyncio.to_thread(chat_agent, text)
            if feedback_count() > fb_before:
                await message.add_reaction("✅")
            await post(message.channel, str(last_chat_result).strip() or "(no reply)",
                       files=new_screenshots(started))
        except Exception as e:
            await post(message.channel, f"⚠️ Chat error: {e}")


# =============================================================================
# SLASH COMMANDS
# =============================================================================

@tree.command(name="status", description="Current phase, remaining tasks, verdicts, and open feedback")
async def status_cmd(interaction: discord.Interaction) -> None:
    if not ours(interaction):
        return
    await interaction.response.send_message(build_status_text()[:1990])


@tree.command(name="review", description="Run a checkpoint review right now")
async def review_cmd(interaction: discord.Interaction) -> None:
    if not ours(interaction):
        return
    if review_lock.locked():
        await interaction.response.send_message("A review is already running — report lands here shortly.")
        return
    await interaction.response.send_message("🔍 On it — reviewing now.")
    asyncio.create_task(do_review(interaction.channel, None, f"requested by @{interaction.user.display_name}"))


@tree.command(name="pending", description="List open feedback the builder hasn't addressed yet")
async def pending_cmd(interaction: discord.Interaction) -> None:
    if not ours(interaction):
        return
    entries = pending_feedback()
    if not entries:
        await interaction.response.send_message("No PENDING feedback — the builder is caught up.")
        return
    lines = "\n".join(f"- **[{fid}]** {src}: {first}" for fid, src, first in entries[:15])
    await interaction.response.send_message(f"📬 {len(entries)} PENDING:\n{lines}"[:1990])


@tree.command(name="approve", description="Human override: approve the final phase so the build can complete")
async def approve_cmd(interaction: discord.Interaction) -> None:
    if not ours(interaction):
        return
    REVIEW_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with VERDICTS_FILE.open("a") as f:
        f.write(f"FINAL: APPROVED (human @{interaction.user.display_name}) — {stamp}\n")
    await interaction.response.send_message(
        "✅ Final approval recorded — the build will mark itself complete on its next check."
    )


@tree.command(name="shutdown", description="Stop the reviewer bot (exports metrics first)")
async def shutdown_cmd(interaction: discord.Interaction) -> None:
    if not ours(interaction):
        return
    await interaction.response.send_message("👋 Shutting down — metrics exported to the hub.")
    if last_chat_result is not None:
        metrics.set_from_agent_result(last_chat_result)
    metrics.export()
    registry.record_run(agent_id=AGENT_ID, run_id=run_id, success=True)
    await client.close()


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    missing = [k for k in ("ANTHROPIC_API_KEY", "DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID")
               if not os.getenv(k)]
    if missing:
        sys.exit(f"reviewer/agent.py: missing {', '.join(missing)} (set in .env or environment)")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
