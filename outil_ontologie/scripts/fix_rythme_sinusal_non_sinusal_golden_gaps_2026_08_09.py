"""
fix_rythme_sinusal_non_sinusal_golden_gaps_2026_08_09.py
==========================================================
Suite au retrait du synonyme trop generique "rythme non sinusal" sur
ARYTHMIE_ATRIALE + ajout de la regle NER dediee ("non sinusal" seul ->
RYTHME_SINUSAL/absent), le pipeline extrait maintenant correctement
RYTHME_SINUSAL/absent partout ou` le texte dit litteralement "non sinusal",
meme quand un diagnostic precis (FA, Flutter, TRIN, BAV2...) est deja
annote par ailleurs. Le golden ne contenait pas ce concept -> ajout.

12 items concernes (tous disent "non sinusal" ou "pas sinusal" dans le
texte etudiant) : 14-02, 24-03, 25-01, 25-04, 37-04, 37-05, 42-01, 42-03,
43-02, 43-04, 44-02, 45-01

Usage : python fix_rythme_sinusal_non_sinusal_golden_gaps_2026_08_09.py [--apply]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "ecg-online" / "data" / "extraction_golden.json"

ADD_RYTHME_SINUSAL_ABSENT = [
    "14-02", "24-03", "25-01", "25-04", "37-04", "37-05",
    "42-01", "42-03", "43-02", "43-04", "44-02", "45-01",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    items = data["items"]

    for iid in ADD_RYTHME_SINUSAL_ABSENT:
        it = items[iid]
        concepts = it["annotation_expert"]["concepts"]
        existing = [c for c in concepts if c.get("ontology_id") == "RYTHME_SINUSAL"]
        if existing:
            # cas particulier 14-02 : golden avait RYTHME_SINUSAL/present (erreur,
            # texte dit "non sinusal") -> corriger le statut au lieu de dupliquer
            for c in existing:
                if c.get("statut") != "absent":
                    c["statut"] = "absent"
                    print(f"  🔁 {iid}: RYTHME_SINUSAL statut -> absent")
                else:
                    print(f"  ⏭️  {iid}: RYTHME_SINUSAL/absent deja present, skip")
            continue
        concepts.append({
            "ontology_id": "RYTHME_SINUSAL",
            "concept_name": "Rythme sinusal",
            "statut": "absent",
            "source": "reannotation_2026-08-09_non_sinusal_gap",
        })
        print(f"  ✅ {iid}: ajout de RYTHME_SINUSAL/absent")

    if args.apply:
        GOLDEN_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ Sauvegardé dans {GOLDEN_PATH}")
    else:
        print("ℹ️  Dry-run (pas de --apply), rien n'a été sauvegardé.")


if __name__ == "__main__":
    main()
