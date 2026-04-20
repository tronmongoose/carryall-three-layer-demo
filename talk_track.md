# Talk track — 10 minutes

Timings are targets; trim ruthlessly.

## 0:00 – 0:45 — Setup

> The argument in `ARCHITECTURE.md` is that agent governance needs three layers: supply chain on what an agent is made of, entitlements on what it should access, and runtime authorization on what it's doing right now. Three companies build those today. I think they should be one product. The ten minutes you're about to see is that argument, compiled into running code.

## 0:45 – 1:15 — Layer 1: discovery (narrated, not run)

> Before you can govern agents you have to know what agents you have. Discovery — the inventory of every agent running in the environment, what skills they've loaded, what credentials they hold — is the unglamorous but necessary starting point. Manifold and a handful of others are building this layer. I'm not rebuilding it and I'm not going to spend the demo time on it. I want the nine minutes we have left on the two layers I think C1 should own.

## 1:15 – 3:15 — Layer 2: Baton (entitlement graph)

Run `make layer2`. Script regenerates `sync.c1z` and prints its contents.

> Layer 2 is the entitlement graph — who should have access to what. ConductorOne already owns this. Baton is the open-source piece: connectors that dump any source system into a standard `.c1z` file. I'm generating a synthetic one here — same schema, same query shape as `baton-github` would produce against a real org. Three users, three repos, nine grants. Alice has admin on `acme/api`. Charlie has read on `acme/frontend` only. In production this file comes from `baton-github` against the customer's real GitHub. The adapter doesn't care.

## 3:15 – 7:15 — Layer 3: Carryall (runtime authorization)

Run `make layer3`. Two scenarios print.

> Layer 3 is what I built. Runtime authorization. The agent declares intent in natural language. A compiler reads the entitlement graph from Layer 2 and produces the minimum set of scopes the agent needs to fulfill that intent. Those scopes are wrapped in an Ed25519-signed envelope with a 300-second TTL and the agent's identity. The envelope is the capability.
>
> Scenario one: the release agent maps to Alice. Alice has admin on `acme/api`. The envelope is issued, signed, and check_access returns ALLOW with the baton grant as the reason. You can see the signature right there.
>
> Scenario two: same agent, mapped to Charlie. Charlie has no grant on `acme/api`. check_access returns DENY. No envelope authorizing that action was ever issued. This is the point: **the unauthorized action was cryptographically impossible, not because someone detected it and responded, but because the capability never existed**.

> The thing I want to underscore: the adapter that bridges Baton into Carryall is a ~270-line class whose seven Protocol methods are the only surface Carryall touches. I added that Protocol to authority-runtime itself in the 0.4.0 release, right before this conversation. Any Baton connector — Okta, Snowflake, Salesforce — plugs in the same way. No Carryall code changes.

## 7:15 – 10:00 — The ask

> Three things I'm proposing, in priority order:
> 1. The role we're already discussing — VP Product, path to CPO.
> 2. Bring Carryall into C1 as the foundation of an agent product line. I built it on my own time, no employer IP. Terms are negotiable as part of the offer.
> 3. A 90-day plan to ship a closed beta: three existing C1 customers running coding agents in production, Carryall against their existing Baton-synced graph, publish the measured blocked-vs-allowed rates as a category-defining piece of research with C1's brand on it.
>
> The rest is execution.

## Backup notes

- If `make layer2` fails: the `.c1z` file might already exist from a prior run; `make clean && make layer2`.
- If `make layer3` fails on ALLOW: show `backend.json`, narrate the flow, skip to the architecture doc.
- Do not debug live. The argument is in the architecture doc, the demo is the garnish.
