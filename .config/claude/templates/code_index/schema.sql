-- Bi-temporal code knowledge graph schema
-- SQLite for temporal/relational queries, ChromaDB for semantic search

-- Code entities (classes, methods, functions)
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('module', 'class', 'method', 'function', 'attribute')),
    qualified_name TEXT NOT NULL,  -- e.g., "mypackage.services.module.function_name"
    file_path TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER,
    signature TEXT,
    docstring TEXT,
    parent_id TEXT REFERENCES entities(id),  -- For methods -> class

    -- Bi-temporal fields
    valid_from TEXT NOT NULL,      -- ISO timestamp: when entity appeared in code
    valid_until TEXT,              -- ISO timestamp: when entity removed (null = current)
    commit_sha_from TEXT,          -- Git commit that introduced
    commit_sha_until TEXT,         -- Git commit that removed
    indexed_at TEXT NOT NULL,      -- When we last scanned this

    -- Metadata
    decorators TEXT,               -- JSON array
    is_async INTEGER DEFAULT 0,
    is_property INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_file ON entities(file_path);
CREATE INDEX IF NOT EXISTS idx_entities_valid ON entities(valid_from, valid_until);
CREATE INDEX IF NOT EXISTS idx_entities_qualified ON entities(qualified_name);

-- Code relationships (calls, inherits, imports, uses_type)
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL REFERENCES entities(id),
    target_id TEXT,                -- May be null if target is external
    target_name TEXT NOT NULL,     -- Name of target (for external refs)
    rel_type TEXT NOT NULL CHECK (rel_type IN ('calls', 'inherits', 'imports', 'uses_type', 'decorates', 'returns', 'raises')),

    -- Bi-temporal
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    commit_sha_from TEXT,

    -- Context
    line_number INTEGER,           -- Where the relationship occurs
    UNIQUE(source_id, target_name, rel_type, line_number)
);

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(rel_type);
CREATE INDEX IF NOT EXISTS idx_relations_valid ON relations(valid_from, valid_until);

-- Fix attempts for learning
CREATE TABLE IF NOT EXISTS fix_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    fix_action TEXT NOT NULL,
    fix_details TEXT,
    file_path TEXT,

    -- Temporal
    attempted_at TEXT NOT NULL,
    completed_at TEXT,
    commit_sha TEXT,

    -- Outcome
    outcome TEXT CHECK (outcome IN ('pending', 'success', 'failed', 'partial')),
    notes TEXT,

    -- For learning
    similar_to_id INTEGER REFERENCES fix_attempts(id)
);

CREATE INDEX IF NOT EXISTS idx_fix_package ON fix_attempts(package);
CREATE INDEX IF NOT EXISTS idx_fix_error ON fix_attempts(error_type);
CREATE INDEX IF NOT EXISTS idx_fix_outcome ON fix_attempts(outcome);

-- Git commit cache for temporal tracking
CREATE TABLE IF NOT EXISTS commits (
    sha TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    author TEXT,
    message TEXT
);

-- Index rebuild history
CREATE TABLE IF NOT EXISTS index_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rebuilt_at TEXT NOT NULL,
    commit_sha TEXT,
    entity_count INTEGER,
    relation_count INTEGER,
    duration_seconds REAL
);

-- Views for common queries

-- Current entities (not removed)
CREATE VIEW IF NOT EXISTS current_entities AS
SELECT * FROM entities WHERE valid_until IS NULL;

-- Current relations
CREATE VIEW IF NOT EXISTS current_relations AS
SELECT * FROM relations WHERE valid_until IS NULL;

-- Entity change history
CREATE VIEW IF NOT EXISTS entity_changes AS
SELECT
    e.qualified_name,
    e.entity_type,
    e.valid_from,
    e.valid_until,
    c_from.message as introduced_by,
    c_until.message as removed_by
FROM entities e
LEFT JOIN commits c_from ON e.commit_sha_from = c_from.sha
LEFT JOIN commits c_until ON e.commit_sha_until = c_until.sha
ORDER BY e.valid_from DESC;

