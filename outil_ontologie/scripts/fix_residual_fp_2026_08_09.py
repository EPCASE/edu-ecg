"""
fix_residual_fp_2026_08_09.py
==============================
Corrige 3 residuels FP apparus apres le batch de 5 clusters :
  - 42-02 : "flutter commun" -> ajout du parent FLUTTER_ATRIAL (golden n'avait
            que le specifique FLUTTER_DROIT_TYPIQUE)
  - 46-01 : "soit un flutter avec bloc de branche gauche" -> hypothese
            FLUTTER_ATRIAL manquante dans la liste des diagnostics differentiels
  - 25-01 : "FC 60" (zone normale 60-100 bpm) -> FREQUENCE_NORMALE omis

Usage : python fix_residual_fp_2026_08_09.py [--apply]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "ecg-online" / "data" / "extraction_golden.json"

ADD = [
    ("42-02", "FLUTTER_ATRIAL", "Flutter atrial", "present"),
    ("46-01", "FLUTTER_ATRIAL", "Flutter atrial", "hypothese"),
    ("25-01", "FREQUENCE_NORMALE", "Normocarde", "present"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    items = data["items"]

    for iid, ontology_id, concept_name, statut in ADD:
        it = items[iid]
        concepts = it["annotation_expert"]["concepts"]
        if any(c.get("ontology_id") == ontology_id for c in concepts):
            print(f"  ⏭️  {iid}: {ontology_id} deja present, skip")
            continue
        concepts.append({
            "ontology_id": ontology_id,
            "concept_name": concept_name,
            "statut": statut,
            "source": "reannotation_2026-08-09_residual_fp_fix",
        })
        print(f"  ✅ {iid}: ajout de {ontology_id}/{statut}")

    if args.apply:
        GOLDEN_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ Sauvegardé dans {GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run (pas de --apply), rien n'a été sauvegardé.")


if __name__ == "__main__":
    main()
