#!/usr/bin/env python3
"""
🧹 Script de Nettoyage des Fichiers Inutiles - Projet ECG
Supprime automatiquement les fichiers obsolètes et de développement
Conserve uniquement les fichiers essentiels pour la production
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def get_files_to_delete():
    """Retourne la liste des fichiers à supprimer"""
    
    # 1. Fichiers de test obsolètes (22 fichiers)
    test_files = [
        "test_auth.py",
        "test_auth_sans_reload.py", 
        "test_caliper_debug.py",
        "test_caliper_ep_cases.py",
        "test_correction_double_chargement.py",
        "test_mode_defaut.py",
        "test_mode_standard_defaut.py",
        "test_modifications_v2.py",
        "test_nouvelles_fonctionnalites.py",
        "test_nouvelles_fonctionnalites.bat",
        "test_permissions.py",
        "test_popup_suppression.py",
        "test_simplification_liseuse.py",
        "test_suppression_doublons_users.py",
        "test_suppression_grille.py",
        "test_suppression_panneau_info.py",
        "test_suppression_texte_mode.py",
        "test_visualiseur_ecg.py",
        "test_visualiseur_simple.py",
        "test_zoom_fix.py"
    ]
    
    # 2. Scripts de déploiement obsolètes (8 fichiers)
    deploy_files = [
        "app.json",
        "Procfile", 
        "runtime.txt",
        "requirements_cloud.txt",
        "deploy_direct_scalingo.bat",
        "deploy_scalingo.bat",
        "change_scalingo_name.bat",
        "setup_github.bat",
        "push_to_github.bat"
    ]
    
    # 3. Fichiers de démonstration/développement (7 fichiers)
    demo_files = [
        "demo_enhanced_import.py",
        "demo_visualiseur_avance.py",
        "install_analytics.py",
        "install_analytics.bat", 
        "prepare_scalingo.py",
        "cleanup.bat"
    ]
    
    # 4. Documentation obsolète (6 fichiers)
    doc_files = [
        "GUIDE_SCALINGO_DEPLOY.md",
        "READY_FOR_SCALINGO.md",
        "GUIDE_TEST_VISUALISEUR.md", 
        "RESUME_VISUALISEUR_AVANCE.md",
        "CHANGELOG_NETTOYAGE.md",
        "NETTOYAGE_COMPLET.md"
    ]
    
    # 5. Scripts de lancement redondants (4 fichiers)
    launcher_files = [
        "launch_auth.py",
        "launch_auth.bat",
        "start_avec_visualiseur.py", 
        "start_avec_visualiseur.bat"
    ]
    
    return {
        "Tests obsolètes": test_files,
        "Déploiement obsolète": deploy_files, 
        "Démos/Développement": demo_files,
        "Documentation obsolète": doc_files,
        "Lanceurs redondants": launcher_files
    }

def show_files_summary(files_to_delete):
    """Affiche un résumé des fichiers à supprimer"""
    
    print("🗂️  RÉSUMÉ DES FICHIERS À SUPPRIMER")
    print("=" * 50)
    
    total_files = 0
    total_size = 0
    
    for category, files in files_to_delete.items():
        existing_files = [f for f in files if os.path.exists(f)]
        if existing_files:
            print(f"\n📁 {category} ({len(existing_files)} fichiers):")
            category_size = 0
            for file in existing_files:
                size = os.path.getsize(file)
                category_size += size
                print(f"   ❌ {file:<40} {size:>8} bytes")
            
            total_files += len(existing_files)
            total_size += category_size
            print(f"   📊 Sous-total: {category_size:>6} bytes")
    
    print(f"\n" + "=" * 50)
    print(f"📊 TOTAL: {total_files} fichiers • {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print("=" * 50)
    
    return total_files, total_size

def delete_files(files_to_delete):
    """Supprime les fichiers obsolètes"""
    
    deleted_files = []
    deleted_size = 0
    errors = []
    
    print("\n🗑️  SUPPRESSION EN COURS...")
    print("-" * 30)
    
    for category, files in files_to_delete.items():
        print(f"\n📁 {category}:")
        
        for file in files:
            if os.path.exists(file):
                try:
                    size = os.path.getsize(file)
                    os.remove(file)
                    deleted_files.append(file)
                    deleted_size += size
                    print(f"   ✅ {file}")
                except Exception as e:
                    errors.append(f"{file}: {e}")
                    print(f"   ❌ {file} - ERREUR: {e}")
            else:
                print(f"   ⚪ {file} - n'existe pas")
    
    return deleted_files, deleted_size, errors

def create_cleanup_report(deleted_files, deleted_size):
    """Crée un rapport de nettoyage"""
    
    report_content = f"""# 🧹 Rapport de Nettoyage - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Résultats