-- Fix success rates by error type
CREATE VIEW IF NOT EXISTS fix_success_rates AS
SELECT
    error_type,
    fix_action,
    COUNT(*) as total,
    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate
FROM fix_attempts
WHERE outcome IS NOT NULL
GROUP BY error_type, fix_action
ORDER BY total DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- FLYWHEEL: Skills, Episodes, Decisions
-- ═══════════════════════════════════════════════════════════════════════════

-- Skills: patterns that work or don't
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- "pin-version-for-import-errors"
    description TEXT,                     -- Human-readable description
    error_type TEXT,                      -- Associated error type (nullable)

    -- LEGACY: integer scoring (kept for backwards compatibility)
    score INTEGER DEFAULT 0,              -- -20 to +20
    class TEXT DEFAULT 'noise' CHECK (class IN ('noise', 'correctable', 'proven', 'anti-pattern')),

    -- PROBABILISTIC: Beta distribution parameters
    alpha REAL DEFAULT 1.0,               -- Beta α parameter (prior + successes)
    beta REAL DEFAULT 1.0,                -- Beta β parameter (prior + failures)

    -- Temporal
    created_at TEXT NOT NULL,
    last_used_at TEXT,
    last_validated_at TEXT,
    promoted_at TEXT,                     -- When promoted to proven/anti-pattern

    -- Metadata
    evidence_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0
);

-- ═══════════════════════════════════════════════════════════════════════════
-- META-LEARNING: Error and Fix Classes
-- ═══════════════════════════════════════════════════════════════════════════

-- Error classes (learned or predefined clusters)
CREATE TABLE IF NOT EXISTS error_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,            -- 'dependency', 'missing', 'build', 'test'
    description TEXT,
    pattern TEXT,                         -- Regex pattern for matching
    embedding BLOB,                       -- Centroid embedding for semantic matching
    created_at TEXT NOT NULL
);

-- Fix classes (learned or predefined clusters)
CREATE TABLE IF NOT EXISTS fix_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,            -- 'constrain', 'add_requirement', 'modify_recipe'
    description TEXT,
    pattern TEXT,
    embedding BLOB,
    created_at TEXT NOT NULL
);

-- Meta-knowledge: class-level success rates (hierarchical prior)
CREATE TABLE IF NOT EXISTS meta_knowledge (
    error_class_id INTEGER NOT NULL REFERENCES error_classes(id),
    fix_class_id INTEGER NOT NULL REFERENCES fix_classes(id),

    -- Beta distribution for class-level success rate
    alpha REAL DEFAULT 1.0,               -- α = a₀ + class_successes
    beta REAL DEFAULT 1.0,                -- β = b₀ + class_failures

    -- Counts
    observation_count INTEGER DEFAULT 0,

    -- Temporal
    created_at TEXT NOT NULL,
    updated_at TEXT,

    PRIMARY KEY (error_class_id, fix_class_id)
);

-- Map individual errors/fixes to their classes
CREATE TABLE IF NOT EXISTS error_class_membership (
    error_type TEXT PRIMARY KEY,
    error_class_id INTEGER NOT NULL REFERENCES error_classes(id),
    confidence REAL DEFAULT 1.0,          -- How sure of classification (0-1)
    assigned_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fix_class_membership (
    fix_action TEXT PRIMARY KEY,
    fix_class_id INTEGER NOT NULL REFERENCES fix_classes(id),
    confidence REAL DEFAULT 1.0,
    assigned_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skills_class ON skills(class);
CREATE INDEX IF NOT EXISTS idx_skills_error ON skills(error_type);
CREATE INDEX IF NOT EXISTS idx_skills_score ON skills(score DESC);

-- Skill evidence: links skills to fix_attempts
CREATE TABLE IF NOT EXISTS skill_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    fix_attempt_id INTEGER NOT NULL REFERENCES fix_attempts(id),
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'failed', 'partial')),
    score_delta INTEGER NOT NULL,         -- How much this evidence changed the score
    recorded_at TEXT NOT NULL,
    UNIQUE(skill_id, fix_attempt_id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_skill ON skill_evidence(skill_id);

-- Episodes: what happened (richer than fix_attempts)
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Context
    task_description TEXT NOT NULL,
    packages TEXT,                        -- JSON array of packages involved
    session_id TEXT,                      -- Group related episodes

    -- What happened
    approach TEXT,                        -- What was tried
    outcome TEXT CHECK (outcome IN ('success', 'failed', 'partial', 'abandoned')),
    lessons TEXT,                         -- What was learned (JSON array)

    -- Links
    skills_applied TEXT,                  -- JSON array of skill IDs used
    skills_discovered TEXT,               -- JSON array of skill IDs learned
    fix_attempts TEXT,                    -- JSON array of fix_attempt IDs

    -- Temporal
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL,

    -- Context snapshot
    commit_sha TEXT,
    files_touched TEXT                    -- JSON array
);

