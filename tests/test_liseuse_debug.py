#!/usr/bin/env python3
"""
Test de la liseuse ECG pour diagnostic
"""

import sys
from pathlib import Path
import json

# Ajouter les chemins
sys.path.append(str(Path(__file__).parent))

def test_chargement_cas():
    """Test du chargement des cas ECG"""
    
    print("🧪 Test de chargement des cas ECG...")
    
    ecg_dir = Path("data/ecg_cases")
    
    if not ecg_dir.exists():
        print("❌ Le répertoire data/ecg_cases n'existe pas")
        return
    
    print(f"📁 Répertoire trouvé : {ecg_dir.absolute()}")
    
    # Lister les cas
    cases = [d for d in ecg_dir.iterdir() if d.is_dir()]
    print(f"📊 {len(cases)} cas trouvés :")
    
    cas_valides = []
    
    for case_folder in cases:
        print(f"\n📁 Cas : {case_folder.name}")
        
        # Vérifier metadata.json
        metadata_path = case_folder / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                print(f"  ✅ Métadonnées : {metadata.get('type', 'N/A')}")
                print(f"     Age: {metadata.get('age', 'N/A')}, Sexe: {metadata.get('sexe', 'N/A')}")
                print(f"     Statut: {metadata.get('statut', 'N/A')}")
                
                # Vérifier le fichier principal
                filename = metadata.get('filename')
                if filename:
                    file_path = case_folder / filename
                    if file_path.exists():
                        print(f"  ✅ Fichier : {filename} ({file_path.stat().st_size} bytes)")
                        cas_valides.append({
                            'case_id': case_folder.name,
                            'metadata': metadata,
                            'file_path': file_path
                        })
                    else:
                        print(f"  ❌ Fichier manquant : {filename}")
                else:
                    print("  ❌ Nom de fichier manquant dans métadonnées")
                    
            except Exception as e:
                print(f"  ❌ Erreur lecture métadonnées : {e}")
        else:
            print("  ❌ metadata.json manquant")
    
    print(f"\n📊 Résumé : {len(cas_valides)}/{len(cases)} cas valides")
    
    if cas_valides:
        print("\n✅ Cas valides pour la liseuse :")
        for cas in cas_valides:
            print(f"  • {cas['case_id']} - {cas['metadata'].get('type', 'N/A')}")
    else:
        print("\n❌ Aucun cas valide trouvé")
        print("\n🔧 Pour corriger :")
        print("1. Vérifiez que les cas sont bien exportés depuis l'Import Intelligent")
        print("2. Chaque cas doit avoir un metadata.json et un fichier image/XML")
        print("3. Utilisez test_creation_manuel.py pour créer un cas de test")

def test_liseuse_integration():
    """Test d'intégration avec la liseuse"""
    
    print("\n🔗 Test d'intégration liseuse...")
    
    try:
        from frontend.liseuse.liseuse_ecg_fonctionnelle import charger_cas_ecg
        
        cas_ecg = charger_cas_ecg()
        print(f"📚 Liseuse a chargé {len(cas_ecg)} cas")
        
        if cas_ecg:
            print("✅ Premier cas :")
            premier_cas = cas_ecg[0]
            print(f"  • ID: {premier_cas.get('case_id', 'N/A')}")
            print(f"  • Type: {premier_cas.get('type', 'N/A')}")
            print(f"  • Fichier: {premier_cas.get('filename', 'N/A')}")
        else:
            print("❌ Aucun cas chargé par la liseuse")
            
    except ImportError as e:
        print(f"❌ Erreur import liseuse : {e}")
    except Exception as e:
        print(f"❌ Erreur liseuse : {e}")

if __name__ == "__main__":
    test_chargement_cas()
    test_liseuse_integration()
