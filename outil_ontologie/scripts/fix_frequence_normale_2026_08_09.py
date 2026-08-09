#!/usr/bin/env python
"""
fix_frequence_normale_2026_08_09.py — Corrige 5 lacunes/erreurs dans
annotation_expert (extraction_golden.json) autour du concept fréquence
cardiaque, découvertes lors du re-test golden 2026-08-09 (v6) :

  1. Item 23-05 : le texte dit "FC 60bpm" mais l'expert avait annoté
     BRADYCARDIE (erreur — 60bpm est dans la plage normale 50-100bpm,
     seuil documenté dans ner_extractor.py règle 5). Remplacé par
     FREQUENCE_NORMALE.
  2. Items 25-02, 25-04, 28-05, 9-03 : le texte mentionne un bpm explicite
     dans la plage normale (60, 60, 54, 96) mais AUCUN concept de fréquence
     n'avait été annoté (omission). Ajout de FREQUENCE_NORMALE.

Usage (depuis la racine "ECG lecture") :
    python outil_ontologie/scripts/fix_frequence_normale_2026_08_09.py
    python outil_ontologie/scripts/fix_frequence_normale_2026_08_09.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ECG_ONLINE = ROOT / "ecg-online"
sys.path.insert(0, str(ECG_ONLINE))

from app import extraction_golden  # noqa: E402

# Items où BRADYCARDIE est une erreur d'annotation à remplacer par FREQUENCE_NORMALE
REPLACE = [
    ("23-05", "BRADYCARDIE", "FREQUENCE_NORMALE"),
]

# Items où FREQUENCE_NORMALE est manquant (omission), à ajouter
ADD = [
    "25-02", "25-04", "28-05", "9-03",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = extraction_golden.load()
    items = data["items"]

    for item_id, old_id, new_id in REPLACE:
        it = items[item_id]
        concepts = it["annotation_expert"]["concepts"]
        replaced = False
        for c in concepts:
            if c.get("ontology_id") == old_id:
                print(f"  🔁 {item_id}: {old_id} -> {new_id}")
                c["ontology_id"] = new_id
                c["concept_name"] = "Frequence normale"
                c["source"] = "correction_2026-08-09_frequence_normale"
                replaced = True
        if not replaced:
            print(f"  ⚠️  {item_id}: {old_id} introuvable, rien remplacé.")

    for item_id in ADD:
        it = items[item_id]
        concepts = it["annotation_expert"].setdefault("concepts", [])
        existing = {c.get("ontology_id") for c in concepts}
        if "FREQUENCE_NORMALE" in existing:
            print(f"  ⏭️  {item_id}: FREQUENCE_NORMALE déjà présent.")
            continue
        print(f"  ✅ {item_id}: ajout de FREQUENCE_NORMALE")
        concepts.append({
            "ontology_id": "FREQUENCE_NORMALE",
            "statut": "present",
            "terme_brut": "Normocarde",
            "concept_name": "Frequence normale",
            "source": "reannotation_2026-08-09_frequence_normale_gap",
        })

    if args.apply:
        extraction_golden.save(data)
        print(f"✅ Sauvegardé dans {extraction_golden.EXTRACTION_GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run : rien n'a été écrit. Relancer avec --apply pour persister.")


if __name__ == "__main__":
    main()
