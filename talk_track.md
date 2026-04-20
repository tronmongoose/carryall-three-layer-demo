# Talk track — 10 minutes

Timings are targets; trim ruthlessly.

## 0:00 – 0:30 — Frame

> In ten minutes I want to lay out a thesis for an agent governance product line at C1, and show you the working prototype. Before I get to identity, let me describe the problem enterprises are actually walking into.

## 0:30 – 1:30 — The problem

> Two things enterprises don't have today, and both of them are prior to any identity question.
>
> One: they don't know where all their AI agents, models, and apps are. Shadow AI. Somebody in marketing wires a GPT into a Google Doc. Somebody in engineering deploys a coding agent against production. Somebody in support spins up a chatbot with a database connection. Nobody has the inventory. You can't govern what you can't see.
>
> Two: even for the agents they do know about, they don't know where the vulnerabilities are in the tools those agents access. Every agent loads skills, MCP servers, model providers, API clients. That's a supply chain. In the public data, roughly one in twelve skills in the largest agent-skill index is confirmed malicious. You can't trust what you haven't vetted.
>
> Those two gaps — inventory and vulnerability — are Layer 1 of the stack. They're necessary. Manifold and a handful of others are building that layer. I'm not rebuilding it.

## 1:30 – 2:00 — The three-layer response

> Governance needs three layers. Layer 1 is what I just described — discovery and supply chain, provided today by Manifold and peers. Layer 2 is the entitlement graph: who should have access to what. C1 already owns this through Baton. Layer 3 is runtime authorization: what can this specific agent do, right now, for this specific task. That layer is unclaimed. The rest of this demo is Layers 2 and 3, running.

## 2:00 – 4:00 — Layer 2: Baton (entitlement graph)

Run `make layer2`. Script regenerates `sync.c1z` and prints its contents.

> Layer 2 is the entitlement graph — who should have access to what. ConductorOne already owns this. Baton is the open-source piece: connectors that dump any source system into a standard `.c1z` file. I'm generating a synthetic one here — same schema, same query shape as `baton-github` would produce against a real org. Three users, three repos, nine grants. Alice has admin on `acme/api`. Charlie has read on `acme/frontend` only. In production this file comes from `baton-github` against the customer's real GitHub. The adapter doesn't care.

## 4:00 – 8:00 — Layer 3: Carryall (runtime authorization)

Run `make layer3`. Two scenarios print.

> Layer 3 is what I built. Runtime authorization. The agent declares intent in natural language. A compiler reads the entitlement graph from Layer 2 and produces the minimum set of scopes the agent needs to fulfill that intent. Those scopes are wrapped in an Ed25519-signed envelope with a 300-second TTL and the agent's identity. The envelope is the capability.
>
> Scenario one: the release agent maps to Alice. Alice has admin on `acme/api`. The envelope is issued, signed, and check_access returns ALLOW with the baton grant as the reason. You can see the signature right there.
>
> Scenario two: same agent, mapped to Charlie. Charlie has no grant on `acme/api`. check_access returns DENY. No envelope authorizing that action was ever issued. This is the point: **the unauthorized action was cryptographically impossible, not because someone detected it and responded, but because the capability never existed**.

> The thing I want to underscore: the adapter that bridges Baton into Carryall is a ~270-line class whose seven Protocol methods are the only surface Carryall touches. I added that Protocol to authority-runtime itself in the 0.4.0 release, right before this conversation. Any Baton connector — Okta, Snowflake, Salesforce — plugs in the same way. No Carryall code changes.

## 8:00 – 10:00 — The ask

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
