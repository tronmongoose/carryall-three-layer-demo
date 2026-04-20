# AuthN/AuthZ demo — three layers of agent governance

Runnable companion to `ARCHITECTURE.md`. Ten minutes. CLI-driven. No React, no docker, no live infra.

## What it shows

The demo runs Layers 2 and 3. Layer 1 (agent discovery / supply chain) is narrated, not executed — the argument is that it exists, not that we rebuild it.

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
README.md                Setup + run instructions (this file)
ARCHITECTURE.md          The strategic one-pager
talk_track.md            10-minute narration, timed
Makefile                 `make demo` and friends
backend.json             CARRYALL_SLOS_CONFIG
scripts/02_baton.py      Layer 2: regenerate sync.c1z and preview it
scripts/03_carryall.py   Layer 3: run the ALLOW and DENY scenarios
vendor/_fixture.py       Synthetic .c1z builder (same shape as baton-github output)
```

## What to say if things break

The demo is the backup, not the centerpiece — `ARCHITECTURE.md` is the primary artifact. If any script fails on demo day: skip to Layer 3, show the `backend.json` + `agent_to_principal` mapping, and describe the ALLOW/DENY flow from the talk track. The architecture argument doesn't depend on live output.
