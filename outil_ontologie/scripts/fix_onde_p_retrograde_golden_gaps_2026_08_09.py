"""
fix_onde_p_retrograde_golden_gaps_2026_08_09.py
=================================================
Corrige 4 items golden ou` le pipeline extrait correctement ONDE_P_RETROGRADE
(concept specifique) mais le golden a soit :
  - annote le concept generique parent MORPHOLOGIE_DE_L_ONDE_P_NON_SINUSALE
    a la place (43-01, 44-01, 44-03 : le texte dit litteralement "onde P
    retrograde", plus precis que la morphologie generique non-sinusale)
  - omis totalement le concept (46-01 : "doute sur des ondes P retrogrades"
    -> ONDE_P_RETROGRADE/hypothese manquant)

Usage : python fix_onde_p_retrograde_golden_gaps_2026_08_09.py [--apply]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "ecg-online" / "data" / "extraction_golden.json"

# items ou` remplacer le concept generique par le concept specifique
REPLACE = ["43-01", "44-01", "44-03"]

# items ou` juste ajouter ONDE_P_RETROGRADE (statut donne)
ADD = [("46-01", "hypothese")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    items = data["items"]

    for iid in REPLACE:
        it = items[iid]
        concepts = it["annotation_expert"]["concepts"]
        found = False
        for c in concepts:
            if c.get("ontology_id") == "MORPHOLOGIE_DE_L_ONDE_P_NON_SINUSALE":
                c["ontology_id"] = "ONDE_P_RETROGRADE"
                c["concept_name"] = "Onde P rétrograde"
                found = True
        if found:
            print(f"  🔁 {iid}: MORPHOLOGIE_DE_L_ONDE_P_NON_SINUSALE -> ONDE_P_RETROGRADE")
        else:
            print(f"  ⚠️  {iid}: concept generique non trouve, rien fait")

    for iid, statut in ADD:
        it = items[iid]
        concepts = it["annotation_expert"]["concepts"]
        if any(c.get("ontology_id") == "ONDE_P_RETROGRADE" for c in concepts):
            print(f"  ⏭️  {iid}: ONDE_P_RETROGRADE deja present, skip")
            continue
        concepts.append({
            "ontology_id": "ONDE_P_RETROGRADE",
            "concept_name": "Onde P rétrograde",
            "statut": statut,
            "source": "reannotation_2026-08-09_onde_p_retrograde_gap",
        })
        print(f"  ✅ {iid}: ajout de ONDE_P_RETROGRADE/{statut}")

    if args.apply:
        GOLDEN_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ Sauvegardé dans {GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run (pas de --apply), rien n'a été sauvegardé.")


if __name__ == "__main__":
    main()
