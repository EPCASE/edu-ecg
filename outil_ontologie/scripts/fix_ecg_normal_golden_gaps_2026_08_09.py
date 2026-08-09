"""
fix_ecg_normal_golden_gaps_2026_08_09.py
=========================================
Corrige 2 items golden ou` ECG_NORMAL est correctement infere par
pattern_inference (le texte decrit un ECG normal element par element sans
dire "ECG normal" litteralement) mais absent du golden -> ajout.

Items concernes :
  - 1-02  : "Rythme sinusal regulier, QRS fins, normo-axes, pas de trouble de
            la repolarisation ni sequelle d'ischemie, QTc normal" -> ECG normal
  - 23-04 : "rythme sinusal, axe normal, pas de trouble de la repolarisation"
            -> ECG normal (implicite, tous les criteres requis presents)

Usage : python fix_ecg_normal_golden_gaps_2026_08_09.py [--apply]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "ecg-online" / "data" / "extraction_golden.json"

ADD_ECG_NORMAL = ["1-02", "23-04"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    items = data["items"]

    for iid in ADD_ECG_NORMAL:
        it = items[iid]
        concepts = it["annotation_expert"]["concepts"]
        if any(c.get("ontology_id") == "ECG_NORMAL" for c in concepts):
            print(f"  ⏭️  {iid}: ECG_NORMAL deja present, skip")
            continue
        concepts.append({
            "ontology_id": "ECG_NORMAL",
            "concept_name": "ECG normal",
            "statut": "present",
            "source": "reannotation_2026-08-09_ecg_normal_gap",
        })
        print(f"  ✅ {iid}: ajout de ECG_NORMAL")

    if args.apply:
        GOLDEN_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ Sauvegardé dans {GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run (pas de --apply), rien n'a été sauvegardé.")


if __name__ == "__main__":
    main()
