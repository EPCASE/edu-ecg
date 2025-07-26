#!/usr/bin/env python3
"""
Vérification de l'architecture du projet Edu-CG
Test pas à pas des modules
"""

import sys
import os
from pathlib import Path

def check_file_structure():
    """Vérifie la structure des fichiers"""
    print("🏗️  VÉRIFICATION DE L'ARCHITECTURE")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    required_files = {
        "Application principale": "frontend/app.py",
        "WP1 - Import": "frontend/admin/import_cases.py", 
        "WP2 - Liseuse": "frontend/admin/ecg_reader.py",
        "WP3 - Annotation": "frontend/admin/annotation_tool.py",
        "WP4 - Utilisateurs": "frontend/admin/user_management.py",
        "Backend - Ontologie": "backend/correction_engine.py",
        "Données - Ontologie": "data/ontologie.owx",
        "Lanceur": "launch.py"
    }
    
    missing_files = []
    existing_files = []
    
    for name, file_path in required_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            existing_files.append(f"✅ {name}: {file_path}")
        else:
            missing_files.append(f"❌ {name}: {file_path}")
    
    print("📁 FICHIERS EXISTANTS:")
    for file_info in existing_files:
        print(f"   {file_info}")
    
    if missing_files:
        print("\n⚠️  FICHIERS MANQUANTS:")
        for file_info in missing_files:
            print(f"   {file_info}")
    
    return len(missing_files) == 0

def check_dependencies():
    """Vérifie les dépendances Python"""
    print("\n📦 VÉRIFICATION DES DÉPENDANCES")
    print("=" * 40)
    
    dependencies = {
        "streamlit": "Interface web",
        "owlready2": "Ontologie OWL",
        "PIL": "Traitement d'images", 
        "pandas": "Manipulation de données",
        "matplotlib": "Graphiques",
        "numpy": "Calculs numériques"
    }
    
    available_deps = []
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            if dep == "PIL":
                import PIL
            else:
                __import__(dep)
            available_deps.append(f"✅ {dep}: {description}")
        except ImportError:
            missing_deps.append(f"❌ {dep}: {description}")
    
    print("✅ DÉPENDANCES DISPONIBLES:")
    for dep_info in available_deps:
        print(f"   {dep_info}")
    
    if missing_deps:
        print("\n⚠️  DÉPENDANCES MANQUANTES:")
        for dep_info in missing_deps:
            print(f"   {dep_info}")
    
    return len(missing_deps) == 0

def check_work_packages():
    """Vérifie les work packages individuellement"""
    print("\n🔧 VÉRIFICATION DES WORK PACKAGES")
    print("=" * 45)
    
    project_root = Path(__file__).parent
    sys.path.append(str(project_root / "backend"))
    sys.path.append(str(project_root / "frontend" / "admin"))
    
    wp_results = {}
    
    # WP1 - Import
    print("🧪 Test WP1 - Import ECG...")
    try:
        # Test d'import direct du module
        spec = __import__('importlib.util', fromlist=[''])
        module_spec = spec.spec_from_file_location(
            "import_cases", 
            project_root / "frontend" / "admin" / "import_cases.py"
        )
        import_module = spec.module_from_spec(module_spec)
        module_spec.loader.exec_module(import_module)
        
        if hasattr(import_module, 'admin_import_cases'):
            print("   ✅ WP1: Fonction admin_import_cases trouvée")
            wp_results["WP1"] = True
        else:
            print("   ❌ WP1: Fonction admin_import_cases manquante")
            wp_results["WP1"] = False
    except Exception as e:
        print(f"   ❌ WP1: Erreur - {e}")
        wp_results["WP1"] = False
    
    # WP2 - Liseuse ECG
    print("🧪 Test WP2 - Liseuse ECG...")
    try:
        spec = __import__('importlib.util', fromlist=[''])
        module_spec = spec.spec_from_file_location(
            "ecg_reader", 
            project_root / "frontend" / "admin" / "ecg_reader.py"
        )
        reader_module = spec.module_from_spec(module_spec)
        module_spec.loader.exec_module(reader_module)
        
        if hasattr(reader_module, 'ecg_reader_interface'):
            print("   ✅ WP2: Fonction ecg_reader_interface trouvée")
            wp_results["WP2"] = True
        else:
            print("   ❌ WP2: Fonction ecg_reader_interface manquante")
            wp_results["WP2"] = False
    except Exception as e:
        print(f"   ❌ WP2: Erreur - {e}")
        wp_results["WP2"] = False
    
    # WP3 - Ontologie
    print("🧪 Test WP3 - Ontologie...")
    try:
        from correction_engine import OntologyCorrector
        
        ontology_path = project_root / "data" / "ontologie.owx"
        if ontology_path.exists():
            corrector = OntologyCorrector(str(ontology_path))
            concepts_count = len(corrector.concepts)
            print(f"   ✅ WP3: Ontologie chargée - {concepts_count} concepts")
            wp_results["WP3"] = True
        else:
            print("   ❌ WP3: Fichier ontologie.owx non trouvé")
            wp_results["WP3"] = False
    except Exception as e:
        print(f"   ❌ WP3: Erreur - {e}")
        wp_results["WP3"] = False
    
    # WP4 - Gestion utilisateurs
    print("🧪 Test WP4 - Gestion utilisateurs...")
    try:
        spec = __import__('importlib.util', fromlist=[''])
        module_spec = spec.spec_from_file_location(
            "user_management", 
            project_root / "frontend" / "admin" / "user_management.py"
        )
        user_module = spec.module_from_spec(module_spec)
        module_spec.loader.exec_module(user_module)
        
        if hasattr(user_module, 'user_management_interface'):
            print("   ✅ WP4: Fonction user_management_interface trouvée")
            wp_results["WP4"] = True
        else:
            print("   ❌ WP4: Fonction user_management_interface manquante")
            wp_results["WP4"] = False
    except Exception as e:
        print(f"   ❌ WP4: Erreur - {e}")
        wp_results["WP4"] = False
    
    return wp_results

