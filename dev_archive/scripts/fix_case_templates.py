"""
Script de correction des cas Epic 1
Remplace les noms longs par les noms exacts de l'ontologie OWL

Auteur: BMAD Master
Date: 2026-01-10
"""

import json
from pathlib import Path

# Mapping des noms incorrects → noms corrects dans l'ontologie
CORRECTIONS = {
    "Bloc auriculo-ventriculaire du second degré mobitz 1": "BAV 2 Mobitz 1",
    "Bloc auriculo-ventriculaire du second degré mobitz 2": "BAV 2 Mobitz 2",
    "Bloc auriculo-ventriculaire du premier degré": "BAV de type 1",
    "Hémibloc antérieur gauche": "Bloc fasciculaire antérieur gauche",
    # Les noms déjà corrects (pas de changement nécessaire)
    # "Syndrome coronarien à la phase aigue sans élévation du segment ST"
    # "Fibrillation atriale"
    # "Bloc de branche droit"
    # "Bloc de branche gauche"
    # "Tachycardie sinusale"
    # "Hypertrophie atriale gauche"
}

def correct_case_file():
    """Corrige le fichier case_templates_epic1.json"""
    
    file_path = Path("data/case_templates_epic1.json")
    
    # Charger
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    corrections_made = 0
    
    # Parcourir chaque cas
    for template in data['templates']:
        case_id = template['case_id']
        
        # Corriger expected_concepts
        new_concepts = []
        for concept in template['expected_concepts']:
            if concept in CORRECTIONS:
                corrected = CORRECTIONS[concept]
                if corrected != concept:
                    print(f"✅ {case_id}: '{concept}' → '{corrected}'")
                    corrections_made += 1
                new_concepts.append(corrected)
            else:
                new_concepts.append(concept)
        
        template['expected_concepts'] = new_concepts
        
        # Corriger implications (clés)
        if 'implications' in template:
            new_implications = {}
            for old_key, value in template['implications'].items():
                new_key = CORRECTIONS.get(old_key, old_key)
                if new_key != old_key:
                    print(f"✅ {case_id} (impl): '{old_key}' → '{new_key}'")
                    corrections_made += 1
                new_implications[new_key] = value
            template['implications'] = new_implications
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Terminé ! {corrections_made} corrections effectuées")
    print(f"📁 Fichier mis à jour: {file_path}")

if __name__ == "__main__":
    correct_case_file()
