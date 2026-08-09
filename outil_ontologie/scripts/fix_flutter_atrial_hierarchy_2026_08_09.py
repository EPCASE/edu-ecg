"""
fix_flutter_atrial_hierarchy_2026-08-09.py — Corrige la hiérarchie de FLUTTER_ATRIAL.

Constat (audit outil_ontologie, 2026-08-09) : FLUTTER_ATRIAL (créé le 09/08
comme concept générique) a été placé comme FRÈRE de FLUTTER_DROIT_TYPIQUE et
FLUTTER_ATRIAL_ATYPIQUE (tous les trois enfants directs de TACHYCARDIE_ATRIALE),
au lieu d'être leur PARENT. Sémantiquement, "flutter atrial" est bien le terme
générique dont "typique/commun" et "atypique" sont des sous-types.

Conséquence mesurée : une réponse étudiante disant juste "flutter atrial" (sans
qualificatif) résout vers FLUTTER_ATRIAL, qui n'est ni parent ni enfant du
validant attendu (FLUTTER_DROIT_TYPIQUE) → 0% de crédit ontologique alors qu'un
crédit dégressif de parent direct (2/3) serait attendu.

Correction :
  - FLUTTER_DROIT_TYPIQUE.parents      : ["TACHYCARDIE_ATRIALE"] -> ["FLUTTER_ATRIAL"]
  - FLUTTER_ATRIAL_ATYPIQUE.parents    : ["TACHYCARDIE_ATRIALE"] -> ["FLUTTER_ATRIAL"]
  - FLUTTER_ATRIAL.parents             : ["TACHYCARDIE_ATRIALE"] (inchangé)
  - FLUTTER_ATRIAL.children            : [] -> ["FLUTTER_DROIT_TYPIQUE", "FLUTTER_ATRIAL_ATYPIQUE"]
  - TACHYCARDIE_ATRIALE.children       : retrait de FLUTTER_DROIT_TYPIQUE et
                                          FLUTTER_ATRIAL_ATYPIQUE (redondant,
                                          maintenant descendants indirects via
                                          FLUTTER_ATRIAL)

Écrit les 3 copies runtime de ontology_v2.json (data/, rag_pipeline/data/,
ecg-online/rag_pipeline/data/) + ecg-online/data/ontology_v2.json si présent.

Usage : python outil_ontologie/scripts/fix_flutter_atrial_hierarchy_2026_08_09.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # ECG lecture/

TARGETS = [
    ROOT / "data" / "ontology_v2.json",
    ROOT / "rag_pipeline" / "data" / "ontology_v2.json",
    ROOT / "ecg-online" / "rag_pipeline" / "data" / "ontology_v2.json",
]


def fix_one(path: Path) -> bool:
    if not path.exists():
        print(f"  ⚠️  Introuvable, ignoré : {path}")
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    concepts = data["concepts"]

    flutter_atrial = concepts.get("FLUTTER_ATRIAL")
    flutter_typique = concepts.get("FLUTTER_DROIT_TYPIQUE")
    flutter_atypique = concepts.get("FLUTTER_ATRIAL_ATYPIQUE")
    tachy_atriale = concepts.get("TACHYCARDIE_ATRIALE")

    if not all([flutter_atrial, flutter_typique, flutter_atypique, tachy_atriale]):
        print(f"  ❌ Concepts manquants dans {path}, abandon pour ce fichier.")
        return False

    changed = False

    # 1. Reparenter FLUTTER_DROIT_TYPIQUE et FLUTTER_ATRIAL_ATYPIQUE sous FLUTTER_ATRIAL
    for cid, c in (("FLUTTER_DROIT_TYPIQUE", flutter_typique),
                   ("FLUTTER_ATRIAL_ATYPIQUE", flutter_atypique)):
        old_parents = c.get("parents", [])
        if old_parents != ["FLUTTER_ATRIAL"]:
            c["parents"] = ["FLUTTER_ATRIAL"]
            changed = True
            print(f"  ✏️  {cid}.parents : {old_parents} -> ['FLUTTER_ATRIAL']")

    # 2. FLUTTER_ATRIAL.children = les deux sous-types
    expected_children = ["FLUTTER_DROIT_TYPIQUE", "FLUTTER_ATRIAL_ATYPIQUE"]
    if flutter_atrial.get("children") != expected_children:
        flutter_atrial["children"] = expected_children
        changed = True
        print(f"  ✏️  FLUTTER_ATRIAL.children -> {expected_children}")

    # 3. Retirer FLUTTER_DROIT_TYPIQUE / FLUTTER_ATRIAL_ATYPIQUE de
    #    TACHYCARDIE_ATRIALE.children (désormais descendants indirects)
    old_ta_children = tachy_atriale.get("children", [])
    new_ta_children = [c for c in old_ta_children
                       if c not in ("FLUTTER_DROIT_TYPIQUE", "FLUTTER_ATRIAL_ATYPIQUE")]
    if new_ta_children != old_ta_children:
        tachy_atriale["children"] = new_ta_children
        changed = True
        print(f"  ✏️  TACHYCARDIE_ATRIALE.children : {old_ta_children} -> {new_ta_children}")

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ Écrit : {path}")
    else:
        print(f"  ⏭️  Déjà à jour : {path}")

    return changed


def main():
    print("Correction hiérarchie FLUTTER_ATRIAL (parent de FLUTTER_DROIT_TYPIQUE / FLUTTER_ATRIAL_ATYPIQUE)")
    print("=" * 78)
    any_changed = False
    for path in TARGETS:
        print(f"\n📄 {path}")
        if fix_one(path):
            any_changed = True

    if any_changed:
        print("\n✅ Terminé. Penser à reconstruire rag_index/ (outil_ontologie/scripts/rebuild_rag_index.py)"
              " et à propager vers ecg-online/rag_pipeline/rag_index/.")
    else:
        print("\n✅ Rien à changer, toutes les copies déjà cohérentes.")


if __name__ == "__main__":
    main()
