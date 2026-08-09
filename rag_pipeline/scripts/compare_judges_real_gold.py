#!/usr/bin/env python3
"""
Comparaison Pipeline actuel vs Juge Sémantique Global — sur le VRAI golden d'extraction
=========================================================================================
Contrairement à `compare_judges_extraction.py` (qui tourne sur le corpus
synthétique `projetLLMjuge/...100_reponses...jsonl` avec un gold PROVISOIRE
projeté par fuzzy-matching), ce script utilise le golden d'extraction RÉEL :

    ecg-online/data/extraction_golden.json

100 réponses réelles d'étudiants, annotées par un expert humain (100/100
annotées, 20/100 en double annotation). Cf. `ecg-online/GOLDEN_EXTRACTION.md`.

Pour le pipeline actuel, on réutilise directement `pipeline_extraction` déjà
figé dans le fichier golden (résultat gelé au moment de la construction de
l'échantillon, déjà validé/corrigé par l'expert comme référence de ce qui a
été produit) — pas besoin de rejouer le pipeline. On ne rejoue EN LIVE que le
juge sémantique global (nouveau composant à évaluer).

Métriques présentées en priorité sous forme de comptes bruts et de taux
intuitifs, à la demande explicite de l'utilisateur (le F1 est fourni en
complément, pas en tête) :
  - TP / FP / FN (comptes bruts)
  - Taux de Faux Positifs ("Miss Rate inversé") = FP / (TP + FP)
    → "sur tout ce que la méthode a proposé, quelle proportion était fausse ?"
  - Taux d'Omission (= 1 - rappel) = FN / (TP + FN)
    → "sur tout ce qu'il fallait trouver, quelle proportion a été manquée ?"
  - Precision / Recall / F1 (secondaire)

Usage :
    python scripts/compare_judges_real_gold.py --limit 10
    python scripts/compare_judges_real_gold.py --out rapport_gold_reel.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from global_semantic_judge import judge_global, build_candidate_catalog
from global_semantic_schema import extract_found_concept_ids
from semantic_layer import normalize_key

logger = logging.getLogger(__name__)

GOLDEN_PATH = (
    Path(__file__).parent.parent.parent
    / "ecg-online"
    / "data"
    / "extraction_golden.json"
)


# ---------------------------------------------------------------------------
# Chargement du golden réel
# ---------------------------------------------------------------------------

def load_golden(path: Path = GOLDEN_PATH) -> Dict[str, dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]


def gold_ids_present(item: dict) -> Set[str]:
    """Concepts annotés par l'expert avec statut 'present' (vérité de terrain)."""
    annotation = item.get("annotation_expert")
    if not annotation:
        return set()
    ids = set()
    for c in annotation.get("concepts", []) or []:
        if c.get("statut", "present") == "present" and c.get("ontology_id"):
            ids.add(normalize_key(c["ontology_id"]))
    return ids


def pipeline_ids_present(item: dict) -> Set[str]:
    """Sortie du pipeline actuel, déjà figée dans le golden (statut 'present')."""
    ids = set()
    for c in item.get("pipeline_extraction", []) or []:
        if c.get("statut", "present") == "present" and c.get("ontology_id"):
            ids.add(normalize_key(c["ontology_id"]))
    return ids


# ---------------------------------------------------------------------------
# Juge global — appel en direct (seul composant rejoué en live)
# ---------------------------------------------------------------------------

def extract_global_judge(texte: str, golden_ids: List[str]) -> Set[str]:
    catalog = build_candidate_catalog(texte, golden_ids)
    report = judge_global(texte, golden_ids=golden_ids, catalog=catalog)
    ids = extract_found_concept_ids(report, include_polarities=("present",))
    return {normalize_key(i) for i in ids}


# ---------------------------------------------------------------------------
# Métriques
# ---------------------------------------------------------------------------

def confusion(predicted: Set[str], gold: Set[str]) -> Dict[str, int]:
    return {
        "tp": len(predicted & gold),
        "fp": len(predicted - gold),
        "fn": len(gold - predicted),
    }


def rates(agg: Dict[str, int]) -> Dict[str, Optional[float]]:
    tp, fp, fn = agg["tp"], agg["fp"], agg["fn"]
    fp_rate = fp / (tp + fp) if (tp + fp) else None      # = 1 - precision
    fn_rate = fn / (tp + fn) if (tp + fn) else None       # = 1 - recall (taux d'omission)
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall and (precision + recall) else None)
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "taux_faux_positifs": round(fp_rate, 3) if fp_rate is not None else None,
        "taux_omission": round(fn_rate, 3) if fn_rate is not None else None,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "f1": round(f1, 3) if f1 is not None else None,
    }


