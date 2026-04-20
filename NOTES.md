# Notes — what building this taught me

Working journal from building a per-action agent-authorization prototype. Started before ConductorOne launched AIAM in March 2026, kept iterating on it after because the exercise kept teaching me things. These are my thinking notes — not a product proposal, not a pitch. What I learned by putting my hands on the hard parts.

---

## 1. What I set out to learn

Going in, I had four open questions about agent authorization architecture. I wanted to stress-test my own thinking by building, not reading:

- **Is "sign every action" practical, or does the signing cost kill you in a real request path?** Envelope schemes sound clean on paper. I didn't trust that they'd survive a real hot path.
- **Can a compiler take an agent's stated intent and narrow it to a minimum-scope capability reliably?** This is where the pitch decks always wave their hands. I wanted to feel where the hand-waving is.
- **What's the right boundary between the entitlement graph and the runtime PDP?** Specifically: does the PDP need to own its own view of the graph, or does it consume the graph vendor's?
- **Is the cryptographic audit trail a nice-to-have, or is it the actual product?** I suspected the audit story might matter more than the runtime enforcement, but I didn't know.

---

## 2. What the prototype confirmed

Things my initial thinking got right, and now I've seen them for myself:

- **Ed25519 signing is free at this scale.** Sub-millisecond per envelope on commodity hardware. The signing cost is not the bottleneck. If anything kills this architecture at scale, it's not the crypto.
- **Consuming the entitlement graph through a narrow Protocol (seven methods) works.** The PDP doesn't need to know anything about the graph source — Baton, Okta, raw SQL, anything that implements the interface plugs in. This is the cleanest boundary in the whole design.
- **The ALLOW/DENY story is genuinely better than a token-scope check.** When an unauthorized action fails because the *capability was never compiled in the first place*, that's a different claim than "we checked and rejected it." The blast radius of a compromised agent shrinks by a real order of magnitude.

---

## 3. What the prototype changed my mind about

This is the section that mattered. If I didn't change my mind building this, I wasn't being rigorous enough.

> **Placeholder — these are starter insights. Erik: please keep the ones that are true for you, rewrite the rest in your voice. Forced insight is worse than no insight.**

- **I thought intent-to-scope compilation via LLM would be clean. It isn't.** It's the messiest part of the whole pipeline. Deterministic keyword maps work for a demo; adversarial intents are an open problem I don't have a good answer for. My current take: any production system has to either bound the intent-expression language aggressively (not free-form English) or accept that the compilation step is the weakest link in the chain. I suspect AIAM sidesteps this problem entirely by operating at the MCP-server-access level rather than the per-action level, which is probably the right move for a platform product even if it gives up some finest-grained authorization.
- **I thought offline envelope verification was the primary benefit of cryptographic capabilities. I now think the hash-chained audit trail is probably more valuable.** Regulators — EU AI Act, SEC cyber disclosure, auditors doing SOC 2 work — will ask "show me evidence for this decision." They will not ask "can you verify this envelope without network access." The signed envelope is the means; the evidentiary chain it produces is what customers will actually pay for.
- **I underestimated how much the entitlement graph dominates the whole stack.** I started this thinking the runtime primitive was the interesting problem. After building the bridge, I think the runtime primitive is only interesting *because* the graph underneath is already solved. If I didn't have Baton to consume, I'd be stuck rebuilding it — which is a five-year problem, not a weekend-project problem. This is the insight that changed how I think about the market structure.
- **Per-action TTLs sound like a feature until you think about caching.** A 300-second TTL means every 5 minutes the agent re-requests a capability. For a high-throughput agent, that's either a lot of PDP load or a cache layer nobody's drawn yet. I don't have a clean answer.

---

## 4. Open questions I'm still sitting with

These are the ones I haven't resolved, and I think the people building production systems in this space are probably also sitting with them:

- **Adversarial intent.** If the agent can describe what it wants in natural language, so can an attacker whose prompt-injected the agent. How do you compile a trustworthy scope from an untrustworthy intent string? I don't think this has a clean solution, and I'd like to know how AIAM is handling it — if at all.
- **Non-repudiation with rotating agent identities.** If an agent's private key rotates daily, how does audit-time verification survive key rotation without a key-registry hop? Does every audit query have to go through a timestamp-service? (I think yes, but that introduces a dependency the PDP architecture is supposed to avoid.)
- **The on-prem story.** Cryptographic envelope verification in an on-prem environment is easy. Entitlement graph freshness in an air-gapped environment is hard. Everyone seems to handwave past this, and it's the number one question I'd expect from a FedRAMP-curious customer.
- **Where does the primitive live in two years?** My guess: per-action authorization becomes table stakes for agent-runtime products, exactly the way OAuth token introspection became table stakes for APIs. The surface it lives on — in the MCP runtime, in the model gateway, in a separate PDP — is the interesting question. I don't know what the right answer is. I have priors, but I don't trust them.

---

## What's in this repo

- `scripts/02_baton.py` — generates and previews a synthetic `.c1z` entitlement graph (same v1 schema `baton-github` emits; populated from a deterministic fixture rather than a real GitHub org, so the demo runs without external credentials)
- `scripts/03_carryall.py` — loads the graph through the `load_backend()` entry-point, runs a compile-intent → sign-envelope → check-access flow with real Ed25519 keys, prints both an ALLOW scenario and a DENY scenario
- `vendor/_fixture.py` — the fixture that builds the synthetic `.c1z`
- `dashboard/index.html` — offline-safe HTML sketch of what a product surface *could* look like if these primitives were productized. This is a thinking aid, not a proposal.

`make demo` runs the CLI flow in ~90 seconds. Real Ed25519, real SQLite-backed `.c1z`, real Protocol-boundary between Carryall and the Baton adapter. Nothing is mocked except the fixture data itself.
