#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage et réorganisation de l'architecture Edu-CG
Nettoie les fichiers obsolètes et organise l'architecture finale
"""

import os
import shutil
from pathlib import Path

def organize_architecture():
    """Réorganise l'architecture finale Edu-CG"""
    
    print("🧹 Nettoyage et réorganisation architecture Edu-CG")
    print("=" * 60)
    
    # Dossiers de destination
    archives_dir = Path("dev_archive")
    tests_dir = Path("tests")
    docs_dir = Path("docs")
    
    # Créer les dossiers si nécessaire
    tests_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)
    
    # 1. FICHIERS ESSENTIELS À GARDER À LA RACINE
    essential_files = {
        "frontend/app.py",
        "backend/correction_engine.py", 
        "data/",
        "users/",
        "launch.py",
        "launch_safe.py",
        "launch_light.py",
        "requirements.txt", 
        "requirements_full.txt",
        "README.md",
        ".streamlit/",
        ".conda/"
    }
    
    # 2. FICHIERS DE TEST À DÉPLACER VERS tests/
    test_files = [
        "test_admin_interface.py",
        "test_app_syntax.py", 
        "test_creation_manuel.py",
        "test_ecg_rapide.py",
        "test_export_debug.py",
        "test_import_intelligent.py",
        "test_interface_epuree.py",
        "test_liseuse_debug.py",
        "test_liseuse_navigation.py",
        "test_navigation_liseuse.py",
        "test_pdfplumber.py",
        "test_pdf_intelligent.py",
        "test_pymupdf.py",
        "launch_app_test.py"
    ]
    
    # 3. FICHIERS OBSOLÈTES À ARCHIVER
    obsolete_files = [
        "correction_engine.py",  # Doublon (existe dans backend/)
        "creer_cas_test.py",
        "diagnostic_pdfjs.py", 
        "import_ecg_rapide.py",
        "install_poppler.py",
        "liseuse_ecg_simple.py",
        "pdf_sans_poppler.py",
        "solution_pdfjs_complete.py"
    ]
    
    # 4. DOCUMENTATION À ORGANISER
    doc_files = [
        "ALTERNATIVES_POPPLER.md",
        "ANNOTATION_FIXEE.md", 
        "ARCHITECTURE_VALIDEE.md",
        "FINI_ERREURS_PDF.md",
        "FIX_PATH_ERROR.md",
        "GUIDE_SOLUTION_PDFJS.md",
        "IMPORT_INTELLIGENT_COMPLETE.md",
        "PROJET_STATUS_FINAL.md", 
        "SOLUTION_FINALE_PDFJS.md",
        "SOLUTION_PDF_MODERNE.md",
        "Projet ECG ontologie et correction automatique.docx"
    ]
    
    # 5. FICHIERS DE LANCEMENT À ORGANISER
    launch_files = [
        "launch.bat",
        "launch_light.bat", 
        "launch_safe.bat",
        "stop_app.bat"
    ]
    
    print("📂 Déplacement des fichiers de test...")
    for test_file in test_files:
        if Path(test_file).exists():
            try:
                shutil.move(test_file, tests_dir / test_file)
                print(f"   ✅ {test_file} → tests/")
            except Exception as e:
                print(f"   ⚠️  Erreur {test_file}: {e}")
    
    print("📚 Déplacement de la documentation...")
    for doc_file in doc_files:
        if Path(doc_file).exists():
            try:
                shutil.move(doc_file, docs_dir / doc_file)
                print(f"   ✅ {doc_file} → docs/")
            except Exception as e:
                print(f"   ⚠️  Erreur {doc_file}: {e}")
    
    print("🗄️  Archivage des fichiers obsolètes...")
    for obs_file in obsolete_files:
        if Path(obs_file).exists():
            try:
                shutil.move(obs_file, archives_dir / obs_file)
                print(f"   ✅ {obs_file} → dev_archive/")
            except Exception as e:
                print(f"   ⚠️  Erreur {obs_file}: {e}")
    
    print("🧹 Nettoyage des fichiers temporaires...")
    # Supprimer __pycache__ à la racine
    if Path("__pycache__").exists():
        shutil.rmtree("__pycache__")
        print("   ✅ __pycache__/ supprimé")
    
    print("=" * 60)
    print("✅ ARCHITECTURE FINALE ORGANISÉE")
    print()
    
    print("📁 STRUCTURE FINALE:")
    print("├── 🖥️  frontend/          # Interface utilisateur")
    print("├── 🧠 backend/           # Logique métier")  
    print("├── 📊 data/              # Données et ontologie")
    print("├── 👥 users/             # Profils utilisateurs")
    print("├── 🧪 tests/             # Scripts de test")
    print("├── 📚 docs/              # Documentation")
    print("├── 🗄️  dev_archive/       # Fichiers obsolètes")
    print("├── 🚀 launch*.py         # Scripts de lancement")
    print("├── 📋 requirements*.txt  # Dépendances")
    print("└── 📖 README.md          # Documentation principale")
    print()
    print("🎯 Architecture propre et maintenable validée !")

if __name__ == "__main__":
    organize_architecture()
