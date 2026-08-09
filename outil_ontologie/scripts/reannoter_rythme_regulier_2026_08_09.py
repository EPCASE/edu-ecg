#!/usr/bin/env python
"""
reannoter_rythme_regulier_2026_08_09.py — Corrige 21 lacunes identifiées dans
annotation_expert (extraction_golden.json) : le texte de l'étudiant mentionne
explicitement "régulier" ou "irrégulier" pour le rythme, mais l'annotateur
humain avait omis d'ajouter le concept RYTHME_REGULIER / IRREGULIER
correspondant lors de l'annotation initiale.

Contexte : un audit du re-test golden (2026-08-09) a montré que sur 70 items
mentionnant "régulier/irrégulier", seuls 29 avaient le concept annoté,
révélant une incohérence systématique de l'annotateur sur ce concept précis
(concept jugé "secondaire" à l'époque, ou simple oubli répété).

Ce script :
  1. Recharge extraction_golden.json
  2. Pour chaque item de la liste ITEMS_TO_FIX, vérifie que le concept
     attendu (RYTHME_REGULIER ou IRREGULIER) est bien absent de
     annotation_expert.concepts, puis l'AJOUTE (statut="present") sans
     toucher au reste de l'annotation.
  3. Sauvegarde le fichier.

Usage (depuis la racine "ECG lecture") :
    python outil_ontologie/scripts/reannoter_rythme_regulier_2026_08_09.py --dry-run
    python outil_ontologie/scripts/reannoter_rythme_regulier_2026_08_09.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
ECG_ONLINE = ROOT / "ecg-online"
sys.path.insert(0, str(ECG_ONLINE))

from app import extraction_golden  # noqa: E402

# (item_id, concept_id à ajouter) — établi par revue manuelle du texte brut.
# Tous les cas ci-dessous mentionnent explicitement "régulier" ou
# "irrégulier" en rapport avec le rythme cardiaque global (pas un autre sens
# du mot), sans ambiguïté clinique.
ITEMS_TO_FIX = [
    ("1-01", "RYTHME_REGULIER"),
    ("1-02", "RYTHME_REGULIER"),
    ("13-01", "RYTHME_REGULIER"),
    ("15-02", "RYTHME_REGULIER"),
    ("18-01", "RYTHME_REGULIER"),
    ("2-02", "RYTHME_REGULIER"),
    ("25-03", "IRREGULIER"),
    ("28-05", "RYTHME_REGULIER"),
    ("37-05", "IRREGULIER"),
    ("40-01", "RYTHME_REGULIER"),
    ("40-02", "RYTHME_REGULIER"),
    ("41-01", "RYTHME_REGULIER"),
    ("42-01", "RYTHME_REGULIER"),
    ("42-03", "RYTHME_REGULIER"),
    ("43-03", "RYTHME_REGULIER"),
    ("44-03", "RYTHME_REGULIER"),
    ("45-01", "RYTHME_REGULIER"),
    ("46-01", "RYTHME_REGULIER"),
    ("47-01", "RYTHME_REGULIER"),
    ("5-01", "RYTHME_REGULIER"),
    ("8-01", "RYTHME_REGULIER"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                     help="Écrit réellement les modifications. Sans ce flag : dry-run.")
    args = ap.parse_args()

    data = extraction_golden.load()
    items = data["items"]

    n_fixed = 0
    n_skipped = 0
    for item_id, concept_id in ITEMS_TO_FIX:
        if item_id not in items:
            print(f"  ⚠️  {item_id} introuvable dans extraction_golden.json, ignoré.")
            continue
        item = items[item_id]
        ann = item.get("annotation_expert")
        if not ann:
            print(f"  ⚠️  {item_id} n'a pas d'annotation_expert, ignoré.")
            continue
        concepts = ann.setdefault("concepts", [])
        existing_ids = {c.get("ontology_id") for c in concepts}
        if concept_id in existing_ids:
            print(f"  ⏭️  {item_id}: {concept_id} déjà présent, rien à faire.")
            n_skipped += 1
            continue
        print(f"  ✅ {item_id}: ajout de {concept_id} (present)")
        concepts.append({
            "ontology_id": concept_id,
            "statut": "present",
            "terme_brut": "régulier" if concept_id == "RYTHME_REGULIER" else "irrégulier",
            "concept_name": "Rythme régulier" if concept_id == "RYTHME_REGULIER" else "Irrégulier",
            "source": "reannotation_2026-08-09_rythme_regulier_gap",
        })
        n_fixed += 1

    print(f"\nRésumé : {n_fixed} items corrigés, {n_skipped} déjà OK, "
          f"{len(ITEMS_TO_FIX) - n_fixed - n_skipped} ignorés/erreurs.")

    if args.apply:
        extraction_golden.save(data)
        print(f"✅ Sauvegardé dans {extraction_golden.EXTRACTION_GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run : rien n'a été écrit. Relancer avec --apply pour persister.")


if __name__ == "__main__":
    main()
