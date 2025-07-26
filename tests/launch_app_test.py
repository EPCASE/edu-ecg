#!/usr/bin/env python3
"""
Lancement de l'application complète pour test final
"""

import subprocess
import sys
import os
from pathlib import Path

def lancer_application():
    """Lance l'application ECG complète"""
    
    print("🚀 Lancement de l'application ECG...")
    print("=" * 50)
    
    # Vérifier le répertoire de travail
    ecg_dir = Path("c:/Users/Administrateur/Desktop/ECG lecture")
    if not ecg_dir.exists():
        print("❌ Répertoire ECG lecture non trouvé")
        return
    
    # Changer vers le répertoire ECG
    os.chdir(ecg_dir)
    print(f"📁 Répertoire de travail : {ecg_dir}")
    
    # Vérifier les fichiers essentiels
    app_file = ecg_dir / "frontend" / "app.py"
    if not app_file.exists():
        print("❌ Fichier app.py non trouvé")
        return
    
    print("✅ Fichiers trouvés")
    
    # Commande de lancement
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🌐 Lancement sur http://localhost:8501")
    print("🔧 Commande :", " ".join(cmd))
    print("=" * 50)
    print("💡 Pour tester la liseuse :")
    print("   1. Aller dans Mode Administrateur")
    print("   2. Sélectionner 'Liseuse ECG (WP2)'")
    print("   3. Tester les annotations")
    print("=" * 50)
    
    try:
        # Lancer l'application
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lancement : {e}")

if __name__ == "__main__":
    lancer_application()
