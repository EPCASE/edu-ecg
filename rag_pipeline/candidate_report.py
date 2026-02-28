"""
📋 Module de Rapport Candidat — Feedback structuré après évaluation
====================================================================
Orchestre le pipeline complet (Briques 2→5) sur le texte d'un candidat
et génère un rapport pédagogique clair :

  1. 🔍 Analyse du texte — concepts extraits par le pipeline IA
  2. 📊 Note & explication — score dégressif par génération, détail par validant
  3. 📝 Éléments descriptifs — concepts vrais ajoutés par le candidat (découvertes)

Utilisation :
    from candidate_report import generate_candidate_report, format_report_text

    report = generate_candidate_report(
        texte_etudiant="fibrillation atriale qrs fins",
        golden_names=["Fibrillation atriale", "Repolarisation précoce"],
        golden_ids=["FIBRILLATION_ATRIALE", "REPOLARISATION_PRÉCOCE"],
        golden_roles=["validant", "descripteur"],
        diagnostic_principal="Fibrillation atriale",
    )
    print(format_report_text(report))

Auteur : BMad Team
Date   : 2026-02-28
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ner_extractor import extract_clinical_terms
from hybrid_search import HybridSearchEngine
from neurosymbolic_judge import resolve_term_to_ontology
from scoring import (
    score_student_response,
    find_owl_concept,
    SCORE_BY_GENERATION,
    SCORE_GENERATION_FLOOR,
    _score_for_generation,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Structures de données du rapport
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExtractedConcept:
    """Un concept extrait du texte du candidat par le pipeline IA."""
    terme_brut: str
    statut: str                # present / absent / hypothese
    ontology_id: str           # ID résolu ou "NONE"
    concept_name: str          # Nom canonique dans l'ontologie
    method: str                # coupe_circuit / juge_llm / fallback_subterm / no_candidates
    justification: str         # Explication de la résolution


@dataclass
class ValidantDetail:
    """Détail du scoring pour un diagnostic validant attendu."""
    golden_name: str
    golden_id: str
    found: bool
    score_pct: float           # 0..100
    match_type: str            # exact / child_gen1 / parent_gen2 / implication / missing
    found_via_id: str          # ID du concept étudiant qui a matché (ou "")
    found_via_name: str        # Nom du concept étudiant qui a matché (ou "")
    explication: str           # Phrase d'explication pour le candidat


@dataclass
class DescripteurDetail:
    """Détail pour un élément descripteur attendu."""
    golden_name: str
    golden_id: str
    found: bool
    match_type: str


@dataclass
class DecouverteDetail:
    """Un concept trouvé par le candidat, vrai, mais non exigé par le barème."""
    concept_name: str
    ontology_id: str
    categorie: str
    statut: str


@dataclass
class CandidateReport:
    """Rapport complet d'évaluation pour un candidat."""
    # Méta
    diagnostic_principal: str
    texte_etudiant: str
    latence_s: float
    erreur: Optional[str] = None

    # Section 1 : Concepts extraits
    concepts_extraits: List[ExtractedConcept] = field(default_factory=list)

    # Section 2 : Note & explication
    score_final_pct: float = 0.0
    validant_details: List[ValidantDetail] = field(default_factory=list)
    nb_validants_trouves: int = 0
    nb_validants_attendus: int = 0

    # Section 3 : Descripteurs
    descripteur_details: List[DescripteurDetail] = field(default_factory=list)
    nb_descripteurs_trouves: int = 0
    nb_descripteurs_attendus: int = 0

    # Section 4 : Découvertes additionnelles
    decouvertes: List[DecouverteDetail] = field(default_factory=list)

    # Statistiques méthodes
    n_coupe_circuit: int = 0
    n_juge_llm: int = 0
    n_fallback: int = 0
    n_no_candidates: int = 0


# ──────────────────────────────────────────────────────────────────────────────
# Moteur de recherche (singleton module-level)
# ──────────────────────────────────────────────────────────────────────────────

_engine: Optional[HybridSearchEngine] = None


