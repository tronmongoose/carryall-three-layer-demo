"""
Layer 2: generate a synthetic .c1z and visualize its contents.

Normally this .c1z would be produced by running baton-github against a real
GitHub organization (BATON_TOKEN=<pat> baton-github). For the demo we ship a
synthetic one — same schema, same query paths, no real-org dependency — so the
narration can focus on the three-layer story instead of IAM logistics.
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))

from carryall_baton.c1z import C1ZReader
from _fixture import build_synthetic_c1z


DEMO_ROOT = Path(__file__).resolve().parents[1]
C1Z_PATH = DEMO_ROOT / "sync.c1z"

console = Console(width=100, force_terminal=True)


def main() -> None:
    console.print(Panel.fit(
        "[bold]Layer 2 — ConductorOne Baton[/bold]  [dim]entitlement graph[/dim]",
        border_style="cyan",
    ))

    build_synthetic_c1z(C1Z_PATH)
    size = C1Z_PATH.stat().st_size
    console.print(
        f"  wrote [bold]{C1Z_PATH.relative_to(DEMO_ROOT)}[/bold] "
        f"[dim]({size} bytes, gzipped SQLite)[/dim]"
    )
    console.print(
        "  [dim italic]in production: BATON_TOKEN=<pat> baton-github[/dim italic]"
    )
    console.print()

    reader = C1ZReader(str(C1Z_PATH))
    with reader.connect() as conn:
        users = reader.list_resources(conn, "user")
        teams = reader.list_resources(conn, "team")
        repos = reader.list_resources(conn, "repo")
        entitlements = reader.list_entitlements(conn)
        grants = reader.list_grants(conn, principal_resource_type_id="user")

    counts = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    counts.add_column("resource", style="dim")
    counts.add_column("count", justify="right")
    counts.add_row("users", str(len(users)))
    counts.add_row("teams", str(len(teams)))
    counts.add_row("repos", str(len(repos)))
    counts.add_row("grants", str(len(grants)))
    console.print(counts)
    console.print()

    resource_name = {(r.resource_type_id, r.id): r.external_id for r in users + teams + repos}
    ent_name = {e.id: e.external_id for e in entitlements}

    by_principal: dict[str, list[tuple[str, str, str]]] = {}
    for g in grants:
        principal = resource_name.get(("user", g.principal_resource_id), g.principal_resource_id)
        target = resource_name.get((g.resource_type_id, g.resource_id), g.resource_id)
        ent = ent_name.get(g.entitlement_id, "?")
        action = ent.rsplit(":", 1)[-1] if ":" in ent else ent
        by_principal.setdefault(principal, []).append((g.resource_type_id, target, action))

    tree = Tree(f"[bold]acme[/bold] [dim](org, {len(grants)} grants across {len(by_principal)} users)[/dim]")
    for principal in sorted(by_principal):
        edges = by_principal[principal]
        has_api_admin = any(t == "acme/api" and a == "admin" for _, t, a in edges)
        has_api_any = any(t == "acme/api" for _, t, _ in edges)
        if has_api_admin:
            label = f"[bold green]{principal}[/bold green] [green dim](admin on acme/api → ALLOW path)[/green dim]"
        elif not has_api_any:
            label = f"[bold red]{principal}[/bold red] [red dim](no grant on acme/api → DENY path)[/red dim]"
        else:
            label = f"[bold]{principal}[/bold]"
        subtree = tree.add(label)
        for rtype, target, action in sorted(edges):
            style = "green" if target == "acme/api" else ""
            entry = f"{rtype}:[{style}]{target}[/{style}] [dim]({action})[/dim]" if style else \
                    f"{rtype}:{target} [dim]({action})[/dim]"
            subtree.add(entry)

    console.print(tree)


if __name__ == "__main__":
    main()
