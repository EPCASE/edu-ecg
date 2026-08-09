#!/usr/bin/env python
"""
rerun_extraction_golden_pipeline.py — Rejoue le pipeline actuel (post-modifs
ontologie) sur les 100 réponses du golden d'extraction, et recalcule P/R/F1
contre l'annotation experte figée (vérité terrain, indépendante de
l'ontologie).

Contexte : `pipeline_extraction` dans data/extraction_golden.json est un
INSTANTANÉ GELÉ au moment de la construction de l'échantillon
(build_extraction_golden_sample.py). Après une modification de l'ontologie
(nouveaux concepts, dédup de synonymes, revert de fusion, etc.), ce champ est
obsolète — ce script le régénère en rejouant candidate_report.generate_
candidate_report() sur chaque item, SANS toucher à annotation_expert.

Usage (depuis la racine "ECG lecture") :
    python outil_ontologie/scripts/rerun_extraction_golden_pipeline.py
    python outil_ontologie/scripts/rerun_extraction_golden_pipeline.py --limit 10
    python outil_ontologie/scripts/rerun_extraction_golden_pipeline.py --write-back
    python outil_ontologie/scripts/rerun_extraction_golden_pipeline.py --out rapport.json

Par défaut, N'ÉCRIT PAS dans extraction_golden.json (dry-run, compare juste
les métriques). Utiliser --write-back pour persister la nouvelle
pipeline_extraction (recommandé après validation manuelle du rapport).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]  # ECG lecture/
ECG_ONLINE = ROOT / "ecg-online"

# On utilise le moteur SOURCE (rag_pipeline/ à la racine), déjà mis à jour
# avec l'ontologie modifiée, plutôt que la copie vendorée d'ecg-online.
ENGINE_DIR = ROOT / "rag_pipeline"

sys.path.insert(0, str(ECG_ONLINE))
sys.path.insert(0, str(ENGINE_DIR))

# Charger .env de ecg-online pour la clé OpenAI
try:
    from dotenv import load_dotenv
    load_dotenv(ECG_ONLINE / ".env")
except ImportError:
    pass

from app import extraction_golden, golden_config  # noqa: E402
from candidate_report import generate_candidate_report  # noqa: E402
from scoring_v3 import build_negation_map  # noqa: E402

ConceptKey = Tuple[str, str]  # (ontology_id, statut)

# Mapping absent(pathologie) -> concept de normalité positif, ex:
# absent(TROUBLE_DE_REPOLARISATION) -> PAS_D_ANOMALIE_DE_LE_REPOLARISATION.
# Permet de réconcilier deux formulations synonymes ("pas de trouble de la
# repolarisation" vs "repolarisation normale") qui se résolvent sur des
# concepts ontologiques différents à l'extraction, mais représentent la même
# réalité clinique. Sans cette normalisation, ces items comptent à tort comme
# FP (le concept absent) + FN (le concept positif attendu manquant).
_NEG_MAP = build_negation_map()


def _normalize_key(oid: str, statut: str) -> ConceptKey:
    """Convertit (oid, 'absent') en (concept_positif, 'present') si un mapping
    de négation existe pour ce concept, sinon renvoie la clé telle quelle."""
    if statut == "absent" and oid in _NEG_MAP:
        return (_NEG_MAP[oid], "present")
    return (oid, statut)


def _pipeline_set_with_method(concepts: List[dict]) -> Dict[ConceptKey, str]:
    out = {}
    for c in concepts:
        oid = c.get("ontology_id")
        statut = c.get("statut", "present")
        if oid:
            out[_normalize_key(oid, statut)] = c.get("method", "?")
    return out


def _expert_set(annotation: dict) -> Set[ConceptKey]:
    if not annotation:
        return set()
    out = set()
    for c in annotation.get("concepts", []) or []:
        oid = c.get("ontology_id")
        statut = c.get("statut", "present")
        if oid:
            out.add(_normalize_key(oid, statut))
    return out


def rerun_pipeline_on_item(cas: int, texte: str) -> List[dict]:
    """Rejoue le pipeline actuel sur un item, renvoie la liste de concepts
    au même format que pipeline_extraction. [] en cas d'erreur (dégradation
    propre, l'item compte alors comme 0 extraction pour ce run)."""
    try:
        contract = golden_config.golden_for_scorer(cas)
        all_pts = contract.get("validants", []) + contract.get("descripteurs", [])
        golden_ids = [p["concept_id"] for p in all_pts]
        golden_names = [p["concept_name"] for p in all_pts]
        golden_roles = ["validant"] * len(contract.get("validants", [])) + \
            ["descripteur"] * len(contract.get("descripteurs", []))
        report = generate_candidate_report(
            texte,
            golden_names=golden_names,
            golden_ids=golden_ids,
            golden_roles=golden_roles,
            diagnostic_principal=contract.get("diagnostic_principal", ""),
            with_feedback=False,
        )
        out = []
        for c in getattr(report, "concepts_extraits", []) or []:
            out.append({
                "terme_brut": getattr(c, "terme_brut", ""),
                "ontology_id": getattr(c, "ontology_id", ""),
                "concept_name": getattr(c, "concept_name", ""),
                "statut": getattr(c, "statut", "present"),
                "method": getattr(c, "method", ""),
            })
        return out
    except Exception as ex:  # noqa: BLE001
        print(f"  ⚠️  Erreur pipeline (cas {cas}): {ex}", file=sys.stderr)
        return []


