"""
🧱 Brique 5 — Scoring Neurosymbolique
=======================================
Fonctions de scoring pour comparer les concepts trouvés par le pipeline RAG
contre le Golden Set expert.

Fonctions principales :
  - find_owl_concept()        : Lookup d'un concept dans l'ontologie JSON
  - apply_implication_rules() : Validation automatique de concepts implicites
  - score_student_response()  : Scoring pondéré complet d'une réponse étudiant

Dépendances :
  - ontology_from_owl.json (produit par regenerate_ontology.py)
  - Aucune dépendance Streamlit / frontend

Auteur : BMad Team
Date   : 2026-02-27
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chargement de l'ontologie (singleton module-level)
# ---------------------------------------------------------------------------

_ONTOLOGY: Optional[Dict] = None


def _get_ontology() -> Dict:
    """Charge l'ontologie JSON une seule fois."""
    global _ONTOLOGY
    if _ONTOLOGY is None:
        # Source unique : ECG lecture/data/ontology_from_owl.json
        # (générée par regenerate_ontology.py depuis le fichier OWL)
        candidates = [
            Path(__file__).parent.parent / "ECG lecture" / "data" / "ontology_from_owl.json",
        ]
        for p in candidates:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    _ONTOLOGY = json.load(f)
                logger.info(f"✅ Ontologie chargée : {p} ({len(_ONTOLOGY.get('concept_mappings', {}))} concepts)")
                return _ONTOLOGY
        raise FileNotFoundError(
            f"ontology_from_owl.json introuvable. Chemins testés : {[str(p) for p in candidates]}"
        )
    return _ONTOLOGY


def load_ontology(path: str | Path) -> Dict:
    """Charge explicitement une ontologie depuis un chemin donné."""
    global _ONTOLOGY
    with open(path, "r", encoding="utf-8") as f:
        _ONTOLOGY = json.load(f)
    logger.info(f"✅ Ontologie chargée : {path} ({len(_ONTOLOGY.get('concept_mappings', {}))} concepts)")
    return _ONTOLOGY


# ---------------------------------------------------------------------------
# Lookup de concepts
# ---------------------------------------------------------------------------

def find_owl_concept(concept_text: str) -> Optional[Dict]:
    """
    Cherche un concept dans l'ontologie OWL pondérée par son label français.

    Stratégie de recherche (par ordre de priorité) :
      1. Match exact sur concept_name (case-insensitive)
      2. Match exact sur un synonyme
      3. Match partiel (contient / est contenu dans)

    Args:
        concept_text: Le texte du concept (ex: "Fibrillation atriale", "BBG")

    Returns:
        dict avec ontology_id, concept_name, poids, categorie, synonymes, implications.
        Retourne un dict par défaut (poids=1) si non trouvé.
    """
    ontology = _get_ontology()
    concept_lower = concept_text.lower().strip()
    concept_mappings = ontology.get("concept_mappings", {})

    # 1. Recherche exacte par concept_name
    for ontology_id, mapping in concept_mappings.items():
        if mapping.get("concept_name", "").lower() == concept_lower:
            return {
                "ontology_id": ontology_id,
                "concept_name": mapping.get("concept_name"),
                "poids": mapping.get("poids", 1),
                "categorie": mapping.get("categorie", "DESCRIPTEUR_ECG"),
                "synonymes": mapping.get("synonymes", []),
                "implications": mapping.get("implications", []),
            }

    # 2. Recherche par synonymes
    for ontology_id, mapping in concept_mappings.items():
        synonymes = [s.lower() for s in mapping.get("synonymes", [])]
        if concept_lower in synonymes:
            return {
                "ontology_id": ontology_id,
                "concept_name": mapping.get("concept_name"),
                "poids": mapping.get("poids", 1),
                "categorie": mapping.get("categorie", "DESCRIPTEUR_ECG"),
                "synonymes": mapping.get("synonymes", []),
                "implications": mapping.get("implications", []),
            }

    # 3. Recherche partielle (contient)
    for ontology_id, mapping in concept_mappings.items():
        concept_name = mapping.get("concept_name", "").lower()
        if concept_lower in concept_name or concept_name in concept_lower:
            return {
                "ontology_id": ontology_id,
                "concept_name": mapping.get("concept_name"),
                "poids": mapping.get("poids", 1),
                "categorie": mapping.get("categorie", "DESCRIPTEUR_ECG"),
                "synonymes": mapping.get("synonymes", []),
                "implications": mapping.get("implications", []),
            }

    # Pas trouvé → retourner un dict par défaut
    return {
        "ontology_id": concept_text.upper().replace(" ", "_"),
        "concept_name": concept_text,
        "poids": 1,
        "categorie": "DESCRIPTEUR_ECG",
        "synonymes": [],
        "implications": [],
    }


