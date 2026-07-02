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