def compute_confusion(new_pipeline: Dict[str, List[dict]], items: Dict[str, dict]) -> dict:
    tp_total = fp_total = fn_total = 0
    by_method = defaultdict(lambda: {"tp": 0, "fp": 0})
    fp_examples: List[dict] = []
    fn_examples: List[dict] = []
    n_used = 0

    for item_id, item in sorted(items.items()):
        annotation = item.get("annotation_expert")
        if not annotation:
            continue
        n_used += 1
        pipeline = _pipeline_set_with_method(new_pipeline.get(item_id, []))
        expert = _expert_set(annotation)

        for key, method in pipeline.items():
            if key in expert:
                tp_total += 1
                by_method[method]["tp"] += 1
            else:
                fp_total += 1
                by_method[method]["fp"] += 1
                fp_examples.append({"item_id": item_id, "ontology_id": key[0],
                                     "statut": key[1], "method": method})

        pipeline_keys = set(pipeline.keys())
        for key in expert:
            if key not in pipeline_keys:
                fn_total += 1
                fn_examples.append({"item_id": item_id, "ontology_id": key[0],
                                     "statut": key[1]})

    def _prf(tp, fp, fn):
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision and recall and (precision + recall) else None)
        return {"tp": tp, "fp": fp, "fn": fn, "precision": precision,
                "recall": recall, "f1": f1}

    per_method = {}
    for method, counts in by_method.items():
        tp, fp = counts["tp"], counts["fp"]
        precision = tp / (tp + fp) if (tp + fp) else None
        per_method[method] = {"tp": tp, "fp": fp, "precision": precision}

    return {
        "n_items_used": n_used,
        "global": _prf(tp_total, fp_total, fn_total),
        "per_method": per_method,
        "fp_examples": fp_examples,
        "fn_examples": fn_examples,
    }


def _fmt_pct(x):
    return f"{x * 100:.1f}%" if isinstance(x, (int, float)) else "n/a"


def print_report(confusion_old: dict, confusion_new: dict) -> None:
    print("=" * 78)
    print("RE-TEST GOLDEN D'EXTRACTION APRÈS MODIFICATIONS ONTOLOGIE")
    print("=" * 78)
    for label, c in (("AVANT (figé dans extraction_golden.json)", confusion_old),
                     ("APRÈS (pipeline rejoué maintenant)", confusion_new)):
        g = c["global"]
        print(f"\n--- {label} ---")
        print(f"  Items utilisés : {c['n_items_used']}")
        print(f"  TP={g['tp']}  FP={g['fp']}  FN={g['fn']}")
        print(f"  Précision : {_fmt_pct(g['precision'])}")
        print(f"  Rappel    : {_fmt_pct(g['recall'])}")
        print(f"  F1        : {_fmt_pct(g['f1'])}")

    print("\n" + "-" * 78)
    print("Delta (après - avant)")
    print("-" * 78)
    go, gn = confusion_old["global"], confusion_new["global"]
    for k in ("tp", "fp", "fn"):
        print(f"  {k.upper()}: {go[k]} -> {gn[k]}  (Δ {gn[k]-go[k]:+d})")
    if go["precision"] and gn["precision"]:
        print(f"  Précision: {_fmt_pct(go['precision'])} -> {_fmt_pct(gn['precision'])}")
    if go["recall"] and gn["recall"]:
        print(f"  Rappel: {_fmt_pct(go['recall'])} -> {_fmt_pct(gn['recall'])}")
    if go["f1"] and gn["f1"]:
        print(f"  F1: {_fmt_pct(go['f1'])} -> {_fmt_pct(gn['f1'])}")
    print("=" * 78)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None,
                     help="Limiter le nombre d'items rejoués (test rapide).")
    ap.add_argument("--write-back", action="store_true",
                     help="Écrit la nouvelle pipeline_extraction dans extraction_golden.json.")
    ap.add_argument("--out", type=Path, default=None,
                     help="Chemin JSON détaillé du rapport avant/après.")
    args = ap.parse_args()

    data = extraction_golden.load()
    items = data["items"]

    # Rejeu du pipeline sur chaque item annoté
    item_ids = [iid for iid, it in sorted(items.items()) if it.get("annotation_expert")]
    if args.limit:
        item_ids = item_ids[:args.limit]

    # Restreint la comparaison aux items effectivement rejoués (fair compare
    # en mode --limit : sinon les items non rejoués comptent comme FN massifs).
    items_subset = {iid: items[iid] for iid in item_ids}

    # Confusion AVANT (pipeline_extraction déjà figé dans le fichier), sur le même sous-ensemble
    old_pipeline = {item_id: items[item_id].get("pipeline_extraction", []) or []
                     for item_id in item_ids}
    confusion_old = compute_confusion(old_pipeline, items_subset)

    print(f"🔄 Rejeu du pipeline sur {len(item_ids)} items annotés...")
    new_pipeline: Dict[str, List[dict]] = {}
    for i, item_id in enumerate(item_ids, 1):
        item = items[item_id]
        print(f"  [{i}/{len(item_ids)}] {item_id} (cas {item['cas']})...", end=" ")
        extracted = rerun_pipeline_on_item(item["cas"], item["reponse_texte"])
        new_pipeline[item_id] = extracted
        print(f"{len(extracted)} concepts")

    confusion_new = compute_confusion(new_pipeline, items_subset)
    print_report(confusion_old, confusion_new)

    if args.out:
        report = {"before": confusion_old, "after": confusion_new}
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📄 Rapport détaillé écrit dans {args.out}")

    if args.write_back:
        if args.limit:
            print("\n⚠️  --write-back ignoré car --limit est utilisé (run partiel). "
                  "Relancer sans --limit pour persister.", file=sys.stderr)
        else:
            for item_id, extracted in new_pipeline.items():
                items[item_id]["pipeline_extraction"] = extracted
            extraction_golden.save(data)
            print(f"\n✅ pipeline_extraction mis à jour dans "
                  f"{extraction_golden.EXTRACTION_GOLDEN_PATH}")


if __name__ == "__main__":
    main()
