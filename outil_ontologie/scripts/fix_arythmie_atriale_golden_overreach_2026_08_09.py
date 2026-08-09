"""
fix_arythmie_atriale_golden_overreach_2026_08_09.py
=====================================================
Suite au retrait du synonyme trop generique "rythme non sinusal" sur
ARYTHMIE_ATRIALE (cf. CHANGELOG_ONTOLOGIE.md), 12 items golden avaient
ARYTHMIE_ATRIALE/present ajoute uniquement a cause de ce synonyme, alors
que le diagnostic reel de l'item est soit :
  (a) un descendant hierarchique legitime (FA, Flutter, TRIN) -> deja
      credite via la regle de scoring V3 1b (enfant trouve credite le
      parent), retirer le doublon explicite est neutre pour le score reel
  (b) un diagnostic SANS RAPPORT avec une arythmie atriale (BAV, tachycardie
      non qualifiee) -> le golden avait tort de l'attendre, c'etait un faux
      credit du au synonyme generique desormais retire

Dans les 2 cas, ARYTHMIE_ATRIALE/present doit etre retire du golden pour
ces 12 items (RYTHME_SINUSAL/absent reste, lui, correctement present -
deja gere par fix_rythme_sinusal_non_sinusal_golden_gaps_2026_08_09.py).

Items : 24-03, 25-01, 25-04, 37-03, 37-04, 37-05, 42-01, 42-03, 43-02,
43-04, 44-02, 45-01

Usage : python fix_arythmie_atriale_golden_overreach_2026_08_09.py [--apply]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "ecg-online" / "data" / "extraction_golden.json"

REMOVE_ARYTHMIE_ATRIALE = [
    "24-03", "25-01", "25-04", "37-03", "37-04", "37-05",
    "42-01", "42-03", "43-02", "43-04", "44-02", "45-01",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    items = data["items"]

    for iid in REMOVE_ARYTHMIE_ATRIALE:
        it = items[iid]
        concepts = it["annotation_expert"]["concepts"]
        before = len(concepts)
        concepts[:] = [c for c in concepts if c.get("ontology_id") != "ARYTHMIE_ATRIALE"]
        after = len(concepts)
        if after < before:
            print(f"  🔁 {iid}: ARYTHMIE_ATRIALE retiré ({before}->{after} concepts)")
        else:
            print(f"  ⏭️  {iid}: ARYTHMIE_ATRIALE absent, skip")

    if args.apply:
        GOLDEN_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ Sauvegardé dans {GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run (pas de --apply), rien n'a été sauvegardé.")


if __name__ == "__main__":
    main()
