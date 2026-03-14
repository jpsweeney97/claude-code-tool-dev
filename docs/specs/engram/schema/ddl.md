---
module: ddl
legacy_sections: ["6.1", "6.2", "6.3", "6.4", "6.5"]
authority: schema
normative: true
status: active
---

## Database Schema

*Schema rationale and design notes are in [rationale.md](rationale.md). Observable behavioral guarantees are in [contracts/behavioral-semantics.md](../contracts/behavioral-semantics.md).*

### Connection Pragmas

Set at connection time, not in schema DDL:

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
```

### Kernel

```sql
-- Central entity registry — every domain object gets an entity_pk
CREATE TABLE entities (
    entity_pk   INTEGER PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('session', 'snapshot', 'task', 'lesson')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Migration tracking — forward-only numbered migrations
CREATE TABLE schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Search projection — ordinary table owned by kernel, source of truth for search
-- Application writes this in the same transaction as domain table mutations
CREATE TABLE search_projection (
    entity_pk        INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    entity_type      TEXT NOT NULL,  -- 'session', 'task', 'lesson' (not 'snapshot')
    title            TEXT NOT NULL,
    body             TEXT,
    tags_json        TEXT,           -- JSON array for exact filtering via json_each
    tags_text        TEXT,           -- space-separated for FTS
    created_at       TEXT NOT NULL,
    last_modified_at TEXT NOT NULL
);

-- FTS5 index — external content mode over search_projection
CREATE VIRTUAL TABLE search_documents USING fts5(
    title,
    body,
    tags_text,
    content='search_projection',
    content_rowid='entity_pk',
    tokenize='unicode61'
);

-- FTS5 sync triggers — maintain index when projection changes
CREATE TRIGGER search_ai AFTER INSERT ON search_projection BEGIN
    INSERT INTO search_documents(rowid, title, body, tags_text)
    VALUES (new.entity_pk, new.title, new.body, new.tags_text);
END;

CREATE TRIGGER search_ad AFTER DELETE ON search_projection BEGIN
    INSERT INTO search_documents(search_documents, rowid, title, body, tags_text)
    VALUES ('delete', old.entity_pk, old.title, old.body, old.tags_text);
END;

CREATE TRIGGER search_au AFTER UPDATE ON search_projection BEGIN
    INSERT INTO search_documents(search_documents, rowid, title, body, tags_text)
    VALUES ('delete', old.entity_pk, old.title, old.body, old.tags_text);
    INSERT INTO search_documents(rowid, title, body, tags_text)
    VALUES (new.entity_pk, new.title, new.body, new.tags_text);
END;
```

### Context Subsystem

```sql
CREATE TABLE sessions (
    entity_pk       INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    session_id      TEXT NOT NULL UNIQUE,  -- Claude Code session UUID
    goal            TEXT,
    branch          TEXT,
    context_summary TEXT,
    tags            TEXT CHECK (tags IS NULL OR json_valid(tags)),  -- JSON array
    started_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    closed_at       TEXT,
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    summary         TEXT
);

CREATE TABLE snapshots (
    entity_pk   INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    session_pk  INTEGER NOT NULL REFERENCES sessions(entity_pk) ON DELETE CASCADE,
    content     TEXT NOT NULL,  -- JSON: structured session state
    kind        TEXT NOT NULL DEFAULT 'checkpoint' CHECK (kind IN ('checkpoint', 'final')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE session_links (
    from_session_pk INTEGER NOT NULL REFERENCES sessions(entity_pk) ON DELETE CASCADE,
    to_session_pk   INTEGER NOT NULL REFERENCES sessions(entity_pk) ON DELETE CASCADE,
    is_primary      INTEGER NOT NULL DEFAULT 0,  -- boolean: primary continuation chain
    PRIMARY KEY (from_session_pk, to_session_pk)
);

CREATE INDEX idx_sessions_branch ON sessions(branch);
CREATE INDEX idx_sessions_closed ON sessions(closed_at);
CREATE INDEX idx_snapshots_session ON snapshots(session_pk);
CREATE UNIQUE INDEX idx_snapshots_final ON snapshots(session_pk) WHERE kind = 'final';
CREATE INDEX idx_search_entity_type ON search_projection(entity_type);
```

### Work Subsystem

```sql
CREATE TABLE tasks (
    entity_pk   INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    task_id     TEXT NOT NULL UNIQUE,  -- server-generated UUID
    title       TEXT NOT NULL,
    description TEXT,                   -- optional task body; maps to search_projection.body
    status      TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'done', 'cancelled')),
    priority    TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    tags        TEXT CHECK (tags IS NULL OR json_valid(tags)),  -- JSON array
    reason      TEXT,  -- close reason; required for 'cancelled', forbidden for 'done' (server-side validation)
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    closed_at   TEXT,
    session_pk  INTEGER REFERENCES sessions(entity_pk) ON DELETE RESTRICT,
    -- Bidirectional invariant: closed_at set iff terminal status
    CHECK ((closed_at IS NULL) = (status NOT IN ('done', 'cancelled')))
);

CREATE TABLE task_dependencies (
    task_pk         INTEGER NOT NULL REFERENCES tasks(entity_pk) ON DELETE CASCADE,
    depends_on_pk   INTEGER NOT NULL REFERENCES tasks(entity_pk) ON DELETE CASCADE,
    PRIMARY KEY (task_pk, depends_on_pk),
    CHECK (task_pk != depends_on_pk)
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_session ON tasks(session_pk);
CREATE INDEX idx_deps_depends_on ON task_dependencies(depends_on_pk);
```

### Knowledge Subsystem

```sql
CREATE TABLE lessons (
    entity_pk           INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    lesson_id           TEXT NOT NULL UNIQUE,  -- server-generated UUID
    insight             TEXT NOT NULL,  -- one-liner
    context             TEXT,           -- freeform body
    tags                TEXT CHECK (tags IS NULL OR json_valid(tags)),  -- JSON array
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'retracted')),
    promoted            INTEGER NOT NULL DEFAULT 0,  -- denormalized cache; truth is provenance_links
    reinforcement_count INTEGER NOT NULL DEFAULT 0,  -- historical: preserved on retraction, not decremented
    anchor_hash         TEXT NOT NULL,  -- server-computed normalized hash of insight; dedup key
    retracted_at        TEXT,           -- set when status transitions to 'retracted'
    retraction_code     TEXT CHECK (retraction_code IS NULL OR retraction_code IN ('incorrect', 'obsolete')),
    retraction_reason   TEXT,           -- freeform explanation for retraction
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    session_pk          INTEGER REFERENCES sessions(entity_pk) ON DELETE RESTRICT
);

