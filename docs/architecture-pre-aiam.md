# Agent Governance: The Three-Layer Stack

> **Archived — pre-AIAM thinking.** I wrote this in early April 2026, before ConductorOne launched AIAM. The core argument — that agent governance needs distinct layers and that the entitlement graph is the right scope source — still holds. But the market framing (specifically the claim that "Layer 3 is unclaimed") is out of date. C1 shipped in this space in March. I'm keeping this doc in the repo because it's honest about what I believed when I started building, and the shift in framing is part of what I learned. Current thinking lives in `NOTES.md`.

**Author:** [Your name]
**Date:** April 2026 (archived April 20, 2026 after AIAM launch)
**Status:** Historical — see `NOTES.md` for current thinking

---

## TL;DR

Governing AI agents requires three distinct layers of control: supply chain intelligence on what agents are made of, entitlement governance on what they can access, and runtime authorization on what they can actually do.

Today, those three layers are being built by three different companies. ConductorOne already owns Layer 2 — the entitlement graph — through Baton and the C1 platform. Manifold is building Layer 1. Layer 3 is unclaimed.

I built a working prototype of Layer 3 — Carryall — that consumes the Baton entitlement graph and issues cryptographically signed, time-boxed capabilities to agents on a per-action basis. It is the natural product extension of what C1 already does for humans, into the world where agents outnumber humans as access requesters.

This document explains the gap, the extension, what it becomes inside C1, and why now.

---

## The Gap

ConductorOne built the right primitive for the human era of identity governance: a unified entitlement graph that answers "who should have access to what." Baton extracts it from any source system. The platform layers human workflow on top — access reviews, JIT requests, birthright policies, certifications.

The entire model assumes a human is the access requester. A human asks. A human reviews. A human revokes. The cycle is measured in days or weeks.

Agents don't fit this model. An agent doesn't request access once and use it for a quarter — it takes thousands of distinct actions per hour, each of which should be authorized against the same entitlement graph, but at machine speed, with cryptographic guarantees, and with an audit trail granular enough to reconstruct any individual decision.

The current industry response has two flavors, both inadequate:

**Give the agent a long-lived token with broad scope.** This is what most production deployments do today. It works until the agent is compromised — by prompt injection, by a malicious skill, by a supply chain attack on its dependencies — at which point the blast radius is the full scope of the token. Recent data from Manifold's Manifest scanner shows 1 in 12 skills on the largest agent skill marketplace are confirmed malicious, and leading scanners miss 91% of behavioral threats. Long-lived tokens in this environment are unacceptable.

**Detect-and-respond on agent behavior.** This is Manifold's bet, and it's a reasonable one. Watch what the agent does, flag anomalies, terminate suspicious sessions. But detection is structurally a lagging control. By the time you've detected the bad action, the bad action has happened. For high-stakes systems — production code, customer data, financial transactions — detection is necessary but not sufficient.

What's missing is a third option: **make the unauthorized action cryptographically impossible in the first place, by issuing the agent only the minimum capability it needs for the specific action it's about to take.**

That's the gap. That's Layer 3.

---

## The Extension

Carryall is a runtime policy decision point and policy enforcement point for agent actions. It consists of:

- **A policy compiler.** The agent declares its intent in natural language ("audit Q1 engineering GitHub access for staleness"). The compiler reads the entitlement graph and produces the minimum set of scopes required to fulfill that intent.
- **A signed envelope.** The compiled scopes are wrapped in an Ed25519-signed envelope with a 300-second TTL, the agent's identity, and the original intent. This envelope is the agent's capability for the action.
- **A verification protocol.** Any backend (vault, database, API gateway, file system) can verify the envelope's signature and scope before serving data. Backends can be progressively brought under envelope verification — there is no big-bang migration.
- **A tamper-evident audit log.** Every envelope issuance, action, and result is logged with a hash chain. The log is independently verifiable.

The entire system is built on a key insight: **the entitlement graph is the right scope source.** ConductorOne has already done the hard work of normalizing identity and permission data across hundreds of systems via Baton. Carryall consumes that graph as its source of truth. There is no second graph to maintain, no parallel data model, no integration drift.

The working prototype demonstrates this end-to-end against `baton-github`, with a ~270-line adapter whose seven Protocol methods are the only surface Carryall touches. Adding any other Baton connector requires no changes to the Carryall code.

---

## What This Becomes at ConductorOne

Carryall, integrated into C1, becomes **"ConductorOne for Agents"** — a natural extension of the existing platform, not a pivot.

**Same buyer.** The IAM/IGA team that buys C1 today is the same team that will buy agent governance tomorrow. They already trust C1 with the entitlement graph. They will not want to manage agent authorization in a separate tool from a separate vendor.

**Same data model.** Agents become first-class identities in the C1 graph, alongside humans and service accounts. The same access reviews, the same SoD policies, the same audit reports — extended to cover agent identities and their per-action capabilities.

