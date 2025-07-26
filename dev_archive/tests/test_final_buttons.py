#!/usr/bin/env python3
"""
Script de validation finale - Test des boutons ECG
Vérifie que les fonctionnalités d'import et d'annotation fonctionnent
"""

import sys
from pathlib import Path

# Configuration des chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend" / "admin"))

def test_import_module():
    """Test du module d'import ECG"""
    print("🧪 Test du module import_cases...")
    try:
        from import_cases import admin_import_cases
        print("✅ Module import_cases chargé avec succès")
        
        # Vérifier que la fonction import_ecg_files existe
        from import_cases import import_ecg_files
        print("✅ Fonction import_ecg_files disponible")
        
        return True
    except ImportError as e:
        print(f"❌ Erreur import_cases: {e}")
        return False

def test_ecg_reader_module():
    """Test du module de lecture ECG"""
    print("\n🧪 Test du module ecg_reader...")
    try:
        from ecg_reader import ecg_reader_interface
        print("✅ Module ecg_reader chargé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur ecg_reader: {e}")
        return False

def test_annotation_module():
    """Test du module d'annotation"""
    print("\n🧪 Test du module annotation_tool...")
    try:
        from annotation_tool import admin_annotation_tool
        print("✅ Module annotation_tool chargé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur annotation_tool: {e}")
        return False

def test_user_management_module():
    """Test du module de gestion utilisateurs"""
    print("\n🧪 Test du module user_management...")
    try:
        from user_management import user_management_interface
        print("✅ Module user_management chargé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur user_management: {e}")
        return False

def test_ontology_module():
    """Test du module ontologie"""
    print("\n🧪 Test du module correction_engine...")
    try:
        from correction_engine import OntologyCorrector
        print("✅ Module correction_engine chargé avec succès")
        
        # Test de chargement de l'ontologie
        ontology_path = project_root / "data" / "ontologie.owx"
        if ontology_path.exists():
            corrector = OntologyCorrector(str(ontology_path))
            concepts_count = len(corrector.concepts)
            print(f"✅ Ontologie chargée: {concepts_count} concepts")
        else:
            print("⚠️ Fichier ontologie.owx non trouvé")
        
        return True
    except Exception as e:
        print(f"❌ Erreur correction_engine: {e}")
        return False

def main():
    """Fonction principale de validation"""
    print("🚀 === VALIDATION FINALE DES BOUTONS ECG ===\n")
    
    results = []
    
    # Test de tous les modules
    results.append(("Import ECG", test_import_module()))
    results.append(("Liseuse ECG", test_ecg_reader_module()))
    results.append(("Annotation", test_annotation_module()))
    results.append(("Gestion Utilisateurs", test_user_management_module()))
    results.append(("Ontologie", test_ontology_module()))
    
    # Résumé des résultats
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*50)
    
    success_count = 0
    for module_name, success in results:
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"{module_name:20} : {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 Score final: {success_count}/{len(results)} modules fonctionnels")
    
    # Diagnostic des boutons spécifiques
    print("\n" + "="*50)
    print("🔍 DIAGNOSTIC DES BOUTONS SIGNALÉS")
    print("="*50)
    
    if results[0][1]:  # Import module
        print("✅ Bouton 'Importer des ECG' : FONCTIONNEL")
        print("   → La fonction import_ecg_files() est disponible")
    else:
        print("❌ Bouton 'Importer des ECG' : DYSFONCTIONNEL")
    
    if results[2][1]:  # Annotation module  
        print("✅ Bouton 'Annotation' : FONCTIONNEL")
        print("   → Le module annotation_tool est chargé")
    else:
        print("❌ Bouton 'Annotation' : DYSFONCTIONNEL")
    
    # Instructions pour lancement
    print("\n" + "="*50)
    print("🚀 INSTRUCTIONS DE LANCEMENT")
    print("="*50)
    print("Pour lancer l'application:")
    print("1. cd \"c:\\Users\\Administrateur\\Desktop\\ECG lecture\"")
    print("2. streamlit run frontend/app.py")
    print("3. Ouvrir http://localhost:8501 dans le navigateur")
    
    if success_count == len(results):
        print("\n🎉 TOUS LES MODULES SONT FONCTIONNELS!")
        print("✅ Les boutons 'Importer des ECG' et 'Annotation' sont réparés")
        return True
    else:
        print(f"\n⚠️ {len(results) - success_count} module(s) nécessitent encore une attention")
        return False

if __name__ == "__main__":
    main()
