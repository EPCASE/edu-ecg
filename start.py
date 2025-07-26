#!/usr/bin/env python3
"""
🫀 ECG Lecture - Lancement Simplifié
Application web unifiée avec authentification intégrée
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path
import os
import socket

def find_free_port(start_port=8501):
    """Trouve un port libre à partir du port de départ"""
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def kill_streamlit_processes():
    """Tue les processus Streamlit existants"""
    try:
        # Sur Windows, tuer les processus streamlit
        subprocess.run(['taskkill', '/f', '/im', 'python.exe', '/fi', 'WINDOWTITLE eq streamlit*'], 
                      capture_output=True, shell=True)
        time.sleep(2)
    except:
        pass

def main():
    """Lance l'application ECG Lecture"""
    
    print("🫀 ECG Lecture - Démarrage...")
    print("=" * 50)
    
    # Vérifier que nous sommes dans le bon répertoire
    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend"
    app_file = frontend_dir / "app.py"
    
    if not app_file.exists():
        print(f"❌ Fichier app.py non trouvé : {app_file}")
        print("Vérifiez que vous êtes dans le bon répertoire.")
        input("Appuyez sur Entrée pour quitter...")
        return
    
    print(f"📁 Répertoire : {project_root}")
    print(f"🎯 Application : {app_file}")
    print()
    
    # Vérifier si le port 8501 est libre
    port = find_free_port(8501)
    if port != 8501:
        print("⚠️ Port 8501 occupé, tentative d'arrêt des instances existantes...")
        kill_streamlit_processes()
        time.sleep(3)
        port = find_free_port(8501)
    
    if port is None:
        print("❌ Impossible de trouver un port libre")
        input("Appuyez sur Entrée pour quitter...")
        return
    
    if port != 8501:
        print(f"⚠️ Utilisation du port {port} au lieu de 8501")
    
    print("🔐 AUTHENTIFICATION ACTIVÉE")
    print("   Comptes de démonstration :")
    print("   👑 Admin    : admin@example.com / admin123")
    print("   👨‍⚕️ Expert   : expert@example.com / expert123")
    print("   🎓 Étudiant : etudiant@example.com / etudiant123")
    print()
    print(f"🌐 URL : http://localhost:{port}")
    print("🛑 Pour arrêter : Ctrl+C")
    print("=" * 50)
    
    try:
        # Commande Streamlit avec le port trouvé
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--server.address", "localhost",
            "--server.port", str(port),
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false"
        ]
        
        print("🚀 Démarrage en cours...")
        
        # Ouvrir le navigateur après 3 secondes
        def open_browser():
            time.sleep(3)
            webbrowser.open(f"http://localhost:{port}")
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Changer vers le répertoire frontend
        os.chdir(frontend_dir)
        
        # Lancer Streamlit
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except FileNotFoundError:
        print("❌ Streamlit non trouvé. Installez-le avec : pip install streamlit")
    except Exception as e:
        print(f"❌ Erreur lors du lancement : {e}")
    
    print("\n👋 Application fermée")

if __name__ == "__main__":
    main()
