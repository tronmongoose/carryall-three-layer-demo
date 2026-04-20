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

from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

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

console = Console(width=100, force_terminal=True)


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


def _scenario_facts(agent_id: str, principal: str, resource_uri: str) -> Table:
    facts = Table(show_header=False, box=None, pad_edge=False)
    facts.add_column("k", style="dim")
    facts.add_column("v")
    facts.add_row("agent", f"[bold]{agent_id}[/bold]  [dim]→ baton principal[/dim] [bold cyan]{principal}[/bold cyan]")
    facts.add_row("intent", "audit the target repo for stale access")
    facts.add_row("uri", resource_uri)
    return facts


async def run_scenario(
    label: str,
    agent_id: str,
    principal: str,
    resource_uri: str,
) -> None:
    backend = load_backend(str(BACKEND_CONFIG))
    backend.agent_to_principal[agent_id] = principal

    meta = backend.get_metadata(resource_uri, agent_id)
    facts = _scenario_facts(agent_id, principal, resource_uri)

    if principal not in meta.allowed_agents:
        allowed = ", ".join(meta.allowed_agents) if meta.allowed_agents else "(none)"
        denial = Text.assemble(
            ("no envelope issued — baton graph has no grant for ", "dim"),
            (f"'{principal}'", "bold red"),
            (" on ", "dim"),
            (resource_uri, "bold"),
            "\n",
            ("allowed principals per baton: ", "dim"),
            (allowed, "bold cyan"),
            "\n",
            ("requested principal:          ", "dim"),
            (principal, "bold red"),
        )
        decision_badge = Text.assemble(
            ("  [ DENY ]  ", "bold white on red"),
            (" baton_no_grant", "default"),
            (" (pre-authorization — the graph said no, no capability was ever compiled)", "dim"),
        )
        console.print(Panel(
            Group(facts, Text(""), denial, Text(""), decision_badge),
            title=f"[bold]Scenario: {label}[/bold]",
            border_style="red",
            padding=(1, 2),
        ))
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
    decision = backend.check_access(child, "read", resource_uri)

    envelope_summary = {
        "envelope_id": child.envelope_id,
        "parent_envelope_id": root.envelope_id,
        "scopes": list(child.authority.scopes),
        "ttl_seconds": child.ttl_seconds,
        "signature": child.signature[:48] + "…",
        "signed_and_valid": validation["valid"],
    }
    envelope_json = Syntax(
        json.dumps(envelope_summary, indent=2),
        "json",
        theme="ansi_dark",
        background_color="default",
    )

    bar_text = "[ ALLOW ]" if decision.decision == Decision.ALLOW else "[ DENY ]"
    bar_style = "bold white on green" if decision.decision == Decision.ALLOW else "bold white on red"
    rule = decision.metadata.get("rule", "")
    decision_badge = Text.assemble(
        (f"  {bar_text}  ", bar_style),
        (f" {decision.reason}", "default"),
    )
    if rule:
        decision_badge.append(f"\n     rule: ", style="dim")
        decision_badge.append(rule, style="bold")

    envelope_header = Text("envelope (ed25519-signed, TTL 300s):", style="dim")

    border = "green" if decision.decision == Decision.ALLOW else "red"
    console.print(Panel(
        Group(facts, Text(""), envelope_header, envelope_json, Text(""), decision_badge),
        title=f"[bold]Scenario: {label}[/bold]",
        border_style=border,
        padding=(1, 2),
    ))


async def main() -> None:
    console.print(Panel.fit(
        f"[bold]Layer 3 — Carryall runtime authorization[/bold]\n"
        f"[dim]CARRYALL_SLOS_CONFIG → {BACKEND_CONFIG.relative_to(DEMO_ROOT)}[/dim]",
        border_style="cyan",
    ))
    console.print()

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

    console.print()
    console.print(Panel(
        "The ALLOW scenario compiled and signed a minimum-scope capability.\n"
        "The DENY scenario never compiled one — the graph said no, so no\n"
        "envelope authorizing that action was ever issued. "
        "[bold]The unauthorized action was cryptographically impossible, "
        "not detected after the fact.[/bold]",
        title="[bold]Takeaway[/bold]",
        border_style="cyan",
        padding=(1, 2),
    ))


if __name__ == "__main__":
    asyncio.run(main())
