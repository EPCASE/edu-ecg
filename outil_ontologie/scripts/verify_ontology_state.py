"""
verify_ontology_state.py — Vérifie que data/ontology_v2.json (à la racine du repo)
reflète bien l'état final documenté dans CHANGELOG_ONTOLOGIE.md (session 2026-08-09) :
- revert de la fusion "voltage" (VOLTAGE_DU_QRS_NORMAL canonique, VOLTAGE_NORMAL_DU_QRS absent)
- retraits de synonymes des catégories A/B/C (dédup collisions pré-existantes)

Usage :
    python outil_ontologie/scripts/verify_ontology_state.py [--path ../../data/ontology_v2.json]
"""
import argparse
import json
import sys
from pathlib import Path

# Synonymes qui doivent avoir été RETIRÉS de ces concepts génériques/parents
# (catégories A/B/C du changelog, 2026-08-09 §8)
EXPECTED_REMOVED = {
    "MORPHOLOGIE_ONDE_P_SINUSALE": ["activité atriale sinusale"],
    "ARYTHMIE_VENTRICULAIRE": ["arythmie ventriculaire polymorphe"],
    "BLOC_DE_BRANCHE_DROIT": ["aspect de bloc de branche droite"],
    "BLOC_DE_BRANCHE_DROIT_COMPLET": ["aspect de bloc de branche droite"],
    "BLOC_DE_BRANCHE_GAUCHE": ["aspect de bloc de branche gauche"],
    "TACHYCARDIE_ATRIALE_FOCALE": ["at"],
    "BLOC_DE_BRANCHE_DROIT_COMPLET__BIS": None,  # placeholder ignoré
    "ONDE_P_NORMALE": ["morphologie normale des ondes p", "ondes p de morphologie normale"],
    "SYNDROME_CORONARIEN_A_LA_PHASE_AIGUE_AVEC_SUS_DECALAGE_DU_SEGMENT_ST": ["onde de pardee"],
    "ONDE_P_PRESENTE": ["onde p avant chaque complexe qrs"],
    "DYSFONCTION_SINUSALE": ["perte de l'automatisme sinusal"],
    "COURANT_DE_LESION_SOUS_ENDOCARDIQUE": ["sous-décalage en miroir"],
    "FLUTTER_ATRIAL_ATYPIQUE": ["ta"],
    "TROUBLES_DE_CONDUCTION_ET_DE_L_AUTOMATICITE": ["trouble de conduction atrioventriculaire"],
    "ECHAPPEMENT": ["échappement jonctionnel"],
    "RYTHME_D_ECHAPPEMENT_JONCTIONNEL": ["rija"],
    "ASPECT_DE_BRUGADA": ["brs"],
    "REPOLARISATION_PRECOCE": ["ers"],
}

EXPECTED_PRESENT = {
    "RYTHME_SINUSAL": ["activité atriale sinusale"],
    "TACHYCARDIE_VENTRICULAIRE_POLYMORPHE": ["arythmie ventriculaire polymorphe"],
    "ASPECT_DE_RETARD_DROIT": ["aspect de bloc de branche droite"],
    "ASPECT_DE_RETARD_GAUCHE": ["aspect de bloc de branche gauche"],
    "TACHYCARDIE_ATRIALE": ["at", "ta"],
    "BLOC_DE_BRANCHE_DROIT": ["bloc de branche droite"],
    "COURANT_DE_LESION_SOUS_EPICARDIQUE": ["onde de pardee"],
    "PARALYSIE_SINUSALE": ["perte de l'automatisme sinusal"],
    "MIROIR": ["sous-décalage en miroir"],
    "BLOC_AURICULO_VENTRICULAIRE": ["trouble de conduction atrioventriculaire"],
    "RYTHME_D_ECHAPPEMENT_JONCTIONNEL": ["échappement jonctionnel"],
    "RYTHME_JONCTIONELLE_ACCELERE": ["rija"],
    "SYNDROME_DE_BRUGADA": ["brs"],
    "SYNDROME_DE_REPOLARISATION_PRECOCE": ["ers"],
}


def norm(s: str) -> str:
    return s.strip().lower()


def check(ontology_path: Path) -> int:
    data = json.loads(ontology_path.read_text(encoding="utf-8"))
    concepts = data["concepts"]
    errors = []
    warnings = []

    # 1. Revert de la fusion voltage
    if "VOLTAGE_DU_QRS_NORMAL" not in concepts:
        errors.append("VOLTAGE_DU_QRS_NORMAL absent — le revert de la fusion voltage n'est PAS appliqué.")
    if "VOLTAGE_NORMAL_DU_QRS" in concepts:
        errors.append("VOLTAGE_NORMAL_DU_QRS toujours présent — devrait avoir été supprimé lors du revert.")
    vqn = concepts.get("VOLTAGE_DU_QRS")
    if vqn and "VOLTAGE_DU_QRS_NORMAL" not in vqn.get("children", []):
        warnings.append("VOLTAGE_DU_QRS.children ne liste pas VOLTAGE_DU_QRS_NORMAL.")
    qrs_normal = concepts.get("QRS_NORMAL")
    if qrs_normal and "VOLTAGE_DU_QRS_NORMAL" not in qrs_normal.get("requires", []):
        warnings.append("QRS_NORMAL.requires ne pointe pas vers VOLTAGE_DU_QRS_NORMAL.")

    # 2. Synonymes retirés (catégories A/B/C)
    for cid, removed_syns in EXPECTED_REMOVED.items():
        if removed_syns is None:
            continue
        c = concepts.get(cid)
        if c is None:
            warnings.append(f"Concept {cid} introuvable (skip check synonymes).")
            continue
        current = [norm(s) for s in c.get("synonymes", [])]
        for rs in removed_syns:
            if norm(rs) in current:
                errors.append(f"Synonyme '{rs}' encore présent sur {cid} (devrait être retiré).")

    # 3. Synonymes conservés sur le concept spécifique
    for cid, kept_syns in EXPECTED_PRESENT.items():
        c = concepts.get(cid)
        if c is None:
            warnings.append(f"Concept {cid} introuvable (skip check synonymes conservés).")
            continue
        current = [norm(s) for s in c.get("synonymes", [])]
        for ks in kept_syns:
            if norm(ks) not in current:
                warnings.append(f"Synonyme '{ks}' absent de {cid} (attendu conservé, cf. catégorie A/B/C).")

    print(f"Concepts totaux : {len(concepts)}")
    print(f"Erreurs bloquantes : {len(errors)}")
    for e in errors:
        print(f"  ❌ {e}")
    print(f"Avertissements : {len(warnings)}")
    for w in warnings:
        print(f"  ⚠️  {w}")

    if not errors and not warnings:
        print("✅ Ontologie conforme à l'état final documenté (2026-08-09).")
    elif not errors:
        print("✅ Aucune erreur bloquante (avertissements mineurs seulement, cf. ci-dessus).")

    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default=str(Path(__file__).resolve().parents[2] / "data" / "ontology_v2.json"),
    )
    args = parser.parse_args()
    sys.exit(check(Path(args.path)))
