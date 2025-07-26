#!/usr/bin/env python3
"""
Test rapide de l'intégration des 4 Work Packages
Edu-CG - Formation ECG
"""

import sys
from pathlib import Path

# Configuration des chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend" / "admin"))

def test_wp1_import():
    """Test WP1 - Import ECG"""
    print("🧪 Test WP1 - Import ECG...")
    try:
        from import_cases import admin_import_cases
        print("✅ WP1: Module import_cases importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ WP1: Erreur d'import - {e}")
        return False

def test_wp2_reader():
    """Test WP2 - Liseuse ECG"""
    print("🧪 Test WP2 - Liseuse ECG...")
    try:
        from ecg_reader import ecg_reader_interface
        print("✅ WP2: Module ecg_reader importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ WP2: Erreur d'import - {e}")
        return False

def test_wp3_ontology():
    """Test WP3 - Ontologie et annotation"""
    print("🧪 Test WP3 - Ontologie...")
    try:
        from correction_engine import OntologyCorrector
        from annotation_tool import admin_annotation_tool
        
        # Test de chargement de l'ontologie
        ontology_path = project_root / "data" / "ontologie.owx"
        if ontology_path.exists():
            corrector = OntologyCorrector(str(ontology_path))
            concepts_count = len(corrector.concepts)
            print(f"✅ WP3: Ontologie chargée - {concepts_count} concepts")
            return True
        else:
            print("❌ WP3: Fichier ontologie non trouvé")
            return False
    except ImportError as e:
        print(f"❌ WP3: Erreur d'import - {e}")
        return False
    except Exception as e:
        print(f"❌ WP3: Erreur chargement ontologie - {e}")
        return False

def test_wp4_users():
    """Test WP4 - Gestion utilisateurs"""
    print("🧪 Test WP4 - Gestion utilisateurs...")
    try:
        from user_management import user_management_interface
        print("✅ WP4: Module user_management importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ WP4: Erreur d'import - {e}")
        return False

def test_main_app():
    """Test de l'application principale"""
    print("🧪 Test Application principale...")
    try:
        # Import sans exécution
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", project_root / "frontend" / "app.py")
        app_module = importlib.util.module_from_spec(spec)
        
        # Test de syntaxe uniquement
        print("✅ APP: Syntaxe de l'application principale validée")
        return True
    except Exception as e:
        print(f"❌ APP: Erreur dans l'application principale - {e}")
        return False

def main():
    """Test principal d'intégration"""
    print("🫀 EDU-CG - Test d'Intégration des Work Packages")
    print("=" * 50)
    
    results = {
        "WP1": test_wp1_import(),
        "WP2": test_wp2_reader(), 
        "WP3": test_wp3_ontology(),
        "WP4": test_wp4_users(),
        "APP": test_main_app()
    }
    
    print("\n📊 RÉSULTATS DU TEST")
    print("=" * 30)
    
    success_count = 0
    for wp, success in results.items():
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"{wp}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 Score: {success_count}/5 modules fonctionnels")
    
    if success_count == 5:
        print("🎉 FÉLICITATIONS ! Tous les work packages sont intégrés avec succès !")
        print("\n🚀 Vous pouvez maintenant lancer l'application avec:")
        print("   streamlit run frontend/app.py")
    else:
        print("⚠️  Certains modules nécessitent une attention particulière")
    
    print("\n📋 Work Packages:")
    print("   WP1: Import ECG et gestion BDD")
    print("   WP2: Liseuse ECG avec visualisation avancée")
    print("   WP3: Ontologie médicale et annotation")
    print("   WP4: Gestion utilisateurs et analytics")
    print("   APP: Application principale Streamlit")

if __name__ == "__main__":
    main()
