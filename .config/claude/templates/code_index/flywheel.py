#!/usr/bin/env python3
"""Code flywheel: skill learning, episodes, and decisions.

The flywheel accumulates project-specific knowledge from fix outcomes,
promoting patterns to skills and avoiding anti-patterns.

Probabilistic model:
- Skills modeled as Beta(α, β) distributions
- Meta-learning: class-level priors transfer to new skills
- Bayesian promotion: P(θ > τ) instead of hard score thresholds
"""

import json
import math
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple


# Score bounds (legacy)
MIN_SCORE = -20
MAX_SCORE = 20

# Promotion thresholds (legacy)
PROVEN_THRESHOLD = 10
ANTI_PATTERN_THRESHOLD = -5
CORRECTABLE_THRESHOLD = 2

# Probabilistic hyperparameters
PRIOR_ALPHA = 1.0      # Beta prior α₀ (uniform)
PRIOR_BETA = 1.0       # Beta prior β₀ (uniform)
KAPPA = 10.0           # Concentration: how tightly skills cluster around class mean
TAU = 0.7              # Promotion threshold: P(success) > τ
CONFIDENCE_THRESHOLD = 0.9  # Require 90% confidence for promotion


def beta_mean(alpha: float, beta: float) -> float:
    """E[θ] = α / (α + β)"""
    return alpha / (alpha + beta)


def beta_stddev(alpha: float, beta: float) -> float:
    """σ = sqrt(αβ / ((α+β)²(α+β+1)))"""
    total = alpha + beta
    return math.sqrt((alpha * beta) / (total * total * (total + 1)))


def beta_cdf_approx(x: float, alpha: float, beta: float) -> float:
    """Approximate CDF using normal approximation (valid for α,β > 5)."""
    if alpha + beta < 5:
        # Not enough data, return 0.5 (uncertain)
        return 0.5
    mean = beta_mean(alpha, beta)
    std = beta_stddev(alpha, beta)
    if std == 0:
        return 1.0 if mean > x else 0.0
    z = (x - mean) / std
    # Approximate standard normal CDF using error function
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def prob_above_threshold(alpha: float, beta: float, threshold: float = TAU) -> float:
    """P(θ > threshold) = 1 - CDF(threshold)"""
    return 1.0 - beta_cdf_approx(threshold, alpha, beta)


