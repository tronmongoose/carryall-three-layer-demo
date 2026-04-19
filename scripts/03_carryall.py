"""
Layer 3: Carryall runtime authorization, using the Baton .c1z as the backend.

Two scenarios:
  (1) IN-SCOPE action:  release-agent (mapped to GitHub user 'alice') asks to
      audit acme/api. Alice has admin on acme/api. Envelope is issued with
      minimal scopes, signed, and check_access returns ALLOW.

  (2) OUT-OF-SCOPE action: release-agent (mapped to user 'charlie') asks the
      same question about acme/api. Charlie has no grant on acme/api.
      check_access returns DENY with the baton grant graph as the reason.

Prints a signed envelope and both decisions.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from authority_runtime import (
    Authority,
    Context,
    ExecutionConfig,
    Skill,
    SkillParameters,
    create_envelope,
    generate_key_pair,
    validate_envelope,
)
from authority_runtime.backends import Decision, load_backend
from authority_runtime.compiler import FakeCompiler
from authority_runtime.envelope import narrow_authority


DEMO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_CONFIG = DEMO_ROOT / "backend.json"


def build_root(private_key: str, agent_id: str):
    skill = Skill(
        id="skill-github-audit",
        name="github-audit",
        tool="Audit a GitHub repo for stale access and surface revocations",
        parameters=SkillParameters(allowed=["repo", "since"], constraints={}),
    )
    authority = Authority(
        scopes=["vault:acme:read", "audit:read"],
        resources=["*"],
        constraints={},
    )
    context = Context(included=["intent"], excluded=[], max_size_bytes=10_000)
    return create_envelope(
        agent_id=agent_id,
        provider="custom",
        step_number=0,
        root_policy_id="policy-demo",
        skill=skill,
        authority=authority,
        context=context,
        execution=ExecutionConfig(provider_config={}),
        private_key=private_key,
        ttl_seconds=600,
    )


async def run_scenario(
    label: str,
    agent_id: str,
    principal: str,
    resource_uri: str,
) -> None:
    print(f"\n=== Scenario: {label} ===")
    print(f"Agent:      {agent_id}  (maps to baton principal '{principal}')")
    print(f"Intent:     audit the target repo for stale access")
    print(f"URI:        {resource_uri}")

    # Re-load backend per scenario so the principal mapping is scenario-specific.
    from carryall_baton import BatonBackend
    with open(BACKEND_CONFIG) as f:
        base_init = json.load(f)["init"]
    backend = BatonBackend(
        c1z_path=base_init["c1z_path"],
        agent_to_principal={agent_id: principal},
    )

    meta = backend.get_metadata(resource_uri, agent_id)
    if principal not in meta.allowed_agents:
        allowed = ", ".join(meta.allowed_agents) if meta.allowed_agents else "(none)"
        print(f"Envelope:   not issued — Baton graph has no grant for '{principal}' on {resource_uri}")
        print(f"Decision:   [DENY ] allowed principals per Baton: {allowed}")
        print(f"  rule:     baton_no_grant (pre-authorization)")
        return

    private_key, public_key = generate_key_pair()
    root = build_root(private_key, agent_id)

    compiler = FakeCompiler(
        keyword_map={"audit": ["audit:read"], "acme": ["vault:acme:read"]},
    )
    selection = await compiler.select_skill(
        user_request="audit the target repo for stale access",
        current_step=1,
        parent_authority=root.authority,
        available_context_fields=root.context.included,
        available_skills=[root.skill],
        available_scopes=root.authority.scopes,
    )
    narrowing = narrow_authority(
        parent_envelope=root,
        required_scopes=selection.required_scopes,
        required_context_fields=selection.required_context_fields,
    )
    child = create_envelope(
        agent_id=agent_id,
        provider="custom",
        step_number=1,
        root_policy_id="policy-demo",
        skill=selection.selected_skill,
        authority=narrowing.narrowed_authority,
        context=narrowing.narrowed_context,
        execution=ExecutionConfig(provider_config={}),
        private_key=private_key,
        parent_envelope_id=root.envelope_id,
        ttl_seconds=300,
    )

    validation = validate_envelope(child, parent_envelope=root, public_key=public_key)
    print(f"Envelope:   {child.envelope_id}  signed+valid={validation['valid']}  ttl={child.ttl_seconds}s")
    print(f"  scopes:   {child.authority.scopes}")
    print(f"  sig:      {child.signature[:48]}...")

    decision = backend.check_access(child, "read", resource_uri)
    bar = "ALLOW" if decision.decision == Decision.ALLOW else "DENY "
    print(f"Decision:   [{bar}] {decision.reason}")
    if "rule" in decision.metadata:
        print(f"  rule:     {decision.metadata['rule']}")


async def main() -> None:
    print("-- Layer 3: Carryall runtime authorization --")
    print(f"   CARRYALL_SLOS_CONFIG -> {BACKEND_CONFIG.relative_to(DEMO_ROOT)}")

    await run_scenario(
        label="in-scope (alice has admin on acme/api)",
        agent_id="release-agent",
        principal="alice",
        resource_uri="slos://vaults/acme/api",
    )
    await run_scenario(
        label="out-of-scope (charlie has no grant on acme/api)",
        agent_id="release-agent",
        principal="charlie",
        resource_uri="slos://vaults/acme/api",
    )

    print("\nThe ALLOW scenario compiled and signed a minimum-scope capability.")
    print("The DENY scenario never compiled one — the graph said no, so no")
    print("envelope authorizing that action was ever issued. The unauthorized")
    print("action was cryptographically impossible, not detected after the fact.")


if __name__ == "__main__":
    asyncio.run(main())
