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
        candidates = [
            Path(__file__).parent / "data" / "ontology_from_owl.json",
            Path(__file__).parent.parent / "data" / "ontology_from_owl.json",
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

def _build_reverse_implications() -> Dict[str, List[str]]:
    """
    Construit un index inversé : concept_enfant → [concept_parent_1, ...]

    L'ontologie stocke : PARENT.implications = [enfant1, enfant2, ...].
    Cette fonction produit : enfant1 → [PARENT], enfant2 → [PARENT], ...

    Utilité : quand l'étudiant donne un signe (enfant), retrouver le
    diagnostic (parent) qu'il supporte partiellement.

    La traversée est **récursive** (multi-niveau, profondeur max 3) :
      ESV → Multiples ESV → Bigéminisme
      ⇒ reverse[Bigéminisme] = [Multiples ESV, ESV]
    """
    ontology = _get_ontology()
    concept_mappings = ontology.get("concept_mappings", {})

    # Étape 1 : reverse direct (1 niveau)
    direct_reverse: Dict[str, Set[str]] = {}
    for oid, mapping in concept_mappings.items():
        for impl_name in mapping.get("implications", []):
            impl_owl = find_owl_concept(impl_name)
            if impl_owl:
                impl_id = impl_owl["ontology_id"]
                direct_reverse.setdefault(impl_id, set()).add(oid)

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
    return reverse


# Score partiel quand l'étudiant donne un concept hiérarchiquement relié
SCORE_CHILD_MATCH = 90.0   # Étudiant plus spécifique (enfant du concept golden)
SCORE_PARENT_MATCH = 40.0  # Étudiant donne un signe pour un diagnostic attendu


def score_student_response(
    found_ids: List[str],
    found_statuts: Dict[str, str],
    golden_names: List[str],
    golden_ids: List[str],
) -> Dict:
    """
    Score pondéré d'une réponse étudiant vs le golden set.

    Le scoring prend en compte :
      - Le poids de chaque concept (1=descripteur, 2=signe, 3=majeur, 4=urgent)
      - Le statut de l'entité (present=100%, hypothese=80%)
      - **Matching hiérarchique** (PARENT / CHILD via implications OWL)
      - Les règles d'implication automatique (forward)
      - Un bonus de +15% si un diagnostic majeur (poids≥3) est trouvé

    Niveaux de matching (par priorité décroissante) :
      1. **EXACT**  — l'ID trouvé est l'ID attendu → 100% (ou 80% si hypothèse)
      2. **CHILD**  — l'ID trouvé est un enfant (impliqué) du golden → 90%
         Ex : étudiant écrit "flutter atrial antihoraire" → golden = "flutter droit typique"
      3. **PARENT** — l'ID trouvé est un parent (le golden est dans ses implications) → 40%
         Ex : étudiant écrit "sus-décalage du segment ST" → golden = "SCA ST+"
      4. **IMPLICATION** — un concept déjà matché implique le golden → 100% (auto-validé)
      5. **MISSING** — aucune correspondance → 0%

    Args:
        found_ids:     Liste des ontology_id trouvés par le pipeline RAG
        found_statuts: Dict {ontology_id: statut} ("present"/"hypothese"/"absent")
        golden_names:  Liste des concept_name attendus (golden set)
        golden_ids:    Liste des ontology_id attendus (golden set)

    Returns:
        Dict avec score_brut_pct, bonus_diag_pct, score_final_pct,
        poids_valides, poids_attendus, matched_expected, missing_expected,
        auto_validated, partial_matches.
    """
    ontology = _get_ontology()
    concept_mappings = ontology.get("concept_mappings", {})
    found_id_set = set(found_ids)

    # Index inversé pour matching hiérarchique
    reverse_implications = _build_reverse_implications()

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
        # Traversée récursive pour couvrir les petits-enfants
        golden_child_ids: Set[str] = set()
        queue = list(golden_implications)
        visited_names: Set[str] = set()
        while queue:
            impl_name = queue.pop(0)
            if impl_name in visited_names:
                continue
            visited_names.add(impl_name)
            impl_owl = find_owl_concept(impl_name)
            if impl_owl:
                golden_child_ids.add(impl_owl["ontology_id"])
                # Ajouter les sous-implications (enfants de l'enfant)
                for sub_impl in impl_owl.get("implications", []):
                    if sub_impl not in visited_names:
                        queue.append(sub_impl)

        best_score = 0.0
        best_type = ""
        best_found_id = ""

        for fid in found_id_set:
            statut = found_statuts.get(fid, "present")
            if statut not in ("present", "hypothese"):
                continue

            # 2a. CHILD : l'étudiant a trouvé un concept qui est un enfant du golden
            #     (le golden implique ce concept → l'étudiant est plus spécifique)
            if fid in golden_child_ids:
                s = SCORE_CHILD_MATCH * (1.0 if statut == "present" else 0.8)
                if s > best_score:
                    best_score = s
                    best_type = "child"
                    best_found_id = fid

            # 2b. PARENT : l'étudiant a trouvé un concept plus général (parent)
            #     que le golden attendu (enfant/plus spécifique).
            #     Ex: étudiant dit "BBG" et golden est "BBG complet"
            #     → BBG implique BBG_COMPLET → BBG est parent de BBG_COMPLET
            #     → reverse[BBG_COMPLET] contient BBG
            #     Vérif : le concept trouvé (fid) est-il un parent du golden (gid) ?
            if gid in reverse_implications:
                parent_ids = reverse_implications[gid]
                if fid in parent_ids:
                    s = SCORE_PARENT_MATCH * (1.0 if statut == "present" else 0.8)
                    if s > best_score:
                        best_score = s
                        best_type = "parent"
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

    # --- Score pondéré ---
    poids_valides = sum(
        concept_weights.get(c, 1) * (concept_scores.get(c, 100.0) / 100.0)
        for c in all_validated
    )
    poids_attendus = sum(concept_weights.get(c, 1) for c in golden_names)

    base_pct = (poids_valides / poids_attendus * 100) if poids_attendus > 0 else 0

    # --- Bonus diagnostic principal (poids ≥ 3) ---
    has_diag = any(concept_weights.get(c, 1) >= 3 for c in all_validated)
    bonus = 0.15 if has_diag else 0
    final_pct = min(100, base_pct * (1 + bonus))

    return {
        "score_brut_pct": round(base_pct, 1),
        "bonus_diag_pct": round(bonus * 100, 0),
        "score_final_pct": round(final_pct, 1),
        "poids_valides": round(poids_valides, 1),
        "poids_attendus": round(poids_attendus, 1),
        "matched_expected": list(all_validated),
        "missing_expected": [g for g in golden_names if g not in all_validated],
        "auto_validated": list(auto_validated),
        "partial_matches": partial_matches,
        "match_types": match_types,
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
