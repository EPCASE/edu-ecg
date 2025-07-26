"""
Test simple pour vérifier l'état du système Edu-CG
"""
import sys
import os

# Configuration du chemin
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'backend'))

def test_environment():
    """Test des dépendances principales"""
    print("🔍 TEST DE L'ENVIRONNEMENT EDU-CG")
    print("=" * 50)
    
    # Test Python
    print(f"🐍 Python version: {sys.version}")
    
    # Test des imports
    try:
        import streamlit as st
        print("✅ Streamlit importé avec succès")
    except ImportError as e:
        print(f"❌ Streamlit: {e}")
    
    try:
        import owlready2
        print("✅ owlready2 importé avec succès")
    except ImportError as e:
        print(f"❌ owlready2: {e}")
    
    try:
        from PIL import Image
        print("✅ PIL/Pillow importé avec succès")
    except ImportError as e:
        print(f"❌ PIL: {e}")
    
    try:
        import pandas as pd
        print("✅ pandas importé avec succès")
    except ImportError as e:
        print(f"❌ pandas: {e}")

def test_ontology():
    """Test de chargement de l'ontologie"""
    print("\n🧠 TEST DE L'ONTOLOGIE")
    print("=" * 50)
    
    try:
        from backend.correction_engine import OntologyCorrector
        
        # Chemin vers l'ontologie
        ontology_path = os.path.join(current_dir, "data", "ontologie.owx")
        if os.path.exists(ontology_path):
            print(f"✅ Fichier ontologie trouvé: {ontology_path}")
            
            # Test du chargement
            corrector = OntologyCorrector(ontology_path)
            print(f"✅ Ontologie chargée avec {len(corrector.concepts)} concepts")
            
            # Test d'un exemple de scoring
            if len(corrector.concepts) > 0:
                example_concept = list(corrector.concepts.keys())[0]
                score = corrector.get_score(example_concept, example_concept)
                print(f"✅ Test scoring: concept identique = {score}%")
            
        else:
            print(f"❌ Fichier ontologie non trouvé: {ontology_path}")
            
    except Exception as e:
        print(f"❌ Erreur ontologie: {e}")

def test_structure():
    """Test de la structure du projet"""
    print("\n📁 TEST DE LA STRUCTURE")
    print("=" * 50)
    
    required_dirs = [
        "frontend",
        "backend", 
        "data",
        "data/ecg_cases"
    ]
    
    required_files = [
        "frontend/app.py",
        "backend/correction_engine.py",
        "data/ontologie.owx"
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(current_dir, dir_path)
        if os.path.exists(full_path):
            print(f"✅ Dossier: {dir_path}")
        else:
            print(f"❌ Dossier manquant: {dir_path}")
    
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ Fichier: {file_path}")
        else:
            print(f"❌ Fichier manquant: {file_path}")

def test_demo():
    """Test de démonstration rapide"""
    print("\n🎯 TEST DE DÉMONSTRATION")
    print("=" * 50)
    
    try:
        from backend.correction_engine import OntologyCorrector
        
        ontology_path = os.path.join(current_dir, "data", "ontologie.owx")
        corrector = OntologyCorrector(ontology_path)
        
        # Test de quelques concepts
        concepts_test = ["rythme", "frequence", "axe", "repolarisation"]
        available_concepts = [c for c in concepts_test if c in corrector.concepts]
        
        if available_concepts:
            print(f"💡 Concepts disponibles pour test: {available_concepts}")
            
            # Test de scoring entre concepts
            if len(available_concepts) >= 2:
                concept1, concept2 = available_concepts[0], available_concepts[1]
                score = corrector.get_score(concept1, concept2)
                explanation = corrector.explain(concept1, concept2)
                
                print(f"🔍 Comparaison '{concept1}' vs '{concept2}':")
                print(f"   Score: {score}%")
                print(f"   Explication: {explanation}")
        
    except Exception as e:
        print(f"❌ Erreur démonstration: {e}")

if __name__ == "__main__":
    test_environment()
    test_structure()
    test_ontology()
    test_demo()
    
    print("\n🏁 TEST TERMINÉ")
    print("=" * 50)
    print("📊 Résumé: Vérifiez les ❌ ci-dessus pour identifier les problèmes")
    print("🚀 Si tout est ✅, l'application est prête !")
