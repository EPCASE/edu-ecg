#!/usr/bin/env python3
"""
Prototype "Hybride Arbitre" — Coupe-circuit conservé + Juge Global en second
lecteur CIBLÉ (catalogue restreint aux concepts non déjà tranchés)
=============================================================================
Contrairement aux simulations offline précédentes (recombinaison de données
déjà collectées), ce script effectue de VRAIS appels au juge global, mais en
lui retirant du catalogue les concepts déjà validés par coupe-circuit — pour
l'empêcher de réintroduire des faux positifs sur des zones déjà tranchées
(le problème observé dans la variante "UNION" testée précédemment).

Architecture testée :
  1. Pipeline actuel (Briques 2-4) tourne normalement → on note SÉPARÉMENT
     les concepts validés par coupe-circuit (`coupe_circuit_ids`, gardés tels
     quels, non remis en cause) et les concepts validés par les méthodes de
     repli faibles (`weak_ids` — juge_llm/lexical_backstop/fallback_subterm/
     pattern_inference).
  2. Le juge global est appelé sur le TEXTE COMPLET avec le CATALOGUE COMPLET
     (garde tout son contexte et toutes ses options — un catalogue restreint
     forcerait le juge à halluciner sur un concept voisin si le bon concept
     est absent, bug identifié lors du premier essai). Le filtrage se fait
     en SORTIE : on ignore les claims qui portent sur un concept déjà
     validé par coupe-circuit (pas de double-compte, pas de remise en cause
     d'une décision déjà fiable à 96.5% de précision).
  3. Résultat final hybride = coupe_circuit_ids ∪ (claims du juge global qui
     ne portent PAS sur un concept déjà dans coupe_circuit_ids).

Testé sur DEUX golds :
  - Le gold RÉEL (`ecg-online/data/extraction_golden.json`, 100 réponses
    étudiantes réelles annotées par un expert).
  - Le gold VIRTUEL/synthétique (`projetLLMjuge/ECG_online_corpus_cible_
    100_reponses_2026-08-02.jsonl`, 100 items ciblant 10 phénomènes rares,
    gold provisoire par projection fuzzy — cf. avertissement dans
    compare_judges_extraction.py).

Usage :
    python scripts/compare_hybrid_arbiter.py --gold real --limit 10
    python scripts/compare_hybrid_arbiter.py --gold synthetic --limit 10
    python scripts/compare_hybrid_arbiter.py --gold both --out rapport_hybride.json
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

from ner_extractor import extract_clinical_terms
from hybrid_search import HybridSearchEngine
from neurosymbolic_judge import resolve_term_to_ontology
from global_semantic_judge import judge_global, build_candidate_catalog
from global_semantic_schema import extract_found_concept_ids
from scoring_v3 import find_owl_concept
from semantic_layer import normalize_key, get_concept

logger = logging.getLogger(__name__)

REAL_GOLD_PATH = (
    Path(__file__).parent.parent.parent / "ecg-online" / "data" / "extraction_golden.json"
)
SYNTHETIC_CORPUS_PATH = (
    Path(__file__).parent.parent.parent
    / "projetLLMjuge"
    / "ECG_online_corpus_cible_100_reponses_2026-08-02.jsonl"
)

WEAK_METHODS = {"juge_llm", "pattern_inference", "lexical_backstop", "fallback_subterm"}


# ---------------------------------------------------------------------------
# Chargement des deux golds sous un format unifié
# ---------------------------------------------------------------------------

def load_real_gold() -> List[Dict]:
    """Retourne une liste unifiée {id, texte, gold_ids, coupe_circuit_ids}."""
    with open(REAL_GOLD_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for item_id, item in sorted(data["items"].items()):
        annotation = item.get("annotation_expert")
        if not annotation:
            continue
        gold_ids = {
            normalize_key(c["ontology_id"])
            for c in annotation.get("concepts", []) or []
            if c.get("statut", "present") == "present" and c.get("ontology_id")
        }
        coupe_circuit_ids = {
            normalize_key(c["ontology_id"])
            for c in item.get("pipeline_extraction", []) or []
            if c.get("statut", "present") == "present"
            and c.get("method") == "coupe_circuit"
            and c.get("ontology_id")
        }
        full_pipeline_ids = {
            normalize_key(c["ontology_id"])
            for c in item.get("pipeline_extraction", []) or []
            if c.get("statut", "present") == "present" and c.get("ontology_id")
        }
        items.append(
            {
                "id": item_id,
                "texte": item["reponse_texte"],
                "gold_ids": gold_ids,
                "coupe_circuit_ids": coupe_circuit_ids,
                "full_pipeline_ids": full_pipeline_ids,
            }
        )
    return items


def project_gold_label(label: str) -> Optional[str]:
    """
    Projette un label texte-libre vers un ontology_id RÉEL, en rejetant
    explicitement le fallback fantôme de `find_owl_concept()` (qui invente
    un ontology_id à partir du texte brut quand aucun concept réel n'est
    trouvé, cf. `scoring_v3.py` L144-149 — bug identifié le 2026-08-02,
    responsable de ~48% d'IDs fantômes dans une première tentative de
    projection du gold synthétique).

    Ne retourne un ID que si `get_concept()` le reconnaît réellement dans
    l'ontologie V2 chargée (source de vérité unique) — sinon retourne None
    (le label est alors ignoré du gold plutôt que de polluer la mesure avec
    un concept qui n'existe nulle part).
    """
    c = find_owl_concept(label)
    if not c or not c.get("ontology_id"):
        return None
    oid = normalize_key(c["ontology_id"])
    if get_concept(oid) is None:
        return None  # fallback fantôme détecté et rejeté
    return oid


def load_synthetic_corpus() -> List[Dict]:
    """Retourne une liste unifiée {id, texte, gold_ids, coupe_circuit_ids}.

    Le gold est projeté par fuzzy-matching (PROVISOIRE, cf. avertissement),
    mais désormais filtré : seuls les labels qui matchent un concept RÉEL de
    l'ontologie (vérifié via `get_concept()`) sont retenus dans `gold_ids` —
    les IDs fantômes générés par le fallback de `find_owl_concept()` sont
    silencieusement ignorés (comptés séparément dans `n_labels_rejected`
    pour transparence).
    `coupe_circuit_ids` est calculé en rejouant le pipeline pour ce corpus
    (pas déjà figé comme pour le golden réel).
    """
    items = []
    n_labels_total = 0
    n_labels_rejected = 0
    with open(SYNTHETIC_CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            gold_labels = raw["expected"].get("correct_elements", [])
            gold_ids = set()
            for label in gold_labels:
                n_labels_total += 1
                oid = project_gold_label(label)
                if oid is not None:
                    gold_ids.add(oid)
                else:
                    n_labels_rejected += 1
                    logger.debug(f"  Label rejeté (pas de concept réel) : '{label}'")
            items.append(
                {
                    "id": raw["id"],
                    "stratum_code": raw.get("stratum_code"),
                    "texte": raw["response"],
                    "gold_ids": gold_ids,
                    "coupe_circuit_ids": None,  # calculé à la volée dans run_item
                    "full_pipeline_ids": None,  # calculé à la volée dans run_item
                }
            )
    if n_labels_total:
        logger.warning(
            f"Projection gold synthétique : {n_labels_rejected}/{n_labels_total} "
            f"labels rejetés ({n_labels_rejected/n_labels_total:.1%}) — "
            f"aucun concept réel trouvé dans l'ontologie."
        )
    return items


# ---------------------------------------------------------------------------
# Extraction — pipeline actuel (pour recalculer coupe_circuit_ids en live,
# nécessaire pour le corpus synthétique qui n'a pas de pipeline_extraction figé)
# ---------------------------------------------------------------------------

_engine: Optional[HybridSearchEngine] = None


def _get_engine() -> HybridSearchEngine:
    global _engine
    if _engine is None:
        _engine = HybridSearchEngine()
    return _engine


def extract_current_pipeline_with_methods(texte: str) -> Tuple[Set[str], Set[str]]:
    """
    Rejoue Briques 2-4 et retourne (coupe_circuit_ids, weak_method_ids)
    séparément, selon la méthode de résolution utilisée par chaque entité.
    """
    engine = _get_engine()
    extraction = extract_clinical_terms(texte)
    coupe_circuit_ids: Set[str] = set()
    weak_ids: Set[str] = set()
    for entite in extraction.entites:
        if entite.statut != "present":
            continue
        candidats = engine.search_top_k(entite.terme_brut)
        resolution = resolve_term_to_ontology(
            entite.terme_brut, entite.contexte_phrase, candidats
        )
        if resolution["ontology_id"] == "NONE":
            continue
        oid = normalize_key(resolution["ontology_id"])
        if resolution["method"] == "coupe_circuit":
            coupe_circuit_ids.add(oid)
        else:
            weak_ids.add(oid)
    return coupe_circuit_ids, weak_ids


# ---------------------------------------------------------------------------
# Juge global — second lecteur ciblé (catalogue restreint)
# ---------------------------------------------------------------------------

def extract_global_judge_targeted(
    texte: str, golden_ids: List[str], exclude_ids: Set[str]
) -> Tuple[Set[str], List[Dict]]:
    """
    Appelle le juge global sur le texte COMPLET avec le catalogue COMPLET
    (le juge garde toutes ses options, y compris les concepts déjà résolus
    par coupe-circuit — sinon, privé de la bonne réponse, il est forcé de
    halluciner sur un concept voisin restant, cf. bug identifié en v1 de ce
    script : catalogue restreint → FP explosés car PR_NORMAL/QRS_FINS/etc.
    absents forçaient le choix de leurs cousins ontologiques).

    Le filtrage `exclude_ids` s'applique en SORTIE seulement : on ignore les
    claims du juge global qui portent sur un concept déjà validé par
    coupe-circuit (pas de double-compte, pas de risque de contredire une
    décision déjà fiable à 96.5% de précision) — mais le juge reste libre
    de proposer CES MÊMES concepts en interne pour raisonner correctement
    sur le reste du texte (ex: comprendre qu'un concept déjà résolu sert de
    prémisse à une inférence implicite d'un autre concept).

    Retourne (ids_present_hors_coupe_circuit, claims_bruts) — les claims
    bruts (avec expression_mode) sont conservés pour permettre de tester
    offline différentes variantes de filtrage de sortie (ex: restreindre
    aux modes implicit/paraphrased) sans refaire d'appel API.
    """
    catalog = build_candidate_catalog(texte, golden_ids)
    report = judge_global(texte, golden_ids=golden_ids, catalog=catalog)
    claims_raw = [
        {
            "claim_id": c.claim_id,
            "concept_id": normalize_key(c.concept_id),
            "polarity": c.polarity,
            "expression_mode": c.expression_mode,
        }
        for c in report.claims
    ]
    ids = extract_found_concept_ids(report, include_polarities=("present",))
    ids = {normalize_key(i) for i in ids}
    return ids - exclude_ids, claims_raw


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
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall and (precision + recall) else None)
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "taux_faux_positifs": round(fp / (tp + fp), 3) if (tp + fp) else None,
        "taux_omission": round(fn / (tp + fn), 3) if (tp + fn) else None,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "f1": round(f1, 3) if f1 is not None else None,
    }


# ---------------------------------------------------------------------------
# Boucle principale — pour un gold donné
# ---------------------------------------------------------------------------

def run_on_gold(items: List[Dict], gold_name: str, limit: Optional[int] = None) -> Dict:
    if limit:
        items = items[:limit]

    per_item = []
    agg_current_full = {"tp": 0, "fp": 0, "fn": 0}   # coupe_circuit + weak (pipeline actuel complet)
    agg_hybrid = {"tp": 0, "fp": 0, "fn": 0}          # coupe_circuit + juge global ciblé

    for i, item in enumerate(items, 1):
        texte = item["texte"]
        gold_ids = item["gold_ids"]

        if item["coupe_circuit_ids"] is not None:
            coupe_circuit_ids = item["coupe_circuit_ids"]
            current_full_ids = item["full_pipeline_ids"]  # golden réel : déjà figé (coupe_circuit + méthodes faibles)
        else:
            t0 = time.time()
            try:
                coupe_circuit_ids, weak_ids = extract_current_pipeline_with_methods(texte)
            except Exception as e:
                logger.error(f"[{item['id']}] Erreur pipeline actuel : {e}")
                coupe_circuit_ids, weak_ids = set(), set()
            current_full_ids = coupe_circuit_ids | weak_ids
            logger.debug(f"  pipeline actuel en {time.time()-t0:.2f}s")

        t0 = time.time()
        try:
            global_targeted_ids, claims_raw = extract_global_judge_targeted(
                texte, list(gold_ids), exclude_ids=coupe_circuit_ids
            )
        except Exception as e:
            logger.error(f"[{item['id']}] Erreur juge global ciblé : {e}")
            global_targeted_ids, claims_raw = set(), []
        t_global = time.time() - t0

        hybrid_ids = coupe_circuit_ids | global_targeted_ids

        c_current = confusion(current_full_ids, gold_ids)
        c_hybrid = confusion(hybrid_ids, gold_ids)
        for k in ("tp", "fp", "fn"):
            agg_current_full[k] += c_current[k]
            agg_hybrid[k] += c_hybrid[k]

        per_item.append({
            "id": item["id"],
            "gold_ids": sorted(gold_ids),
            "coupe_circuit_ids": sorted(coupe_circuit_ids),
            "global_judge_claims_raw": claims_raw,
            "current_pipeline_full": {"found_ids": sorted(current_full_ids), **rates(c_current)},
            "hybrid_arbiter": {"found_ids": sorted(hybrid_ids), "latency_global_s": round(t_global, 2), **rates(c_hybrid)},
        })

        logger.info(
            f"[{gold_name} {i}/{len(items)}] {item['id']} — "
            f"actuel FP={c_current['fp']} FN={c_current['fn']} | "
            f"hybride FP={c_hybrid['fp']} FN={c_hybrid['fn']}"
        )

    return {
        "gold": gold_name,
        "n_items": len(items),
        "current_pipeline_micro": rates(agg_current_full),
        "hybrid_arbiter_micro": rates(agg_hybrid),
        "per_item": per_item,
    }


def print_report(result: Dict):
    def fmt(m):
        return (
            f"  TP={m['tp']:<4} FP={m['fp']:<4} FN={m['fn']:<4}  |  "
            f"Taux de FP={m['taux_faux_positifs']:.1%}  Taux d'omission={m['taux_omission']:.1%}  |  "
            f"(P={m['precision']:.1%} R={m['recall']:.1%} F1={m['f1']:.1%})"
        )
    print("\n" + "=" * 78)
    print(f"📊 HYBRIDE ARBITRE (second lecteur ciblé) — gold : {result['gold']}")
    print("=" * 78)
    print(f"N items testés : {result['n_items']}\n")
    print("Pipeline actuel complet (coupe_circuit + méthodes de repli) :")
    print(fmt(result["current_pipeline_micro"]))
    print("\nHybride (coupe_circuit + juge global second lecteur ciblé) :")
    print(fmt(result["hybrid_arbiter_micro"]))
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", choices=["real", "synthetic", "both"], default="both")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    results = {}
    if args.gold in ("real", "both"):
        items = load_real_gold()
        results["real"] = run_on_gold(items, "REEL (100 réponses réelles annotées)", limit=args.limit)
        print_report(results["real"])
    if args.gold in ("synthetic", "both"):
        items = load_synthetic_corpus()
        results["synthetic"] = run_on_gold(items, "VIRTUEL (corpus synthétique 10 phénomènes, gold fuzzy provisoire)", limit=args.limit)
        print_report(results["synthetic"])

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Rapport complet écrit dans : {args.out}")


if __name__ == "__main__":
    main()
