#!/usr/bin/env bash
# Layer 1: Manifold Manifest (supply chain intelligence)
#
# Opens the Manifest intelligence index in the default browser. We consume
# this as a human — no API integration. The three-layer story says Layer 1
# is provided today by Manifold; we don't rebuild it.

set -eu

cat <<'MSG'
-- Layer 1: Manifold Manifest (supply chain intelligence) --

Opening https://manifest.manifold.security in your default browser.

What to show in the demo:
  1. Search for any agent skill or MCP server the audience cares about.
  2. Point to the verdict card and the "1 in 12 skills are confirmed
     malicious" posture line from Manifold's April 2026 research.
  3. Narration: "This is the supply chain layer. We don't rebuild it —
     we consume it. Manifold owns this one. Our job is Layer 2 and 3."

(No live API calls are made. This step is purely visual anchor.)
MSG

URL="https://manifest.manifold.security"
if command -v open >/dev/null 2>&1; then
    open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
else
    echo "open manually: $URL"
fi
