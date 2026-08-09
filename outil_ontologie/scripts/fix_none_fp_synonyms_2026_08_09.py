#!/usr/bin/env python
"""
fix_none_fp_synonyms_2026_08_09.py — Ajoute des synonymes manquants identifiés
lors du re-test golden 2026-08-09 (v5), pour des termes bruts fréquents dans
les copies étudiantes qui se résolvaient en NONE faute de synonyme exact :

  - "hypertrophie" (générique, sans précision gauche/droite/atriale)
    -> HYPERTROPHIE_VENTRICULAIRE
  - "séquelle d'ischémie" -> ISCHEMIQUE
  - "troubles de la dépolarisation" -> TROUBLE_DE_LA_DEPOLARISATION_VENTRICULAIRE
  - "blocage de l'onde P" -> UNE_ONDE_P_BLOQUEE

Applique aux 3 copies runtime de l'ontologie.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHS = [
    ROOT / "data" / "ontology_v2.json",
    ROOT / "rag_pipeline" / "data" / "ontology_v2.json",
    ROOT / "ecg-online" / "rag_pipeline" / "data" / "ontology_v2.json",
]


def add_synonyms(concepts: dict, concept_id: str, new_syns: list[str]) -> None:
    c = concepts[concept_id]
    syn = c.get("synonymes") or []
    for s in new_syns:
        if s not in syn:
            syn.append(s)
    c["synonymes"] = syn


def main():
    for p in PATHS:
        data = json.loads(p.read_text(encoding="utf-8"))
        concepts = data["concepts"] if "concepts" in data else data

        add_synonyms(concepts, "HYPERTROPHIE_VENTRICULAIRE", [
            "hypertrophie", "signes d'hypertrophie", "hypertrophie ventriculaire",
        ])
        add_synonyms(concepts, "ISCHEMIQUE", [
            "séquelle d'ischémie", "ischémie décelée",
        ])
        add_synonyms(concepts, "TROUBLE_DE_LA_DEPOLARISATION_VENTRICULAIRE", [
            "troubles de la dépolarisation", "trouble de la dépolarisation",
            "trouble de dépolarisation",
        ])
        add_synonyms(concepts, "UNE_ONDE_P_BLOQUEE", [
            "blocage de l'onde P", "blocage de la onde P",
        ])

        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{p} : OK")


if __name__ == "__main__":
    main()
