#!/usr/bin/env python3
"""
🎯 Script de démonstration Edu-CG
Teste le pipeline complet : chargement ontologie → correction → feedback
"""

import sys
import os
from pathlib import Path

# Ajout des chemins pour les imports
project_root = Path(__file__).parent
sys.path.append(str(project_root / "backend"))

from correction_engine import OntologyCorrector

def demo_correction_engine():
    """Démonstration du moteur de correction ECG"""
    
    print("🫀 === DEMO EDU-CG : MOTEUR DE CORRECTION ECG ===\n")
    
    # Chargement de l'ontologie
    ontology_path = project_root / "data" / "ontologie.owx"
    print(f"📂 Chargement de l'ontologie : {ontology_path}")
    
    try:
        corrector = OntologyCorrector(str(ontology_path))
        print(f"✅ Ontologie chargée avec succès !")
        print(f"📊 Nombre de concepts disponibles : {len(corrector.concepts)}\n")
        
        # Affichage des premiers concepts
        concepts = list(corrector.concepts.keys())[:10]
        print("🧠 Premiers concepts ECG disponibles :")
        for i, concept in enumerate(concepts, 1):
            print(f"   {i}. {concept}")
        print()
        
        # Tests de correction
        print("🧪 === TESTS DE CORRECTION ===\n")
        
        if len(concepts) >= 2:
            concept1, concept2 = concepts[0], concepts[1]
            
            # Test 1 : Correspondance exacte
            print("1️⃣ Test correspondance exacte :")
            score = corrector.get_score(concept1, concept1)
            explanation = corrector.explain(concept1, concept1)
            print(f"   Attendu: {concept1}")
            print(f"   Proposé: {concept1}")
            print(f"   → {explanation}\n")
            
            # Test 2 : Concepts différents
            print("2️⃣ Test concepts différents :")
            score = corrector.get_score(concept1, concept2)
            explanation = corrector.explain(concept1, concept2)
            print(f"   Attendu: {concept1}")
            print(f"   Proposé: {concept2}")
            print(f"   → {explanation}\n")
            
            # Test 3 : Concept inexistant
            print("3️⃣ Test concept inexistant :")
            score = corrector.get_score(concept1, "CONCEPT_INEXISTANT")
            explanation = corrector.explain(concept1, "CONCEPT_INEXISTANT")
            print(f"   Attendu: {concept1}")
            print(f"   Proposé: CONCEPT_INEXISTANT")
            print(f"   → {explanation}\n")
        
        # Recherche de relations hiérarchiques
        print("🔍 === ANALYSE DES RELATIONS HIERARCHIQUES ===\n")
        hierarchy_found = False
        
        for concept_name, concept_cls in list(corrector.concepts.items())[:20]:  # Limite pour la démo
            parents = []
            for parent in concept_cls.is_a:
                if hasattr(parent, 'name') and parent.name in corrector.concepts:
                    parents.append(parent.name)
            
            if parents and not hierarchy_found:
                hierarchy_found = True
                parent = parents[0]
                child = concept_name
                
                print(f"🔼 Relation trouvée : {child} → {parent}")
                
                # Test enfant vers parent
                score1 = corrector.get_score(parent, child)
                explanation1 = corrector.explain(parent, child)
                print(f"   Test (parent attendu, enfant proposé) : {explanation1}")
                
                # Test parent vers enfant
                score2 = corrector.get_score(child, parent)
                explanation2 = corrector.explain(child, parent)
                print(f"   Test (enfant attendu, parent proposé) : {explanation2}\n")
                break
        
        if not hierarchy_found:
            print("ℹ️  Aucune relation hiérarchique simple trouvée dans les premiers concepts.\n")
        
        # Mode interactif
        print("🎮 === MODE INTERACTIF ===")
        print("Testez le moteur de correction en temps réel !")
        print("(Tapez 'quit' pour quitter)\n")
        
        while True:
            print(f"Concepts disponibles (exemples) : {', '.join(concepts[:5])}...")
            expected = input("💡 Concept attendu : ").strip()
            
            if expected.lower() == 'quit':
                break
                
            user_input = input("🎯 Votre réponse : ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            explanation = corrector.explain(expected, user_input)
            print(f"   📊 {explanation}\n")
    
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return False
    
    print("🎉 Démonstration terminée ! Le moteur de correction fonctionne correctement.")
    return True

if __name__ == "__main__":
    demo_correction_engine()
