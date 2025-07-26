#!/usr/bin/env python3
"""
🧪 Test du Système d'Authentification
Script pour tester rapidement la création d'utilisateurs
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend"))

def test_user_creation():
    """Test de création d'utilisateur"""
    from auth_system import load_users_database, save_users_database, hash_password
    from datetime import datetime
    
    print("🧪 Test du système d'authentification...")
    
    # Charger la base de données
    users_db = load_users_database()
    print(f"✅ Base de données chargée : {len(users_db)} utilisateurs")
    
    # Tester la création d'un utilisateur
    test_user = {
        "password_hash": hash_password("test123"),
        "role": "etudiant",
        "name": "Test Utilisateur",
        "email": "test@example.com",
        "created_date": datetime.now().isoformat(),
        "last_login": None,
        "active": True,
        "created_by": "admin"
    }
    
    users_db["test_user"] = test_user
    save_users_database(users_db)
    
    print("✅ Utilisateur test créé avec succès")
    print("Identifiants : test_user / test123")
    
    # Relire pour vérifier
    users_db_reloaded = load_users_database()
    if "test_user" in users_db_reloaded:
        print("✅ Utilisateur test présent dans la base")
    else:
        print("❌ Erreur : utilisateur test non trouvé")
    
    print("\n🎯 Comptes disponibles :")
    for username, data in users_db_reloaded.items():
        role_label = {
            'etudiant': '🎓 Étudiant',
            'expert': '👨‍⚕️ Expert',
            'admin': '👑 Admin'
        }.get(data['role'], data['role'])
        print(f"  • {username} ({role_label}) - {data['name']}")

if __name__ == "__main__":
    test_user_creation()
