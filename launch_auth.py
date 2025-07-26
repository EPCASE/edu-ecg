#!/usr/bin/env python3
"""
🔐 Lancement Edu-CG avec Système d'Authentification
Version sécurisée avec gestion des rôles utilisateurs
"""

import streamlit.web.cli as stcli
import sys
import os
from pathlib import Path

def main():
    """Lance l'application avec authentification"""
    
    # Configuration du répertoire de travail
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🔐 Lancement Edu-CG avec authentification...")
    print("=" * 50)
    print("🎓 Comptes de démonstration disponibles :")
    print("• Étudiant : etudiant_demo / etudiant123")
    print("• Expert   : expert_demo / expert123") 
    print("• Admin    : admin / admin123")
    print("=" * 50)
    print("🌐 Application disponible sur : http://localhost:8501")
    print("🔒 Système d'authentification activé")
    
    # Arguments Streamlit
    sys.argv = [
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port=8501",
        "--server.address=localhost",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]
    
    # Lancement
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
