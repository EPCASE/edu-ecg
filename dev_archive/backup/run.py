#!/usr/bin/env python3
"""
🚀 Lanceur pour Edu-CG
Script pour démarrer l'application Streamlit avec la bonne configuration
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Lance l'application Streamlit"""
    
    project_root = Path(__file__).parent
    app_path = project_root / "frontend" / "app.py"
    
    print("🫀 === LANCEMENT EDU-CG ===")
    print(f"📂 Dossier : {project_root}")
    print(f"🎯 Application : {app_path}")
    print("🌐 Ouverture du navigateur...")
    print()
    
    # Commande Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(app_path),
        "--server.headless", "false",
        "--server.enableCORS", "false"
    ]
    
    try:
        subprocess.run(cmd, cwd=str(project_root))
    except KeyboardInterrupt:
        print("\n⏹️  Application arrêtée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du lancement : {e}")

if __name__ == "__main__":
    main()
