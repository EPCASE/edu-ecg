#!/usr/bin/env python3
"""
Script de test rapide pour valider l'installation
"""

import sys
from pathlib import Path

# Ajouter les chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "backend"))

def test_imports():
    """Test des imports essentiels"""
    
    print("🧪 === TEST DES IMPORTS ===")
    
    # Test Streamlit
    try:
        import streamlit as st
        print("✅ Streamlit:", st.__version__)
    except ImportError as e:
        print("❌ Streamlit:", e)
        return False
    
    # Test Pillow
    try:
        from PIL import Image
        print("✅ Pillow: OK")
    except ImportError as e:
        print("❌ Pillow:", e)
        return False
    
    # Test owlready2
    try:
        from owlready2 import get_ontology
        print("✅ owlready2: OK")
    except ImportError as e:
        print("❌ owlready2:", e)
        return False
    
    # Test correction engine
    try:
        from correction_engine import OntologyCorrector
        print("✅ Backend: OK")
    except ImportError as e:
        print("❌ Backend:", e)
        return False
    
    # Test ontologie
    try:
        ontology_path = project_root / "data" / "ontologie.owx"
        if ontology_path.exists():
            corrector = OntologyCorrector(str(ontology_path))
            print(f"✅ Ontologie: {len(corrector.concepts)} concepts")
        else:
            print(f"❌ Ontologie: fichier non trouvé - {ontology_path}")
            return False
    except Exception as e:
        print("❌ Ontologie:", e)
        return False
    
    return True

def main():
    """Test principal"""
    
    print("🫀 === VALIDATION EDU-CG ===\n")
    
    if test_imports():
        print("\n🎉 === TOUS LES TESTS PASSENT ===")
        print("✅ L'application Edu-CG est prête à être lancée !")
        print("\n🚀 Pour lancer l'application :")
        print("   python run.py")
        print("   ou")
        print("   streamlit run frontend/app.py")
        return True
    else:
        print("\n❌ === ERREURS DÉTECTÉES ===")
        print("Veuillez corriger les erreurs avant de lancer l'application.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
