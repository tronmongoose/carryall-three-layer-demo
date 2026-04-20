# Talk track — 5 minutes

Only use this if asked to show something, or if the conversation naturally lands on agent authorization. Not a pitch. Time it with a stopwatch at least once before the meeting.

## 0:00 – 0:45 — Frame the artifact honestly

> Quick context before I open anything: I built this before C1 launched AIAM in March. I kept working on it after because the exercise kept teaching me things I couldn't get from reading blog posts or specs. What I want to show you isn't a product pitch — it's a prototype. Five minutes. Then I'd love to talk about what I learned from building it, because I think some of the open questions in this space are more interesting than the solved ones.

## 0:45 – 1:30 — Layer 2: the entitlement graph

Run `make layer2`.

> This is a synthetic `.c1z` — same schema `baton-github` emits, same tables, just populated from a fixture instead of a real org so it runs anywhere. Three users, three repos, nine grants. Alice has admin on `acme/api`. Charlie doesn't. That's the shape that matters for what comes next. I didn't rebuild Baton — I'm consuming its output through the same schema your connectors already produce.

## 1:30 – 3:30 — Layer 3: the prototype

Run `make layer3`.

> Two scenarios. Agent declares intent in natural language — "audit the target repo for stale access." A compiler narrows the agent's parent authority down to the minimum scopes that satisfy that intent. The result is wrapped in an Ed25519-signed envelope with a 300-second TTL and the agent's identity. That envelope is the capability.
>
> Scenario one: agent maps to Alice. Alice has admin on `acme/api`. Envelope gets compiled and signed. Check-access returns ALLOW with the Baton grant as the reason. Signature is right there.
>
> Scenario two: same agent, mapped to Charlie. No grant on `acme/api`. Check-access short-circuits before envelope compilation. No capability authorizing that action was ever issued. Not rejected after the fact — never created. That's the distinction this primitive is trying to make.

## 3:30 – 5:00 — What building this taught me

> Three things I want to say about what I learned, because I think they're the interesting part.
>
> One: the crypto is not the hard part. Ed25519 signing is free at this scale. If this architecture has a weakness, it isn't the envelope — it's the intent-to-scope compilation step. That's the messiest piece of the pipeline, and I don't have a good answer for adversarial intents. I'd genuinely like to know how AIAM handles that — my guess is it sidesteps the problem by operating at MCP-server granularity rather than per-action, and I think that's probably the right call for a platform product.
>
> Two: I started thinking cryptographic capabilities were interesting because of the runtime enforcement. After building it, I think the hash-chained audit trail is probably the more valuable half. Regulators don't ask "can you verify this envelope offline?" — they ask "show me evidence for this decision." The signed envelope is the means; the evidentiary chain is what customers pay for.
>
> And three — the one that matters most — the hardest problem in this whole space isn't the runtime primitive. It's the entitlement graph underneath. I could not have built this prototype in two days if I had to also build Baton. The reason the runtime layer is interesting is *because* Baton exists. The five years of connector work you've done is what makes anyone's runtime primitive useful or useless. That's the moat, and I don't think it's the agent layer — I think it's the graph.

---

## Backup notes

- If `make layer2` fails: the `.c1z` might already exist from a prior run; `make clean && make layer2`.
- If `make layer3` fails on ALLOW: show `backend.json`, narrate the flow, skip to NOTES.md.
- If live demo is entirely off the table: offer NOTES.md as the artifact and a 3-min Loom as follow-up.
- Do not debug live. If something breaks, move to the conversation.

## What to avoid saying

- "C1 should build this." (They did — it's called AIAM.)
- "This is Layer 3." (Map was pre-AIAM; drop the layer framing unless asked.)
- Anything that sounds like a 90-day execution plan.
- Any framing that compares this prototype to AIAM as a product. Compare to it only as a *learning experience*.