# ---------------------------------------------------------------------------
# Règles d'implication
# ---------------------------------------------------------------------------

def apply_implication_rules(
    matched_concepts: List[str],
    all_expected_concepts: List[str],
) -> Set[str]:
    """
    Applique les règles d'implication automatique.
    Si un diagnostic est identifié, valide automatiquement ses implications.

    Exemple : BAV_COMPLET trouvé → BAV est auto-validé.

    Args:
        matched_concepts: Liste des concept_name déjà matchés.
        all_expected_concepts: Liste de tous les concept_name attendus (golden set).

    Returns:
        Set de concept_name auto-validés par implication.
    """
    auto_validated: Set[str] = set()
    ontology = _get_ontology()

    implication_rules = ontology.get("implication_rules", {})
    concept_mappings = ontology.get("concept_mappings", {})

    for matched_concept in matched_concepts:
        # Trouver l'ontology_id du concept matché
        mapping_key = None
        for ontology_id, mapping in concept_mappings.items():
            if mapping.get("concept_name", "").lower() == matched_concept.lower():
                mapping_key = ontology_id
                break

        if mapping_key and mapping_key in implication_rules:
            implications = implication_rules[mapping_key]
            for implied_concept in implications:
                if (
                    implied_concept in all_expected_concepts
                    and implied_concept not in matched_concepts
                ):
                    auto_validated.add(implied_concept)
                    logger.debug(
                        f"   ↪ Implication : {matched_concept} → {implied_concept}"
                    )

    return auto_validated


# ---------------------------------------------------------------------------
# Scoring complet d'une réponse
# ---------------------------------------------------------------------------

def _build_reverse_implications() -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, int]]]:
    """
    Construit un index inversé : concept_enfant → [concept_parent_1, ...]
    + un index de profondeur : concept_enfant → {parent_id: generation}

    L'ontologie stocke : PARENT.implications = [enfant1, enfant2, ...].
    Cette fonction produit : enfant1 → [PARENT], enfant2 → [PARENT], ...

    Utilité : quand l'étudiant donne un signe (enfant), retrouver le
    diagnostic (parent) qu'il supporte partiellement, avec la distance.

    La traversée est **récursive** (multi-niveau, profondeur max 3) :
      ESV → Multiples ESV → Bigéminisme
      ⇒ reverse[Bigéminisme] = {Multiples ESV: 1, ESV: 2}
    """
    ontology = _get_ontology()
    concept_mappings = ontology.get("concept_mappings", {})

    # Étape 1 : reverse direct (1 niveau) + profondeur
    direct_reverse: Dict[str, Set[str]] = {}
    depth_map: Dict[str, Dict[str, int]] = {}  # child_id → {parent_id: generation}
    for oid, mapping in concept_mappings.items():
        for impl_name in mapping.get("implications", []):
            impl_owl = find_owl_concept(impl_name)
            if impl_owl:
                impl_id = impl_owl["ontology_id"]
                direct_reverse.setdefault(impl_id, set()).add(oid)
                depth_map.setdefault(impl_id, {})[oid] = 1  # Gen 1 = parent direct

    # Étape 2 : propager récursivement (max 3 niveaux)
    full_reverse: Dict[str, Set[str]] = {k: set(v) for k, v in direct_reverse.items()}
    max_depth = 3
    for _depth in range(1, max_depth):
        changed = False
        for child_id, parent_ids in list(full_reverse.items()):
            for parent_id in list(parent_ids):
                grandparent_ids = direct_reverse.get(parent_id, set())
                for gp_id in grandparent_ids:
                    if gp_id not in full_reverse[child_id]:
                        full_reverse[child_id].add(gp_id)
                        # Profondeur = profondeur du parent + 1
                        gen = depth_map.get(child_id, {}).get(parent_id, 1) + 1
                        depth_map.setdefault(child_id, {})[gp_id] = gen
                        changed = True
        if not changed:
            break

    # Convertir en listes
    reverse: Dict[str, List[str]] = {k: list(v) for k, v in full_reverse.items()}

    n_extra = sum(
        len(full_reverse.get(k, set()) - direct_reverse.get(k, set()))
        for k in full_reverse
    )
    logger.info(
        f"  ↪ Index inversé implications (récursif) : "
        f"{len(reverse)} enfants → parents (+{n_extra} relations multi-niveaux)"
    )
    return reverse, depth_map