**Same compliance story.** SOC 2, ISO 27001, and the EU AI Act all demand auditability of automated decisions. C1 already produces audit trails for human access. Carryall extends the same evidentiary model to every action taken by every agent, with cryptographic signatures that strengthen the chain of evidence rather than weaken it.

**New revenue surface.** Agent governance is a net-new product line, not a feature of the existing one. Pricing can be per-agent, per-envelope, or per-protected-resource — all of which are independent from the existing per-seat human IGA pricing. Initial customer profile: any C1 customer running production AI agents, which by 2027 will be roughly all of them.

**Defensive moat.** Manifold and the wave of agent-security startups behind them are building Layer 1 (supply chain) and a thinner version of Layer 3 (runtime detection). None of them have Layer 2. C1 is the only company that can credibly ship all three layers as a single platform, because C1 is the only company that already owns the entitlement graph the other two layers need.

---

## Why Now

Three timing signals converge in 2026:

**1. Agent deployment crossed the production threshold.** Coding agents, customer support agents, and internal automation agents are no longer pilots. They are running with elevated permissions in production environments at most enterprise customers C1 already sells to. The CISO conversation has shifted from "should we deploy agents" to "how do we govern the ones already deployed."

**2. The supply chain attack surface is now empirically dangerous.** Manifold's own data — published April 2026 — confirms 1,295 high-risk skills out of ~140,000 indexed, with one documented incident of a malicious skill manipulated to #1 ranking and executed ~3,900 times across 50+ cities in six days. This is npm-circa-2018 dynamics, but with the blast radius of full agent permissions instead of build pipelines.

**3. Regulatory clocks are starting.** The EU AI Act's high-risk system provisions begin enforcement in stages through 2026-2027. NIST AI RMF and the SEC's cybersecurity disclosure rules are pulling auditability requirements into corporate compliance programs. The companies that can produce cryptographic audit trails for agent actions in 2026 will be the ones positioned to win regulated-industry deals in 2027.

The window for C1 to claim Layer 3 is approximately 12 months. After that, either Manifold extends downward into authorization (likely — they are already moving from pure detection into supply chain intelligence with Manifest), or a new entrant raises a Series A with the explicit pitch of "the runtime authorization layer the IGA vendors missed." Either outcome cedes a category C1 should own.

---

## What I'm Proposing

Three things, in priority order:

1. **The role we're already discussing.** I want to lead product at C1 as VP, on the path to CPO. The thesis above is what I'd execute against in year one regardless of how Carryall is handled.

2. **Bring Carryall inside C1 as the foundation of an agent product line.** I built the prototype on my own time with no employer IP entanglement. I would contribute the codebase to C1 in exchange for terms we negotiate as part of the offer. The plugin is already submitted to the Anthropic marketplace, which gives C1 a distribution surface into the developer audience starting day one.

3. **A 90-day plan to ship a closed beta.** Concrete: pick three existing C1 customers running coding agents in production, deploy Carryall against their existing Baton-synced entitlement graph for one repo each, measure blocked-vs-allowed action rates, publish the results as a category-defining piece of research with C1's brand on it.

The demo I have prepared shows the technical foundation working end-to-end across all three layers. The rest is execution, and execution is the part of this conversation I'm most excited to have.

---

## Appendix: Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   LAYER 1: SUPPLY CHAIN INTELLIGENCE                             │
│   ───────────────────────────────────                            │
│   Verify the agent itself before it runs.                        │
│   Provided today by: Manifold (Manifest), others.                │
│                                                                  │
│   "Is this skill safe to install?"                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   LAYER 2: ENTITLEMENT GOVERNANCE              ← C1 OWNS THIS    │
│   ──────────────────────────────                                 │
│   Maintain the graph of who/what should have access.             │
│   Provided today by: ConductorOne (Baton + platform).            │
│                                                                  │
│   "What should this identity be allowed to access?"              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   LAYER 3: RUNTIME AUTHORIZATION              ← C1 SHOULD OWN    │
│   ───────────────────────────────                THIS NEXT       │
│   Issue scoped, signed, time-boxed capabilities per action.      │
│   Provided today by: Carryall (prototype).                       │
│                                                                  │
│   "What can this specific agent do, right now, for this task?"   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

The three layers are complementary. C1 is the only vendor positioned
to ship all three because C1 is the only vendor that already owns the
entitlement graph the other two layers need to be useful.
```

---

## References

- ConductorOne Baton: https://github.com/ConductorOne/baton
- Carryall plugin: https://github.com/tronmongoose/agent.carryall_plugin
- Manifold Manifest: https://manifest.manifold.security
- Manifold supply-chain research (April 2026): https://www.manifold.security/blog/manifest-ai-supply-chain-intelligence
