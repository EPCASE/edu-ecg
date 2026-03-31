#!/usr/bin/env python3
"""
Brique 5 - Scoring V2 Composite
=================================
Scoring composite exploitant l'expansion semantique de la Brique 4.5.

Score par pattern = base (50) + requires (30) + qualifiers (10) + supports (5)
                  - exclusion (= 0)

Auteur : BMad Team
Date   : 2026-03-31
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from semantic_layer import (
    SemanticResult,
    PatternExpansion,
    ImplicitPattern,
    expand_found_concepts,
    get_concept,
    is_hidden,
    load_ontology_v2,
    normalize_key,
    _get_ontology_v2,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring weights (from ontology_v2.json scoring_rules)
# ---------------------------------------------------------------------------

PATTERN_BASE_SCORE = 50
REQUIRES_WEIGHT = 30
QUALIFIER_WEIGHT = 10
SUPPORTS_WEIGHT = 5

CATEGORIE_MULTIPLIER = {
    "DIAGNOSTIC_URGENT": 5,
    "DIAGNOSTIC_MAJEUR": 4,
    "DIAGNOSTIC_MOYEN": 3,
    "DESCRIPTION_ECG": 2,
    "QUALIFICATEUR": 1,
    "TOPOGRAPHIE": 1,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PatternScore:
    """Score detaille d'un pattern."""
    pattern_id: str
    concept_name: str = ""
    categorie: str = ""
    poids: int = 2

    base_score: float = 0.0
    requires_score: float = 0.0
    qualifier_score: float = 0.0
    supports_score: float = 0.0
    exclusion_penalty: bool = False

    raw_score: float = 0.0
    weighted_score: float = 0.0

    requires_ratio: float = 0.0
    requires_satisfied: List[str] = field(default_factory=list)
    requires_missing: List[str] = field(default_factory=list)
    qualifiers_found: List[str] = field(default_factory=list)
    supports_found: List[str] = field(default_factory=list)
    is_implicit: bool = False
    directly_found: bool = False

    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "concept_name": self.concept_name,
            "categorie": self.categorie,
            "poids": self.poids,
            "base_score": self.base_score,
            "requires_score": round(self.requires_score, 1),
            "qualifier_score": self.qualifier_score,
            "supports_score": self.supports_score,
            "exclusion_penalty": self.exclusion_penalty,
            "raw_score": round(self.raw_score, 1),
            "weighted_score": round(self.weighted_score, 1),
            "requires_ratio": round(self.requires_ratio, 3),
            "requires_satisfied": self.requires_satisfied,
            "requires_missing": self.requires_missing,
            "qualifiers_found": self.qualifiers_found,
            "supports_found": self.supports_found,
            "is_implicit": self.is_implicit,
            "directly_found": self.directly_found,
        }