CREATE INDEX IF NOT EXISTS idx_episodes_outcome ON episodes(outcome);
CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id);

-- Decisions: why we chose X over Y
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- The decision
    question TEXT NOT NULL,               -- "Should we use pin_version or add_requirement?"
    choice TEXT NOT NULL,                 -- "pin_version"
    alternatives TEXT,                    -- JSON array of alternatives considered
    rationale TEXT,                       -- Why this choice

    -- Context
    episode_id INTEGER REFERENCES episodes(id),
    error_type TEXT,
    package TEXT,

    -- Outcome tracking
    outcome TEXT CHECK (outcome IN ('validated', 'regretted', 'superseded', 'pending')),
    outcome_notes TEXT,

    -- Temporal
    made_at TEXT NOT NULL,
    validated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON decisions(outcome);

-- Canary validations: track skill validation attempts
CREATE TABLE IF NOT EXISTS canary_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL REFERENCES skills(id),

    -- Validation context
    test_package TEXT NOT NULL,
    test_error_type TEXT,

    -- Result
    passed INTEGER NOT NULL,              -- 1 = passed, 0 = failed
    notes TEXT,

    -- Temporal
    validated_at TEXT NOT NULL
);

-- ═══════════════════════════════════════════════════════════════════════════
-- FLYWHEEL VIEWS
-- ═══════════════════════════════════════════════════════════════════════════

-- Proven skills (safe to recommend)
CREATE VIEW IF NOT EXISTS proven_skills AS
SELECT * FROM skills WHERE class = 'proven' ORDER BY score DESC;

-- Anti-patterns (actively avoid)
CREATE VIEW IF NOT EXISTS anti_patterns AS
SELECT * FROM skills WHERE class = 'anti-pattern' ORDER BY score ASC;

-- Skills ready for promotion (high score but not yet proven)
CREATE VIEW IF NOT EXISTS promotion_candidates AS
SELECT * FROM skills
WHERE class = 'correctable' AND score >= 5
ORDER BY score DESC;

-- Recent episodes with outcomes
CREATE VIEW IF NOT EXISTS recent_episodes AS
SELECT
    e.*,
    (SELECT COUNT(*) FROM json_each(e.skills_discovered)) as skills_learned
FROM episodes e
WHERE e.completed_at IS NOT NULL
ORDER BY e.completed_at DESC
LIMIT 50;

-- Skill effectiveness by error type
CREATE VIEW IF NOT EXISTS skill_effectiveness AS
SELECT
    s.name as skill_name,
    s.error_type,
    s.class,
    s.score,
    s.success_count,
    s.failure_count,
    CASE WHEN (s.success_count + s.failure_count) > 0
         THEN ROUND(100.0 * s.success_count / (s.success_count + s.failure_count), 1)
         ELSE 0 END as success_rate
FROM skills s
WHERE s.evidence_count > 0
ORDER BY s.score DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- PROBABILISTIC VIEWS
-- ═══════════════════════════════════════════════════════════════════════════

