"""
Vendored helper: builds a synthetic baton .c1z with the same schema and shape
as carryall-baton-backend/tests/conftest.py, extracted so the demo scripts
can regenerate sync.c1z without depending on pytest.
"""

from __future__ import annotations

import gzip
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path


SCHEMA = """
CREATE TABLE v1_resources (
    id TEXT PRIMARY KEY,
    resource_type_id TEXT NOT NULL,
    external_id TEXT,
    parent_resource_type_id TEXT,
    parent_resource_id TEXT,
    sync_id TEXT,
    data BLOB,
    discovered_at TEXT
);
CREATE INDEX idx_resources_type ON v1_resources(resource_type_id);

CREATE TABLE v1_entitlements (
    id TEXT PRIMARY KEY,
    resource_type_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    external_id TEXT,
    sync_id TEXT,
    data BLOB,
    discovered_at TEXT
);

CREATE TABLE v1_grants (
    principal_resource_type_id TEXT NOT NULL,
    principal_resource_id TEXT NOT NULL,
    resource_type_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    entitlement_id TEXT NOT NULL,
    external_id TEXT,
    sync_id TEXT,
    data BLOB,
    discovered_at TEXT
);

CREATE TABLE v1_sync_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT,
    ended_at TEXT
);
"""


def _make_id(prefix: str, name: str) -> str:
    return f"{prefix}-{name}-{uuid.uuid5(uuid.NAMESPACE_URL, prefix + ':' + name).hex[:8]}"


def _populate(conn: sqlite3.Connection) -> None:
    sync_id = "sync-demo"

    resource_rows = []
    resource_rows.append((_make_id("org", "acme"), "org", "acme", None, None, sync_id, b"", "2026-04-18T00:00:00Z"))
    for u in ("alice", "bob", "charlie"):
        resource_rows.append((_make_id("user", u), "user", u, None, None, sync_id, b"", "2026-04-18T00:00:00Z"))
    for ext in ("acme:engineering", "acme:sre"):
        resource_rows.append((_make_id("team", ext), "team", ext, "org", _make_id("org", "acme"), sync_id, b"", "2026-04-18T00:00:00Z"))
    for r in ("acme/api", "acme/frontend", "acme/infra"):
        resource_rows.append((_make_id("repo", r), "repo", r, "org", _make_id("org", "acme"), sync_id, b"", "2026-04-18T00:00:00Z"))

    conn.executemany("INSERT INTO v1_resources VALUES (?, ?, ?, ?, ?, ?, ?, ?)", resource_rows)

    entitlements = []
    for ext in ("acme:engineering", "acme:sre"):
        entitlements.append((_make_id("ent-team-member", ext), "team", _make_id("team", ext), f"{ext}:member", sync_id, b"", "2026-04-18T00:00:00Z"))
    for r in ("acme/api", "acme/frontend", "acme/infra"):
        for action in ("read", "write", "admin"):
            entitlements.append((_make_id(f"ent-repo-{action}", r), "repo", _make_id("repo", r), f"{r}:{action}", sync_id, b"", "2026-04-18T00:00:00Z"))
    conn.executemany("INSERT INTO v1_entitlements VALUES (?, ?, ?, ?, ?, ?, ?)", entitlements)

    def grant(principal, resource_type, resource, ent_prefix, ent_ext):
        return (
            "user",
            _make_id("user", principal),
            resource_type,
            _make_id(resource_type, resource),
            _make_id(ent_prefix, resource),
            f"grant-{principal}-{ent_ext.replace(':', '-')}",
            sync_id,
            b"",
            "2026-04-18T00:00:00Z",
        )

    grants = [
        grant("alice",   "team", "acme:engineering", "ent-team-member",  "acme:engineering:member"),
        grant("alice",   "repo", "acme/api",         "ent-repo-admin",   "acme/api:admin"),
        grant("alice",   "repo", "acme/frontend",    "ent-repo-write",   "acme/frontend:write"),
        grant("bob",     "team", "acme:engineering", "ent-team-member",  "acme:engineering:member"),
        grant("bob",     "repo", "acme/api",         "ent-repo-write",   "acme/api:write"),
        grant("bob",     "team", "acme:sre",         "ent-team-member",  "acme:sre:member"),
        grant("bob",     "repo", "acme/infra",       "ent-repo-admin",   "acme/infra:admin"),
        grant("charlie", "team", "acme:sre",         "ent-team-member",  "acme:sre:member"),
        grant("charlie", "repo", "acme/frontend",    "ent-repo-read",    "acme/frontend:read"),
    ]
    conn.executemany("INSERT INTO v1_grants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", grants)

    conn.execute("INSERT INTO v1_sync_runs VALUES (?, ?, ?)", (sync_id, "2026-04-18T00:00:00Z", "2026-04-18T00:00:01Z"))
    conn.commit()


def build_synthetic_c1z(out_path: Path) -> None:
    """Write a fresh synthetic .c1z to ``out_path``."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        sqlite_path = Path(tmp.name)
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.executescript(SCHEMA)
        _populate(conn)
        conn.close()

        with open(sqlite_path, "rb") as src, gzip.open(out_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
    finally:
        sqlite_path.unlink(missing_ok=True)
