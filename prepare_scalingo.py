#!/usr/bin/env python3
"""
Script de préparation pour le déploiement Scalingo
Vérifie que tout est prêt pour le déploiement
"""

import os
import sys
import subprocess

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} manquant: {filepath}")
        return False

def check_git_repo():
    """Vérifie que le repository git est initialisé"""
    if os.path.exists('.git'):
        print("✅ Repository git initialisé")
        return True
    else:
        print("❌ Repository git non initialisé")
        print("   Exécutez: git init")
        return False

def check_dependencies():
    """Vérifie que les dépendances principales sont disponibles"""
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} installé")
        
        import pandas
        print(f"✅ Pandas {pandas.__version__} installé")
        
        import numpy
        print(f"✅ Numpy {numpy.__version__} installé")
        
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        return False

def main():
    """Vérification complète avant déploiement"""
    print("🚀 Vérification pré-déploiement Scalingo")
    print("=" * 50)
    
    checks = []
    
    # Vérifier les fichiers essentiels
    checks.append(check_file_exists("Procfile", "Procfile"))
    checks.append(check_file_exists("runtime.txt", "Runtime Python"))
    checks.append(check_file_exists("requirements.txt", "Requirements"))
    checks.append(check_file_exists("app.json", "Configuration Scalingo"))
    checks.append(check_file_exists("frontend/app.py", "Application principale"))
    
    # Vérifier la structure
    checks.append(check_file_exists("data/ontologie.owx", "Ontologie ECG"))
    checks.append(check_file_exists("backend/correction_engine.py", "Moteur de correction"))
    
    # Vérifier git
    checks.append(check_git_repo())
    
    # Vérifier les dépendances
    checks.append(check_dependencies())
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("🎉 PRÊT POUR LE DÉPLOIEMENT!")
        print("\nCommandes de déploiement:")
        print("1. git add .")
        print("2. git commit -m 'Version prête pour Scalingo'")
        print("3. git push scalingo main")
        print("\nConsultez GUIDE_SCALINGO_DEPLOY.md pour les détails")
        return 0
    else:
        print("❌ Problèmes détectés - résolvez-les avant le déploiement")
        return 1

if __name__ == "__main__":
    sys.exit(main())