-- Skill statistics with Beta distribution metrics
CREATE VIEW IF NOT EXISTS skill_bayesian_stats AS
SELECT
    s.id,
    s.name,
    s.error_type,
    s.class,
    s.alpha,
    s.beta,
    -- E[θ] = α / (α + β)
    ROUND(s.alpha / (s.alpha + s.beta), 4) as mean,
    -- Var[θ] = αβ / ((α+β)²(α+β+1))
    ROUND(SQRT((s.alpha * s.beta) / ((s.alpha + s.beta) * (s.alpha + s.beta) * (s.alpha + s.beta + 1))), 4) as stddev,
    -- Approximate P(θ > 0.7) using z-score (normal approx for large α, β)
    CASE
        WHEN s.alpha + s.beta < 5 THEN NULL  -- Not enough data for approx
        ELSE ROUND((s.alpha / (s.alpha + s.beta) - 0.7) /
             SQRT((s.alpha * s.beta) / ((s.alpha + s.beta) * (s.alpha + s.beta) * (s.alpha + s.beta + 1))), 2)
    END as z_score_above_70pct,
    s.evidence_count
FROM skills s;

-- Probabilistic promotion status
CREATE VIEW IF NOT EXISTS skill_promotion_status AS
SELECT
    b.*,
    CASE
        -- Proven: z-score > 1.28 means P(θ > 0.7) > 0.9
        WHEN b.z_score_above_70pct > 1.28 THEN 'proven'
        -- Anti-pattern: mean < 0.3 with high confidence
        WHEN b.mean < 0.3 AND b.evidence_count >= 5 THEN 'anti_pattern'
        -- Correctable: has some evidence
        WHEN b.evidence_count >= 2 THEN 'correctable'
        ELSE 'noise'
    END as bayesian_class,
    CASE
        WHEN b.z_score_above_70pct > 1.28 THEN 'high'
        WHEN b.z_score_above_70pct > 0.84 THEN 'medium'
        WHEN b.z_score_above_70pct > 0 THEN 'low'
        ELSE 'uncertain'
    END as confidence
FROM skill_bayesian_stats b;

-- Meta-knowledge with computed statistics
CREATE VIEW IF NOT EXISTS meta_knowledge_stats AS
SELECT
    ec.name as error_class,
    fc.name as fix_class,
    mk.alpha,
    mk.beta,
    mk.observation_count,
    ROUND(mk.alpha / (mk.alpha + mk.beta), 4) as class_mean,
    ROUND(SQRT((mk.alpha * mk.beta) / ((mk.alpha + mk.beta) * (mk.alpha + mk.beta) * (mk.alpha + mk.beta + 1))), 4) as class_stddev
FROM meta_knowledge mk
JOIN error_classes ec ON mk.error_class_id = ec.id
JOIN fix_classes fc ON mk.fix_class_id = fc.id
ORDER BY class_mean DESC;

-- Default error classes (seed data)
INSERT OR IGNORE INTO error_classes (name, description, pattern, created_at) VALUES
    ('dependency', 'Version conflicts, missing deps, incompatible packages', 'version|conflict|incompatible|dep', datetime('now')),
    ('missing', 'Missing modules, files, headers, imports', 'missing|not.found|no.module|import.error', datetime('now')),
    ('build', 'Compilation, linking, recipe errors', 'build|compile|link|recipe|cmake', datetime('now')),
    ('test', 'Test failures, import name issues', 'test|assert|import.name', datetime('now')),
    ('hash', 'Checksum mismatches, download issues', 'hash|sha256|checksum|download', datetime('now'));

-- Default fix classes (seed data)
INSERT OR IGNORE INTO fix_classes (name, description, pattern, created_at) VALUES
    ('constrain', 'Pin versions, add constraints, lock ranges', 'pin|constrain|lock|version', datetime('now')),
    ('add_requirement', 'Add host/run/build requirements', 'add.*req|requirement', datetime('now')),
    ('modify_recipe', 'Edit meta.yaml, build scripts', 'recipe|meta.yaml|build.sh', datetime('now')),
    ('fetch_metadata', 'Get info from PyPI, update checksums', 'pypi|fetch|sha256|metadata', datetime('now')),
    ('skip_or_isolate', 'Skip tests, isolate problematic code', 'skip|isolate|disable', datetime('now'));