def check_main_app():
    """Vérifie l'application principale"""
    print("\n🚀 VÉRIFICATION APPLICATION PRINCIPALE")
    print("=" * 45)
    
    project_root = Path(__file__).parent
    app_path = project_root / "frontend" / "app.py"
    
    if not app_path.exists():
        print("❌ Fichier app.py non trouvé")
        return False
    
    try:
        # Lecture et vérification du contenu
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            "streamlit",
            "route_admin_pages", 
            "user_management_interface",
            "ecg_reader_interface",
            "admin_import_cases",
            "admin_annotation_tool"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print("❌ Éléments manquants dans app.py:")
            for element in missing_elements:
                print(f"   - {element}")
            return False
        else:
            print("✅ Application principale: Tous les éléments requis présents")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de app.py: {e}")
        return False

def main():
    """Vérification complète de l'architecture"""
    print("🫀 EDU-CG - VÉRIFICATION ARCHITECTURE PROJET")
    print("=" * 60)
    
    # Tests séquentiels
    files_ok = check_file_structure()
    deps_ok = check_dependencies()
    wp_results = check_work_packages()
    app_ok = check_main_app()
    
    # Résumé final
    print("\n📊 RÉSUMÉ DE L'ARCHITECTURE")
    print("=" * 40)
    
    wp_success = sum(wp_results.values())
    total_checks = len(wp_results) + 3  # WP + files + deps + app
    
    print(f"📁 Structure fichiers: {'✅' if files_ok else '❌'}")
    print(f"📦 Dépendances: {'✅' if deps_ok else '❌'}")
    print(f"🚀 Application principale: {'✅' if app_ok else '❌'}")
    print(f"🔧 Work Packages: {wp_success}/4")
    
    for wp, status in wp_results.items():
        print(f"   {wp}: {'✅' if status else '❌'}")
    
    overall_success = files_ok and deps_ok and app_ok and (wp_success == 4)
    
    print(f"\n🎯 STATUT GLOBAL: {'✅ ARCHITECTURE VALIDÉE' if overall_success else '⚠️ CORRECTIONS NÉCESSAIRES'}")
    
    if overall_success:
        print("\n🎉 FÉLICITATIONS ! L'architecture est complète et fonctionnelle.")
        print("🚀 Vous pouvez lancer l'application avec:")
        print("   streamlit run frontend/app.py")
    else:
        print("\n⚠️ Des corrections sont nécessaires avant le lancement.")
    
    return overall_success

if __name__ == "__main__":
    main()