@dataclass
class ScoringResult:
    """Resultat complet du scoring V2."""
    pattern_scores: List[PatternScore] = field(default_factory=list)
    finding_scores: List[Dict] = field(default_factory=list)
    total_score: float = 0.0
    max_possible_score: float = 0.0
    score_ratio: float = 0.0
    semantic_result: Optional[SemanticResult] = None

    def to_dict(self) -> Dict:
        return {
            "pattern_scores": [ps.to_dict() for ps in self.pattern_scores],
            "finding_scores": self.finding_scores,
            "total_score": round(self.total_score, 1),
            "max_possible_score": round(self.max_possible_score, 1),
            "score_ratio": round(self.score_ratio, 3),
            "summary": {
                "patterns_found": sum(1 for ps in self.pattern_scores if ps.directly_found),
                "patterns_implicit": sum(1 for ps in self.pattern_scores if ps.is_implicit),
                "patterns_excluded": sum(1 for ps in self.pattern_scores if ps.exclusion_penalty),
                "findings_matched": len(self.finding_scores),
            },
        }


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def score_pattern(expansion: PatternExpansion, is_implicit: bool = False) -> PatternScore:
    """
    Score composite d'un pattern.
    Score = base (50 si trouve) + requires (30 * ratio) + qualifiers (10 * n, cap 30)
          + supports (5 * n, cap 15) - exclusion (= 0)
    """
    c = get_concept(expansion.pattern_id)
    ps = PatternScore(pattern_id=expansion.pattern_id)

    if c:
        ps.concept_name = c.get("concept_name", expansion.pattern_id)
        ps.categorie = c.get("categorie", "DESCRIPTION_ECG")
        ps.poids = c.get("poids", 2)

    ps.is_implicit = is_implicit
    ps.directly_found = expansion.directly_found

    if expansion.is_excluded:
        ps.exclusion_penalty = True
        ps.raw_score = 0.0
        ps.weighted_score = 0.0
        return ps

    if expansion.directly_found:
        ps.base_score = PATTERN_BASE_SCORE

    ps.requires_ratio = expansion.requires_ratio
    ps.requires_satisfied = expansion.requires_satisfied
    ps.requires_missing = expansion.requires_missing
    ps.requires_score = REQUIRES_WEIGHT * expansion.requires_ratio

    ps.qualifiers_found = expansion.qualifiers_found
    ps.qualifier_score = min(QUALIFIER_WEIGHT * len(expansion.qualifiers_found), 30)

    ps.supports_found = expansion.supports_found
    ps.supports_score = min(SUPPORTS_WEIGHT * len(expansion.supports_found), 15)

    ps.raw_score = ps.base_score + ps.requires_score + ps.qualifier_score + ps.supports_score

    multiplier = CATEGORIE_MULTIPLIER.get(ps.categorie, 2)
    ps.weighted_score = ps.raw_score * (multiplier / 4.0)

    return ps


def score_finding(concept_id: str) -> Dict:
    """Score simple pour un finding orphelin."""
    c = get_concept(concept_id)
    if not c:
        return {"concept_id": concept_id, "score": 1, "poids": 1}
    poids = c.get("poids", 2)
    return {
        "concept_id": concept_id,
        "concept_name": c.get("concept_name", concept_id),
        "categorie": c.get("categorie", "DESCRIPTION_ECG"),
        "poids": poids,
        "score": poids,
    }


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_student_response_v2(
    found_ids: List[str],
    expected_ids: Optional[List[str]] = None,
) -> ScoringResult:
    """
    Point d'entree principal du scoring V2.

    1. Appelle la Brique 4.5 (expansion semantique)
    2. Score chaque pattern (explicite ou implicite)
    3. Score les findings orphelins
    4. Calcule le score total
    """
    sem = expand_found_concepts(found_ids)
    result = ScoringResult()
    result.semantic_result = sem

    # Score explicit patterns
    for pid, expansion in sem.expanded_patterns.items():
        ps = score_pattern(expansion, is_implicit=False)
        result.pattern_scores.append(ps)

    # Score implicit patterns
    for pid, imp in sem.implicit_patterns.items():
        fake_exp = PatternExpansion(
            pattern_id=imp.pattern_id,
            requires=imp.requires,
            requires_satisfied=imp.requires_satisfied,
            requires_missing=[r for r in imp.requires if r not in imp.requires_satisfied],
            requires_ratio=imp.requires_ratio,
            supports_found=imp.supports_found,
            directly_found=False,
        )
        ps = score_pattern(fake_exp, is_implicit=True)
        result.pattern_scores.append(ps)

    # Score orphan findings
    used_in_patterns = set()
    for exp in sem.expanded_patterns.values():
        used_in_patterns.update(exp.requires_satisfied)
        used_in_patterns.update(exp.supports_found)
    for imp in sem.implicit_patterns.values():
        used_in_patterns.update(imp.requires_satisfied)
        used_in_patterns.update(imp.supports_found)

    orphan_findings = [f for f in sem.findings if f not in used_in_patterns]
    for fid in orphan_findings:
        result.finding_scores.append(score_finding(fid))

    # Sort by weighted_score desc
    result.pattern_scores.sort(key=lambda ps: ps.weighted_score, reverse=True)

    # Totals
    result.total_score = (
        sum(ps.weighted_score for ps in result.pattern_scores)
        + sum(fs.get("score", 0) for fs in result.finding_scores)
    )

    if expected_ids:
        result.max_possible_score = _calculate_max_score(expected_ids)
        if result.max_possible_score > 0:
            result.score_ratio = result.total_score / result.max_possible_score

    return result


