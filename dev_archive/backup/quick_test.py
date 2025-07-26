"""
Test rapide des composants principaux d'Edu-CG
"""
import os
import sys
from pathlib import Path

def test_quick():
    print("🔍 TEST RAPIDE EDU-CG")
    print("=" * 30)
    
    # Vérification de la structure
    current_dir = Path(__file__).parent
    
    # Fichiers critiques
    files_to_check = [
        "frontend/app.py",
        "backend/correction_engine.py", 
        "data/ontologie.owx"
    ]
    
    print("📁 Structure du projet:")
    for file_path in files_to_check:
        full_path = current_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} - MANQUANT")
    
    # Test d'import
    print("\n📦 Test des imports:")
    
    # Streamlit
    try:
        import streamlit
        print(f"  ✅ streamlit {streamlit.__version__}")
    except ImportError:
        print("  ❌ streamlit - pip install streamlit")
    
    # owlready2
    try:
        import owlready2
        print(f"  ✅ owlready2")
    except ImportError:
        print("  ❌ owlready2 - pip install owlready2")
    
    # PIL
    try:
        from PIL import Image
        print(f"  ✅ PIL/Pillow")
    except ImportError:
        print("  ❌ PIL - pip install pillow")
    
    # Test de l'ontologie si possible
    print("\n🧠 Test ontologie:")
    try:
        sys.path.append(str(current_dir / "backend"))
        from correction_engine import OntologyCorrector
        
        ontology_path = current_dir / "data" / "ontologie.owx"
        corrector = OntologyCorrector(str(ontology_path))
        
        print(f"  ✅ Ontologie chargée: {len(corrector.concepts)} concepts")
        
    except Exception as e:
        print(f"  ❌ Erreur ontologie: {e}")
    
    print("\n🚀 Pour lancer l'application:")
    print("    python launch.py")
    print("    ou")
    print("    streamlit run frontend/app.py")

if __name__ == "__main__":
    test_quick()
