"""
Script pour mapper les templates Epic 1 vers l'ontologie OWL
et ajouter les synonymes manquants
"""
import json
from pathlib import Path

# Charger ontologie OWL
with open('data/ontology_from_owl.json', encoding='utf-8') as f:
    owl_data = json.load(f)

# Charger templates Epic 1
with open('data/case_templates_epic1.json', encoding='utf-8') as f:
    templates_data = json.load(f)

mappings = owl_data['concept_mappings']

# Fonction de recherche dans l'ontologie
def find_in_ontology(search_term):
    """Cherche un concept dans l'ontologie (case-insensitive, partial match)"""
    results = []
    search_lower = search_term.lower()
    
    for ontology_id, mapping in mappings.items():
        concept_name = mapping['concept_name'].lower()
        
        # Match exact ou contient
        if search_lower == concept_name or search_lower in concept_name or concept_name in search_lower:
            results.append({
                'ontology_id': ontology_id,
                'concept_name': mapping['concept_name'],
                'poids': mapping['poids'],
                'categorie': mapping['categorie'],
                'score': 100 if search_lower == concept_name else 50
            })
    
    # Trier par score (exact d'abord)
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

print("=" * 100)
print("MAPPING TEMPLATES EPIC 1 vers ONTOLOGIE OWL")
print("=" * 100)

# Analyser chaque template
for template in templates_data['templates']:
    case_id = template['case_id']
    diagnostic = template['diagnostic_principal']
    expected = template['expected_concepts']
    
    print(f"\n{'='*100}")
    print(f"📋 CAS: {case_id}")
    print(f"🎯 Diagnostic: {diagnostic}")
    print(f"{'='*100}")
    
    # Chercher le diagnostic principal dans l'ontologie
    print(f"\n🔍 Recherche diagnostic principal: '{diagnostic}'")
    results = find_in_ontology(diagnostic)
    if results:
        best = results[0]
        print(f"  ✅ TROUVÉ: {best['concept_name']} (poids {best['poids']}, {best['categorie']})")
    else:
        print(f"  ❌ NON TROUVÉ - Besoin de l'ajouter à l'ontologie")
    
    # Chercher chaque concept attendu
    print(f"\n📝 Concepts attendus ({len(expected)}):")
    suggestions = []
    
    for concept in expected:
        print(f"\n  🔍 '{concept}'")
        results = find_in_ontology(concept)
        
        if results:
            best = results[0]
            emoji = {4: '🚨', 3: '⚡', 2: '⚠️', 1: '📝'}.get(best['poids'], '📝')
            print(f"     ✅ {emoji} {best['concept_name']} (poids {best['poids']})")
            
            suggestions.append({
                'template_concept': concept,
                'owl_concept': best['concept_name'],
                'ontology_id': best['ontology_id'],
                'poids': best['poids'],
                'categorie': best['categorie']
            })
        else:
            print(f"     ❌ NON TROUVÉ dans l'ontologie")
            print(f"     💡 Suggestion: Ajouter '{concept}' comme synonyme dans l'ontologie")
    
    # Afficher résumé pour ce cas
    if suggestions:
        print(f"\n  📊 RÉSUMÉ - {len(suggestions)}/{len(expected)} concepts trouvés:")
        total_poids = sum(s['poids'] for s in suggestions)
        print(f"     Total poids: {total_poids} points")
        
        # Grouper par catégorie
        by_cat = {}
        for s in suggestions:
            cat = s['categorie']
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(s)
        
        for cat, cat_items in sorted(by_cat.items(), key=lambda x: x[1][0]['poids'], reverse=True):
            emoji = {4: '🚨', 3: '⚡', 2: '⚠️', 1: '📝'}.get(cat_items[0]['poids'], '📝')
            print(f"     {emoji} {cat}: {len(cat_items)} concepts")

print("\n" + "=" * 100)
print("RECOMMANDATIONS")
print("=" * 100)

print("""
🎯 OPTION 1: Enrichir l'ontologie OWL
   - Ajouter les concepts manquants dans Protégé
   - Ajouter des synonymes (ex: "bav 2 mobitz 1" → "Bloc auriculo-ventriculaire du second degré Mobitz 1")
   - Re-exporter et reconvertir

📝 OPTION 2: Modifier les templates
   - Utiliser les labels exacts de l'ontologie OWL
   - Remplacer les concepts manquants par leurs équivalents trouvés
   - Exemple: "ecg normal" au lieu de 6 descripteurs séparés

⚙️ OPTION 3: Ajouter des synonymes dans le JSON
   - Modifier concept_mappings dans ontology_from_owl.json
   - Ajouter les termes courants comme synonymes

🚀 RECOMMANDATION: Commencer par Option 2 (modifier templates)
   C'est le plus rapide pour tester le système pondéré maintenant.
""")
