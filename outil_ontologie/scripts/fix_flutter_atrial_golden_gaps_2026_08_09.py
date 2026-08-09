#!/usr/bin/env python
"""
fix_flutter_atrial_golden_gaps_2026_08_09.py — Corrige les lacunes du golden
liées au concept FLUTTER_ATRIAL (créé le 2026-08-09, donc absent de
l'ontologie au moment de l'annotation initiale de plusieurs items).

Découvert lors du re-test golden v6 :
  - 41-01, 42-01 : contiennent un concept fantôme
    {"ontology_id": "", "concept_name": "Flutter atrial", "source": "ajoute_gpt56"}
    — preuve que l'annotateur/outil avait identifié "Flutter atrial" dans le
    texte AVANT que le concept canonique n'existe (ontology_id resté vide).
    On répare en fixant ontology_id="FLUTTER_ATRIAL".
  - 37-01 : texte "Flutter atrial" (générique) — golden n'a que
    TACHYCARDIE_ATRIALE (ancêtre). On ajoute FLUTTER_ATRIAL (plus spécifique,
    présent dans le texte).
  - 42-03, 45-01 : texte "Flutter atrial typique" — golden a déjà
    FLUTTER_DROIT_TYPIQUE (le concept le plus spécifique, correct). Avec la
    hiérarchie corrigée (FLUTTER_ATRIAL parent de FLUTTER_DROIT_TYPIQUE), le
    pipeline extrait FLUTTER_ATRIAL en plus (crédité comme "enfant trouvé"
    en scoring réel, mais compté FP par la métrique brute d'extraction).
    On ajoute FLUTTER_ATRIAL au golden pour refléter les deux niveaux
    mentionnés dans le texte.

Usage :
    python outil_ontologie/scripts/fix_flutter_atrial_golden_gaps_2026_08_09.py
    python outil_ontologie/scripts/fix_flutter_atrial_golden_gaps_2026_08_09.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ECG_ONLINE = ROOT / "ecg-online"
sys.path.insert(0, str(ECG_ONLINE))

from app import extraction_golden  # noqa: E402

# Items avec concept fantôme ontology_id="" et concept_name="Flutter atrial"
FIX_EMPTY_ID = ["41-01", "42-01"]

# Items où FLUTTER_ATRIAL doit être ajouté (déjà présent dans le texte, absent du golden)
ADD_FLUTTER_ATRIAL = ["37-01", "42-03", "45-01"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = extraction_golden.load()
    items = data["items"]

    for item_id in FIX_EMPTY_ID:
        it = items[item_id]
        concepts = it["annotation_expert"]["concepts"]
        fixed = False
        for c in concepts:
            if c.get("ontology_id") == "" and c.get("concept_name", "").lower() == "flutter atrial":
                print(f"  🔧 {item_id}: ontology_id vide -> FLUTTER_ATRIAL")
                c["ontology_id"] = "FLUTTER_ATRIAL"
                c["source"] = "correction_2026-08-09_ontology_id_vide"
                fixed = True
        if not fixed:
            print(f"  ⚠️  {item_id}: concept fantôme introuvable, rien fait.")

    for item_id in ADD_FLUTTER_ATRIAL:
        it = items[item_id]
        concepts = it["annotation_expert"].setdefault("concepts", [])
        existing = {c.get("ontology_id") for c in concepts}
        if "FLUTTER_ATRIAL" in existing:
            print(f"  ⏭️  {item_id}: FLUTTER_ATRIAL déjà présent.")
            continue
        print(f"  ✅ {item_id}: ajout de FLUTTER_ATRIAL")
        concepts.append({
            "ontology_id": "FLUTTER_ATRIAL",
            "statut": "present",
            "terme_brut": "Flutter atrial",
            "concept_name": "Flutter atrial",
            "source": "reannotation_2026-08-09_flutter_atrial_gap",
        })

    if args.apply:
        extraction_golden.save(data)
        print(f"✅ Sauvegardé dans {extraction_golden.EXTRACTION_GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run : rien n'a été écrit. Relancer avec --apply pour persister.")


if __name__ == "__main__":
    main()