# ---------------------------------------------------------------------------
# Score dégressif par distance générationnelle (CHILD et PARENT)
# ---------------------------------------------------------------------------
# Plus l'étudiant est loin du concept validant dans l'arbre ontologique,
# moins il a de points. Le score décroît de 10% par génération.
#
# Exemples (CHILD — étudiant cite un descendant du golden) :
#   Gen 1 : étudiant dit "Absence d'onde P" pour golden "FA"          → 90%
#   Gen 2 : étudiant dit un sous-signe d'un signe de FA               → 80%
#   Gen 3+: encore plus indirect                                       → 70%, 60% (plancher)
#
# Exemples (PARENT — étudiant cite un ancêtre du golden) :
#   Gen 1 : étudiant dit "BBG" pour golden "BBG complet"              → 90%
#   Gen 2 : étudiant dit une catégorie très large                      → 80%
#   Gen 3+: encore plus vague                                          → 70%, 60% (plancher)
#
SCORE_BY_GENERATION = {1: 90.0, 2: 80.0, 3: 70.0}  # Gen → score %
SCORE_GENERATION_FLOOR = 60.0  # Plancher pour gen 4+


def _score_for_generation(generation: int) -> float:
    """Retourne le score % pour une distance générationnelle donnée."""
    return SCORE_BY_GENERATION.get(generation, SCORE_GENERATION_FLOOR)