CREATE INDEX idx_lessons_promoted ON lessons(promoted);
CREATE INDEX idx_lessons_status ON lessons(status);
CREATE INDEX idx_lessons_anchor ON lessons(anchor_hash);
CREATE INDEX idx_lessons_session ON lessons(session_pk);
```

### Cross-cutting

```sql
-- Internal entity-to-entity lineage (derived_from_task_ids, derived_from_lesson_ids)
CREATE TABLE entity_derivations (
    entity_pk        INTEGER NOT NULL REFERENCES entities(entity_pk) ON DELETE CASCADE,
    source_entity_pk INTEGER NOT NULL REFERENCES entities(entity_pk) ON DELETE CASCADE,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (entity_pk, source_entity_pk)
);

-- External provenance + promotion targets (sources, external_refs, promoted_to)
-- Append-only: rows are never deleted (except by CASCADE from entities); only update is NULL label backfill
CREATE TABLE provenance_links (
    id              INTEGER PRIMARY KEY,
    entity_pk       INTEGER NOT NULL REFERENCES entities(entity_pk) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,  -- 'source', 'external_ref', 'promoted_to'
    target_type     TEXT NOT NULL,  -- 'url', 'file', 'github_issue', 'github_pr', etc.
    target_ref      TEXT NOT NULL,  -- URI or path
    target_label    TEXT,           -- human-readable display name (from Ref.label); excluded from uniqueness
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (entity_pk, relation_type, target_type, target_ref)
);

CREATE INDEX idx_derivations_source ON entity_derivations(source_entity_pk);
CREATE INDEX idx_provenance_entity ON provenance_links(entity_pk);
CREATE INDEX idx_provenance_target ON provenance_links(target_type, target_ref);
```
