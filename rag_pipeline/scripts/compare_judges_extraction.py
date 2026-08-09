#!/usr/bin/env python3
"""
Comparaison F1 / accord inter-juges — Pipeline actuel vs Juge Sémantique Global
=================================================================================
Phase 5 (simplifiée) de la proposition d'itération (cf. `projetLLMjuge/
ECG_online_proposition_iteration_juge_global_2026-08-02.md` §10).

⚠️ IMPORTANT — statut du gold utilisé ici :
Le corpus `projetLLMjuge/ECG_online_corpus_cible_100_reponses_2026-08-02.jsonl`
contient des `correct_elements`/`problematic_elements` en **texte libre**, pas
encore d'`ontology_id` annotés par un cardiologue (Phase 1 du plan — double
annotation + adjudication — n'est PAS encore faite). Ce script projette donc
les `correct_elements` vers des ontology_id via un lookup fuzzy
(`scoring_v3.find_owl_concept`), à titre de **gold provisoire, non validé
cliniquement**. Les métriques F1 produites ici sont donc INDICATIVES, pas un
résultat final citable — cf. §7 de la proposition ("double annotation
recommandée").

Ce script compare volontairement la capacité d'EXTRACTION des deux méthodes
(precision / recall / F1 / accord inter-méthodes), PAS la note finale (qui est
déterministe et calibrable séparément par scoring_v3, donc pas discriminante
pour juger la qualité d'un juge sémantique).

Usage :
    python scripts/compare_judges_extraction.py --limit 10
    python scripts/compare_judges_extraction.py --strata EXPLICIT,CONTRADICTORY
    python scripts/compare_judges_extraction.py --out rapport_comparaison.json

Auteur : BMad Team
Date   : 2026-08-02
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

# Windows console : forcer UTF-8 en sortie pour les emojis des logs/prints.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from ner_extractor import extract_clinical_terms
from hybrid_search import HybridSearchEngine
from neurosymbolic_judge import resolve_term_to_ontology
from global_semantic_judge import judge_global, build_candidate_catalog
from global_semantic_schema import extract_found_concept_ids
from scoring_v3 import find_owl_concept
from semantic_layer import normalize_key

logger = logging.getLogger(__name__)

CORPUS_PATH = (
    Path(__file__).parent.parent.parent
    / "projetLLMjuge"
    / "ECG_online_corpus_cible_100_reponses_2026-08-02.jsonl"
)


# ---------------------------------------------------------------------------
# Chargement du corpus + projection du gold provisoire
# ---------------------------------------------------------------------------

def load_corpus(path: Path = CORPUS_PATH) -> List[Dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def project_gold_ids(correct_elements: List[str]) -> Set[str]:
    """
    Projette une liste de libellés texte-libre vers des ontology_id via le
    lookup fuzzy existant (find_owl_concept). GOLD PROVISOIRE — cf. avertissement
    en tête de fichier : à remplacer par une vraie annotation experte (Phase 1).
    """
    ids = set()
    for label in correct_elements:
        c = find_owl_concept(label)
        if c and c.get("ontology_id"):
            ids.add(normalize_key(c["ontology_id"]))
    return ids


# ---------------------------------------------------------------------------
# Extraction — Pipeline actuel (Briques 2+3+4)
# ---------------------------------------------------------------------------

_engine: Optional[HybridSearchEngine] = None


def _get_engine() -> HybridSearchEngine:
    global _engine
    if _engine is None:
        _engine = HybridSearchEngine()
    return _engine


def extract_current_pipeline(texte: str) -> Set[str]:
    """
    Reproduit Briques 2→4 (NER → recherche hybride → juge local) et retourne
    l'ensemble des ontology_id en statut 'present' — SANS passer par le
    scoring V3 (on compare l'extraction, pas la note, cf. demande explicite).
    """
    engine = _get_engine()
    extraction = extract_clinical_terms(texte)
    found: Set[str] = set()
    for entite in extraction.entites:
        if entite.statut != "present":
            continue
        candidats = engine.search_top_k(entite.terme_brut)
        resolution = resolve_term_to_ontology(
            entite.terme_brut, entite.contexte_phrase, candidats
        )
        if resolution["ontology_id"] != "NONE":
            found.add(normalize_key(resolution["ontology_id"]))
    return found


def extract_global_judge(texte: str, golden_ids: List[str]) -> Set[str]:
    """Appelle le juge global et projette sa sortie vers un set d'ontology_id 'present'."""
    catalog = build_candidate_catalog(texte, golden_ids)
    report = judge_global(texte, golden_ids=golden_ids, catalog=catalog)
    ids = extract_found_concept_ids(report, include_polarities=("present",))
    return {normalize_key(i) for i in ids}


# ---------------------------------------------------------------------------
# Métriques
# ---------------------------------------------------------------------------

def prf1(predicted: Set[str], gold: Set[str]) -> Tuple[float, float, float, int, int, int]:
    """Precision, recall, F1 micro pour un seul item (TP/FP/FN comptés)."""
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, tp, fp, fn


def cohen_kappa_binary(pairs: List[Tuple[bool, bool]]) -> float:
    """
    Cohen's kappa sur une série de décisions binaires appariées
    (ex: "le concept X est-il présent ?" jugé par méthode A vs méthode B,
    pour chaque (item, concept) observé par au moins une des deux méthodes).
    """
    if not pairs:
        return 0.0
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    p_a_true = sum(1 for a, _ in pairs if a) / n
    p_b_true = sum(1 for _, b in pairs if b) / n
    pe = p_a_true * p_b_true + (1 - p_a_true) * (1 - p_b_true)
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def run_comparison(
    items: List[Dict],
    limit: Optional[int] = None,
    strata: Optional[List[str]] = None,
) -> Dict:
    if strata:
        items = [it for it in items if it["stratum_code"] in strata]
    if limit:
        items = items[:limit]

    per_item = []
    agg_current = {"tp": 0, "fp": 0, "fn": 0}
    agg_global = {"tp": 0, "fp": 0, "fn": 0}
    kappa_pairs: List[Tuple[bool, bool]] = []

    for i, item in enumerate(items, 1):
        texte = item["response"]
        gold_labels = item["expected"].get("correct_elements", [])
        gold_ids = project_gold_ids(gold_labels)

        t0 = time.time()
        try:
            current_ids = extract_current_pipeline(texte)
        except Exception as e:
            logger.error(f"[{item['id']}] Erreur pipeline actuel : {e}")
            current_ids = set()
        t_current = time.time() - t0

        t0 = time.time()
        try:
            global_ids = extract_global_judge(texte, list(gold_ids))
        except Exception as e:
            logger.error(f"[{item['id']}] Erreur juge global : {e}")
            global_ids = set()
        t_global = time.time() - t0

        p_c, r_c, f1_c, tp_c, fp_c, fn_c = prf1(current_ids, gold_ids)
        p_g, r_g, f1_g, tp_g, fp_g, fn_g = prf1(global_ids, gold_ids)

        agg_current["tp"] += tp_c
        agg_current["fp"] += fp_c
        agg_current["fn"] += fn_c
        agg_global["tp"] += tp_g
        agg_global["fp"] += fp_g
        agg_global["fn"] += fn_g

        # Accord inter-méthodes (indépendant du gold) : sur l'union des
        # concepts vus par au moins une méthode, les deux sont-elles d'accord ?
        union_concepts = current_ids | global_ids | gold_ids
        for cid in union_concepts:
            kappa_pairs.append((cid in current_ids, cid in global_ids))

        per_item.append(
            {
                "id": item["id"],
                "stratum_code": item["stratum_code"],
                "gold_ids_provisoires": sorted(gold_ids),
                "current_pipeline": {
                    "found_ids": sorted(current_ids),
                    "precision": round(p_c, 3),
                    "recall": round(r_c, 3),
                    "f1": round(f1_c, 3),
                    "latency_s": round(t_current, 2),
                },
                "global_judge": {
                    "found_ids": sorted(global_ids),
                    "precision": round(p_g, 3),
                    "recall": round(r_g, 3),
                    "f1": round(f1_g, 3),
                    "latency_s": round(t_global, 2),
                },
            }
        )

        logger.info(
            f"[{i}/{len(items)}] {item['id']} ({item['stratum_code']}) — "
            f"actuel F1={f1_c:.2f} | global F1={f1_g:.2f}"
        )

    def micro(agg):
        tp, fp, fn = agg["tp"], agg["fp"], agg["fn"]
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3), "tp": tp, "fp": fp, "fn": fn}

    return {
        "n_items": len(items),
        "gold_status": "PROVISOIRE — projection fuzzy des correct_elements, pas encore d'annotation experte (Phase 1 non faite)",
        "current_pipeline_micro": micro(agg_current),
        "global_judge_micro": micro(agg_global),
        "inter_method_cohen_kappa": round(cohen_kappa_binary(kappa_pairs), 3),
        "per_item": per_item,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre d'items testés.")
    parser.add_argument("--strata", type=str, default=None, help="Filtrer par stratum_code, séparés par des virgules.")
    parser.add_argument("--out", type=str, default=None, help="Chemin du rapport JSON de sortie.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    items = load_corpus()
    strata = args.strata.split(",") if args.strata else None
    result = run_comparison(items, limit=args.limit, strata=strata)

    print("\n" + "=" * 70)
    print("📊 COMPARAISON EXTRACTION — Pipeline actuel vs Juge Sémantique Global")
    print("=" * 70)
    print(f"⚠️  {result['gold_status']}\n")
    print(f"N items testés : {result['n_items']}\n")
    print("Pipeline actuel (Briques 2-4) :")
    print(f"  P={result['current_pipeline_micro']['precision']:.1%}  "
          f"R={result['current_pipeline_micro']['recall']:.1%}  "
          f"F1={result['current_pipeline_micro']['f1']:.1%}")
    print("Juge sémantique global :")
    print(f"  P={result['global_judge_micro']['precision']:.1%}  "
          f"R={result['global_judge_micro']['recall']:.1%}  "
          f"F1={result['global_judge_micro']['f1']:.1%}")
    print(f"\nAccord inter-méthodes (Cohen's kappa) : {result['inter_method_cohen_kappa']}")
    print("=" * 70)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Rapport complet écrit dans : {args.out}")


if __name__ == "__main__":
    main()