def _get_engine() -> HybridSearchEngine:
    global _engine
    if _engine is None:
        _engine = HybridSearchEngine()
    return _engine


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _explain_match_type(match_type: str, found_name: str, golden_name: str) -> str:
    """Génère une explication lisible pour le candidat."""
    if match_type == "exact":
        return f"✅ Vous avez identifié « {golden_name} » — correspondance exacte."

    if match_type.startswith("child_gen"):
        gen = match_type.replace("child_gen", "")
        score = _score_for_generation(int(gen))
        return (
            f"🟠 Vous avez mentionné « {found_name} » qui est un signe/sous-type "
            f"de « {golden_name} » (descendant génération {gen} → {score:.0f}%)."
        )

    if match_type.startswith("parent_gen"):
        gen = match_type.replace("parent_gen", "")
        score = _score_for_generation(int(gen))
        return (
            f"🔴 Vous avez mentionné « {found_name} » qui est un concept plus général "
            f"que « {golden_name} » (ancêtre génération {gen} → {score:.0f}%)."
        )

    if match_type == "implication":
        return (
            f"🔵 « {golden_name} » est auto-validé par implication logique "
            f"(un autre concept trouvé l'implique)."
        )

    # missing
    return f"❌ « {golden_name} » n'a pas été identifié dans votre réponse."


def _match_type_label(mt: str) -> str:
    """Label court lisible pour un match_type."""
    if mt == "exact":
        return "Exact (100%)"
    if mt.startswith("child_gen"):
        gen = mt.replace("child_gen", "")
        score = _score_for_generation(int(gen))
        return f"Descendant gen{gen} ({score:.0f}%)"
    if mt.startswith("parent_gen"):
        gen = mt.replace("parent_gen", "")
        score = _score_for_generation(int(gen))
        return f"Ancêtre gen{gen} ({score:.0f}%)"
    if mt == "implication":
        return "Implication (100%)"
    return "Manquant (0%)"


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline principal
# ──────────────────────────────────────────────────────────────────────────────

