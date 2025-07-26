#!/usr/bin/env python3
"""
Test de l'export ECG pour debug
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw
import json
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

def test_export_ecg():
    """Test de création d'un ECG"""
    
    print("🧪 Test de l'export ECG...")
    
    # Créer une image de test
    test_image = Image.new('RGB', (400, 300), 'white')
    draw = ImageDraw.Draw(test_image)
    
    # Dessiner quelque chose de simple
    draw.rectangle([10, 10, 390, 290], outline='black', width=2)
    draw.text((50, 150), "ECG Test Export", fill='black')
    
    # Simuler les données de l'export
    case_id = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    cropped_data = {
        'image': test_image,
        'original_filename': 'test_export.png',
        'coordinates': (0, 0, 400, 300)
    }
    
    metadata = {
        'age': 45,
        'sexe': 'M',
        'contexte': 'Test d\'export automatique'
    }
    
    # Exécuter l'export
    print(f"📝 ID du cas : {case_id}")
    success = executer_export_simple(case_id, cropped_data, metadata)
    
    if success:
        print("✅ Export réussi !")
        
        # Vérifier les fichiers créés
        export_dir = Path("data/ecg_cases") / case_id
        if export_dir.exists():
            print(f"📁 Dossier créé : {export_dir}")
            files = list(export_dir.iterdir())
            print("📋 Fichiers créés :")
            for file in files:
                print(f"  • {file.name} ({file.stat().st_size} bytes)")
        else:
            print("❌ Dossier non créé")
    else:
        print("❌ Export échoué")

def executer_export_simple(case_id, cropped_data, metadata):
    """Version simplifiée de l'export pour test"""
    
    try:
        # Créer le répertoire de destination
        export_dir = Path("data/ecg_cases") / case_id
        export_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Création dans : {export_dir.absolute()}")
        
        # Sauvegarder l'image
        filename = f"{case_id}.png"
        image_path = export_dir / filename
        
        if 'image' not in cropped_data or cropped_data['image'] is None:
            print("❌ Aucune image à sauvegarder")
            return False
            
        cropped_data['image'].save(image_path, 'PNG', optimize=True)
        print(f"✅ Image sauvegardée : {filename}")
        
        # Métadonnées JSON
        metadata_json = {
            'case_id': case_id,
            'filename': filename,
            'created_date': datetime.now().isoformat(),
            'type': 'image',
            'age': metadata.get('age', 0),
            'sexe': metadata.get('sexe', 'Non spécifié'),
            'contexte': metadata.get('contexte', 'ECG importé'),
            'diagnostic': 'À analyser',
            'statut': 'imported',
            'metadata': {
                'source_file': cropped_data.get('original_filename', 'unknown'),
                'import_method': 'test_export',
                'crop_coordinates': cropped_data.get('coordinates', None)
            }
        }
        
        metadata_path = export_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_json, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Métadonnées sauvegardées : metadata.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur export : {e}")
        print(f"🔍 Type d'erreur : {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_export_ecg()
