#!/usr/bin/env python3
"""
Test rapide de création d'ECG et vérification dans la liseuse
"""

from pathlib import Path
import json
from datetime import datetime
from PIL import Image, ImageDraw

def test_creation_cas_simple():
    """Crée un cas simple pour test"""
    
    print("🧪 Test de création d'un cas ECG simple...")
    
    # ID du cas
    case_id = f"test_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Créer le répertoire
    case_dir = Path("data/ecg_cases") / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Créer une image simple
    img = Image.new('RGB', (600, 400), 'white')
    draw = ImageDraw.Draw(img)
    
    # Fond quadrillé
    for x in range(0, 600, 25):
        draw.line([(x, 0), (x, 400)], fill='#ffdddd', width=1)
    for y in range(0, 400, 25):
        draw.line([(0, y), (600, y)], fill='#ffdddd', width=1)
    
    # Tracé ECG simple
    points = []
    for x in range(0, 600, 4):
        y = 200 + 30 * (1 if (x % 100) < 10 else 0)  # Spikes simples
        points.append((x, y))
    
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill='red', width=2)
    
    draw.text((50, 50), f"ECG Test Manuel - {case_id}", fill='black')
    draw.text((50, 350), "Test de l'export manuel", fill='gray')
    
    # Sauvegarder l'image
    image_path = case_dir / f"{case_id}.png"
    img.save(image_path, 'PNG')
    
    # Métadonnées
    metadata = {
        'case_id': case_id,
        'filename': f"{case_id}.png",
        'created_date': datetime.now().isoformat(),
        'type': 'image',
        'age': 55,
        'sexe': 'M',
        'contexte': 'Test manuel de création de cas',
        'diagnostic': 'ECG de test - À analyser',
        'statut': 'imported',
        'metadata': {
            'source_file': 'test_manual.py',
            'import_method': 'test_manuel',
            'image_size': [600, 400]
        }
    }
    
    # Sauvegarder métadonnées
    metadata_path = case_dir / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cas créé : {case_id}")
    print(f"📁 Dossier : {case_dir}")
    print(f"📋 Fichiers :")
    print(f"  • {image_path.name} ({image_path.stat().st_size} bytes)")
    print(f"  • {metadata_path.name} ({metadata_path.stat().st_size} bytes)")
    
    return case_id

def verifier_structure_liseuse():
    """Vérifie la structure pour la liseuse"""
    
    print("\n🔍 Vérification de la structure ECG...")
    
    ecg_dir = Path("data/ecg_cases")
    if not ecg_dir.exists():
        print("❌ Répertoire data/ecg_cases n'existe pas")
        return
    
    cases = [d for d in ecg_dir.iterdir() if d.is_dir()]
    print(f"📊 {len(cases)} cas trouvés :")
    
    for case_dir in cases:
        print(f"\n📁 {case_dir.name}")
        
        # Vérifier metadata.json
        metadata_path = case_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                print(f"  ✅ metadata.json - {metadata.get('type', 'N/A')}")
                print(f"     Age: {metadata.get('age', 'N/A')}, Sexe: {metadata.get('sexe', 'N/A')}")
            except Exception as e:
                print(f"  ❌ metadata.json - Erreur: {e}")
        else:
            print("  ❌ metadata.json manquant")
        
        # Vérifier fichier principal
        files = list(case_dir.glob("*.png")) + list(case_dir.glob("*.jpg")) + list(case_dir.glob("*.xml"))
        if files:
            for file in files:
                print(f"  ✅ {file.name} ({file.stat().st_size} bytes)")
        else:
            print("  ❌ Aucun fichier ECG trouvé")

if __name__ == "__main__":
    # Créer un cas de test
    case_id = test_creation_cas_simple()
    
    # Vérifier la structure
    verifier_structure_liseuse()
    
    print(f"\n🎯 Test terminé. Cas créé : {case_id}")
    print("💡 Vous pouvez maintenant tester dans la liseuse ECG")