def generate_candidate_report(
    texte_etudiant: str,
    golden_names: List[str],
    golden_ids: List[str],
    golden_roles: List[str],
    diagnostic_principal: str = "",
    moteur: Optional[HybridSearchEngine] = None,
) -> CandidateReport:
    """
    Exécute le pipeline complet et construit un CandidateReport.

    Args:
        texte_etudiant:       Texte libre du candidat.
        golden_names:         Noms des concepts attendus (golden set).
        golden_ids:           IDs ontologiques correspondants.
        golden_roles:         "validant" ou "descripteur" pour chaque concept.
        diagnostic_principal: Diagnostic principal du cas (pour affichage).
        moteur:               HybridSearchEngine pré-initialisé (optionnel).

    Returns:
        CandidateReport complet.
    """
    engine = moteur or _get_engine()

    report = CandidateReport(
        diagnostic_principal=diagnostic_principal,
        texte_etudiant=texte_etudiant,
        latence_s=0.0,
    )

    if not texte_etudiant or texte_etudiant.strip() in ("", "nan"):
        report.erreur = "Texte vide"
        return report

    t0 = time.time()

    try:
        # ═══════════════════════════════════════════════════════════════
        # Brique 2 : Extraction NER
        # ═══════════════════════════════════════════════════════════════
        extraction = extract_clinical_terms(texte_etudiant)

        # ═══════════════════════════════════════════════════════════════
        # Briques 3 + 4 : Recherche hybride + Juge neurosymbolique
        # ═══════════════════════════════════════════════════════════════
        student_matched_ids: Dict[str, str] = {}  # id → statut
        methods: List[str] = []

        for entite in extraction.entites:
            candidats = engine.search_top_k(entite.terme_brut)
            resolution = resolve_term_to_ontology(
                entite.terme_brut, entite.contexte_phrase, candidats
            )
            matched_id = resolution["ontology_id"]
            method = resolution["method"]
            methods.append(method)

            concept = ExtractedConcept(
                terme_brut=entite.terme_brut,
                statut=entite.statut,
                ontology_id=matched_id,
                concept_name=resolution.get("concept_name", ""),
                method=method,
                justification=resolution.get("justification", ""),
            )
            report.concepts_extraits.append(concept)

            if matched_id != "NONE":
                student_matched_ids[matched_id] = entite.statut

        # Stats méthodes
        report.n_coupe_circuit = methods.count("coupe_circuit")
        report.n_juge_llm = methods.count("juge_llm")
        report.n_fallback = methods.count("fallback_subterm")
        report.n_no_candidates = methods.count("no_candidates")

        # ═══════════════════════════════════════════════════════════════
        # Brique 5 : Scoring ensembliste
        # ═══════════════════════════════════════════════════════════════
        scoring = score_student_response(
            found_ids=list(student_matched_ids.keys()),
            found_statuts=student_matched_ids,
            golden_names=golden_names,
            golden_ids=golden_ids,
            golden_roles=golden_roles,
        )

        report.score_final_pct = scoring["score_final_pct"]

        # ─── Construire le détail des validants ──────────────────────
        report.nb_validants_attendus = scoring["validant_total"]
        report.nb_validants_trouves = scoring["validant_found"]

        # Index rapide partial_matches par golden_name
        partial_by_golden = {}
        for pm in scoring.get("partial_matches", []):
            partial_by_golden[pm["golden_name"]] = pm

        # Index rapide : concept_name → ontology_id depuis les concepts extraits
        id_to_name = {}
        for c in report.concepts_extraits:
            if c.ontology_id != "NONE":
                id_to_name[c.ontology_id] = c.concept_name or c.terme_brut

        # Construire validant_details
        for gname, gid, role in zip(golden_names, golden_ids, golden_roles):
            if role != "validant":
                continue

            mt = scoring.get("match_types", {}).get(gname, "missing")
            found = gname in scoring.get("concepts_valides_attendus", [])
            pm = partial_by_golden.get(gname)
            found_id = pm["found_id"] if pm else ""
            found_name = id_to_name.get(found_id, found_id)
            score_pct = pm["score_pct"] if pm else (100.0 if mt == "exact" else 0.0)

            # Pour les validants auto-validés par implication
            if mt == "implication" and not pm:
                score_pct = 100.0
                found = True

            report.validant_details.append(ValidantDetail(
                golden_name=gname,
                golden_id=gid,
                found=found,
                score_pct=score_pct,
                match_type=mt,
                found_via_id=found_id,
                found_via_name=found_name,
                explication=_explain_match_type(mt, found_name, gname),
            ))

        # ─── Construire le détail des descripteurs ───────────────────
        report.nb_descripteurs_attendus = scoring["descripteur_total"]
        report.nb_descripteurs_trouves = scoring["descripteur_found"]

        for gname, gid, role in zip(golden_names, golden_ids, golden_roles):
            if role != "descripteur":
                continue
            mt = scoring.get("match_types", {}).get(gname, "missing")
            found = gname in scoring.get("concepts_valides_attendus", [])
            report.descripteur_details.append(DescripteurDetail(
                golden_name=gname,
                golden_id=gid,
                found=found,
                match_type=mt,
            ))

        # ─── Découvertes additionnelles ──────────────────────────────
        for dec in scoring.get("decouvertes_additionnelles", []):
            report.decouvertes.append(DecouverteDetail(
                concept_name=dec["concept_name"],
                ontology_id=dec["ontology_id"],
                categorie=dec["categorie"],
                statut=dec["statut"],
            ))

    except Exception as e:
        report.erreur = str(e)[:200]

    report.latence_s = round(time.time() - t0, 2)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# Formatage texte (terminal / console)
# ──────────────────────────────────────────────────────────────────────────────

