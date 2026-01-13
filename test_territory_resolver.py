"""
🧪 Test du Territory Resolver
"""

import json
from backend.territory_resolver import get_territory_config

# Charger l'ontologie
with open('data/ontology_from_owl.json', 'r', encoding='utf-8') as f:
    ontology = json.load(f)

print("🧪 TEST DU TERRITORY RESOLVER")
print("=" * 80)

# Test 1: STEMI (doit avoir territoire + miroir, required)
print("\n1️⃣  TEST STEMI:")
stemi_config = get_territory_config("STEMI", ontology)
if stemi_config:
    print(f"   ✅ Concept trouvé: {stemi_config['concept_name']}")
    print(f"   📍 Show territory selector: {stemi_config['show_territory_selector']}")
    print(f"   🪞 Show mirror selector: {stemi_config['show_mirror_selector']}")
    print(f"   ⚠️  Required: {stemi_config['is_required']}")
    print(f"   📊 Importance: {stemi_config['importance']}")
    print(f"   🗺️  Territoires ({len(stemi_config['territories'])}): {stemi_config['territories']}")
    print(f"   🪞 Miroirs ({len(stemi_config['mirrors'])}): {stemi_config['mirrors']}")
else:
    print("   ❌ STEMI non trouvé ou sans métadonnées territoire")

# Test 2: NSTEMI (a métadonnées mais importance optionnelle)
print("\n2️⃣  TEST NSTEMI:")
nstemi_config = get_territory_config("NSTEMI", ontology)
if nstemi_config:
    print(f"   ✅ Concept trouvé: {nstemi_config['concept_name']}")
    print(f"   ⚠️  Required: {nstemi_config['is_required']}")
    print(f"   📊 Importance: {nstemi_config['importance']}")
else:
    print("   ❌ NSTEMI non trouvé ou sans métadonnées territoire")

# Test 3: Concept sans métadonnées (ex: "Hypertrophie VG")
print("\n3️⃣  TEST Hypertrophie VG (pas de métadonnées territoire):")
hvg_config = get_territory_config("Hypertrophie VG", ontology)
if hvg_config:
    print(f"   ❌ ERREUR: Hypertrophie VG ne devrait pas avoir de config territoire")
else:
    print("   ✅ Pas de config (attendu)")

# Test 4: Concept inexistant
print("\n4️⃣  TEST concept inexistant:")
fake_config = get_territory_config("ConceptInexistant", ontology)
if fake_config:
    print(f"   ❌ ERREUR: Concept inexistant ne devrait rien retourner")
else:
    print("   ✅ None retourné (attendu)")

print("\n" + "=" * 80)
print("✅ Tests terminés")