def cohen_kappa_binary(pairs: List[Tuple[bool, bool]]) -> float:
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

def run_comparison(items: Dict[str, dict], limit: Optional[int] = None) -> Dict:
    item_ids = sorted(items.keys())
    if limit:
        item_ids = item_ids[:limit]

    per_item = []
    agg_current = {"tp": 0, "fp": 0, "fn": 0}
    agg_global = {"tp": 0, "fp": 0, "fn": 0}
    kappa_pairs: List[Tuple[bool, bool]] = []

    for i, item_id in enumerate(item_ids, 1):
        item = items[item_id]
        texte = item["reponse_texte"]
        gold_ids = gold_ids_present(item)
        current_ids = pipeline_ids_present(item)  # déjà figé, pas de rejeu

        t0 = time.time()
        try:
            global_ids = extract_global_judge(texte, list(gold_ids))
        except Exception as e:
            logger.error(f"[{item_id}] Erreur juge global : {e}")
            global_ids = set()
        t_global = time.time() - t0

        c_current = confusion(current_ids, gold_ids)
        c_global = confusion(global_ids, gold_ids)

        for k in ("tp", "fp", "fn"):
            agg_current[k] += c_current[k]
            agg_global[k] += c_global[k]

        union_concepts = current_ids | global_ids | gold_ids
        for cid in union_concepts:
            kappa_pairs.append((cid in current_ids, cid in global_ids))

        per_item.append({
            "id": item_id,
            "cas": item.get("cas"),
            "double_annotation": item.get("double_annotation", False),
            "gold_ids": sorted(gold_ids),
            "current_pipeline": {"found_ids": sorted(current_ids), **rates(
                {"tp": c_current["tp"], "fp": c_current["fp"], "fn": c_current["fn"]})},
            "global_judge": {"found_ids": sorted(global_ids), "latency_s": round(t_global, 2),
                              **rates({"tp": c_global["tp"], "fp": c_global["fp"], "fn": c_global["fn"]})},
        })

        logger.info(
            f"[{i}/{len(item_ids)}] {item_id} — "
            f"actuel FP={c_current['fp']} FN={c_current['fn']} | "
            f"global FP={c_global['fp']} FN={c_global['fn']}"
        )

    return {
        "n_items": len(item_ids),
        "gold_status": "RÉEL — golden d'extraction officiel (100 réponses étudiantes réelles, "
                        "annotation experte humaine, cf. ecg-online/GOLDEN_EXTRACTION.md)",
        "current_pipeline_micro": rates(agg_current),
        "global_judge_micro": rates(agg_global),
        "inter_method_cohen_kappa": round(cohen_kappa_binary(kappa_pairs), 3),
        "per_item": per_item,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    items = load_golden()
    result = run_comparison(items, limit=args.limit)

    def fmt(m):
        fp_r = m["taux_faux_positifs"]
        fn_r = m["taux_omission"]
        return (
            f"  TP={m['tp']:<4} FP={m['fp']:<4} FN={m['fn']:<4}  |  "
            f"Taux de FP={fp_r:.1%}  Taux d'omission={fn_r:.1%}  |  "
            f"(P={m['precision']:.1%} R={m['recall']:.1%} F1={m['f1']:.1%})"
        )

    print("\n" + "=" * 78)
    print("📊 COMPARAISON EXTRACTION — VRAI golden (100 réponses réelles annotées)")
    print("=" * 78)
    print(f"✅ {result['gold_status']}\n")
    print(f"N items testés : {result['n_items']}\n")
    print("Pipeline actuel (Briques 2-4, sortie figée dans le golden) :")
    print(fmt(result["current_pipeline_micro"]))
    print("\nJuge sémantique global (rejoué en direct) :")
    print(fmt(result["global_judge_micro"]))
    print(f"\nAccord inter-méthodes (Cohen's kappa) : {result['inter_method_cohen_kappa']}")
    print("=" * 78)
    print("\nLecture : « Taux de FP » = parmi ce que la méthode a proposé, quelle part était fausse (hallucination).")
    print("          « Taux d'omission » = parmi ce qu'il fallait trouver, quelle part a été manquée.")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Rapport complet écrit dans : {args.out}")


if __name__ == "__main__":
    main()