def _calculate_max_score(expected_ids: List[str]) -> float:
    """Score maximum possible pour un golden set."""
    total = 0.0
    for eid in expected_ids:
        c = get_concept(eid)
        if not c:
            total += 2
            continue
        ctype = c.get("type", "finding")
        if ctype == "pattern":
            total += PATTERN_BASE_SCORE + REQUIRES_WEIGHT
        else:
            total += c.get("poids", 2)
    return total


# ---------------------------------------------------------------------------
# Comparison with golden set
# ---------------------------------------------------------------------------

def compare_with_golden_set(
    found_ids: List[str],
    expected_ids: List[str],
) -> Dict:
    """Compare la reponse etudiant avec le golden set expert."""
    # Normaliser les cles (accents pipeline V1 vs cles V2 sans accents)
    found_ids = [normalize_key(fid) for fid in found_ids]
    expected_ids = [normalize_key(eid) for eid in expected_ids]

    found_set = set(found_ids)
    expected_set = set(expected_ids)

    matched = found_set & expected_set
    missed = expected_set - found_set
    extra = found_set - expected_set

    student_score = score_student_response_v2(found_ids, expected_ids)

    implicit_matches = set()
    if student_score.semantic_result:
        for pid in student_score.semantic_result.implicit_patterns:
            if pid in expected_set:
                implicit_matches.add(pid)

    return {
        "matched_exact": sorted(matched),
        "matched_implicit": sorted(implicit_matches),
        "missed": sorted(missed - implicit_matches),
        "extra": sorted(extra),
        "student_score": student_score.to_dict(),
        "counts": {
            "expected": len(expected_ids),
            "found": len(found_ids),
            "matched_exact": len(matched),
            "matched_implicit": len(implicit_matches),
            "missed": len(missed - implicit_matches),
            "extra": len(extra),
        },
    }


# ---------------------------------------------------------------------------
# Format lisible
# ---------------------------------------------------------------------------

def format_scoring_summary(result: ScoringResult) -> str:
    """Resume lisible du scoring."""
    lines = []
    lines.append("=== Scoring V2 Summary ===")
    lines.append(f"Total score: {result.total_score:.1f}")
    if result.max_possible_score > 0:
        lines.append(f"Max possible: {result.max_possible_score:.1f}")
        lines.append(f"Ratio: {result.score_ratio:.0%}")

    lines.append("")
    lines.append("--- Pattern Scores ---")
    for ps in result.pattern_scores:
        tag = "[IMPLICIT]" if ps.is_implicit else "[EXPLICIT]"
        excl = " [EXCLUDED]" if ps.exclusion_penalty else ""
        lines.append(
            f"  {tag} {ps.pattern_id}: "
            f"raw={ps.raw_score:.1f} weighted={ps.weighted_score:.1f}{excl}"
        )
        lines.append(
            f"    base={ps.base_score} + req={ps.requires_score:.1f} "
            f"+ qual={ps.qualifier_score} + sup={ps.supports_score}"
        )
        if ps.requires_missing:
            lines.append(f"    requires manquants: {ps.requires_missing}")

    if result.finding_scores:
        lines.append("")
        lines.append("--- Orphan Finding Scores ---")
        for fs in result.finding_scores:
            lines.append(f"  {fs["concept_id"]}: score={fs["score"]}")

    return "\n".join(lines)