def score_student_response(
    found_ids: List[str],
    found_statuts: Dict[str, str],
    golden_names: List[str],
    golden_ids: List[str],
    golden_roles: Optional[List[str]] = None,
) -> Dict:
    """
    Score d'une réponse étudiant vs le golden set.

    **Score = moyenne des % des diagnostics VALIDANTS matchés.**
    Les concepts descripteurs sont trackés séparément (non inclus dans la note).

    Niveaux de matching (par priorité décroissante) :
      1. **EXACT**  — l'ID trouvé est l'ID attendu → 100% (ou 80% si hypothèse)
      2. **CHILD**  — l'ID trouvé est un descendant du golden → 90/80/70/60% selon génération
      3. **PARENT** — l'ID trouvé est un ancêtre du golden → 90/80/70/60% selon génération
      4. **IMPLICATION** — un concept déjà matché implique le golden → 100% (auto-validé)
      5. **MISSING** — aucune correspondance → 0%

    Args:
        found_ids:     Liste des ontology_id trouvés par le pipeline RAG
        found_statuts: Dict {ontology_id: statut} ("present"/"hypothese"/"absent")
        golden_names:  Liste des concept_name attendus (golden set)
        golden_ids:    Liste des ontology_id attendus (golden set)
        golden_roles:  Liste des rôles ("validant"/"descripteur") pour chaque concept.
                       Si None, tous sont considérés comme validants.

    Returns:
        Dict avec score_final_pct (validants uniquement), matched/missing,
        validant_found/validant_total, descripteur_found/descripteur_total,
        match_types, partial_matches.
    """
    ontology = _get_ontology()
    concept_mappings = ontology.get("concept_mappings", {})
    found_id_set = set(found_ids)

    # Index inversé pour matching hiérarchique (+ profondeur)
    reverse_implications, reverse_depths = _build_reverse_implications()

    # --- Phase 1 : Matching direct (EXACT) ---
    matched_concepts: List[str] = []
    concept_weights: Dict[str, int] = {}
    concept_scores: Dict[str, float] = {}
    match_types: Dict[str, str] = {}  # gname → "exact" / "child" / "parent" / "implication"
    partial_matches: List[Dict] = []

    for gname, gid in zip(golden_names, golden_ids):
        owl = find_owl_concept(gname)
        poids = owl.get("poids", 1) if owl else 1
        concept_weights[gname] = poids

        if gid in found_id_set:
            statut = found_statuts.get(gid, "present")
            if statut in ("present", "hypothese"):
                matched_concepts.append(gname)
                concept_scores[gname] = 100.0 if statut == "present" else 80.0
                match_types[gname] = "exact"

    # --- Phase 2 : Matching hiérarchique (CHILD / PARENT) pour les non matchés ---
    already_matched = set(matched_concepts)

    for gname, gid in zip(golden_names, golden_ids):
        if gname in already_matched:
            continue

        owl_golden = find_owl_concept(gname)
        if not owl_golden:
            continue

        golden_implications = owl_golden.get("implications", [])
        # IDs des concepts impliqués par le golden (ses enfants/descendants)
        # Traversée BFS récursive avec tracking de la PROFONDEUR (génération)
        # golden_child_depths[ontology_id] = distance générationnelle (1 = enfant direct)
        golden_child_depths: Dict[str, int] = {}
        queue: List[Tuple[str, int]] = [(name, 1) for name in golden_implications]
        visited_names: Set[str] = set()
        while queue:
            impl_name, depth = queue.pop(0)
            if impl_name in visited_names:
                continue
            visited_names.add(impl_name)
            impl_owl = find_owl_concept(impl_name)
            if impl_owl:
                impl_id = impl_owl["ontology_id"]
                # Garder la profondeur minimale (chemin le plus court)
                if impl_id not in golden_child_depths or depth < golden_child_depths[impl_id]:
                    golden_child_depths[impl_id] = depth
                # Ajouter les sous-implications (enfants de l'enfant) à gen+1
                for sub_impl in impl_owl.get("implications", []):
                    if sub_impl not in visited_names:
                        queue.append((sub_impl, depth + 1))

        best_score = 0.0
        best_type = ""
        best_found_id = ""

        for fid in found_id_set:
            statut = found_statuts.get(fid, "present")
            if statut not in ("present", "hypothese"):
                continue

            # 2a. CHILD : l'étudiant a trouvé un concept qui est un descendant du golden
            #     Score dégressif par génération : gen1=90%, gen2=80%, gen3=70%, gen4+=60%
            if fid in golden_child_depths:
                generation = golden_child_depths[fid]
                base_score = _score_for_generation(generation)
                s = base_score * (1.0 if statut == "present" else 0.8)
                if s > best_score:
                    best_score = s
                    best_type = f"child_gen{generation}"
                    best_found_id = fid

            # 2b. PARENT : l'étudiant a trouvé un concept plus général (ancêtre)
            #     Score dégressif par génération : gen1=90%, gen2=80%, gen3=70%, gen4+=60%
            if gid in reverse_implications:
                parent_ids = reverse_implications[gid]
                if fid in parent_ids:
                    generation = reverse_depths.get(gid, {}).get(fid, 1)
                    base_score = _score_for_generation(generation)
                    s = base_score * (1.0 if statut == "present" else 0.8)
                    if s > best_score:
                        best_score = s
                        best_type = f"parent_gen{generation}"
                        best_found_id = fid

        if best_score > 0:
            matched_concepts.append(gname)
            concept_scores[gname] = best_score
            match_types[gname] = best_type
            partial_matches.append({
                "golden_name": gname,
                "golden_id": gid,
                "found_id": best_found_id,
                "match_type": best_type,
                "score_pct": best_score,
            })
            logger.info(
                f"   🔗 {best_type.upper()} match : {best_found_id} → {gname} ({best_score:.0f}%)"
            )

    # --- Phase 3 : Implications automatiques (forward) ---
    auto_validated = apply_implication_rules(matched_concepts, golden_names)
    for av in auto_validated:
        match_types[av] = "implication"
    all_validated = set(matched_concepts) | auto_validated

    # --- Phase 3b : Logique ensembliste — Séparer attendus vs découvertes ---
    # all_expected_concepts = l'ensemble des concepts du Golden Set (barème prof)
    all_expected_set = set(golden_names)

    # 1. Ce que l'étudiant a validé ET qui était attendu par le prof
    concepts_valides_attendus = all_validated.intersection(all_expected_set)

    # 2. Ce que l'étudiant a validé de justesse (vrai sur l'ECG) MAIS non exigé
    #    → concepts trouvés par le pipeline RAG dont l'ontology_id n'est pas dans le golden set
    #    On reconstruit la liste à partir des found_ids non couverts par le golden
    golden_id_set = set(golden_ids)
    decouvertes_additionnelles_ids = found_id_set - golden_id_set
    decouvertes_additionnelles = []
    for did in decouvertes_additionnelles_ids:
        statut = found_statuts.get(did, "present")
        if statut not in ("present", "hypothese"):
            continue  # Ignorer les concepts niés par l'étudiant
        # Retrouver le concept_name depuis l'ontologie
        if did in concept_mappings:
            cname = concept_mappings[did].get("concept_name", did)
            cat = concept_mappings[did].get("categorie", "DESCRIPTEUR_ECG")
            decouvertes_additionnelles.append({
                "ontology_id": did,
                "concept_name": cname,
                "categorie": cat,
                "statut": statut,
            })

    logger.info(
        f"   📊 Attendus validés: {len(concepts_valides_attendus)}/{len(all_expected_set)}, "
        f"Découvertes additionnelles: {len(decouvertes_additionnelles)}"
    )

    # --- Classer validants vs descripteurs ---
    if golden_roles is None:
        golden_roles = ["validant"] * len(golden_names)
    concept_roles: Dict[str, str] = {}
    for gname, role in zip(golden_names, golden_roles):
        concept_roles[gname] = role

    validant_names = [g for g in golden_names if concept_roles[g] == "validant"]
    descripteur_names = [g for g in golden_names if concept_roles[g] == "descripteur"]

    validant_matched = [g for g in validant_names if g in concepts_valides_attendus]
    validant_missing = [g for g in validant_names if g not in concepts_valides_attendus]
    descripteur_matched = [g for g in descripteur_names if g in concepts_valides_attendus]
    descripteur_missing = [g for g in descripteur_names if g not in concepts_valides_attendus]

    # --- Score STRICT = basé uniquement sur concepts_valides_attendus ---
    # Les découvertes additionnelles ne rapportent AUCUN point (pas de bonus)
    # mais ne font PAS perdre de points non plus.
    # Chaque validant matché contribue son % (exact=100, child=90, parent=40, impl=100)
    # Les validants manqués contribuent 0%
    if len(validant_names) > 0:
        score_sum = sum(concept_scores.get(v, 100.0) for v in validant_matched)
        # Les manqués contribuent 0
        final_pct = score_sum / len(validant_names)
    else:
        final_pct = 100.0  # Pas de validant demandé = OK par défaut

    return {
        "score_final_pct": round(min(100, final_pct), 1),
        "matched_expected": list(concepts_valides_attendus),
        "missing_expected": [g for g in golden_names if g not in concepts_valides_attendus],
        "auto_validated": list(auto_validated),
        "partial_matches": partial_matches,
        "match_types": match_types,
        # Logique ensembliste — attendus vs découvertes
        "concepts_valides_attendus": list(concepts_valides_attendus),
        "decouvertes_additionnelles": decouvertes_additionnelles,
        # Détails validants / descripteurs
        "validant_total": len(validant_names),
        "validant_found": len(validant_matched),
        "validant_matched": validant_matched,
        "validant_missing": validant_missing,
        "descripteur_total": len(descripteur_names),
        "descripteur_found": len(descripteur_matched),
        "descripteur_matched": descripteur_matched,
        "descripteur_missing": descripteur_missing,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    onto = _get_ontology()
    mappings = onto.get("concept_mappings", {})
    rules = onto.get("implication_rules", {})

    print(f"✅ Ontologie : {len(mappings)} concepts, {len(rules)} règles d'implication")
    print()

    # Test find_owl_concept
    tests = ["Fibrillation atriale", "BBG", "Tachycardie ventriculaire", "concept_inexistant"]
    for t in tests:
        r = find_owl_concept(t)
        print(f"  find_owl_concept('{t}') → {r['ontology_id']} (p={r['poids']}, {r['categorie']})")

    print("\n✅ Brique 5 — Scoring prêt.")
