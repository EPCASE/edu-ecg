"""
🧪 Test rapide du scoring dégressif par génération
===================================================
Vérifie que le nouveau barème (90/80/70/60 par gen) fonctionne correctement
sur un cas réel avant de lancer le benchmark complet.
"""
import json
import sys
import logging
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

from scoring import (
    _get_ontology, find_owl_concept, _build_reverse_implications,
    _score_for_generation, score_student_response,
    SCORE_BY_GENERATION, SCORE_GENERATION_FLOOR,
)

print("=" * 80)
print("🧪 TEST 1 — Vérification du barème par génération")
print("=" * 80)
for gen in range(1, 6):
    score = _score_for_generation(gen)
    print(f"   Gen {gen} → {score:.0f}%")

assert _score_for_generation(1) == 90.0
assert _score_for_generation(2) == 80.0
assert _score_for_generation(3) == 70.0
assert _score_for_generation(4) == 60.0  # plancher
assert _score_for_generation(5) == 60.0  # plancher
print("   ✅ Barème OK\n")

# ─── TEST 2 : Vérifier l'arbre d'implications de FA ──────────
print("=" * 80)
print("🧪 TEST 2 — Arbre d'implications : FIBRILLATION_ATRIALE")
print("=" * 80)

owl_fa = find_owl_concept("Fibrillation atriale")
if owl_fa:
    print(f"   ID: {owl_fa['ontology_id']}")
    print(f"   Implications directes (gen 1) : {owl_fa.get('implications', [])}")
    
    # BFS comme dans scoring.py pour voir les profondeurs
    golden_child_depths = {}
    queue = [(name, 1) for name in owl_fa.get("implications", [])]
    visited = set()
    while queue:
        impl_name, depth = queue.pop(0)
        if impl_name in visited:
            continue
        visited.add(impl_name)
        impl_owl = find_owl_concept(impl_name)
        if impl_owl:
            impl_id = impl_owl["ontology_id"]
            if impl_id not in golden_child_depths or depth < golden_child_depths[impl_id]:
                golden_child_depths[impl_id] = depth
            for sub in impl_owl.get("implications", []):
                if sub not in visited:
                    queue.append((sub, depth + 1))
    
    print(f"\n   Descendants trouvés ({len(golden_child_depths)}) :")
    for cid, gen in sorted(golden_child_depths.items(), key=lambda x: (x[1], x[0])):
        score = _score_for_generation(gen)
        print(f"      Gen {gen} ({score:>2.0f}%) : {cid}")
else:
    print("   ⚠️ Fibrillation atriale non trouvée dans l'ontologie")

# ─── TEST 3 : Reverse implications (PARENT) avec profondeur ──
print(f"\n{'='*80}")
print("🧪 TEST 3 — Reverse implications avec profondeur")
print("=" * 80)

reverse_impl, reverse_depths = _build_reverse_implications()
print(f"   {len(reverse_impl)} concepts ont des parents dans l'index inversé")

# Exemple : BBG_COMPLET → qui sont ses parents ?
test_concepts = ["BBG_COMPLET", "FIBRILLATION_ATRIALE", "TACHYCARDIE_VENTRICULAIRE"]
for tc in test_concepts:
    if tc in reverse_impl:
        parents = reverse_impl[tc]
        depths = reverse_depths.get(tc, {})
        print(f"\n   {tc} ← parents :")
        for pid in parents:
            gen = depths.get(pid, "?")
            print(f"      Gen {gen} : {pid}")
    else:
        print(f"\n   {tc} : pas de parents dans l'index inversé")

# ─── TEST 4 : Scoring complet sur un cas réel ────────────────
print(f"\n{'='*80}")
print("🧪 TEST 4 — Scoring complet sur cas simulés")
print("=" * 80)

# Cas A : Étudiant parfait → dit exactement FA
print("\n--- Cas A : Étudiant dit 'Fibrillation atriale' (EXACT) ---")
result_a = score_student_response(
    found_ids=["FIBRILLATION_ATRIALE"],
    found_statuts={"FIBRILLATION_ATRIALE": "present"},
    golden_names=["Fibrillation atriale"],
    golden_ids=["FIBRILLATION_ATRIALE"],
    golden_roles=["validant"],
)
print(f"   Score: {result_a['score_final_pct']:.1f}%")
print(f"   Match types: {result_a.get('match_types', {})}")

# Cas B : Étudiant dit un signe (child gen1)
owl_fa = find_owl_concept("Fibrillation atriale")
if owl_fa and owl_fa.get("implications"):
    child_name = owl_fa["implications"][0]
    child_owl = find_owl_concept(child_name)
    if child_owl:
        child_id = child_owl["ontology_id"]
        print(f"\n--- Cas B : Étudiant dit '{child_name}' (CHILD gen1 de FA) ---")
        result_b = score_student_response(
            found_ids=[child_id],
            found_statuts={child_id: "present"},
            golden_names=["Fibrillation atriale"],
            golden_ids=["FIBRILLATION_ATRIALE"],
            golden_roles=["validant"],
        )
        print(f"   Score: {result_b['score_final_pct']:.1f}%")
        print(f"   Match types: {result_b.get('match_types', {})}")
        print(f"   Partial matches: {result_b.get('partial_matches', [])}")

# Cas C : Étudiant dit un child en hypothèse
        print(f"\n--- Cas C : Même child '{child_name}' mais en HYPOTHÈSE ---")
        result_c = score_student_response(
            found_ids=[child_id],
            found_statuts={child_id: "hypothese"},
            golden_names=["Fibrillation atriale"],
            golden_ids=["FIBRILLATION_ATRIALE"],
            golden_roles=["validant"],
        )
        print(f"   Score: {result_c['score_final_pct']:.1f}%")
        print(f"   Match types: {result_c.get('match_types', {})}")

# Cas D : Étudiant dit un concept non relié → 0%
print(f"\n--- Cas D : Étudiant dit 'ECG normal' pour golden 'FA' (non relié) ---")
result_d = score_student_response(
    found_ids=["ECG_NORMAL"],
    found_statuts={"ECG_NORMAL": "present"},
    golden_names=["Fibrillation atriale"],
    golden_ids=["FIBRILLATION_ATRIALE"],
    golden_roles=["validant"],
)
print(f"   Score: {result_d['score_final_pct']:.1f}%")
print(f"   Match types: {result_d.get('match_types', {})}")

# Cas E : Golden avec descripteur + validant
print(f"\n--- Cas E : Golden mixte (1 validant + 1 descripteur), étudiant ne trouve que le descripteur ---")
result_e = score_student_response(
    found_ids=["BLOC_INTERATRIAL"],
    found_statuts={"BLOC_INTERATRIAL": "present"},
    golden_names=["ECG normal", "Bloc interatrial"],
    golden_ids=["ECG_NORMAL", "BLOC_INTERATRIAL"],
    golden_roles=["validant", "descripteur"],
)
print(f"   Score: {result_e['score_final_pct']:.1f}% (seul le validant compte)")
print(f"   Validants: {result_e.get('validant_found', '?')}/{result_e.get('validant_total', '?')}")
print(f"   Descripteurs: {result_e.get('descripteur_found', '?')}/{result_e.get('descripteur_total', '?')}")

print(f"\n{'='*80}")
print("✅ Tests terminés — Vérifiez les scores ci-dessus")
print("=" * 80)