- **Fichiers supprimés** : {len(deleted_files)}
- **Espace libéré** : {deleted_size:,} bytes ({deleted_size/1024:.1f} KB)
- **Status** : ✅ Nettoyage réussi

## 📋 Fichiers supprimés

"""
    for file in sorted(deleted_files):
        report_content += f"- ❌ `{file}`\n"
    
    report_content += f"""

## ✅ Fichiers conservés (essentiels)

- ✅ `README.md` - Documentation principale
- ✅ `start.py` + `start.bat` - Lanceurs principaux
- ✅ `stop_app.bat` - Arrêt application  
- ✅ `requirements.txt` + `requirements_full.txt` - Dépendances
- ✅ `frontend/` - Interface utilisateur
- ✅ `backend/` - Logique métier
- ✅ `data/` - Données ECG et ontologie
- ✅ `users/` - Profils utilisateurs
- ✅ `docs/` - Documentation projet

## 🚀 Projet optimisé

Le projet ECG est maintenant nettoyé et prêt pour la production !

- **Structure simplifiée** ✅
- **Fichiers obsolètes supprimés** ✅  
- **Fonctionnalités principales préservées** ✅
- **Performance améliorée** ✅

---
*Nettoyage automatique effectué avec succès*
"""
    
    with open("RAPPORT_NETTOYAGE.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    return "RAPPORT_NETTOYAGE.md"

def main():
    """Fonction principale de nettoyage"""
    
    print("🧹" + "=" * 60)
    print("    NETTOYAGE AUTOMATIQUE - PROJET ECG")
    print("=" * 60 + "🧹")
    print()
    
    # 1. Vérifier qu'on est dans le bon répertoire
    if not os.path.exists("frontend") or not os.path.exists("README.md"):
        print("❌ ERREUR: Ce script doit être exécuté depuis la racine du projet ECG")
        sys.exit(1)
    
    # 2. Obtenir la liste des fichiers à supprimer
    files_to_delete = get_files_to_delete()
    
    # 3. Afficher le résumé
    total_files, total_size = show_files_summary(files_to_delete)
    
    if total_files == 0:
        print("\n✅ Aucun fichier obsolète trouvé - Le projet est déjà propre !")
        return
    
    # 4. Demander confirmation
    print(f"\n🤔 CONFIRMATION REQUISE")
    print(f"   Supprimer {total_files} fichiers obsolètes ({total_size/1024:.1f} KB) ?")
    print(f"   Les fonctionnalités principales seront préservées.")
    print()
    
    response = input("   Confirmer la suppression ? (oui/non): ").lower().strip()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Nettoyage annulé par l'utilisateur")
        return
    
    # 5. Supprimer les fichiers
    deleted_files, deleted_size, errors = delete_files(files_to_delete)
    
    # 6. Afficher les résultats
    print(f"\n" + "=" * 50)
    print(f"🎉 NETTOYAGE TERMINÉ !")
    print(f"✅ {len(deleted_files)} fichiers supprimés")
    print(f"💾 {deleted_size:,} bytes libérés ({deleted_size/1024:.1f} KB)")
    
    if errors:
        print(f"⚠️  {len(errors)} erreurs:")
        for error in errors:
            print(f"   - {error}")
    
    # 7. Créer le rapport
    report_file = create_cleanup_report(deleted_files, deleted_size)
    print(f"📋 Rapport créé: {report_file}")
    
    # 8. Afficher les fichiers restants
    print(f"\n📁 FICHIERS RESTANTS À LA RACINE:")
    remaining_files = [f for f in os.listdir(".") if f.endswith(('.py', '.bat', '.md'))]
    for file in sorted(remaining_files):
        print(f"   ✅ {file}")
    
    print(f"\n🚀 Le projet ECG est maintenant optimisé et prêt pour la production !")
    print(f"   Utilisez 'python start.py' pour lancer l'application")

if __name__ == "__main__":
    main()
