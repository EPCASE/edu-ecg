"""
🔐 Système d'Authentification et Gestion des Rôles
Module de connexion avec 3 types d'utilisateurs :
- Étudiant : Consultation cas, sessions, stats personnelles
- Expert : + Import ECG, création sessions
- Admin : Accès complet système
"""

import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path
import uuid

# Configuration des rôles et permissions
ROLES_CONFIG = {
    'etudiant': {
        'label': '🎓 Étudiant',
        'permissions': ['view_cases', 'view_sessions', 'view_personal_stats', 'annotate_cases'],
        'sidebar_items': ['Cas ECG', 'Mes Sessions', 'Mes Statistiques']
    },
    'expert': {
        'label': '👨‍⚕️ Expert',
        'permissions': ['view_cases', 'view_sessions', 'view_personal_stats', 'annotate_cases', 
                       'import_ecg', 'create_sessions', 'manage_own_cases'],
        'sidebar_items': ['Import ECG', 'Liseuse ECG', 'Cas ECG', 'Sessions', 'Mes Statistiques']
    },
    'admin': {
        'label': '👑 Administrateur',
        'permissions': ['all'],
        'sidebar_items': ['Import ECG', 'Liseuse ECG', 'Cas ECG', 'Sessions', 'Base de Données', 
                         'Utilisateurs', 'Analytics', 'Configuration']
    }
}

def init_auth_system():
    """Initialise le système d'authentification"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

def load_users_database():
    """Charge la base de données des utilisateurs"""
    users_file = Path("users/users_auth.json")
    
    if not users_file.exists():
        # Créer la base avec utilisateurs par défaut
        default_users = {
            "admin": {
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "name": "Administrateur",
                "email": "admin@example.com",
                "created_date": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            },
            "expert_demo": {
                "password_hash": hash_password("expert123"),
                "role": "expert",
                "name": "Dr. Expert Demo",
                "email": "expert@example.com",
                "created_date": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            },
            "etudiant_demo": {
                "password_hash": hash_password("etudiant123"),
                "role": "etudiant",
                "name": "Étudiant Demo",
                "email": "etudiant@example.com",
                "created_date": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            }
        }
        
        users_file.parent.mkdir(exist_ok=True)
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2, ensure_ascii=False)
        
        return default_users
    
    with open(users_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users_database(users_data):
    """Sauvegarde la base de données des utilisateurs"""
    users_file = Path("users/users_auth.json")
    users_file.parent.mkdir(exist_ok=True)
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)

def hash_password(password):
    """Hache un mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Vérifie un mot de passe"""
    return hash_password(password) == hashed

def login_interface():
    """Interface de connexion"""
    st.markdown("### 🔐 Connexion Edu-CG")
    
    # Afficher les comptes de démonstration
    with st.expander("👥 Comptes de Démonstration", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            **🎓 Étudiant Demo**
            - Login: `etudiant_demo`
            - Mot de passe: `etudiant123`
            - Accès: Cas, sessions, stats
            """)
        
        with col2:
            st.info("""
            **👨‍⚕️ Expert Demo**
            - Login: `expert_demo`
            - Mot de passe: `expert123`
            - Accès: + Import, création
            """)
        
        with col3:
            st.info("""
            **👑 Admin**
            - Login: `admin`
            - Mot de passe: `admin123`
            - Accès: Complet
            """)
    
    # Formulaire de connexion
    with st.form("login_form"):
        username = st.text_input("👤 Nom d'utilisateur")
        password = st.text_input("🔒 Mot de passe", type="password")
        login_button = st.form_submit_button("🚀 Se connecter", use_container_width=True)
        
        if login_button:
            if authenticate_user(username, password):
                st.success("✅ Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Nom d'utilisateur ou mot de passe incorrect")

def authenticate_user(username, password):
    """Authentifie un utilisateur"""
    users_db = load_users_database()
    
    if username in users_db:
        user_data = users_db[username]
        if user_data.get('active', True) and verify_password(password, user_data['password_hash']):
            # Mettre à jour la dernière connexion
            user_data['last_login'] = datetime.now().isoformat()
            users_db[username] = user_data
            save_users_database(users_db)
            
            # Stocker les informations de session
            st.session_state.authenticated = True
            st.session_state.user_info = {
                'username': username,
                'name': user_data['name'],
                'email': user_data['email'],
                'role': user_data['role']
            }
            st.session_state.user_role = user_data['role']
            return True
    
    return False

