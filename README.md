# Agent authorization prototype

A learning artifact. A small CLI + design sketch around a per-action authorization primitive for AI agents — cryptographic envelopes, Ed25519-signed, short TTL, scope-narrowed from stated intent. I built it before ConductorOne launched AIAM in March 2026 and kept iterating on it because the exercise kept teaching me things.

This is **not** a product pitch. The primary artifact is `NOTES.md` — an honest technical journal of what building this taught me, what it changed my mind about, and the open questions I'm still sitting with. The CLI + dashboard exist to make those notes concrete.

## What it shows

The demo runs two scripts: a Baton entitlement-graph build, and a Carryall runtime-authorization flow against that graph.

| # | Script | Layer | Who owns it |
|---|---|---|---|
| 2 | `scripts/02_baton.py` | Entitlement graph | ConductorOne Baton (`.c1z`) |
| 3 | `scripts/03_carryall.py` | Runtime authorization | Carryall (Authority Runtime + Baton adapter) |

Layer 3 fires two scenarios against the Baton-backed graph:

- **ALLOW** — `release-agent` → baton principal `alice` → `admin` grant on `acme/api`.
- **DENY** — same agent mapped to `charlie`, who has no grant on `acme/api`.

The ALLOW returns a real Ed25519-signed envelope with a 300s TTL. The DENY never issues a capability.

## Setup

This assumes you have the two sibling repos checked out:

```
/Users/erikh/code/carryall/authority-runtime-python   # library (v0.4.0)
/Users/erikh/code/carryall-baton-backend              # adapter (v0.1.0)
/Users/erikh/code/AuthN.Z.demo.apr26                  # this demo
```

Install both in the authority-runtime venv (or any venv you point `PYTHON` at):

```bash
make setup
```

This also installs [`rich`](https://rich.readthedocs.io/) for the terminal UI (panels, trees, syntax-highlighted envelope JSON).

## Run

```bash
make demo
```

The demo pauses between layers so you can narrate. `make layer2` and `make layer3` run them individually. `make verify` runs both non-interactively as a smoke test.

## The `.c1z`

`sync.c1z` is generated fresh each run by `scripts/02_baton.py`. It's a real gzipped SQLite database matching baton-sdk's `v1_resources`/`v1_entitlements`/`v1_grants` schema. Schema and sample data live in `vendor/_fixture.py`.

**In production**, this file comes from `BATON_TOKEN=<github-pat> baton-github` — the script prints that reminder. The demo uses a synthetic `.c1z` on purpose: no throwaway GitHub org, no live PAT, zero setup friction. The adapter code path is the same either way.

## Config

`backend.json` is the `CARRYALL_SLOS_CONFIG` the demo loads:

```json
{
  "backend": "baton",
  "init": {
    "c1z_path": "./sync.c1z",
    "agent_to_principal": { "release-agent": "alice" }
  }
}
```

`load_backend()` resolves `"baton"` through the `authority_runtime.backends` entry-point group registered by `carryall-baton-backend`. No glue code in this repo.

## Files

```
README.md                           Setup + run instructions (this file)
NOTES.md                            Primary artifact — honest journal of what building taught me
talk_track.md                       5-minute narration if shown live
docs/architecture-pre-aiam.md       Pre-AIAM thinking, archived for honesty
dashboard/index.html                Offline HTML design sketch (Architecture + Dashboard tabs)
Makefile                            `make demo` and friends
backend.json                        CARRYALL_SLOS_CONFIG
scripts/02_baton.py                 Generate + preview the synthetic .c1z graph
scripts/03_carryall.py              Run ALLOW + DENY scenarios with real Ed25519 envelopes
vendor/_fixture.py                  Synthetic .c1z builder (same v1 schema baton-github emits)
```

## What to say if things break

`NOTES.md` is the primary artifact; the live demo is the garnish. If scripts fail on demo day, the notes stand alone. Don't debug live — the conversation after the demo is the point.