def format_report_text(report: CandidateReport) -> str:
    """
    Formate un CandidateReport en texte lisible (terminal / console).
    """
    lines: List[str] = []
    W = 80

    lines.append("═" * W)
    lines.append(f"📋 RAPPORT D'ÉVALUATION — {report.diagnostic_principal}")
    lines.append("═" * W)

    if report.erreur:
        lines.append(f"\n⚠️  Erreur : {report.erreur}")
        return "\n".join(lines)

    # ─── Section 1 : Concepts extraits ────────────────────────────────────
    lines.append(f"\n{'─'*W}")
    lines.append(f"🔍 SECTION 1 — Analyse de votre texte ({len(report.concepts_extraits)} concepts identifiés)")
    lines.append(f"{'─'*W}")
    lines.append(f'   Votre texte : « {report.texte_etudiant} »\n')

    for i, c in enumerate(report.concepts_extraits, 1):
        statut_icon = {"present": "✓", "absent": "✗", "hypothese": "?"}.get(c.statut, "·")
        if c.ontology_id != "NONE":
            lines.append(
                f"   {i}. [{statut_icon}] « {c.terme_brut} »  →  {c.concept_name}"
                f"  ({c.method})"
            )
        else:
            lines.append(
                f"   {i}. [{statut_icon}] « {c.terme_brut} »  →  ⚠️ non résolu"
            )

    # ─── Section 2 : Note & explication ───────────────────────────────────
    lines.append(f"\n{'─'*W}")
    lines.append(
        f"📊 SECTION 2 — Votre note : {report.score_final_pct:.1f}% "
        f"({report.nb_validants_trouves}/{report.nb_validants_attendus} diagnostics validants)"
    )
    lines.append(f"{'─'*W}")

    # Rappel du barème
    lines.append(f"   Barème : Exact=100% | Gen1=90% | Gen2=80% | Gen3=70% | Gen4+={SCORE_GENERATION_FLOOR:.0f}% | Hypothèse=×0.8\n")

    for vd in report.validant_details:
        score_str = f"{vd.score_pct:5.1f}%"
        lines.append(f"   {vd.explication}")
        if vd.found and vd.match_type != "exact":
            lines.append(f"          → Score pour ce validant : {score_str}")
        elif not vd.found:
            lines.append(f"          → Score pour ce validant : 0.0%")

    # Score final
    lines.append(f"\n   ══ NOTE FINALE : {report.score_final_pct:.1f}% ══")

    # ─── Section 3 : Descripteurs ─────────────────────────────────────────
    if report.nb_descripteurs_attendus > 0:
        lines.append(f"\n{'─'*W}")
        lines.append(
            f"📝 SECTION 3 — Éléments descriptifs "
            f"({report.nb_descripteurs_trouves}/{report.nb_descripteurs_attendus} identifiés)"
        )
        lines.append(f"{'─'*W}")
        lines.append(
            f"   Ces éléments font partie du diagnostic mais ne sont pas notés :\n"
        )

        for dd in report.descripteur_details:
            if dd.found:
                lines.append(f"   ✅ « {dd.golden_name} » — identifié")
            else:
                lines.append(f"   ⬜ « {dd.golden_name} » — non mentionné")

    # ─── Section 4 : Découvertes ──────────────────────────────────────────
    if report.decouvertes:
        lines.append(f"\n{'─'*W}")
        lines.append(
            f"🟢 SECTION 4 — Découvertes additionnelles "
            f"({len(report.decouvertes)} concepts vrais, non exigés)"
        )
        lines.append(f"{'─'*W}")
        lines.append(
            f"   Vous avez identifié des éléments cliniquement pertinents\n"
            f"   au-delà du barème strict. Ils ne rapportent pas de points\n"
            f"   mais montrent la qualité de votre lecture :\n"
        )

        for dec in report.decouvertes:
            cat_label = dec.categorie.replace("_", " ").capitalize()
            lines.append(f"   🟢 {dec.concept_name}  ({cat_label})")

    # ─── Footer ───────────────────────────────────────────────────────────
    lines.append(f"\n{'═'*W}")
    lines.append(f"⏱️  Temps d'analyse : {report.latence_s:.1f}s")
    lines.append("═" * W)

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Formatage HTML (pour Streamlit / notebook)
# ──────────────────────────────────────────────────────────────────────────────