def logout_user():
    """Déconnecte l'utilisateur"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.user_role = None
    st.rerun()

def check_permission(required_permission):
    """Vérifie si l'utilisateur a la permission requise"""
    if not st.session_state.authenticated:
        return False
    
    user_role = st.session_state.user_role
    if user_role not in ROLES_CONFIG:
        return False
    
    permissions = ROLES_CONFIG[user_role]['permissions']
    return 'all' in permissions or required_permission in permissions

def get_user_sidebar_items():
    """Retourne les éléments de sidebar pour l'utilisateur connecté"""
    if not st.session_state.authenticated:
        return []
    
    user_role = st.session_state.user_role
    if user_role in ROLES_CONFIG:
        return ROLES_CONFIG[user_role]['sidebar_items']
    return []

def display_user_info():
    """Affiche les informations utilisateur dans la sidebar"""
    if st.session_state.authenticated:
        user_info = st.session_state.user_info
        role_config = ROLES_CONFIG.get(user_info['role'], {})
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Utilisateur Connecté")
        st.sidebar.markdown(f"**{role_config.get('label', user_info['role'])}**")
        st.sidebar.markdown(f"👋 {user_info['name']}")
        st.sidebar.markdown(f"📧 {user_info['email']}")
        
        if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
            logout_user()

def create_user_interface():
    """Interface de création d'utilisateur (admin seulement)"""
    if not check_permission('all'):
        st.error("❌ Accès non autorisé")
        return
    
    st.markdown("### ➕ Créer un Nouvel Utilisateur")
    
    # Utiliser des colonnes pour éviter les conflits de rechargement
    with st.container():
        # Formulaire dans un container stable
        st.markdown("#### 📝 Informations utilisateur")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("👤 Nom d'utilisateur*", key="new_user_username")
            name = st.text_input("👨‍💼 Nom complet*", key="new_user_name")
            email = st.text_input("📧 Email*", key="new_user_email")
        
        with col2:
            password = st.text_input("🔒 Mot de passe*", type="password", key="new_user_password")
            confirm_password = st.text_input("🔒 Confirmer mot de passe*", type="password", key="new_user_confirm")
            
            # Utiliser des boutons radio au lieu d'un selectbox
            st.markdown("**👥 Rôle utilisateur :**")
            role_options = {
                'etudiant': '🎓 Étudiant',
                'expert': '👨‍⚕️ Expert', 
                'admin': '👑 Administrateur'
            }
            
            role = st.radio(
                "Sélectionner le rôle :",
                options=list(role_options.keys()),
                format_func=lambda x: role_options[x],
                key="new_user_role",
                label_visibility="collapsed"
            )
        
        # Aperçu des permissions du rôle sélectionné
        if role:
            st.markdown("#### 🔍 Permissions du rôle sélectionné")
            permissions = ROLES_CONFIG.get(role, {}).get('permissions', [])
            sidebar_items = ROLES_CONFIG.get(role, {}).get('sidebar_items', [])
            
            col_perm1, col_perm2 = st.columns(2)
            
            with col_perm1:
                st.markdown("**Accès autorisés :**")
                for item in sidebar_items:
                    st.markdown(f"• {item}")
            
            with col_perm2:
                st.markdown("**Restrictions :**")
                if role == 'etudiant':
                    st.markdown("• Pas d'import ECG")
                    st.markdown("• Pas de création de cas")
                    st.markdown("• Pas d'administration")
                elif role == 'expert':
                    st.markdown("• Pas d'administration système")
                    st.markdown("• Pas de gestion utilisateurs")
                else:
                    st.markdown("• Aucune restriction")
        
        st.markdown("---")
        
        # Bouton de création
        if st.button("✅ Créer l'utilisateur", type="primary", use_container_width=True, key="create_user_btn"):
            if not all([username, name, email, password]):
                st.error("❌ Tous les champs marqués * sont obligatoires")
            elif password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas")
            elif len(password) < 6:
                st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
            else:
                users_db = load_users_database()
                if username in users_db:
                    st.error("❌ Ce nom d'utilisateur existe déjà")
                else:
                    # Créer le nouvel utilisateur
                    users_db[username] = {
                        "password_hash": hash_password(password),
                        "role": role,
                        "name": name,
                        "email": email,
                        "created_date": datetime.now().isoformat(),
                        "last_login": None,
                        "active": True,
                        "created_by": st.session_state.user_info['username']
                    }
                    save_users_database(users_db)
                    st.success(f"✅ Utilisateur {username} créé avec succès !")
                    st.success(f"🔐 Mot de passe : `{password}`")
                    st.info("💡 Communiquez ces identifiants à l'utilisateur de manière sécurisée")

