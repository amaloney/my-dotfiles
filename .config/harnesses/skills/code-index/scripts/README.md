# Bi-Temporal Code Knowledge Graph + Probabilistic Flywheel

Code indexing with bi-temporal tracking, semantic search, and Bayesian skill learning.

## Quick Start

```bash
cd .harness/code_index

# Build the index
python3 build_index_temporal.py

# Query
python3 query_temporal.py search "build container"
python3 query_temporal.py callers my_function
python3 query_temporal.py changes 7d

# Flywheel
python3 flywheel.py status
python3 flywheel.py skills --bayesian
python3 flywheel.py recommend missing_module
python3 flywheel.py meta
```

## Components

| File                      | Purpose                                                      |
| ------------------------- | ------------------------------------------------------------ |
| `schema.sql`              | SQLite schema (entities, relations, flywheel, meta-learning) |
| `build_index_temporal.py` | AST extraction with bi-temporal tracking                     |
| `query_temporal.py`       | Semantic + relational + temporal queries                     |
| `flywheel.py`             | Probabilistic skill learning with meta-knowledge             |

## Probabilistic Flywheel

Skills as Beta distributions: `θ ~ Beta(α, β)` → `E[θ] = α/(α+β)`, `σ = √(αβ/((α+β)²(α+β+1)))`. Posterior: `α' = α + x`,
`β' = β + (1-x)`. P(effective): `P(θ > τ) = 1 - I_τ(α, β)`.

### Promotion

`proven`: P(θ>0.7)>0.9. `anti-pattern`: E[θ]<0.3 ∧ n≥5. `correctable`: n≥2. `noise`: otherwise.

### Meta-Learning

Zero-evidence skills inherit from class: `E[θ] = (a₀ + s_CF)/(a₀ + b₀ + n_CF)`.

## CLI Reference

### flywheel.py

| Command                         | Description                                   |
| ------------------------------- | --------------------------------------------- |
| `status`                        | Show flywheel status with Bayesian metrics    |
| `skills`                        | List skills (add `--bayesian` for α, β, μ, σ) |
| `skills --class proven`         | Filter by class                               |
| `recommend <error_type>`        | Get recommendations with confidence intervals |
| `meta`                          | Show class-level meta-knowledge               |
| `meta --error-class dependency` | Filter meta-knowledge                         |
| `classify <value>`              | Classify error type or fix action             |
| `episodes`                      | List recent episodes                          |

### query_temporal.py

| Command           | Description                              |
| ----------------- | ---------------------------------------- |
| `search <query>`  | Semantic search                          |
| `callers <name>`  | Who calls this?                          |
| `calls <name>`    | What does this call?                     |
| `changes <since>` | What changed? (e.g., `7d`, `2026-09-01`) |
| `impact <name>`   | Change impact analysis                   |
| `fix-rates`       | Fix success rates by error type          |

## Installation

```bash
# From project root
~/.config/harnesses/skills/code-index/scripts/install.sh .
cd .harness/code_index
python3 build_index_temporal.py
```

## Schema

**Core**: `entities`, `relations`, `fix_attempts`. **Flywheel**: `skills`, `skill_evidence`, `episodes`, `decisions`.
**Meta**: `error_classes`, `fix_classes`, `meta_knowledge`, `*_membership` tables.

## Hyperparameters

| Parameter              | Default | Meaning                                                      |
| ---------------------- | ------- | ------------------------------------------------------------ |
| `PRIOR_ALPHA`          | 1.0     | Beta prior α₀ (uniform)                                      |
| `PRIOR_BETA`           | 1.0     | Beta prior β₀ (uniform)                                      |
| `KAPPA`                | 10.0    | Concentration (how tightly skills cluster around class mean) |
| `TAU`                  | 0.7     | Promotion threshold (P(success) > τ)                         |
| `CONFIDENCE_THRESHOLD` | 0.9     | Require 90% confidence for promotion                         |
