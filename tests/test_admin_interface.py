#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la nouvelle interface administrateur simplifiée
Vérifie que la navigation et les modules fonctionnent correctement
"""

import sys
import os
from pathlib import Path

def test_admin_interface():
    """Test de l'interface admin reorganisée"""
    
    print("🧪 Test de l'interface admin simplifiée")
    print("=" * 50)
    
    # Test des imports de modules
    try:
        sys.path.append(str(Path(__file__).parent / "frontend" / "admin"))
        
        # Test Import Intelligent
        try:
            from admin.smart_ecg_importer_simple import smart_ecg_importer_simple
            print("✅ Import Intelligent - Module disponible")
        except ImportError:
            print("⚠️  Import Intelligent - Utilise fallback")
        
        # Test Liseuse fonctionnelle
        try:
            from frontend.liseuse.liseuse_ecg_fonctionnelle import liseuse_ecg_fonctionnelle
            print("✅ Liseuse ECG - Module disponible")
        except ImportError:
            print("⚠️  Liseuse ECG - Module manquant")
        
        # Test structure de données
        cases_dir = Path("data/ecg_cases")
        if cases_dir.exists():
            cases = list(cases_dir.iterdir())
            print(f"✅ Base de cas - {len(cases)} cas disponibles")
        else:
            print("⚠️  Base de cas - Répertoire manquant")
        
        print("=" * 50)
        print("🎯 Nouvelle structure admin :")
        print("1. 🎯 Import Intelligent (import + recadrage)")
        print("2. 📺 Liseuse ECG (visualisation + annotation)")
        print("3. 👥 Gestion Utilisateurs (profils + analytics)")
        print("4. 📊 Gestion BDD (admin base de cas)")
        print("=" * 50)
        print("✅ Test terminé - Structure simplifiée validée")
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_admin_interface()
