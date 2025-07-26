#!/usr/bin/env python3
"""
🔧 Installation automatique des modules Analytics
Script pour installer les dépendances manquantes
"""

import subprocess
import sys
import importlib

def check_module(module_name):
    """Vérifie si un module est installé"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_package(package):
    """Installe un package via pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🔧 Vérification des modules Analytics...")
    print("=" * 50)
    
    modules_to_check = {
        'plotly': 'plotly>=5.17.0',
        'pandas': 'pandas>=2.0.0'
    }
    
    missing_modules = []
    
    for module, package in modules_to_check.items():
        if check_module(module):
            print(f"✅ {module} - OK")
        else:
            print(f"❌ {module} - MANQUANT")
            missing_modules.append(package)
    
    if not missing_modules:
        print("\n🎉 Tous les modules sont installés !")
        return
    
    print(f"\n📦 Installation de {len(missing_modules)} module(s)...")
    
    for package in missing_modules:
        print(f"Installation de {package}...")
        if install_package(package):
            print(f"✅ {package} installé avec succès")
        else:
            print(f"❌ Erreur lors de l'installation de {package}")
    
    print("\n🔄 Redémarrez l'application pour utiliser les nouveaux modules.")
    print("=" * 50)

if __name__ == "__main__":
    main()
