#!/usr/bin/env python3
"""
🧪 Test des Permissions
Vérifie que les rôles et permissions fonctionnent correctement
"""

import sys
from pathlib import Path

# Ajouter le chemin frontend
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend"))

from auth_system import ROLES_CONFIG, check_permission
import streamlit as st

def test_permissions():
    """Test les permissions pour chaque rôle"""
    
    print("🧪 Test des permissions ECG Lecture")
    print("=" * 50)
    
    # Test pour chaque rôle
    for role_key, role_config in ROLES_CONFIG.items():
        print(f"\n{role_config['label']} ({role_key}):")
        print(f"Permissions: {role_config['permissions']}")
        print(f"Menu sidebar: {role_config['sidebar_items']}")
        
        # Simuler la session utilisateur
        st.session_state.authenticated = True
        st.session_state.user_role = role_key
        
        # Test de permissions spécifiques
        permissions_tests = [
            ('view_cases', 'Voir les cas ECG'),
            ('import_ecg', 'Importer des ECG'),
            ('all', 'Accès administrateur complet')
        ]
        
        print("  Tests d'accès:")
        for perm, desc in permissions_tests:
            has_perm = check_permission(perm)
            status = "✅" if has_perm else "❌"
            print(f"    {status} {desc}")
    
    print("\n" + "=" * 50)
    print("✅ Test terminé")

if __name__ == "__main__":
    test_permissions()
