"""
Layer 2: generate a synthetic .c1z and preview its contents.

Normally this .c1z would be produced by running baton-github against a real
GitHub organization (BATON_TOKEN=<pat> baton-github). For the demo we ship a
synthetic one — same schema, same query paths, no real-org dependency — so the
narration can focus on the three-layer story instead of IAM logistics.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The test fixture generator that ships with carryall-baton-backend builds the
# same v1_resources/v1_entitlements/v1_grants structure baton connectors emit.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))

from carryall_baton.c1z import C1ZReader
from _fixture import build_synthetic_c1z


DEMO_ROOT = Path(__file__).resolve().parents[1]
C1Z_PATH = DEMO_ROOT / "sync.c1z"


def main() -> None:
    print("-- Layer 2: ConductorOne Baton (entitlement graph) --\n")

    build_synthetic_c1z(C1Z_PATH)
    print(f"wrote {C1Z_PATH.relative_to(DEMO_ROOT)} ({C1Z_PATH.stat().st_size} bytes, gzipped SQLite)")
    print("  (in production this comes from `BATON_TOKEN=<pat> baton-github`)\n")

    reader = C1ZReader(str(C1Z_PATH))
    with reader.connect() as conn:
        users = reader.list_resources(conn, "user")
        teams = reader.list_resources(conn, "team")
        repos = reader.list_resources(conn, "repo")
        grants = reader.list_grants(conn, principal_resource_type_id="user")

    print(f"Resources: {len(users)} users, {len(teams)} teams, {len(repos)} repos")
    print(f"Grants:    {len(grants)} principal→entitlement→resource edges\n")

    print("Repos in this sync:")
    for r in repos:
        print(f"  - {r.external_id}")

    print("\nExample grants:")
    for g in grants[:4]:
        print(
            f"  - {g.principal_resource_type_id}:{g.principal_resource_id[:28]}... "
            f"-> {g.resource_type_id}:{g.resource_id[:28]}... "
            f"(entitlement {g.entitlement_id[:28]}...)"
        )


if __name__ == "__main__":
    main()
