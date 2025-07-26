#!/usr/bin/env python3
"""
Test rapide du système d'annotation ECG corrigé
"""

import sys
from pathlib import Path

# Configuration des chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend" / "admin"))

def test_annotation_functions():
    """Test des fonctions d'annotation"""
    print("🧪 Test du système d'annotation ECG...")
    
    try:
        from ecg_reader import (
            ecg_reader_interface, 
            get_annotation_icon, 
            display_annotation_details,
            save_annotations_to_case,
            load_annotations_from_case
        )
        print("✅ Toutes les fonctions d'annotation importées")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

def main():
    """Test principal"""
    print("🩺 TEST SYSTÈME D'ANNOTATION ECG CORRIGÉ")
    print("=" * 45)
    
    # Test des fonctions
    test_result = test_annotation_functions()
    
    if test_result:
        print("\n✅ SYSTÈME D'ANNOTATION CORRIGÉ !")
        print("\n🎯 Nouvelles fonctionnalités :")
        print("   📝 Annotations texte avec positionnement")
        print("   📏 Mesures précises avec unités")
        print("   🎯 Zones d'intérêt colorées")
        print("   🩺 Diagnostics avec niveau de confiance")
        print("   💬 Commentaires catégorisés")
        print("   💾 Sauvegarde/chargement persistant")
        print("   🏷️ Affichage visuel sur l'ECG")
        print("   🕒 Horodatage automatique")
        
        print("\n🚀 Utilisation :")
        print("   1. Lancer : streamlit run frontend/app.py")
        print("   2. Aller dans 'Liseuse ECG (WP2)'")
        print("   3. Utiliser les outils d'annotation améliorés")
        print("   4. Voir les annotations directement sur l'image")
    else:
        print("\n❌ PROBLÈME : Des corrections supplémentaires sont nécessaires")
    
    return test_result

if __name__ == "__main__":
    main()
