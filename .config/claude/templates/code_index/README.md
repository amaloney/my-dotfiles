# Bi-Temporal Code Knowledge Graph + Probabilistic Flywheel

Code indexing with bi-temporal tracking, semantic search, and Bayesian skill learning.

## Quick Start

```bash
cd .claude/code_index

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

| File | Purpose |
|------|---------|
| `schema.sql` | SQLite schema (entities, relations, flywheel, meta-learning) |
| `build_index_temporal.py` | AST extraction with bi-temporal tracking |
| `query_temporal.py` | Semantic + relational + temporal queries |
| `flywheel.py` | Probabilistic skill learning with meta-knowledge |

## Probabilistic Flywheel

Skills are modeled as **Beta distributions** instead of integer scores:

```
Traditional: score = 8 (what does this mean?)
Bayesian:    θ ~ Beta(9, 2) → E[θ] = 0.82, σ = 0.11, P(effective) = 94%
```

### Generative Model

$$\alpha_{CF} \sim \text{Beta}(a_0, b_0) \quad \text{(class-level prior)}$$

$$\theta_{ef} \mid \alpha_{CF} \sim \text{Beta}(\alpha_{CF} \cdot \kappa, (1-\alpha_{CF}) \cdot \kappa) \quad \text{(skill prior)}$$

$$x_i \mid \theta_{ef} \sim \text{Bernoulli}(\theta_{ef}) \quad \text{(observations)}$$

### Key Equations

**Expected success rate:**

$$\mathbb{E}[\theta] = \frac{\alpha}{\alpha + \beta}$$

**Uncertainty:**

$$\sigma = \sqrt{\frac{\alpha \beta}{(\alpha + \beta)^2 (\alpha + \beta + 1)}}$$

**Probability effective:**

$$P(\theta > \tau) = 1 - I_\tau(\alpha, \beta)$$

**Posterior update:**

$$\alpha' = \alpha + x, \quad \beta' = \beta + (1 - x)$$

### Bayesian Promotion

$$\text{class} = \begin{cases}
\texttt{proven} & \text{if } P(\theta > 0.7) > 0.9 \\
\texttt{anti-pattern} & \text{if } \mathbb{E}[\theta] < 0.3 \land n \geq 5 \\
\texttt{correctable} & \text{if } n \geq 2 \\
\texttt{noise} & \text{otherwise}
\end{cases}$$

### Meta-Learning Transfer

For new $(e', f')$ with zero evidence, inherit from class:

$$\mathbb{E}[\theta_{e'f'}] = \mathbb{E}[\alpha_{CF}] = \frac{a_0 + s_{CF}}{a_0 + b_0 + n_{CF}}$$

```
New error: "numpy_abi_conflict" (never seen)
  → Classify: dependency class (C)
  → Inherit: θ ~ Beta(α_CF · κ, (1-α_CF) · κ)
  → Recommend: "constrain fixes work 82% ± 8%"
```

## CLI Reference

### flywheel.py

| Command | Description |
|---------|-------------|
| `status` | Show flywheel status with Bayesian metrics |
| `skills` | List skills (add `--bayesian` for α, β, μ, σ) |
| `skills --class proven` | Filter by class |
| `recommend <error_type>` | Get recommendations with confidence intervals |
| `meta` | Show class-level meta-knowledge |
| `meta --error-class dependency` | Filter meta-knowledge |
| `classify <value>` | Classify error type or fix action |
| `episodes` | List recent episodes |

### query_temporal.py

| Command | Description |
|---------|-------------|
| `search <query>` | Semantic search |
| `callers <name>` | Who calls this? |
| `calls <name>` | What does this call? |
| `changes <since>` | What changed? (e.g., `7d`, `2026-09-01`) |
| `impact <name>` | Change impact analysis |
| `fix-rates` | Fix success rates by error type |

## Installation

```bash
# From project root
mkdir -p .claude/code_index
cp ~/.config/claude/templates/code_index/* .claude/code_index/
cd .claude/code_index
python3 build_index_temporal.py
```

## Schema Overview

### Core Tables

- `entities` — Code entities (classes, methods, functions) with bi-temporal fields
- `relations` — Relationships (calls, inherits, imports, uses_type)
- `fix_attempts` — Fix attempt history for learning

### Flywheel Tables

- `skills` — Learned patterns with Beta(α, β) parameters
- `skill_evidence` — Links skills to fix attempts
- `episodes` — Task execution records
- `decisions` — Why we chose X over Y

### Meta-Learning Tables

- `error_classes` — Error type clusters (dependency, missing, build, test)
- `fix_classes` — Fix action clusters (constrain, add_requirement, modify_recipe)
- `meta_knowledge` — Class-level success rates Beta(α, β)
- `error_class_membership` — Maps error types to classes
- `fix_class_membership` — Maps fix actions to classes

## Hyperparameters

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `PRIOR_ALPHA` | 1.0 | Beta prior α₀ (uniform) |
| `PRIOR_BETA` | 1.0 | Beta prior β₀ (uniform) |
| `KAPPA` | 10.0 | Concentration (how tightly skills cluster around class mean) |
| `TAU` | 0.7 | Promotion threshold (P(success) > τ) |
| `CONFIDENCE_THRESHOLD` | 0.9 | Require 90% confidence for promotion |
