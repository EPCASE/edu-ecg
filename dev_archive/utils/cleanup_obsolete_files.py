#!/usr/bin/env python3
"""
Nettoyage des fichiers obsolètes à la racine
Organise et archive les fichiers de développement/test
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_archive_structure():
    """Crée la structure d'archivage"""
    
    base_path = Path(".")
    
    # Créer les dossiers d'archive
    archives = {
        "dev_archive": "Archive des fichiers de développement",
        "dev_archive/tests": "Scripts de test et validation",  
        "dev_archive/demos": "Anciens prototypes et démonstrations",
        "dev_archive/utils": "Utilitaires de développement",
        "dev_archive/backup": "Sauvegardes et fichiers historiques"
    }
    
    for folder, description in archives.items():
        folder_path = base_path / folder
        folder_path.mkdir(exist_ok=True)
        
        # Créer un README dans chaque dossier
        readme_path = folder_path / "README.md"
        if not readme_path.exists():
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# {folder.replace('_', ' ').title()}\n\n")
                f.write(f"{description}\n\n")
                f.write(f"Créé le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def analyze_files():
    """Analyse les fichiers à la racine"""
    
    current_files = [f for f in os.listdir(".") if f.endswith('.py')]
    
    # Classification des fichiers
    file_categories = {
        "ESSENTIELS": [
            "launch.py",  # Script de lancement
        ],
        "TESTS": [
            "test_final_buttons.py",
            "test_keyerror_final.py", 
            "test_keyerror_fix.py",
            "test_pdf_support.py",
            "test_pdf_fix.py",
            "test_annotations.py",
            "test_correction_engine.py",
            "test_integration.py",
            "test_ontology.py",
            "test_system.py",
            "check_architecture.py"
        ],
        "OBSOLETES": [
            "demo.py",
            "demo_final.py", 
            "run.py",
            "quick_test.py",
            "validate.py",
            "diagnostic.py",
            "ecg_reader_backup.py"
        ],
        "UTILITAIRES": [
            "fix_rerun.py",
            "get_ontology.py"
        ]
    }
    
    return file_categories

def move_files():
    """Déplace les fichiers vers leurs dossiers d'archive"""
    
    file_categories = analyze_files()
    
    moves = {
        "TESTS": "dev_archive/tests",
        "OBSOLETES": "dev_archive/backup", 
        "UTILITAIRES": "dev_archive/utils"
    }
    
    moved_files = []
    
    for category, target_folder in moves.items():
        files = file_categories.get(category, [])
        
        for filename in files:
            if os.path.exists(filename):
                source = Path(filename)
                target = Path(target_folder) / filename
                
                try:
                    shutil.move(str(source), str(target))
                    moved_files.append((filename, category, target_folder))
                    print(f"✅ {filename} → {target_folder}")
                except Exception as e:
                    print(f"❌ Erreur déplacement {filename}: {e}")
    
    return moved_files

def create_cleanup_summary():
    """Crée un résumé du nettoyage"""
    
    file_categories = analyze_files()
    
    summary = f"""# 🧹 Résumé du nettoyage - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📁 Structure après nettoyage

### ✅ Fichiers essentiels (restent à la racine)
"""
    
    for filename in file_categories["ESSENTIELS"]:
        if os.path.exists(filename):
            summary += f"- `{filename}` - Script de lancement principal\n"
    
    summary += f"""
### 📂 Archives créées

#### `dev_archive/tests/` - Scripts de validation
"""
    for filename in file_categories["TESTS"]:
        if os.path.exists(f"dev_archive/tests/{filename}"):
            summary += f"- `{filename}` - Test de validation\n"

    summary += f"""
#### `dev_archive/backup/` - Fichiers obsolètes  
"""
    for filename in file_categories["OBSOLETES"]:
        if os.path.exists(f"dev_archive/backup/{filename}"):
            summary += f"- `{filename}` - Ancien prototype/backup\n"

    summary += f"""
#### `dev_archive/utils/` - Utilitaires de développement
"""
    for filename in file_categories["UTILITAIRES"]:
        if os.path.exists(f"dev_archive/utils/{filename}"):
            summary += f"- `{filename}` - Utilitaire de développement\n"

    summary += f"""

## 🎯 Avantages du nettoyage

- ✅ **Racine épurée** : Seuls les fichiers essentiels restent visibles
- ✅ **Organisation claire** : Fichiers classés par fonction
- ✅ **Historique préservé** : Aucun fichier supprimé, tout archivé
- ✅ **Documentation** : Chaque archive documentée

## 🚀 Prochaines étapes

1. **Valider** que l'application fonctionne toujours
2. **Tester** `python launch.py` 
3. **Mettre à jour** le README principal
4. **Commiter** les changements

---

*Nettoyage effectué automatiquement par le script de maintenance*
"""
    
    with open("CLEANUP_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(summary)
    
    return summary

def main():
    """Fonction principale de nettoyage"""
    
    print("🧹 === NETTOYAGE FICHIERS OBSOLETES ===\n")
    
    # 1. Créer la structure d'archive
    print("1️⃣ Création structure d'archive...")
    create_archive_structure()
    print("✅ Structure créée\n")
    
    # 2. Analyser les fichiers
    print("2️⃣ Analyse des fichiers...")
    file_categories = analyze_files()
    
    for category, files in file_categories.items():
        print(f"📁 {category}: {len(files)} fichier(s)")
    print()
    
    # 3. Demander confirmation
    print("3️⃣ Déplacement des fichiers...")
    response = input("🤔 Procéder au déplacement ? (o/N): ").lower()
    
    if response in ['o', 'oui', 'y', 'yes']:
        moved_files = move_files()
        print(f"\n✅ {len(moved_files)} fichier(s) déplacé(s)")
    else:
        print("❌ Nettoyage annulé")
        return
    
    # 4. Créer le résumé
    print("\n4️⃣ Création du résumé...")
    summary = create_cleanup_summary()
    print("✅ Résumé créé: CLEANUP_SUMMARY.md")
    
    print("\n🎉 NETTOYAGE TERMINÉ!")
    print("\n📋 Fichiers restants à la racine:")
    remaining = [f for f in os.listdir(".") if f.endswith('.py')]
    for f in remaining:
        print(f"  - {f}")
    
    print(f"\n🚀 L'application reste fonctionnelle avec `python launch.py`")

if __name__ == "__main__":
    main()