def format_report_html(report: CandidateReport) -> str:
    """
    Formate un CandidateReport en HTML stylisé (dark theme).
    Compatible Streamlit (st.markdown) et IPython (display(HTML(...))).
    """
    if report.erreur:
        return f'<div style="color:#ff6b6b; padding:20px;">⚠️ Erreur : {report.erreur}</div>'

    # Couleur du score
    score = report.score_final_pct
    if score >= 90:
        score_color = "#4CAF50"
        score_emoji = "🎉"
        score_label = "Excellent"
    elif score >= 70:
        score_color = "#FF9800"
        score_emoji = "👍"
        score_label = "Bien"
    elif score >= 50:
        score_color = "#FF5722"
        score_emoji = "📚"
        score_label = "À améliorer"
    else:
        score_color = "#F44336"
        score_emoji = "💪"
        score_label = "À retravailler"

    html_parts: List[str] = []

    # ─── Container ────────────────────────────────────────────────────
    html_parts.append(f"""
    <div style="background:#1e1e1e; color:#e0e0e0; padding:24px; border-radius:12px;
                font-family:'Segoe UI', system-ui, sans-serif; line-height:1.6;">
    """)

    # ─── Header : Score ───────────────────────────────────────────────
    html_parts.append(f"""
    <div style="text-align:center; margin-bottom:24px;">
        <div style="font-size:14px; color:#999; text-transform:uppercase; letter-spacing:2px;">
            {report.diagnostic_principal}
        </div>
        <div style="font-size:64px; font-weight:bold; color:{score_color}; margin:8px 0;">
            {score:.0f}%
        </div>
        <div style="font-size:18px; color:{score_color};">
            {score_emoji} {score_label} — {report.nb_validants_trouves}/{report.nb_validants_attendus} diagnostics validants
        </div>
        <div style="font-size:12px; color:#666; margin-top:4px;">
            Barème : Exact=100% | Gen1=90% | Gen2=80% | Gen3=70% | Hypothèse=×0.8
        </div>
    </div>
    """)

    # ─── Section 1 : Concepts extraits ────────────────────────────────
    html_parts.append(f"""
    <div style="background:#252525; border-radius:8px; padding:16px; margin-bottom:16px;">
        <h3 style="color:#90CAF9; margin:0 0 12px 0; font-size:16px;">
            🔍 Analyse de votre texte — {len(report.concepts_extraits)} concepts identifiés
        </h3>
        <div style="background:#2d2d2d; padding:10px; border-radius:6px; margin-bottom:12px;
                    font-style:italic; color:#bbb;">
            « {report.texte_etudiant} »
        </div>
    """)

    for c in report.concepts_extraits:
        if c.ontology_id != "NONE":
            method_badge = {
                "coupe_circuit": "⚡",
                "juge_llm": "🧠",
                "fallback_subterm": "🔄",
            }.get(c.method, "·")
            html_parts.append(f"""
            <div style="padding:4px 0; border-bottom:1px solid #333;">
                <span style="color:#4CAF50;">●</span>
                <strong>« {c.terme_brut} »</strong>
                → <span style="color:#81C784;">{c.concept_name}</span>
                <span style="color:#666; font-size:12px; margin-left:8px;">{method_badge} {c.method}</span>
            </div>
            """)
        else:
            html_parts.append(f"""
            <div style="padding:4px 0; border-bottom:1px solid #333;">
                <span style="color:#9E9E9E;">●</span>
                <strong>« {c.terme_brut} »</strong>
                → <span style="color:#9E9E9E;">non résolu</span>
            </div>
            """)

    html_parts.append("</div>")

    # ─── Section 2 : Détail du scoring ────────────────────────────────
    html_parts.append(f"""
    <div style="background:#252525; border-radius:8px; padding:16px; margin-bottom:16px;">
        <h3 style="color:#FFD54F; margin:0 0 12px 0; font-size:16px;">
            📊 Détail de votre note — {report.score_final_pct:.1f}%
        </h3>
    """)

    for vd in report.validant_details:
        if vd.match_type == "exact":
            color = "#4CAF50"
            icon = "✅"
        elif vd.match_type.startswith("child"):
            color = "#FF9800"
            icon = "🟠"
        elif vd.match_type.startswith("parent"):
            color = "#F44336"
            icon = "🔴"
        elif vd.match_type == "implication":
            color = "#2196F3"
            icon = "🔵"
        else:
            color = "#9E9E9E"
            icon = "❌"

        score_bar_width = min(100, max(0, vd.score_pct))
        html_parts.append(f"""
        <div style="background:#2d2d2d; border-radius:6px; padding:10px; margin-bottom:8px;
                    border-left:4px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>{icon} <strong style="color:{color};">{vd.golden_name}</strong></span>
                <span style="color:{color}; font-weight:bold; font-size:18px;">{vd.score_pct:.0f}%</span>
            </div>
            <div style="background:#1a1a1a; border-radius:4px; height:6px; margin:6px 0;">
                <div style="background:{color}; width:{score_bar_width}%; height:100%; border-radius:4px;"></div>
            </div>
            <div style="color:#aaa; font-size:13px;">{vd.explication}</div>
        </div>
        """)

    html_parts.append("</div>")

    # ─── Section 3 : Descripteurs ─────────────────────────────────────
    if report.nb_descripteurs_attendus > 0:
        html_parts.append(f"""
        <div style="background:#252525; border-radius:8px; padding:16px; margin-bottom:16px;">
            <h3 style="color:#CE93D8; margin:0 0 12px 0; font-size:16px;">
                📝 Éléments descriptifs — {report.nb_descripteurs_trouves}/{report.nb_descripteurs_attendus} identifiés
            </h3>
            <div style="color:#999; font-size:13px; margin-bottom:8px;">
                Ces éléments font partie du diagnostic mais ne sont pas notés.
            </div>
        """)

        for dd in report.descripteur_details:
            if dd.found:
                html_parts.append(f"""
                <div style="padding:4px 8px;">
                    <span style="color:#4CAF50;">✅</span> {dd.golden_name}
                </div>
                """)
            else:
                html_parts.append(f"""
                <div style="padding:4px 8px;">
                    <span style="color:#666;">⬜</span>
                    <span style="color:#888;">{dd.golden_name}</span>
                </div>
                """)

        html_parts.append("</div>")

    # ─── Section 4 : Découvertes ──────────────────────────────────────
    if report.decouvertes:
        html_parts.append(f"""
        <div style="background:#252525; border-radius:8px; padding:16px; margin-bottom:16px;">
            <h3 style="color:#00BCD4; margin:0 0 12px 0; font-size:16px;">
                🟢 Découvertes additionnelles — {len(report.decouvertes)} concepts vrais
            </h3>
            <div style="color:#999; font-size:13px; margin-bottom:8px;">
                Vous avez identifié des éléments cliniquement pertinents au-delà du barème.
                Ils ne rapportent pas de points mais montrent la qualité de votre lecture.
            </div>
        """)

        for dec in report.decouvertes:
            cat_label = dec.categorie.replace("_", " ").capitalize()
            html_parts.append(f"""
            <div style="padding:4px 8px; border-bottom:1px solid #333;">
                <span style="color:#00BCD4;">🟢</span> <strong>{dec.concept_name}</strong>
                <span style="color:#666; font-size:12px; margin-left:8px;">({cat_label})</span>
            </div>
            """)

        html_parts.append("</div>")

    # ─── Footer ───────────────────────────────────────────────────────
    html_parts.append(f"""
    <div style="text-align:center; color:#666; font-size:12px; margin-top:8px;">
        ⏱️ Temps d'analyse : {report.latence_s:.1f}s
    </div>
    </div>
    """)

    return "\n".join(html_parts)


# ──────────────────────────────────────────────────────────────────────────────
# CLI — Test rapide
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    from pathlib import Path
    from dotenv import load_dotenv

    # Charger .env
    load_dotenv(Path(__file__).parent.parent / "ECG lecture" / ".env")

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    os.chdir(str(Path(__file__).parent))

    # Cas test : FA avec réponse partielle
    report = generate_candidate_report(
        texte_etudiant="fibrillation atriale qrs fins tachycardie",
        golden_names=["Fibrillation atriale", "Repolarisation précoce"],
        golden_ids=["FIBRILLATION_ATRIALE", "REPOLARISATION_PRÉCOCE"],
        golden_roles=["validant", "descripteur"],
        diagnostic_principal="Fibrillation atriale",
    )

    print(format_report_text(report))