def list_users_interface():
    """Interface de gestion des utilisateurs (admin seulement)"""
    if not check_permission('all'):
        st.error("❌ Accès non autorisé")
        return
    
    st.markdown("### 👥 Gestion des Utilisateurs")
    
    users_db = load_users_database()
    
    if users_db:
        # Statistiques rapides
        col1, col2, col3, col4 = st.columns(4)
        
        total_users = len(users_db)
        active_users = sum(1 for u in users_db.values() if u.get('active', True))
        students = sum(1 for u in users_db.values() if u.get('role') == 'etudiant')
        experts = sum(1 for u in users_db.values() if u.get('role') == 'expert')
        
        with col1:
            st.metric("Total Utilisateurs", total_users)
        with col2:
            st.metric("Actifs", active_users)
        with col3:
            st.metric("Étudiants", students)
        with col4:
            st.metric("Experts", experts)
        
        st.markdown("---")
        
        # Convertir en DataFrame pour affichage
        users_list = []
        for username, data in users_db.items():
            users_list.append({
                'Utilisateur': username,
                'Nom': data['name'],
                'Email': data['email'],
                'Rôle': ROLES_CONFIG.get(data['role'], {}).get('label', data['role']),
                'Statut': '✅ Actif' if data.get('active', True) else '❌ Inactif',
                'Dernière connexion': data.get('last_login', 'Jamais') or 'Jamais',
                'Créé le': data.get('created_date', 'N/A')[:10] if data.get('created_date') else 'N/A'
            })
        
        df = pd.DataFrame(users_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Actions sur les utilisateurs
        st.markdown("#### ⚙️ Actions sur les Utilisateurs")
        
        # Sélection avec des boutons radio pour éviter les conflits
        usernames = list(users_db.keys())
        
        col_select, col_actions = st.columns([1, 2])
        
        with col_select:
            st.markdown("**Sélectionner un utilisateur :**")
            selected_user = st.radio(
                "Utilisateur à modifier :",
                options=usernames,
                key="selected_user_radio",
                label_visibility="collapsed"
            )
        
        with col_actions:
            if selected_user:
                st.markdown(f"**Actions pour : {selected_user}**")
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("🔄 Reset Password", key=f"reset_{selected_user}"):
                        # Générer un nouveau mot de passe temporaire
                        import uuid
                        temp_password = f"temp{uuid.uuid4().hex[:8]}"
                        users_db[selected_user]['password_hash'] = hash_password(temp_password)
                        save_users_database(users_db)
                        st.success(f"✅ Nouveau mot de passe: `{temp_password}`")
                        st.info("L'utilisateur doit changer ce mot de passe à la prochaine connexion")
                
                with col_btn2:
                    current_status = users_db[selected_user].get('active', True)
                    action_label = "❌ Désactiver" if current_status else "✅ Activer"
                    if st.button(action_label, key=f"toggle_{selected_user}"):
                        users_db[selected_user]['active'] = not current_status
                        save_users_database(users_db)
                        status_msg = "désactivé" if current_status else "activé"
                        st.success(f"✅ Utilisateur {selected_user} {status_msg}")
                        st.rerun()
                
                with col_btn3:
                    if st.button("🗑️ Supprimer", key=f"delete_{selected_user}"):
                        if selected_user != st.session_state.user_info['username']:
                            del users_db[selected_user]
                            save_users_database(users_db)
                            st.success(f"✅ Utilisateur {selected_user} supprimé")
                            st.rerun()
                        else:
                            st.error("❌ Vous ne pouvez pas supprimer votre propre compte")
    
    else:
        st.info("Aucun utilisateur enregistré.")

def require_auth(func):
    """Décorateur pour protéger les pages"""
    def wrapper(*args, **kwargs):
        if not st.session_state.authenticated:
            login_interface()
            return
        return func(*args, **kwargs)
    return wrapper

def require_permission(permission):
    """Décorateur pour vérifier les permissions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_permission(permission):
                st.error("❌ Vous n'avez pas les permissions nécessaires pour accéder à cette page")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator
