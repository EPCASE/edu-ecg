"""
🧱 Brique 2-4 bis — Schéma du Juge Sémantique Global (prototype)
==================================================================
Schéma Pydantic de sortie du juge global : un graphe de propositions
structuré, PAS une note. Cf. `projetLLMjuge/ECG_online_proposition_iteration_
juge_global_2026-08-02.md` §4 pour la spécification complète.

Ce module ne modifie AUCUN fichier existant du pipeline (ner_extractor,
neurosymbolic_judge, scoring_v3). Il est autonome et peut être expérimenté
en parallèle (shadow mode) sans risque de régression.

Auteur : BMad Team
Date   : 2026-08-02
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums (via Literal, compatible Structured Outputs OpenAI)
# ---------------------------------------------------------------------------

Polarity = Literal["present", "absent", "discussed", "rejected"]
Certainty = Literal["asserted", "probable", "possible", "uncertain"]
ExpressionMode = Literal[
    "explicit",
    "paraphrased",
    "implicit_complete",
    "implicit_partial",
    "unsupported",
]


class Claim(BaseModel):
    """Une proposition clinique extraite du discours global de la réponse."""

    claim_id: str = Field(description="Identifiant local court, ex: 'c1'.")
    concept_id: str = Field(
        description=(
            "L'ontology_id du concept ECG concerné (ex: 'FIBRILLATION_ATRIALE'), "
            "choisi UNIQUEMENT parmi les IDs fournis dans le catalogue candidat."
        )
    )
    polarity: Polarity = Field(
        description="present=affirmé vrai, absent=nié, discussed=évoqué sans trancher, rejected=évoqué puis écarté."
    )
    certainty: Certainty = Field(
        description="Degré de certitude exprimé par l'étudiant."
    )
    expression_mode: ExpressionMode = Field(
        description=(
            "explicit=concept nommé; paraphrased=nommé avec un autre vocabulaire; "
            "implicit_complete=déduit d'une combinaison complète de signes décrits; "
            "implicit_partial=déduit d'une combinaison incomplète; "
            "unsupported=affirmé sans aucun argument textuel."
        )
    )
    evidence_spans: List[str] = Field(
        default_factory=list,
        description="Segments EXACTS du texte étudiant qui justifient cette proposition.",
    )
    inferred_from: List[str] = Field(
        default_factory=list,
        description="claim_id des propositions explicites qui permettent d'inférer celle-ci (si implicite).",
    )


class Measurement(BaseModel):
    """Une mesure numérique et sa cohérence avec l'interprétation donnée."""

    name: str = Field(description="Nom de la mesure, ex: 'PR', 'QRS', 'QTc', 'fréquence', 'axe'.")
    value: float = Field(description="Valeur numérique extraite.")
    unit: str = Field(description="Unité, ex: 'ms', 'bpm', '°'.")
    interpreted_as: str = Field(
        default="",
        description="Conclusion clinique que l'étudiant tire de cette mesure (ex: 'PR_COURT').",
    )
    coherent: bool = Field(
        description="False si la valeur numérique est incompatible avec l'interprétation donnée par l'étudiant."
    )
    explanation: str = Field(
        default="",
        description="Si coherent=False, explication courte de l'incohérence.",
    )


class Contradiction(BaseModel):
    """Une contradiction interne détectée entre deux propositions de la réponse."""

    claim_ids: List[str] = Field(
        description="Les claim_id des propositions qui s'opposent (typiquement 2)."
    )
    explanation: str = Field(description="Nature de la contradiction.")


class UnsupportedClaim(BaseModel):
    """Une affirmation grave non soutenue par le texte (diagnostic sans argument)."""

    claim_id: str
    concept_id: str
    severity: Literal["faible", "modérée", "élevée", "critique"] = Field(
        description="Criticité clinique du diagnostic non soutenu."
    )
    explanation: str = Field(default="")


class UnresolvedMention(BaseModel):
    """Un segment du texte qui ne peut être rattaché à aucun concept du catalogue."""

    text_span: str
    reason: str = Field(default="")


class GlobalSemanticReport(BaseModel):
    """
    Sortie structurée complète du juge sémantique global pour UNE réponse
    étudiante sur UN cas. Ne contient AUCUNE note — uniquement des
    propositions, validées ensuite par le code déterministe (cf. proposition
    §4 et §12 — garde-fous).
    """

    claims: List[Claim] = Field(default_factory=list)
    measurements: List[Measurement] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    unsupported_claims: List[UnsupportedClaim] = Field(default_factory=list)
    unresolved_mentions: List[UnresolvedMention] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Vue simplifiée pour l'adaptateur / la comparaison avec le pipeline actuel
# ---------------------------------------------------------------------------

def extract_found_concept_ids(
    report: GlobalSemanticReport,
    *,
    include_polarities: tuple = ("present",),
    min_expression_mode: Optional[set] = None,
) -> List[str]:
    """
    Projette un GlobalSemanticReport vers une simple liste d'ontology_id
    "trouvés" — le format attendu par le scorer déterministe existant
    (`found_ids`, cf. `scoring_v3.py`) et par le harnais de comparaison F1.

    Ceci NE remplace PAS scoring_v3 : c'est juste une projection pour pouvoir
    comparer les deux méthodes d'EXTRACTION (juge actuel vs juge global) sur
    un pied d'égalité, indépendamment de toute note.

    Args:
        report: Le rapport structuré du juge global.
        include_polarities: Polarités comptées comme "trouvées" (par défaut
            seulement "present" ; on ignore absent/discussed/rejected).
        min_expression_mode: Si fourni, restreint aux modes d'expression
            listés (ex: {"explicit"} pour ne comparer que le F1 explicite).

    Returns:
        Liste d'ontology_id (dédupliquée, ordre stable).
    """
    seen: List[str] = []
    for claim in report.claims:
        if claim.polarity not in include_polarities:
            continue
        if min_expression_mode is not None and claim.expression_mode not in min_expression_mode:
            continue
        if claim.concept_id and claim.concept_id not in seen:
            seen.append(claim.concept_id)
    return seen