@dataclass
class Skill:
    """A learned pattern that works or doesn't."""
    id: int
    name: str
    description: Optional[str]
    error_type: Optional[str]
    score: int  # Legacy integer score
    skill_class: str  # noise, correctable, proven, anti-pattern
    evidence_count: int
    success_count: int
    failure_count: int
    created_at: str
    last_used_at: Optional[str]
    # Probabilistic fields
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def success_rate(self) -> float:
        """Legacy percentage success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return 100.0 * self.success_count / total

    @property
    def mean(self) -> float:
        """E[θ] - expected success probability."""
        return beta_mean(self.alpha, self.beta)

    @property
    def stddev(self) -> float:
        """Standard deviation of success probability."""
        return beta_stddev(self.alpha, self.beta)

    @property
    def confidence_interval(self) -> Tuple[float, float]:
        """95% credible interval (mean ± 1.96σ)."""
        margin = 1.96 * self.stddev
        return (max(0, self.mean - margin), min(1, self.mean + margin))

    @property
    def prob_effective(self) -> float:
        """P(θ > 0.7) - probability skill is effective."""
        return prob_above_threshold(self.alpha, self.beta, TAU)

    @property
    def bayesian_class(self) -> str:
        """Probabilistic skill class based on P(θ > τ)."""
        p_effective = self.prob_effective
        if p_effective > CONFIDENCE_THRESHOLD:
            return "proven"
        elif self.mean < 0.3 and self.evidence_count >= 5:
            return "anti-pattern"
        elif self.evidence_count >= 2:
            return "correctable"
        return "noise"


@dataclass
class MetaKnowledge:
    """Class-level success rate (hierarchical prior)."""
    error_class: str
    fix_class: str
    alpha: float
    beta: float
    observation_count: int

    @property
    def mean(self) -> float:
        return beta_mean(self.alpha, self.beta)

    @property
    def stddev(self) -> float:
        return beta_stddev(self.alpha, self.beta)


@dataclass
class Episode:
    """A record of what happened during a task."""
    id: int
    task_description: str
    packages: List[str]
    approach: Optional[str]
    outcome: Optional[str]
    lessons: List[str]
    skills_applied: List[int]
    skills_discovered: List[int]
    started_at: str
    completed_at: Optional[str]


@dataclass
class SkillRecommendation:
    """A skill recommendation for a task."""
    skill: Optional[Skill]
    confidence: str  # "high" (proven), "medium" (correctable), "low" (noise), "class-level"
    reason: str
    # Bayesian fields
    mean: float = 0.5
    stddev: float = 0.25
    prob_effective: float = 0.5
    source: str = "skill"  # "skill" or "meta" (class-level)


class Flywheel:
    """The learning flywheel for code knowledge.

    Probabilistic model:
    - Level 0: Hyperpriors (α₀, β₀, κ, τ)
    - Level 1: Meta-parameters α_CF (class-level success rates)
    - Level 2: Skill parameters θ_ef ~ Beta(α, β)
    - Level 3: Observations x_i ∈ {0, 1}
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        # Cache for class patterns
        self._error_class_patterns: Optional[Dict[str, re.Pattern]] = None
        self._fix_class_patterns: Optional[Dict[str, re.Pattern]] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # Ensure flywheel tables exist
            self._ensure_tables()
        return self.conn

    def _ensure_tables(self):
        """Create flywheel tables if they don't exist."""
        schema_path = self.db_path.parent / "schema.sql"
        if schema_path.exists():
            # Extract just the flywheel portion and execute
            self.conn.executescript(schema_path.read_text())
            self.conn.commit()

        # Migrate existing skills to Bayesian parameters if needed
        self._migrate_to_bayesian()

    def _migrate_to_bayesian(self):
        """Add alpha/beta columns and migrate existing data."""
        # Check if alpha column exists
        columns = [row[1] for row in self.conn.execute("PRAGMA table_info(skills)").fetchall()]
        if "alpha" not in columns:
            try:
                self.conn.execute("ALTER TABLE skills ADD COLUMN alpha REAL DEFAULT 1.0")
                self.conn.execute("ALTER TABLE skills ADD COLUMN beta REAL DEFAULT 1.0")
                # Migrate existing skills: α = 1 + successes, β = 1 + failures
                self.conn.execute("""
                    UPDATE skills SET
                        alpha = 1.0 + success_count,
                        beta = 1.0 + failure_count
                """)
                self.conn.commit()
            except sqlite3.Error:
                pass  # Column might already exist

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # ═══════════════════════════════════════════════════════════════
    # CLASSIFICATION (Meta-Learning)
    # ═══════════════════════════════════════════════════════════════

    def _load_class_patterns(self) -> None:
        """Load regex patterns for error/fix classification."""
        conn = self._get_conn()

        self._error_class_patterns = {}
        for row in conn.execute("SELECT name, pattern FROM error_classes WHERE pattern IS NOT NULL"):
            try:
                self._error_class_patterns[row["name"]] = re.compile(row["pattern"], re.IGNORECASE)
            except re.error:
                pass

        self._fix_class_patterns = {}
        for row in conn.execute("SELECT name, pattern FROM fix_classes WHERE pattern IS NOT NULL"):
            try:
                self._fix_class_patterns[row["name"]] = re.compile(row["pattern"], re.IGNORECASE)
            except re.error:
                pass

    def classify_error(self, error_type: str) -> Optional[str]:
        """Map error type to error class using patterns."""
        conn = self._get_conn()

        # Check cached membership first
        row = conn.execute(
            "SELECT ec.name FROM error_class_membership ecm "
            "JOIN error_classes ec ON ecm.error_class_id = ec.id "
            "WHERE ecm.error_type = ?",
            (error_type,)
        ).fetchone()
        if row:
            return row["name"]

        # Load patterns if needed
        if self._error_class_patterns is None:
            self._load_class_patterns()

        # Match against patterns
        for class_name, pattern in self._error_class_patterns.items():
            if pattern.search(error_type):
                # Cache the mapping
                self._cache_error_class(error_type, class_name)
                return class_name

        return None

    def classify_fix(self, fix_action: str) -> Optional[str]:
        """Map fix action to fix class using patterns."""
        conn = self._get_conn()

        # Check cached membership first
        row = conn.execute(
            "SELECT fc.name FROM fix_class_membership fcm "
            "JOIN fix_classes fc ON fcm.fix_class_id = fc.id "
            "WHERE fcm.fix_action = ?",
            (fix_action,)
        ).fetchone()
        if row:
            return row["name"]

        # Load patterns if needed
        if self._fix_class_patterns is None:
            self._load_class_patterns()

        # Match against patterns
        for class_name, pattern in self._fix_class_patterns.items():
            if pattern.search(fix_action):
                # Cache the mapping
                self._cache_fix_class(fix_action, class_name)
                return class_name

        return None

    def _cache_error_class(self, error_type: str, class_name: str) -> None:
        """Cache error type to class mapping."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR IGNORE INTO error_class_membership (error_type, error_class_id, assigned_at)
                SELECT ?, id, ? FROM error_classes WHERE name = ?
            """, (error_type, datetime.now().isoformat(), class_name))
            conn.commit()
        except sqlite3.Error:
            pass

    def _cache_fix_class(self, fix_action: str, class_name: str) -> None:
        """Cache fix action to class mapping."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR IGNORE INTO fix_class_membership (fix_action, fix_class_id, assigned_at)
                SELECT ?, id, ? FROM fix_classes WHERE name = ?
            """, (fix_action, datetime.now().isoformat(), class_name))
            conn.commit()
        except sqlite3.Error:
            pass

    def get_meta_knowledge(self, error_class: str, fix_class: str) -> Optional[MetaKnowledge]:
        """Get class-level prior for (error_class, fix_class)."""
        conn = self._get_conn()
        row = conn.execute("""
            SELECT ec.name as error_class, fc.name as fix_class,
                   mk.alpha, mk.beta, mk.observation_count
            FROM meta_knowledge mk
            JOIN error_classes ec ON mk.error_class_id = ec.id
            JOIN fix_classes fc ON mk.fix_class_id = fc.id
            WHERE ec.name = ? AND fc.name = ?
        """, (error_class, fix_class)).fetchone()

        if row:
            return MetaKnowledge(
                error_class=row["error_class"],
                fix_class=row["fix_class"],
                alpha=row["alpha"],
                beta=row["beta"],
                observation_count=row["observation_count"]
            )
        return None

    def update_meta_knowledge(self, error_class: str, fix_class: str, success: bool) -> None:
        """Update class-level prior after observing outcome."""
        conn = self._get_conn()

        # Ensure meta_knowledge row exists
        conn.execute("""
            INSERT OR IGNORE INTO meta_knowledge (error_class_id, fix_class_id, created_at)
            SELECT ec.id, fc.id, ?
            FROM error_classes ec, fix_classes fc
            WHERE ec.name = ? AND fc.name = ?
        """, (datetime.now().isoformat(), error_class, fix_class))

        # Update counts
        if success:
            conn.execute("""
                UPDATE meta_knowledge SET
                    alpha = alpha + 1,
                    observation_count = observation_count + 1,
                    updated_at = ?
                WHERE error_class_id = (SELECT id FROM error_classes WHERE name = ?)
                  AND fix_class_id = (SELECT id FROM fix_classes WHERE name = ?)
            """, (datetime.now().isoformat(), error_class, fix_class))
        else:
            conn.execute("""
                UPDATE meta_knowledge SET
                    beta = beta + 1,
                    observation_count = observation_count + 1,
                    updated_at = ?
                WHERE error_class_id = (SELECT id FROM error_classes WHERE name = ?)
                  AND fix_class_id = (SELECT id FROM fix_classes WHERE name = ?)
            """, (datetime.now().isoformat(), error_class, fix_class))

        conn.commit()

    def get_inherited_prior(self, error_type: str, fix_action: str) -> Tuple[float, float]:
        """Get prior (α, β) for a new skill from class-level meta-knowledge."""
        error_class = self.classify_error(error_type)
        fix_class = self.classify_fix(fix_action)

        if error_class and fix_class:
            meta = self.get_meta_knowledge(error_class, fix_class)
            if meta and meta.observation_count > 0:
                # Inherit from class: α = class_mean * κ, β = (1 - class_mean) * κ
                class_mean = meta.mean
                return (class_mean * KAPPA, (1 - class_mean) * KAPPA)

        # Fall back to uniform prior
        return (PRIOR_ALPHA, PRIOR_BETA)

    # ═══════════════════════════════════════════════════════════════
    # SKILL MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    def get_or_create_skill(self, name: str, error_type: Optional[str] = None,
                           description: Optional[str] = None) -> int:
        """Get existing skill or create new one.

        New skills inherit prior from class-level meta-knowledge.
        """
        conn = self._get_conn()

        # Check if exists
        row = conn.execute(
            "SELECT id FROM skills WHERE name = ?", (name,)
        ).fetchone()

        if row:
            return row[0]

        # Get inherited prior from meta-knowledge
        fix_action = name.split("-for-")[0] if "-for-" in name else name
        prior_alpha, prior_beta = self.get_inherited_prior(
            error_type or "",
            fix_action
        )

        # Create new skill with inherited prior
        cursor = conn.execute("""
            INSERT INTO skills (name, error_type, description, alpha, beta, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, error_type, description, prior_alpha, prior_beta, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

    def record_skill_evidence(self, skill_id: int, fix_attempt_id: int,
                             outcome: str) -> None:
        """Record evidence for a skill from a fix attempt.

        Updates both legacy score and Bayesian (α, β) parameters.
        Also updates class-level meta-knowledge.
        """
        conn = self._get_conn()

        # Determine score delta based on outcome
        if outcome == "success":
            score_delta = 2
            success = True
        elif outcome == "failed":
            score_delta = -2
            success = False
        else:  # partial
            score_delta = 0
            success = None

        # Record evidence
        try:
            conn.execute("""
                INSERT INTO skill_evidence (skill_id, fix_attempt_id, outcome, score_delta, recorded_at)
                VALUES (?, ?, ?, ?, ?)
            """, (skill_id, fix_attempt_id, outcome, score_delta, datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            return  # Already recorded

        # Update skill: legacy score + Bayesian parameters
        if success is True:
            conn.execute("""
                UPDATE skills SET
                    score = MAX(?, MIN(?, score + ?)),
                    alpha = alpha + 1,
                    evidence_count = evidence_count + 1,
                    success_count = success_count + 1,
                    last_used_at = ?
                WHERE id = ?
            """, (MIN_SCORE, MAX_SCORE, score_delta, datetime.now().isoformat(), skill_id))
        elif success is False:
            conn.execute("""
                UPDATE skills SET
                    score = MAX(?, MIN(?, score + ?)),
                    beta = beta + 1,
                    evidence_count = evidence_count + 1,
                    failure_count = failure_count + 1,
                    last_used_at = ?
                WHERE id = ?
            """, (MIN_SCORE, MAX_SCORE, score_delta, datetime.now().isoformat(), skill_id))
        else:
            conn.execute("""
                UPDATE skills SET
                    evidence_count = evidence_count + 1,
                    last_used_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), skill_id))

        conn.commit()

        # Update class-level meta-knowledge
        if success is not None:
            skill = self.get_skill(skill_id)
            if skill and skill.error_type:
                error_class = self.classify_error(skill.error_type)
                # Extract fix action from skill name (e.g., "pin-version-for-missing-module" -> "pin-version")
                fix_action = skill.name.split("-for-")[0] if "-for-" in skill.name else skill.name
                fix_class = self.classify_fix(fix_action)

                if error_class and fix_class:
                    self.update_meta_knowledge(error_class, fix_class, success)

        # Check for class transitions (legacy + Bayesian)
        self._update_skill_class(skill_id)

    def _update_skill_class(self, skill_id: int) -> None:
        """Update skill class based on current score."""
        conn = self._get_conn()
        skill = conn.execute(
            "SELECT score, class, evidence_count FROM skills WHERE id = ?",
            (skill_id,)
        ).fetchone()

        if not skill:
            return

        score, current_class, evidence = skill["score"], skill["class"], skill["evidence_count"]
        new_class = current_class

        # Determine new class
        if score >= PROVEN_THRESHOLD and evidence >= 3:
            new_class = "proven"
        elif score <= ANTI_PATTERN_THRESHOLD:
            new_class = "anti-pattern"
        elif score >= CORRECTABLE_THRESHOLD:
            new_class = "correctable"
        elif current_class not in ("proven", "anti-pattern"):
            new_class = "noise"

        # Update if changed
        if new_class != current_class:
            conn.execute("""
                UPDATE skills SET class = ?, promoted_at = ?
                WHERE id = ?
            """, (new_class, datetime.now().isoformat(), skill_id))
            conn.commit()

    def get_skill(self, skill_id: int) -> Optional[Skill]:
        """Get a skill by ID."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
        if row:
            return self._row_to_skill(row)
        return None

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM skills WHERE name = ?", (name,)).fetchone()
        if row:
            return self._row_to_skill(row)
        return None

    def _row_to_skill(self, row: sqlite3.Row) -> Skill:
        return Skill(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            error_type=row["error_type"],
            score=row["score"],
            skill_class=row["class"],
            evidence_count=row["evidence_count"],
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            alpha=row["alpha"] if "alpha" in row.keys() else 1.0,
            beta=row["beta"] if "beta" in row.keys() else 1.0,
        )

    # ═══════════════════════════════════════════════════════════════
    # SKILL QUERIES
    # ═══════════════════════════════════════════════════════════════

    def get_proven_skills(self, error_type: Optional[str] = None) -> List[Skill]:
        """Get proven skills, optionally filtered by error type."""
        conn = self._get_conn()
        if error_type:
            rows = conn.execute("""
                SELECT * FROM skills
                WHERE class = 'proven' AND (error_type = ? OR error_type IS NULL)
                ORDER BY score DESC
            """, (error_type,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM proven_skills"
            ).fetchall()
        return [self._row_to_skill(row) for row in rows]

    def get_anti_patterns(self, error_type: Optional[str] = None) -> List[Skill]:
        """Get anti-patterns to avoid."""
        conn = self._get_conn()
        if error_type:
            rows = conn.execute("""
                SELECT * FROM skills
                WHERE class = 'anti-pattern' AND (error_type = ? OR error_type IS NULL)
                ORDER BY score ASC
            """, (error_type,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM anti_patterns"
            ).fetchall()
        return [self._row_to_skill(row) for row in rows]

    def get_recommendations(self, error_type: str) -> List[SkillRecommendation]:
        """Get skill recommendations for an error type (legacy + Bayesian)."""
        recommendations = []

        # Get proven skills (high confidence) - now using Bayesian criteria
        for skill in self.get_proven_skills(error_type):
            ci_low, ci_high = skill.confidence_interval
            recommendations.append(SkillRecommendation(
                skill=skill,
                confidence="high",
                reason=f"Proven: {skill.mean:.0%} ± {skill.stddev:.0%} (P(effective)={skill.prob_effective:.0%})",
                mean=skill.mean,
                stddev=skill.stddev,
                prob_effective=skill.prob_effective,
                source="skill"
            ))

        # Get correctable skills (medium confidence)
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM skills
            WHERE class = 'correctable' AND (error_type = ? OR error_type IS NULL)
            ORDER BY alpha / (alpha + beta) DESC LIMIT 3
        """, (error_type,)).fetchall()

        for row in rows:
            skill = self._row_to_skill(row)
            recommendations.append(SkillRecommendation(
                skill=skill,
                confidence="medium",
                reason=f"Promising: {skill.mean:.0%} ± {skill.stddev:.0%} ({skill.evidence_count} observations)",
                mean=skill.mean,
                stddev=skill.stddev,
                prob_effective=skill.prob_effective,
                source="skill"
            ))

        # If no skill-level recommendations, try meta-knowledge
        if not recommendations:
            meta_recs = self.get_meta_recommendations(error_type)
            recommendations.extend(meta_recs)

        return recommendations

    def get_meta_recommendations(self, error_type: str) -> List[SkillRecommendation]:
        """Get recommendations from class-level meta-knowledge (for new error types)."""
        recommendations = []
        error_class = self.classify_error(error_type)

        if not error_class:
            return recommendations

        conn = self._get_conn()
        rows = conn.execute("""
            SELECT fc.name as fix_class, mk.alpha, mk.beta, mk.observation_count
            FROM meta_knowledge mk
            JOIN error_classes ec ON mk.error_class_id = ec.id
            JOIN fix_classes fc ON mk.fix_class_id = fc.id
            WHERE ec.name = ? AND mk.observation_count > 0
            ORDER BY mk.alpha / (mk.alpha + mk.beta) DESC
            LIMIT 3
        """, (error_class,)).fetchall()

        for row in rows:
            meta = MetaKnowledge(
                error_class=error_class,
                fix_class=row["fix_class"],
                alpha=row["alpha"],
                beta=row["beta"],
                observation_count=row["observation_count"]
            )
            recommendations.append(SkillRecommendation(
                skill=None,
                confidence="class-level",
                reason=f"Meta: {meta.fix_class} fixes work {meta.mean:.0%} ± {meta.stddev:.0%} for {error_class} errors ({meta.observation_count} obs)",
                mean=meta.mean,
                stddev=meta.stddev,
                prob_effective=prob_above_threshold(meta.alpha, meta.beta, TAU),
                source="meta"
            ))

        return recommendations

    def get_warnings(self, error_type: str, proposed_action: str) -> List[str]:
        """Get warnings if proposed action matches an anti-pattern."""
        warnings = []

        # Check if action matches any anti-pattern
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM skills
            WHERE class = 'anti-pattern'
              AND (error_type = ? OR error_type IS NULL)
              AND name LIKE ?
        """, (error_type, f"%{proposed_action}%")).fetchall()

        for row in rows:
            skill = self._row_to_skill(row)
            warnings.append(
                f"WARNING: '{skill.name}' is an anti-pattern (score {skill.score}, "
                f"failed {skill.failure_count}x). Consider alternative approach."
            )

        return warnings

    # ═══════════════════════════════════════════════════════════════
    # EPISODE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    def start_episode(self, task_description: str, packages: List[str] = None,
                     session_id: Optional[str] = None) -> int:
        """Start a new episode."""
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO episodes (task_description, packages, session_id, started_at)
            VALUES (?, ?, ?, ?)
        """, (
            task_description,
            json.dumps(packages or []),
            session_id,
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid

    def complete_episode(self, episode_id: int, outcome: str,
                        approach: Optional[str] = None,
                        lessons: List[str] = None,
                        skills_applied: List[int] = None,
                        skills_discovered: List[int] = None,
                        fix_attempts: List[int] = None) -> None:
        """Complete an episode with outcome."""
        conn = self._get_conn()
        started = conn.execute(
            "SELECT started_at FROM episodes WHERE id = ?", (episode_id,)
        ).fetchone()

        duration = None
        if started:
            start_time = datetime.fromisoformat(started["started_at"])
            duration = (datetime.now() - start_time).total_seconds()

        conn.execute("""
            UPDATE episodes SET
                outcome = ?,
                approach = ?,
                lessons = ?,
                skills_applied = ?,
                skills_discovered = ?,
                fix_attempts = ?,
                completed_at = ?,
                duration_seconds = ?
            WHERE id = ?
        """, (
            outcome,
            approach,
            json.dumps(lessons or []),
            json.dumps(skills_applied or []),
            json.dumps(skills_discovered or []),
            json.dumps(fix_attempts or []),
            datetime.now().isoformat(),
            duration,
            episode_id
        ))
        conn.commit()

    def get_similar_episodes(self, task_description: str, limit: int = 5) -> List[Episode]:
        """Find similar past episodes (simple keyword matching)."""
        conn = self._get_conn()
        # Simple word-based matching
        words = task_description.lower().split()[:5]  # First 5 words
        conditions = " OR ".join(["task_description LIKE ?" for _ in words])
        params = [f"%{w}%" for w in words]

        rows = conn.execute(f"""
            SELECT * FROM episodes
            WHERE outcome IS NOT NULL AND ({conditions})
            ORDER BY completed_at DESC
            LIMIT ?
        """, params + [limit]).fetchall()

        return [self._row_to_episode(row) for row in rows]

    def _row_to_episode(self, row: sqlite3.Row) -> Episode:
        return Episode(
            id=row["id"],
            task_description=row["task_description"],
            packages=json.loads(row["packages"] or "[]"),
            approach=row["approach"],
            outcome=row["outcome"],
            lessons=json.loads(row["lessons"] or "[]"),
            skills_applied=json.loads(row["skills_applied"] or "[]"),
            skills_discovered=json.loads(row["skills_discovered"] or "[]"),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    # ═══════════════════════════════════════════════════════════════
    # DECISION TRACKING
    # ═══════════════════════════════════════════════════════════════

    def record_decision(self, question: str, choice: str,
                       rationale: Optional[str] = None,
                       alternatives: List[str] = None,
                       episode_id: Optional[int] = None,
                       error_type: Optional[str] = None,
                       package: Optional[str] = None) -> int:
        """Record a decision for future reference."""
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO decisions
            (question, choice, alternatives, rationale, episode_id, error_type, package, made_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question, choice,
            json.dumps(alternatives or []),
            rationale, episode_id, error_type, package,
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid

    def validate_decision(self, decision_id: int, outcome: str, notes: Optional[str] = None) -> None:
        """Update decision outcome after validation."""
        conn = self._get_conn()
        conn.execute("""
            UPDATE decisions SET outcome = ?, outcome_notes = ?, validated_at = ?
            WHERE id = ?
        """, (outcome, notes, datetime.now().isoformat(), decision_id))
        conn.commit()

    def get_similar_decisions(self, error_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar past decisions."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM decisions
            WHERE error_type = ? AND outcome = 'validated'
            ORDER BY validated_at DESC
            LIMIT ?
        """, (error_type, limit)).fetchall()
        return [dict(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════
    # FLYWHEEL LEARNING
    # ═══════════════════════════════════════════════════════════════

    def learn_from_fix_attempt(self, fix_attempt_id: int, error_type: str,
                               fix_action: str, outcome: str,
                               package: Optional[str] = None) -> Optional[int]:
        """Learn from a fix attempt, potentially creating or updating a skill."""
        # Generate skill name from error type and action
        skill_name = f"{fix_action}-for-{error_type}".lower().replace("_", "-")

        # Get or create skill
        skill_id = self.get_or_create_skill(
            name=skill_name,
            error_type=error_type,
            description=f"Use {fix_action} to fix {error_type} errors"
        )

        # Record evidence
        self.record_skill_evidence(skill_id, fix_attempt_id, outcome)

        return skill_id

    def get_flywheel_status(self) -> Dict[str, Any]:
        """Get current flywheel status with Bayesian metrics."""
        conn = self._get_conn()

        skills_by_class = {}
        for row in conn.execute("""
            SELECT class, COUNT(*) as count, AVG(score) as avg_score,
                   AVG(alpha / (alpha + beta)) as avg_mean
            FROM skills GROUP BY class
        """).fetchall():
            skills_by_class[row["class"]] = {
                "count": row["count"],
                "avg_score": round(row["avg_score"] or 0, 1),
                "avg_mean": round(row["avg_mean"] or 0.5, 3)
            }

        episodes = conn.execute("""
            SELECT outcome, COUNT(*) as count FROM episodes
            WHERE outcome IS NOT NULL GROUP BY outcome
        """).fetchall()

        total_episodes = sum(row["count"] for row in episodes)
        success_episodes = next(
            (row["count"] for row in episodes if row["outcome"] == "success"), 0
        )

        # Meta-knowledge stats
        meta_stats = conn.execute("""
            SELECT COUNT(*) as pairs,
                   SUM(observation_count) as total_obs,
                   AVG(alpha / (alpha + beta)) as avg_class_mean
            FROM meta_knowledge
            WHERE observation_count > 0
        """).fetchone()

        return {
            "skills": {
                "total": sum(c["count"] for c in skills_by_class.values()),
                "by_class": skills_by_class,
            },
            "episodes": {
                "total": total_episodes,
                "success_rate": round(100.0 * success_episodes / total_episodes, 1) if total_episodes > 0 else 0,
            },
            "meta_knowledge": {
                "class_pairs": meta_stats["pairs"] or 0,
                "total_observations": meta_stats["total_obs"] or 0,
                "avg_class_success_rate": round(meta_stats["avg_class_mean"] or 0.5, 3)
            },
            "promotion_candidates": conn.execute(
                "SELECT COUNT(*) FROM promotion_candidates"
            ).fetchone()[0],
            "hyperparameters": {
                "prior_alpha": PRIOR_ALPHA,
                "prior_beta": PRIOR_BETA,
                "kappa": KAPPA,
                "tau": TAU,
                "confidence_threshold": CONFIDENCE_THRESHOLD
            }
        }


def main():
    """CLI for flywheel operations."""
    import argparse

    parser = argparse.ArgumentParser(prog="flywheel", description="Code flywheel operations (probabilistic)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Status
    subparsers.add_parser("status", help="Show flywheel status with Bayesian metrics")

    # Skills
    p = subparsers.add_parser("skills", help="List skills with Bayesian stats")
    p.add_argument("--class", dest="skill_class", choices=["proven", "correctable", "anti-pattern", "noise"])
    p.add_argument("--error-type", help="Filter by error type")
    p.add_argument("--bayesian", action="store_true", help="Show Bayesian stats (α, β, μ, σ)")

    # Recommend
    p = subparsers.add_parser("recommend", help="Get recommendations for error type")
    p.add_argument("error_type", help="Error type")

    # Meta-knowledge
    p = subparsers.add_parser("meta", help="Show meta-knowledge (class-level priors)")
    p.add_argument("--error-class", help="Filter by error class")

    # Classify
    p = subparsers.add_parser("classify", help="Classify an error type or fix action")
    p.add_argument("value", help="Error type or fix action to classify")
    p.add_argument("--type", choices=["error", "fix"], default="error")

    # Episodes
    p = subparsers.add_parser("episodes", help="List recent episodes")
    p.add_argument("-n", "--limit", type=int, default=10)

    args = parser.parse_args()

    db_path = Path(__file__).parent / "code_graph.db"
    flywheel = Flywheel(db_path)

    try:
        if args.command == "status":
            status = flywheel.get_flywheel_status()
            print(json.dumps(status, indent=2))

        elif args.command == "skills":
            conn = flywheel._get_conn()
            query = "SELECT * FROM skills"
            params = []

            if args.skill_class:
                query += " WHERE class = ?"
                params.append(args.skill_class)
            if args.error_type:
                if params:
                    query += " AND error_type = ?"
                else:
                    query += " WHERE error_type = ?"
                params.append(args.error_type)

            query += " ORDER BY alpha / (alpha + beta) DESC"

            for row in conn.execute(query, params).fetchall():
                skill = flywheel._row_to_skill(row)
                if args.bayesian:
                    print(f"[{skill.bayesian_class:12}] {skill.name}")
                    print(f"    α={skill.alpha:.1f} β={skill.beta:.1f} | "
                          f"μ={skill.mean:.2f} σ={skill.stddev:.2f} | "
                          f"P(eff)={skill.prob_effective:.0%} | n={skill.evidence_count}")
                else:
                    print(f"[{skill.skill_class:12}] {skill.name} "
                          f"(μ={skill.mean:.0%} ± {skill.stddev:.0%}, "
                          f"P(eff)={skill.prob_effective:.0%}, n={skill.evidence_count})")

        elif args.command == "recommend":
            recs = flywheel.get_recommendations(args.error_type)
            if not recs:
                print(f"No recommendations for '{args.error_type}'")
            else:
                for rec in recs:
                    name = rec.skill.name if rec.skill else f"[{rec.source}]"
                    print(f"[{rec.confidence:11}] {name}")
                    print(f"              μ={rec.mean:.0%} ± {rec.stddev:.0%}, P(eff)={rec.prob_effective:.0%}")
                    print(f"              {rec.reason}")

            warnings = flywheel.get_warnings(args.error_type, "")
            for w in warnings:
                print(f"\n{w}")

        elif args.command == "meta":
            conn = flywheel._get_conn()
            query = """
                SELECT ec.name as error_class, fc.name as fix_class,
                       mk.alpha, mk.beta, mk.observation_count
                FROM meta_knowledge mk
                JOIN error_classes ec ON mk.error_class_id = ec.id
                JOIN fix_classes fc ON mk.fix_class_id = fc.id
                WHERE mk.observation_count > 0
            """
            params = []
            if args.error_class:
                query += " AND ec.name = ?"
                params.append(args.error_class)
            query += " ORDER BY mk.alpha / (mk.alpha + mk.beta) DESC"

            print(f"{'Error Class':<15} {'Fix Class':<20} {'α':>6} {'β':>6} {'Mean':>7} {'StdDev':>7} {'N':>4}")
            print("-" * 75)
            for row in conn.execute(query, params).fetchall():
                meta = MetaKnowledge(
                    error_class=row["error_class"],
                    fix_class=row["fix_class"],
                    alpha=row["alpha"],
                    beta=row["beta"],
                    observation_count=row["observation_count"]
                )
                print(f"{meta.error_class:<15} {meta.fix_class:<20} "
                      f"{meta.alpha:>6.1f} {meta.beta:>6.1f} "
                      f"{meta.mean:>6.1%} {meta.stddev:>6.1%} "
                      f"{meta.observation_count:>4}")

        elif args.command == "classify":
            if args.type == "error":
                result = flywheel.classify_error(args.value)
                print(f"Error '{args.value}' → class '{result or 'unknown'}'")
            else:
                result = flywheel.classify_fix(args.value)
                print(f"Fix '{args.value}' → class '{result or 'unknown'}'")

        elif args.command == "episodes":
            conn = flywheel._get_conn()
            for row in conn.execute("""
                SELECT * FROM episodes
                WHERE outcome IS NOT NULL
                ORDER BY completed_at DESC
                LIMIT ?
            """, (args.limit,)).fetchall():
                ep = flywheel._row_to_episode(row)
                print(f"[{ep.outcome:8}] {ep.task_description[:60]}")
                if ep.lessons:
                    for lesson in ep.lessons[:2]:
                        print(f"           └─ {lesson}")

    finally:
        flywheel.close()


if __name__ == "__main__":
    main()