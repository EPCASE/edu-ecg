#!/usr/bin/env python3
"""
Edu-ECG - Plateforme d'enseignement interactif de l'électrocardiogramme
Copyright (c) 2024 - Tous droits réservés
Licence MIT - Voir fichier LICENSE pour les détails

Application principale Streamlit pour l'apprentissage de l'ECG
avec annotation semi-automatique et ontologie médicale.

Auteur: [Votre nom]
Version: 1.0
Date: Décembre 2024
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import random
from PIL import Image
import shutil
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="🫀 Edu-CG - Formation ECG",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajout des chemins pour les imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend" / "admin"))
sys.path.append(str(project_root / "frontend"))

# Import du système d'authentification
from auth_system import (
    init_auth_system, login_interface, display_user_info, 
    check_permission, get_user_sidebar_items, require_auth, 
    create_user_interface, list_users_interface
)

try:
    from correction_engine import OntologyCorrector
    from import_cases import admin_import_cases
    from annotation_tool import admin_annotation_tool
    from annotation_components import smart_annotation_input, display_annotation_summary
    try:
        from ecg_reader import ecg_reader_interface
        ECG_READER_AVAILABLE = True
    except ImportError:
        ECG_READER_AVAILABLE = False
    try:
        from user_management import user_management_interface
        USER_MANAGEMENT_AVAILABLE = True
    except ImportError:
        USER_MANAGEMENT_AVAILABLE = False
    ONTOLOGY_LOADED = True
except ImportError as e:
    ONTOLOGY_LOADED = False
    ECG_READER_AVAILABLE = False
    USER_MANAGEMENT_AVAILABLE = False
    st.error(f"⚠️ Erreur import modules : {e}")

def load_ontology():
    """Chargement de l'ontologie ECG"""
    if 'corrector' not in st.session_state:
        try:
            ontology_path = project_root / "data" / "ontologie.owx"
            st.session_state.corrector = OntologyCorrector(str(ontology_path))
            st.session_state.concepts = list(st.session_state.corrector.concepts.keys())
            return True
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement de l'ontologie : {e}")
            return False
    return True

def main():
    """Application principale Edu-CG avec authentification"""
    
    # Initialiser le système d'authentification
    init_auth_system()
    
    # Vérifier si l'utilisateur est connecté
    if not st.session_state.authenticated:
        login_interface()
        return
    
    # Application principale après authentification
    main_app_with_auth()

def main_app_with_auth():
    """Application principale après authentification"""
    
    # Charger l'ontologie si nécessaire
    if ONTOLOGY_LOADED:
        load_ontology()
    
    # Titre avec informations utilisateur
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🫀 ECG Lecture & Annotation Platform")
    with col2:
        user_info = st.session_state.user_info
        st.markdown(f"**{user_info['name']}** ({user_info['role']})")
    
    # Navigation selon les permissions utilisateur
    with st.sidebar:
        st.markdown("## 🔧 Navigation")
        
        # Informations utilisateur
        display_user_info()
        
        st.markdown("---")
        
        # Initialiser la page sélectionnée
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'home'
        
        # Menu selon le rôle utilisateur
        user_role = st.session_state.user_role  # Utiliser user_role au lieu de user_info['role']
        
        # Pages communes à tous
        if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'home'
            st.rerun()
        
        # Menu selon les permissions
        if user_role in ['admin', 'expert']:  # Utiliser les vrais noms de rôles
            st.markdown("### 📋 Gestion de Contenu")
            if st.button("📥 Import ECG", type="primary" if st.session_state.selected_page == 'import' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'import'
                st.rerun()
            
            if st.button("📖 Liseuse ECG", type="primary" if st.session_state.selected_page == 'reader' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'reader'
                st.rerun()
            
            # Menu Sessions pour experts et admins
            if check_permission('create_sessions') or check_permission('all'):
                if st.button("📚 Sessions ECG", type="primary" if st.session_state.selected_page == 'sessions' else "secondary", use_container_width=True):
                    st.session_state.selected_page = 'sessions'
                    st.rerun()
        
        # Menu pour tous les utilisateurs
        st.markdown("### 📚 Formation")
        if st.button("📋 Cas ECG", type="primary" if st.session_state.selected_page == 'cases' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'cases'
            st.rerun()
        
        if st.button("🎯 Exercices", type="primary" if st.session_state.selected_page == 'exercises' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'exercises'
            st.rerun()
        
        if st.button("📊 Mes Sessions", type="primary" if st.session_state.selected_page == 'progress' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'progress'
            st.rerun()
        
        # Menu Admin uniquement
        if user_role == 'admin':  # Utiliser le vrai nom de rôle
            st.markdown("### ⚙️ Administration")
            if st.button("🗄️ Base de Données", type="primary" if st.session_state.selected_page == 'database' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'database'
                st.rerun()
            
            if st.button("👥 Utilisateurs", type="primary" if st.session_state.selected_page == 'users' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'users'
                st.rerun()
    
    # Routage des pages selon les permissions
    route_pages_with_auth(st.session_state.selected_page)

def route_pages_with_auth(page):
    """Routage des pages avec contrôle d'authentification"""
    
    if page == 'home':
        # Page d'accueil selon le rôle
        user_role = st.session_state.user_role  # Utiliser user_role
        if user_role == 'etudiant':  # Utiliser le vrai nom de rôle
            page_student_home()
        else:
            page_admin_home()
    
    elif page == 'import':
        if check_permission('import_ecg') or check_permission('all'):
            try:
                from admin.smart_ecg_importer_simple import smart_ecg_importer_simple
                smart_ecg_importer_simple()
            except ImportError:
                st.error("❌ Module d'import non disponible")
                st.info("💡 Vérifiez que le module admin/smart_ecg_importer_simple.py existe")
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'reader':
        if check_permission('annotate_cases') or check_permission('all'):
            try:
                from liseuse.liseuse_ecg_simple import liseuse_ecg_simple
                liseuse_ecg_simple()
            except ImportError:
                st.error("❌ Module de lecture ECG non disponible")
                st.info("💡 Utilisez l'import intelligent pour créer des cas d'abord")
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'cases':
        page_ecg_cases()
    
    elif page == 'exercises':
        page_exercises()
    
    elif page == 'progress':
        page_student_progress()
    
    elif page == 'sessions':
        if check_permission('create_sessions') or check_permission('all'):
            page_sessions_management()
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'database':
        if check_permission('all'):
            page_database_management()
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'users':
        if check_permission('all'):
            page_users_management_with_auth()
        else:
            st.error("❌ Accès non autorisé")
    
    else:
        # Fallback vers l'ancienne navigation pour compatibilité
        if page in ["📥 Import ECG (WP1)", "📺 Liseuse ECG (WP2)", "🎯 Exercices & Tests (WP3)", 
                   "📊 Analytics & Base (WP4)", "👥 Users Management", "🗄️ Base de Données"]:
            route_admin_pages(page)
        else:
            page_admin_home()

def page_users_management_with_auth():
    """Page de gestion des utilisateurs avec l'interface d'authentification"""
    st.markdown("## 👥 Gestion des Utilisateurs")
    
    tab1, tab2 = st.tabs(["👤 Liste des Utilisateurs", "➕ Créer Utilisateur"])
    
    with tab1:
        list_users_interface()
    
    with tab2:
        create_user_interface()
    
    # SIDEBAR NAVIGATION avec boutons simples
    with st.sidebar:
        st.markdown("## 🔧 Navigation")
        
        # Commutateur Admin/Étudiant dans la sidebar
        if 'user_mode' not in st.session_state:
            st.session_state.user_mode = 'admin'
        
        mode_display = "👨‍⚕️ Administrateur" if st.session_state.user_mode == 'admin' else "🎓 Étudiant"
        
        if st.button(f"🔄 Changer : {mode_display}", type="secondary", use_container_width=True, key="change_mode_btn"):
            st.session_state.user_mode = 'student' if st.session_state.user_mode == 'admin' else 'admin'
            # Reset de la page sélectionnée lors du changement de mode
            if 'selected_page' in st.session_state:
                del st.session_state.selected_page
            st.rerun()
        
        st.markdown("---")
        
        # Initialiser la page sélectionnée
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'home'
        
        # Menu selon le mode avec BOUTONS SIMPLES
        if st.session_state.user_mode == 'admin':
            st.markdown("### 👨‍⚕️ Menu Admin")
            
            # Boutons sidebar admin
            if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True, key="admin_home_btn"):
                st.session_state.selected_page = 'home'
                st.rerun()
            
            if st.button("📥 Import ECG", type="primary" if st.session_state.selected_page == 'import' else "secondary", use_container_width=True, key="admin_import_btn"):
                st.session_state.selected_page = 'import'
                st.rerun()
            
            if st.button("📺 Liseuse ECG", type="primary" if st.session_state.selected_page == 'reader' else "secondary", use_container_width=True, key="admin_reader_btn"):
                st.session_state.selected_page = 'reader'
                st.rerun()
            
            if st.button("👥 Utilisateurs", type="primary" if st.session_state.selected_page == 'users' else "secondary", use_container_width=True, key="admin_users_btn"):
                st.session_state.selected_page = 'users'
                st.rerun()
            
            if st.button("📊 Base de Données", type="primary" if st.session_state.selected_page == 'database' else "secondary", use_container_width=True, key="admin_database_btn"):
                st.session_state.selected_page = 'database'
                st.rerun()
            
        else:
            st.markdown("### 🎓 Menu Étudiant")
            
            # Boutons sidebar étudiant
            if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True, key="student_home_btn"):
                st.session_state.selected_page = 'home'
                st.rerun()
            
            if st.button("📚 Cas ECG", type="primary" if st.session_state.selected_page == 'cases' else "secondary", use_container_width=True, key="student_cases_btn"):
                st.session_state.selected_page = 'cases'
                st.rerun()
            
            if st.button("🎯 Exercices", type="primary" if st.session_state.selected_page == 'exercises' else "secondary", use_container_width=True, key="student_exercises_btn"):
                st.session_state.selected_page = 'exercises'
                st.rerun()
            
            if st.button("📈 Mes Progrès", type="primary" if st.session_state.selected_page == 'progress' else "secondary", use_container_width=True, key="student_progress_btn"):
                st.session_state.selected_page = 'progress'
                st.rerun()
        
        st.markdown("---")
        
        # Statut système dans la sidebar
        st.markdown("### 🧠 Statut Système")
        if ONTOLOGY_LOADED and load_ontology():
            st.success("✅ Ontologie OK")
            st.caption(f"📊 {len(st.session_state.concepts)} concepts")
        else:
            st.error("❌ Ontologie KO")
        
        st.caption(f"🔄 Mode : {mode_display}")
        
        if st.button("🔧 Recharger", use_container_width=True, key="reload_system_btn"):
            load_ontology()
            st.rerun()
    
    # Routage des pages selon le mode
    if st.session_state.user_mode == 'admin':
        route_admin_sidebar_pages(st.session_state.selected_page)
    else:
        route_student_sidebar_pages(st.session_state.selected_page)

def route_admin_sidebar_pages(page):
    """Routage des pages administrateur avec sidebar"""
    
    if page == 'home':
        page_admin_home()
    elif page == 'import':
        try:
            from admin.smart_ecg_importer_simple import smart_ecg_importer_simple
            smart_ecg_importer_simple()
        except ImportError:
            st.error("❌ Module d'import non disponible")
    elif page == 'reader':
        try:
            from liseuse.liseuse_ecg_simple import liseuse_ecg_simple
            liseuse_ecg_simple()
        except ImportError:
            st.error("❌ Module de lecture ECG non disponible")
            st.info("💡 Utilisez l'import intelligent pour créer des cas d'abord")
    elif page == 'users':
        try:
            from user_management import user_management_interface
            user_management_interface()
        except ImportError:
            st.error("❌ Module de gestion utilisateurs non disponible")
    elif page == 'database':
        page_database_management()

def route_student_sidebar_pages(page):
    """Routage des pages étudiant avec sidebar"""
    
    if page == 'home':
        page_student_home()
    elif page == 'cases':
        page_ecg_cases()
    elif page == 'exercises':
        page_exercises()
    elif page == 'progress':
        page_student_progress()

def route_admin_pages(page):
    """Routage des pages administrateur"""
    
    if page == "🏠 Accueil":
        page_admin_home()
    elif page == "📤 Import ECG (WP1)":
        admin_import_cases()
    elif page == "🎯 Import Intelligent":
        try:
            from admin.smart_ecg_importer_simple import smart_ecg_importer_simple
            smart_ecg_importer_simple()
        except ImportError as e:
            # Fallback vers version avec onglets
            try:
                from admin.smart_ecg_importer import smart_ecg_importer
                smart_ecg_importer()
            except ImportError:
                st.error(f"❌ Erreur d'import du module : {e}")
                st.info("🔧 Utilisation de l'import simple en fallback")
                admin_import_cases()
    elif page == "📺 Liseuse ECG":
        try:
            from liseuse.liseuse_ecg_simple import liseuse_ecg_simple
            liseuse_ecg_simple()
        except ImportError:
            # Fallback vers ancienne liseuse
            if ECG_READER_AVAILABLE:
                ecg_reader_interface()
            else:
                st.warning("⚠️ Module Liseuse ECG non disponible")
    elif page == "✏️ Annotation Admin":
        admin_annotation_tool()
    elif page == "👥 Gestion Utilisateurs":
        if USER_MANAGEMENT_AVAILABLE:
            user_management_interface()
        else:
            st.warning("⚠️ Module Gestion Utilisateurs non disponible")
    elif page == "📊 Gestion BDD":
        page_database_management()

def route_student_pages(page):
    """Routage des pages étudiant"""
    
    if page == "🏠 Accueil":
        page_student_home()
    elif page == "📚 Cas ECG":
        page_ecg_cases()
    elif page == "🎯 Exercices":
        page_exercises()
    elif page == "📈 Mes progrès":
        page_student_progress()

def page_admin_home():
    """Page d'accueil administrateur"""
    
    # Présentation de l'application
    st.markdown("## 🫀 Edu-CG - Plateforme d'apprentissage ECG")
    
    st.markdown("""
    **Edu-CG** est une plateforme interactive d'apprentissage de l'électrocardiogramme qui propose :
    - 🧠 **Correction intelligente** basée sur une ontologie de 281 concepts ECG
    - 📱 **Interface moderne** compatible desktop, tablette et mobile  
    - 🎓 **Workflow pédagogique** : annotation expert → formation étudiant → évaluation
    - 📊 **Analytics détaillés** avec scoring nuancé et suivi de progression
    """)
    
    st.markdown("---")
    
    # Tableau de bord compact
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cases_count = count_total_cases()
        st.metric("📋 Cas ECG", cases_count)
    
    with col2:
        annotated_count = count_annotated_cases()
        st.metric("✅ Annotés", annotated_count)
    
    with col3:
        if cases_count > 0:
            progress = annotated_count / cases_count
            st.metric("📈 Progression", f"{progress*100:.0f}%")
        else:
            st.metric("📈 Progression", "0%")
    
    st.markdown("---")
    
    # Actions principales - CORRIGÉES
    st.markdown("### 🚀 Actions rapides")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Import Intelligent", type="primary", use_container_width=True):
            st.session_state.selected_page = "import"
            st.rerun()
    
    with col2:
        if st.button("📺 Liseuse ECG", use_container_width=True):
            st.session_state.selected_page = "reader"
            st.rerun()

def page_student_home():
    """Page d'accueil étudiant"""
    
    # Présentation de l'application
    st.markdown("## 🎓 Formation à l'ECG")
    
    st.markdown("""
    Bienvenue dans **Edu-CG**, votre plateforme d'apprentissage de l'électrocardiogramme !
    
    **Votre parcours d'apprentissage :**
    - 📚 **Consultez les cas ECG** pour découvrir différentes pathologies
    - 🎯 **Pratiquez avec les exercices** d'annotation interactive
    - 📈 **Suivez vos progrès** avec des analytics détaillés
    - 🧠 **Bénéficiez de corrections intelligentes** basées sur l'ontologie médicale
    """)
    
    st.markdown("---")
    
    # Actions principales - CORRIGÉES
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 Cas ECG", type="primary", use_container_width=True):
            st.session_state.selected_page = "cases"
            st.rerun()
    
    with col2:
        if st.button("🎯 Exercices", use_container_width=True):
            st.session_state.selected_page = "exercises"
            st.rerun()
    
    with col3:
        if st.button("📈 Mes progrès", use_container_width=True):
            st.session_state.selected_page = "progress"
            st.rerun()
    
    st.markdown("---")
    
    # Profil compact
    st.markdown("### 📊 Votre progression")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📝 Exercices réalisés", "0")
    
    with col2:
        st.metric("🎯 Score moyen", "-%")
    
    with col3:
        st.metric("🎯 Niveau", "Débutant")

def page_ecg_cases():
    """Page de consultation des cas ECG pour étudiants"""
    
    st.header("📚 Cas ECG disponibles")
    st.markdown("*Sélectionnez un cas pour vous exercer à l'interprétation*")
    
    # Chargement des cas depuis data/ecg_cases
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    available_cases = []
    
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                
                # Chercher les images ECG dans le dossier
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(case_dir.glob(ext))
                
                if metadata_file.exists() and image_files:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        
                        # Ajouter toutes les informations sur les images
                        sorted_images = sorted(image_files, key=lambda x: x.name)
                        case_data['image_paths'] = [str(img) for img in sorted_images]
                        case_data['image_path'] = str(sorted_images[0])  # Première image pour compatibilité
                        case_data['total_images'] = len(sorted_images)
                        case_data['case_folder'] = str(case_dir)
                        
                        available_cases.append(case_data)
                    except Exception as e:
                        st.warning(f"⚠️ Erreur lecture métadonnées {case_dir.name}: {e}")
    
    if available_cases:
        st.success(f"✅ {len(available_cases)} cas disponibles pour l'entraînement")
        
        for i, case_data in enumerate(available_cases):
            case_id = case_data.get('case_id', f'cas_{i}')
            
            with st.expander(f"📋 Cas ECG: {case_id}", expanded=(i == 0)):
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    # Affichage de tous les ECG du cas
                    if 'image_paths' in case_data and case_data['image_paths']:
                        total_images = len(case_data['image_paths'])
                        
                        if total_images > 1:
                            st.info(f"📊 Ce cas contient **{total_images} ECG**")
                            
                            # Navigation entre les ECG
                            ecg_preview_index = st.selectbox(
                                "Aperçu ECG :",
                                range(total_images),
                                format_func=lambda i: f"ECG {i+1}/{total_images}",
                                key=f"preview_ecg_{case_id}_{i}"
                            )
                        else:
                            ecg_preview_index = 0
                            st.info(f"📊 Ce cas contient **1 ECG**")
                        
                        # Affichage de l'ECG sélectionné
                        image_path = Path(case_data['image_paths'][ecg_preview_index])
                        if image_path.exists():
                            st.image(str(image_path), 
                                   caption=f"ECG {ecg_preview_index+1}/{total_images} - {case_id}",
                                   use_container_width=True)
                        else:
                            st.warning(f"⚠️ ECG {ecg_preview_index+1} non trouvé")
                            
                    elif 'image_path' in case_data:
                        # Compatibilité avec l'ancien format
                        image_path = Path(case_data['image_path'])
                        if image_path.exists():
                            st.image(str(image_path), 
                                   caption=f"ECG - {case_id}",
                                   use_container_width=True)
                        else:
                            st.warning("⚠️ Image ECG non trouvée")
                    else:
                        st.info("📄 Cas ECG (format non-image)")
                
                with col2:
                    st.markdown("**📋 Informations du cas**")
                    
                    # Informations cliniques si disponibles
                    if case_data.get('age'):
                        st.write(f"**Âge :** {case_data['age']} ans")
                    if case_data.get('sexe'):
                        st.write(f"**Sexe :** {case_data['sexe']}")
                    if case_data.get('context'):
                        st.write(f"**Contexte :** {case_data['context']}")
                    
                    # Vérifier s'il y a des annotations expertes
                    annotations = case_data.get('annotations', [])
                    expert_annotations = [ann for ann in annotations 
                                        if ann.get('type') == 'expert' or ann.get('auteur') == 'expert']
                    
                    if expert_annotations:
                        st.success("✅ Cas avec annotation experte")
                    else:
                        st.info("💭 Cas en attente d'annotation experte")
                    
                    st.markdown("---")
                    
                    # Bouton pour commencer l'exercice
                    if st.button(f"🎯 S'exercer sur ce cas", 
                               key=f"exercise_{case_id}",
                               type="primary",
                               help="Commencer l'annotation de ce cas ECG en mode apprentissage"):
                        # Créer une session individuelle pour ce cas
                        case_name = case_data.get('case_id', case_data.get('name', f'cas_{i}'))
                        individual_session = {
                            'session_data': {
                                'name': f"Exercice individuel - {case_data.get('name', 'Cas ECG')}",
                                'description': f"Exercice sur le cas {case_data.get('name', 'ECG')}",
                                'difficulty': case_data.get('difficulty', '🟡 Intermédiaire'),
                                'time_limit': 30,
                                'cases': [case_name],
                                'show_feedback': True,
                                'allow_retry': True
                            },
                            'cases': [case_name],
                            'current_case_index': 0,
                            'responses': {},
                            'start_time': datetime.now().isoformat(),
                            'scores': {},
                            'individual_mode': True  # Marquer comme exercice individuel
                        }
                        st.session_state['current_session'] = individual_session
                        st.session_state.selected_page = "exercises"  # CORRECTION: utiliser selected_page au lieu de student_page
                        st.success(f"🎯 Exercice sur '{case_data.get('name', 'ce cas')}' démarré !")
                        st.rerun()
    
    else:
        st.warning("⚠️ Aucun cas ECG disponible")
        st.info("""
        **💡 Pour avoir des cas disponibles :**
        1. Passez en mode Administrateur/Expert
        2. Utilisez l'Import Intelligent pour ajouter des ECG
        3. Annotez les cas dans la Liseuse ECG
        4. Les cas annotés apparaîtront ici pour les étudiants
        """)

def page_exercises():
    """Page d'exercices pour étudiants avec sessions ECG"""
    
    st.header("🎯 Exercices d'interprétation ECG")
    
    # Vérifier s'il y a une session en cours
    if 'current_session' in st.session_state:
        # Déterminer si c'est un exercice individuel ou une session
        session = st.session_state['current_session']
        is_individual = session.get('individual_mode', False)
        
        if is_individual:
            st.info("📝 **Exercice individuel en cours**")
        else:
            st.info("📚 **Session d'exercices en cours**")
            
        run_ecg_session()
    else:
        # Onglets pour organiser le contenu
        tab1, tab2 = st.tabs(["📚 Sessions", "💡 Aide"])
        
        with tab1:
            # Affichage des sessions disponibles
            display_available_sessions()
        
        with tab2:
            st.markdown("""
            ### 🎯 Comment faire des exercices ?
            
            **📖 Deux façons de pratiquer :**
            
            1. **🎯 Exercice individuel** :
               - Allez dans **"📚 Cas ECG"**
               - Sélectionnez un cas qui vous intéresse
               - Cliquez sur **"🎯 S'exercer sur ce cas"**
               - Vous serez redirigé ici pour commencer l'exercice
            
            2. **📚 Sessions programmées** :
               - Vos enseignants créent des sessions d'exercices
               - Ces sessions apparaissent dans l'onglet "Sessions" ci-dessus
               - Cliquez sur **"▶️ Commencer"** pour démarrer
            
            **💡 Conseils :**
            - Les exercices individuels sont parfaits pour réviser un cas spécifique
            - Les sessions permettent de travailler sur plusieurs cas thématiques
            - Vous recevrez un feedback intelligent basé sur l'ontologie médicale
            """)
            
            # Bouton pour retourner aux cas ECG
            if st.button("📚 Explorer les cas ECG", type="primary"):
                st.session_state.selected_page = "cases"  # CORRECTION: utiliser selected_page
                st.rerun()

def evaluate_student_exercise_intelligent(case_data, student_responses):
    """Évaluation intelligente d'un exercice étudiant avec comparaison ontologique"""
    
    try:
        from annotation_intelligente import compare_annotations
        
        # Récupérer les annotations expertes du cas
        annotations = case_data.get('annotations', [])
        expert_annotations = []
        
        for ann in annotations:
            if ann.get('type') == 'expert_tags' and ann.get('annotation_tags'):
                expert_annotations.extend(ann['annotation_tags'])
            elif ann.get('type') == 'expert' and ann.get('annotation_experte'):
                # Pour les annotations textuelles, extraire des concepts clés
                # (simplification - en production, on analyserait le texte)
                expert_annotations.append(ann['annotation_experte'][:50] + "...")
        
        if expert_annotations:
            # Comparaison ontologique
            comparison = compare_annotations(expert_annotations, student_responses)
            
            st.markdown("### 🎯 Résultats de l'évaluation")
            
            score = comparison.get('score', 0)
            
            # Affichage du score avec couleurs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if score >= 80:
                    st.success(f"🏆 Excellent: {score}%")
                elif score >= 60:
                    st.warning(f"👍 Bien: {score}%")
                else:
                    st.error(f"📚 À revoir: {score}%")
            
            with col2:
                st.info(f"📊 {len(student_responses)} concepts analysés")
            
            with col3:
                st.metric("Score ontologique", f"{score}%")
            
            # Feedback détaillé
            if 'details' in comparison and comparison['details']:
                st.markdown("### 📝 Feedback détaillé")
                for detail in comparison['details']:
                    st.write(detail)
            
            # Conseils d'amélioration
            if score < 70:
                st.markdown("### � Conseils pour s'améliorer")
                st.info("""
                - Observez attentivement le rythme cardiaque
                - Analysez la morphologie des ondes P, QRS, T
                - Vérifiez les intervalles PR et QT
                - Considérez l'axe électrique du cœur
                """)
        
        else:
            st.warning("⚠️ Aucune annotation experte disponible pour ce cas")
            st.info("✅ Votre interprétation a été enregistrée pour révision")
    
    except ImportError:
        st.error("❌ Module de comparaison ontologique non disponible")
        st.info("✅ Interprétation enregistrée - évaluation manuelle requise")

def page_student_progress():
    """Page de suivi des progrès étudiant"""
    
    st.header("📈 Mes progrès")
    st.info("🚧 Fonctionnalité en développement (WP4)")
    
    # Simulation de statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Exercices", "0", "Commencez !")
    
    with col2:
        st.metric("📊 Score moyen", "-%", "En attente")
    
    with col3:
        st.metric("🏆 Niveau", "Débutant", "")
    
    with col4:
        st.metric("⏱️ Temps total", "0h", "")

def page_sessions_management():
    """Page de gestion des sessions ECG pour experts et admins"""
    
    st.title("📚 Gestion des Sessions ECG")
    st.markdown("*Interface dédiée à la création et gestion des sessions d'exercices*")
    
    # Statistiques des sessions
    sessions_count = count_ecg_sessions()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Sessions totales", sessions_count)
    
    with col2:
        st.metric("✅ Sessions actives", "0")  # À implémenter
    
    with col3:
        st.metric("👥 Étudiants inscrits", "0")  # À implémenter
    
    st.markdown("---")
    
    # Onglets pour organiser les fonctionnalités
    tab1, tab2, tab3 = st.tabs(["➕ Créer Session", "📋 Mes Sessions", "📊 Statistiques"])
    
    with tab1:
        st.markdown("### ➕ Créer une nouvelle session d'exercices")
        create_session_interface()
    
    with tab2:
        st.markdown("### 📋 Sessions existantes")
        display_user_sessions()
    
    with tab3:
        st.markdown("### 📊 Statistiques des sessions")
        display_sessions_statistics()

def create_session_interface():
    """Interface de création de session pour experts"""
    
    with st.form("create_session_expert"):
        col1, col2 = st.columns(2)
        
        with col1:
            session_name = st.text_input(
                "📝 Nom de la session",
                placeholder="Ex: ECG Cardiologie - Niveau 1",
                help="Nom descriptif pour identifier la session"
            )
            
            session_description = st.text_area(
                "📋 Description",
                placeholder="Description des objectifs et contenu de la session...",
                help="Description détaillée pour les étudiants"
            )
            
            difficulty = st.selectbox(
                "📊 Difficulté",
                ["🟢 Débutant", "🟡 Intermédiaire", "🔴 Avancé"],
                help="Niveau de difficulté de la session"
            )
        
        with col2:
            time_limit = st.number_input(
                "⏱️ Durée limite (minutes)",
                min_value=5,
                max_value=180,
                value=30,
                help="Temps limite pour compléter la session"
            )
            
            # Sélection des cas ECG disponibles
            available_cases = get_available_cases_for_sessions()
            
            if available_cases:
                selected_cases = st.multiselect(
                    "📋 Cas ECG à inclure",
                    options=available_cases,
                    help="Sélectionnez les cas ECG pour cette session"
                )
            else:
                st.warning("⚠️ Aucun cas ECG disponible. Importez des cas d'abord.")
                selected_cases = []
            
            show_feedback = st.checkbox(
                "💡 Afficher le feedback immédiat",
                value=True,
                help="Les étudiants voient le feedback après chaque réponse"
            )
            
            allow_retry = st.checkbox(
                "🔄 Autoriser les tentatives multiples",
                value=True,
                help="Les étudiants peuvent refaire la session"
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ Créer la session", type="primary", use_container_width=True):
                if session_name and selected_cases:
                    create_ecg_session(
                        name=session_name,
                        description=session_description,
                        difficulty=difficulty,
                        time_limit=time_limit,
                        cases=selected_cases,
                        show_feedback=show_feedback,
                        allow_retry=allow_retry,
                        created_by=st.session_state.user_info.get('name', 'Expert')
                    )
                    st.success(f"✅ Session '{session_name}' créée avec succès!")
                    st.rerun()
                else:
                    st.error("❌ Veuillez remplir le nom et sélectionner au moins un cas ECG")
        
        with col2:
            if st.form_submit_button("🔄 Réinitialiser", use_container_width=True):
                st.rerun()

def get_available_cases_for_sessions():
    """Récupère la liste des cas ECG disponibles pour les sessions"""
    
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    available_cases = []
    
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                
                # Chercher les images ECG dans le dossier
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(case_dir.glob(ext))
                
                if metadata_file.exists() and image_files:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        
                        # Vérifier s'il y a des annotations expertes
                        annotations = case_data.get('annotations', [])
                        expert_annotations = [ann for ann in annotations 
                                            if ann.get('type') == 'expert' or ann.get('auteur') == 'expert']
                        
                        if expert_annotations:
                            case_display = f"✅ {case_data.get('case_id', case_dir.name)}"
                        else:
                            case_display = f"⚠️ {case_data.get('case_id', case_dir.name)} (sans annotation experte)"
                        
                        available_cases.append(case_display)
                    except Exception:
                        continue
    
    return available_cases

def create_ecg_session(name, description, difficulty, time_limit, cases, show_feedback, allow_retry, created_by):
    """Crée une nouvelle session ECG"""
    
    sessions_dir = Path(__file__).parent.parent / "data" / "ecg_sessions"
    sessions_dir.mkdir(exist_ok=True)
    
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_file = sessions_dir / f"{session_id}.json"
    
    session_data = {
        'session_id': session_id,
        'name': name,
        'description': description,
        'difficulty': difficulty,
        'time_limit': time_limit,
        'cases': [case.replace('✅ ', '').replace('⚠️ ', '').split(' (')[0] for case in cases],
        'show_feedback': show_feedback,
        'allow_retry': allow_retry,
        'created_by': created_by,
        'created_date': datetime.now().isoformat(),
        'status': 'active',
        'participants': []
    }
    
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

def display_user_sessions():
    """Affiche les sessions créées par l'utilisateur"""
    
    sessions_dir = Path(__file__).parent.parent / "data" / "ecg_sessions"
    
    if not sessions_dir.exists():
        st.info("📭 Aucune session créée pour le moment")
        return
    
    current_user = st.session_state.user_info.get('name', 'Expert')
    user_sessions = []
    
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Afficher toutes les sessions pour les admins, seulement les siennes pour les experts
            if st.session_state.user_role == 'admin' or session_data.get('created_by') == current_user:
                user_sessions.append(session_data)
        except Exception:
            continue
    
    if user_sessions:
        st.success(f"📚 {len(user_sessions)} session(s) trouvée(s)")
        
        for session in user_sessions:
            with st.expander(f"📚 {session['name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {session.get('description', 'Aucune description')}")
                    st.markdown(f"**Difficulté:** {session.get('difficulty', 'Non spécifiée')}")
                    st.markdown(f"**Durée:** {session.get('time_limit', 30)} minutes")
                    st.markdown(f"**Cas ECG:** {len(session.get('cases', []))} cas")
                    
                    cases_list = ", ".join(session.get('cases', [])[:3])
                    if len(session.get('cases', [])) > 3:
                        cases_list += f" et {len(session.get('cases', [])) - 3} autre(s)"
                    st.markdown(f"**Contenu:** {cases_list}")
                
                with col2:
                    st.markdown(f"**Créé par:** {session.get('created_by', 'Inconnu')}")
                    created_date = session.get('created_date', '')
                    if created_date:
                        try:
                            date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime("%d/%m/%Y")
                            st.markdown(f"**Date:** {formatted_date}")
                        except:
                            st.markdown(f"**Date:** {created_date[:10]}")
                    
                    status = session.get('status', 'active')
                    if status == 'active':
                        st.success("✅ Active")
                    else:
                        st.warning("⏸️ Inactive")
                    
                    # Actions
                    if st.button(f"✏️ Modifier", key=f"edit_{session['session_id']}"):
                        st.info("🚧 Modification en développement")
                    
                    if st.button(f"📊 Stats", key=f"stats_{session['session_id']}"):
                        st.info("🚧 Statistiques en développement")
    else:
        st.info("📭 Aucune session créée par vous")

def display_sessions_statistics():
    """Affiche les statistiques des sessions"""
    
    st.info("🚧 Statistiques des sessions en développement")
    
    # Simulation de statistiques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📈 Taux de complétion", "0%")
    
    with col2:
        st.metric("⭐ Score moyen", "0%")
    
    with col3:
        st.metric("⏱️ Temps moyen", "0 min")

def page_database_management():
    """Page de gestion de base de données"""
    
    st.title("📊 Gestion Base de Données")
    
    # Statistiques de la base
    cases_count = count_total_cases()
    annotated_count = count_annotated_cases()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Cas totaux", cases_count)
    
    with col2:
        st.metric("✅ Cas annotés", annotated_count)
    
    with col3:
        if cases_count > 0:
            progress = annotated_count / cases_count
            st.metric("📈 Progression", f"{progress*100:.0f}%")
        else:
            st.metric("📈 Progression", "0%")
    
    st.markdown("---")
    
    # Onglets pour organiser les fonctionnalités
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Cas ECG", "📚 Sessions ECG", "📊 Analytics", "💾 Backup", "🏷️ Tags", "📄 Templates"])
    
    with tab1:
        display_advanced_cases_management()
    
    with tab2:
        display_sessions_management()
    
    with tab3:
        display_database_analytics_tab()
    
    with tab4:
        display_backup_management_tab()
    
    with tab5:
        display_tagging_management_tab()
    
    with tab6:
        display_templates_management_tab()

def display_advanced_cases_management():
    """Interface avancée de gestion des cas ECG"""
    
    st.markdown("### 📋 Gestion Avancée des Cas ECG")
    
    # Contrôles de recherche et filtrage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input(
            "🔍 Recherche",
            placeholder="Titre, annotation, mots-clés...",
            help="Recherche dans les titres, annotations et mots-clés"
        )
    
    with col2:
        sort_by = st.selectbox(
            "📊 Trier par",
            ["Date d'ajout (récent)", "Date d'ajout (ancien)", "Titre (A-Z)", "Titre (Z-A)", "Nb annotations"],
            help="Critère de tri des cas ECG"
        )
    
    with col3:
        filter_annotated = st.selectbox(
            "🏷️ Filtrer",
            ["Tous les cas", "Cas annotés", "Cas non annotés"],
            help="Filtrer selon l'état d'annotation"
        )
    
    st.markdown("---")
    
    # Charger et filtrer les cas
    cases_data = load_and_filter_cases(search_term, sort_by, filter_annotated)
    
    if not cases_data:
        st.info("📭 Aucun cas ECG trouvé selon vos critères.")
        return
    
    st.markdown(f"**📊 {len(cases_data)} cas trouvé(s)**")
    
    # Affichage des cas avec pagination
    cases_per_page = 10
    total_pages = (len(cases_data) + cases_per_page - 1) // cases_per_page
    
    if total_pages > 1:
        page_num = st.number_input(
            f"📄 Page", 
            min_value=1, 
            max_value=total_pages, 
            value=1,
            help=f"Page courante sur {total_pages} pages"
        )
        start_idx = (page_num - 1) * cases_per_page
        end_idx = min(start_idx + cases_per_page, len(cases_data))
        page_cases = cases_data[start_idx:end_idx]
    else:
        page_cases = cases_data
        page_num = 1
    
    # Affichage des cas
    for case in page_cases:
        display_case_card(case)
    
    # Gestion de la confirmation de suppression avec dialog modal
    if 'delete_confirm' in st.session_state:
        case_to_delete = st.session_state['delete_confirm']
        
        # Utiliser st.dialog si disponible (Streamlit 1.32+)
        try:
            @st.dialog("🗑️ Confirmation de suppression")
            def show_delete_confirmation():
                st.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #ff4757;">⚠️ Attention !</h3>
                    <p style="font-size: 18px;">Voulez-vous vraiment supprimer le cas :</p>
                    <div style="background: #fff5f5; padding: 15px; border-radius: 8px; border: 2px solid #ff4757; margin: 15px 0;">
                        <strong style="color: #ff4757; font-size: 20px;">📋 {case_to_delete}</strong>
                    </div>
                    <p style="color: #dc3545; font-weight: bold;">⚠️ Cette action est irréversible !</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Confirmer", type="primary", use_container_width=True):
                        with st.spinner("🗑️ Suppression..."):
                            success = delete_case(case_to_delete)
                            if success:
                                keys_to_delete = [key for key in st.session_state.keys() if case_to_delete in str(key)]
                                for key in keys_to_delete:
                                    del st.session_state[key]
                                del st.session_state['delete_confirm']
                                st.success(f"✅ Cas '{case_to_delete}' supprimé !")
                                st.rerun()
                
                with col2:
                    if st.button("❌ Annuler", use_container_width=True):
                        del st.session_state['delete_confirm']
                        st.rerun()
            
            # Afficher la dialog
            show_delete_confirmation()
            
        except (AttributeError, TypeError):
            # Fallback si st.dialog n'est pas disponible
            st.error("🚨 **CONFIRMATION DE SUPPRESSION**")
            
            # Container en haut de page
            with st.container():
                st.markdown(f"""
                <div style="
                    background: #fff;
                    border: 4px solid #ff4757;
                    border-radius: 15px;
                    padding: 30px;
                    margin: 20px auto;
                    max-width: 600px;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(255, 71, 87, 0.3);
                ">
                    <h2 style="color: #ff4757; margin: 0 0 20px 0;">🗑️ Suppression de cas</h2>
                    <p style="font-size: 18px; margin: 15px 0;">Voulez-vous supprimer le cas :</p>
                    <div style="background: #fff5f5; padding: 15px; border-radius: 8px; border: 2px solid #ff4757; margin: 20px 0;">
                        <strong style="color: #ff4757; font-size: 22px;">📋 {case_to_delete}</strong>
                    </div>
                    <p style="color: #dc3545; font-weight: bold; font-size: 16px;">⚠️ Cette action est définitive !</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Boutons centrés
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    subcol1, subcol2 = st.columns(2)
                    
                    with subcol1:
                        if st.button("✅ **CONFIRMER**", type="primary", key="confirm_delete", use_container_width=True):
                            with st.spinner("🗑️ Suppression..."):
                                success = delete_case(case_to_delete)
                                if success:
                                    keys_to_delete = [key for key in st.session_state.keys() if case_to_delete in str(key)]
                                    for key in keys_to_delete:
                                        del st.session_state[key]
                                    del st.session_state['delete_confirm']
                                    st.balloons()
                                    st.success(f"✅ Cas supprimé !")
                                    st.rerun()
                    
                    with subcol2:
                        if st.button("❌ **ANNULER**", key="cancel_delete", use_container_width=True):
                            del st.session_state['delete_confirm']
                            st.rerun()
            
            # Stopper l'exécution pour ne montrer que la confirmation
            st.stop()

def load_and_filter_cases(search_term, sort_by, filter_annotated):
    """Charge et filtre les cas ECG selon les critères"""
    
    # Utilisation d'un chemin absolu cohérent
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    if not cases_dir.exists():
        return []
    
    cases_data = []
    
    for case_folder in cases_dir.iterdir():
        if case_folder.is_dir():
            case_info = load_case_info(case_folder)
            if case_info:
                cases_data.append(case_info)
    
    # Filtrage par recherche
    if search_term:
        search_lower = search_term.lower()
        filtered_cases = []
        
        for case in cases_data:
            # Recherche dans le titre
            if search_lower in case.get('name', '').lower():
                filtered_cases.append(case)
                continue
            
            # Recherche dans les annotations
            annotations = case.get('annotations', [])
            found_in_annotations = False
            for ann in annotations:
                if search_lower in ann.get('concept', '').lower() or search_lower in ann.get('interpretation', '').lower():
                    found_in_annotations = True
                    break
            
            if found_in_annotations:
                filtered_cases.append(case)
        
        cases_data = filtered_cases
    
    # Filtrage par état d'annotation
    if filter_annotated == "Cas annotés":
        cases_data = [case for case in cases_data if case.get('annotations')]
    elif filter_annotated == "Cas non annotés":
        cases_data = [case for case in cases_data if not case.get('annotations')]
    
    # Tri
    if sort_by == "Date d'ajout (récent)":
        cases_data.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    elif sort_by == "Date d'ajout (ancien)":
        cases_data.sort(key=lambda x: x.get('created_date', ''))
    elif sort_by == "Titre (A-Z)":
        cases_data.sort(key=lambda x: x.get('name', '').lower())
    elif sort_by == "Titre (Z-A)":
        cases_data.sort(key=lambda x: x.get('name', '').lower(), reverse=True)
    elif sort_by == "Nb annotations":
        cases_data.sort(key=lambda x: len(x.get('annotations', [])), reverse=True)
    
    return cases_data

def load_case_info(case_folder):
    """Charge les informations d'un cas ECG - REPRODUCTION EXACTE DE LA LOGIQUE ÉTUDIANT"""
    
    try:
        case_name = case_folder.name
        metadata_file = case_folder / "metadata.json"
        
        # Chercher les images ECG dans le dossier - EXACTEMENT COMME CÔTÉ ÉTUDIANT
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(case_folder.glob(ext))
        
        # Vérifier qu'il y a metadata.json ET des images - COMME CÔTÉ ÉTUDIANT
        if not (metadata_file.exists() and image_files):
            return None
        
        # Charger les métadonnées - EXACTEMENT COMME CÔTÉ ÉTUDIANT
        with open(metadata_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        # Ajouter toutes les informations sur les images - COPIE EXACTE CÔTÉ ÉTUDIANT
        sorted_images = sorted(image_files, key=lambda x: x.name)
        case_data['image_paths'] = [str(img) for img in sorted_images]
        case_data['image_path'] = str(sorted_images[0])  # Première image pour compatibilité
        case_data['total_images'] = len(sorted_images)
        case_data['case_folder'] = str(case_folder)
        
        # Ajouts spécifiques admin
        case_data['name'] = case_name
        case_data['folder_path'] = str(case_folder)
        
        # Charger les annotations séparément pour l'admin
        annotations_file = case_folder / "annotations.json"
        if annotations_file.exists():
            with open(annotations_file, 'r', encoding='utf-8') as f:
                case_data['annotations'] = json.load(f)
        elif 'annotations' not in case_data:
            case_data['annotations'] = []
        
        # Compter les fichiers ECG pour l'admin
        ecg_files = []
        for ext in ['.png', '.jpg', '.jpeg', '.pdf']:
            ecg_files.extend(case_folder.glob(f"*{ext}"))
        case_data['ecg_files_count'] = len(ecg_files)
        
        return case_data
        
    except Exception as e:
        st.warning(f"Erreur lors du chargement du cas {case_folder.name}: {e}")
        return None

def display_case_card(case):
    """Affiche une carte pour un cas ECG - UTILISE LA LOGIQUE ÉTUDIANT QUI FONCTIONNE"""
    
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: #f9f9f9;">
        """, unsafe_allow_html=True)
        
        # En-tête du cas
        case_id = case.get('case_id', case['name'])
        
        # Informations principales
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**📋 Cas ECG: {case_id}**")
            annotations_count = len(case.get('annotations', []))
            st.markdown(f"🏷️ {annotations_count} annotation(s) | 📁 {case.get('ecg_files_count', 0)} fichier(s)")
        
        with col2:
            created_date = case.get('created_date', '')
            if created_date:
                try:
                    date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                except:
                    formatted_date = created_date[:10] if len(created_date) >= 10 else created_date
            else:
                formatted_date = "Date inconnue"
            st.markdown(f"📅 {formatted_date}")
        
        with col3:
            # Actions admin
            if st.button("✏️", key=f"edit_{case['name']}", help="Éditer"):
                st.session_state[f"editing_{case['name']}"] = True
                st.rerun()
            
            if st.button("🗑️", key=f"delete_{case['name']}", help="Supprimer"):
                st.session_state['delete_confirm'] = case['name']
                st.rerun()
        
        st.markdown("---")
        
        # COPIE EXACTE DE LA LOGIQUE ÉTUDIANT POUR L'AFFICHAGE DES ECG
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Affichage de tous les ECG du cas - LOGIQUE ÉTUDIANT
            if 'image_paths' in case and case['image_paths']:
                total_images = len(case['image_paths'])
                
                if total_images > 1:
                    st.info(f"📊 Ce cas contient **{total_images} ECG**")
                    
                    # Navigation entre les ECG - EXACTEMENT COMME CÔTÉ ÉTUDIANT
                    ecg_preview_index = st.selectbox(
                        "Aperçu ECG :",
                        range(total_images),
                        format_func=lambda i: f"ECG {i+1}/{total_images}",
                        key=f"admin_preview_ecg_{case_id}"
                    )
                else:
                    ecg_preview_index = 0
                    st.info(f"📊 Ce cas contient **1 ECG**")
                
                # Affichage de l'ECG sélectionné - EXACTEMENT COMME CÔTÉ ÉTUDIANT
                image_path = Path(case['image_paths'][ecg_preview_index])
                if image_path.exists():
                    st.image(str(image_path), 
                           caption=f"📋 Admin - ECG {ecg_preview_index+1}/{total_images} - {case_id}",
                           use_container_width=True)
                else:
                    st.warning(f"⚠️ ECG {ecg_preview_index+1} non trouvé")
                    
            elif 'image_path' in case:
                # Compatibilité avec l'ancien format - COMME CÔTÉ ÉTUDIANT
                image_path = Path(case['image_path'])
                if image_path.exists():
                    st.image(str(image_path), 
                           caption=f"📋 Admin - {case_id}",
                           use_container_width=True)
                else:
                    st.warning("⚠️ Image ECG non trouvée")
            else:
                st.info("📄 Cas ECG (format non-image)")
        
        with col2:
            st.markdown("**📋 Informations du cas**")
            
            # Aperçu des annotations
            if case.get('annotations'):
                concepts = [ann.get('concept', '') for ann in case['annotations'][:2]]
                concepts_text = ", ".join(concepts)
                if len(case['annotations']) > 2:
                    concepts_text += "..."
                st.markdown(f"🔍 {concepts_text}")
            else:
                st.markdown("🔍 Pas d'annotations")
            
            # Vérifier s'il y a des annotations expertes
            annotations = case.get('annotations', [])
            expert_annotations = [ann for ann in annotations 
                                if ann.get('type') == 'expert' or ann.get('auteur') == 'expert']
            
            if expert_annotations:
                st.success("✅ Cas avec annotation experte")
            else:
                st.info("💭 Cas en attente d'annotation experte")
        
        # Interface d'édition
        if st.session_state.get(f"editing_{case['name']}", False):
            display_case_edit_form(case)
        
        st.markdown("</div>", unsafe_allow_html=True)

def display_case_edit_form(case):
    """Affiche le formulaire d'édition d'un cas"""
    
    st.markdown("#### ✏️ Édition du cas")
    
    with st.form(f"edit_case_{case['name']}"):
        new_name = st.text_input("Nouveau nom", value=case['name'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ Sauvegarder", type="primary"):
                if new_name and new_name != case['name']:
                    rename_case(case['name'], new_name)
                    st.session_state[f"editing_{case['name']}"] = False
                    st.success(f"Cas renommé en '{new_name}'")
                    st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Annuler"):
                st.session_state[f"editing_{case['name']}"] = False
                st.rerun()


def display_database_analytics_tab():
    """Onglet Analytics de la base de données"""
    try:
        from frontend.admin.database_analytics import display_database_analytics
        display_database_analytics()
    except ImportError:
        st.warning("⚠️ Module Analytics non disponible. Installer: pip install plotly pandas")
        st.info("📊 Les analytics avancés nécessitent des dépendances supplémentaires")

def display_backup_management_tab():
    """Onglet gestion des backups"""
    try:
        from frontend.admin.database_backup import display_backup_system
        display_backup_system()
    except ImportError as e:
        st.error(f"❌ Erreur chargement module backup : {e}")

def display_tagging_management_tab():
    """Onglet gestion des tags"""
    try:
        from frontend.admin.advanced_tagging import display_advanced_tagging_system
        display_advanced_tagging_system()
    except ImportError as e:
        st.error(f"❌ Erreur chargement module tags : {e}")

def display_templates_management_tab():
    """Onglet gestion des templates"""
    try:
        from frontend.admin.templates_system import display_templates_system
        display_templates_system()
    except ImportError as e:
        st.error(f"❌ Erreur chargement module templates : {e}")

def display_sessions_management():
    """Interface de gestion des sessions ECG"""
    
    st.markdown("### 📚 Gestion des Sessions ECG")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("➕ Créer une nouvelle session", type="primary"):
            st.session_state['creating_session'] = True
            st.rerun()
    
    with col2:
        sessions_count = count_ecg_sessions()
        st.metric("📚 Sessions", sessions_count)
    
    # Interface de création de session
    if st.session_state.get('creating_session', False):
        create_ecg_session_interface()
    
    # Liste des sessions existantes
    display_ecg_sessions()

def display_multi_ecg_import():
    """Interface supprimée - utilisez Import Intelligent"""
    st.warning("⚠️ Cette fonctionnalité a été retirée. Utilisez 'Import Intelligent' pour ajouter des ECG.")
    
    with st.form("multi_ecg_import"):
        case_name = st.text_input(
            "Nom du cas d'étude",
            placeholder="FONCTIONNALITÉ SUPPRIMÉE",
            help="Utilisez 'Import Intelligent' pour ajouter des ECG",
            disabled=True
        )
        
        uploaded_files = st.file_uploader(
            "Sélectionnez plusieurs fichiers ECG",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            accept_multiple_files=True,
            help="Importez plusieurs ECG (images ou PDF) pour un même cas"
        )
        
        case_description = st.text_area(
            "Description du cas (optionnel)",
            placeholder="Description des ECG importés, contexte clinique...",
            help="Description pour contextualiser les ECG"
        )
        
        submitted = st.form_submit_button("� Importer les ECG", type="primary")
        
        if submitted and case_name and uploaded_files:
            import_multi_ecg_case(case_name, uploaded_files, case_description)

def import_multi_ecg_case(case_name, uploaded_files, description):
    """Importe plusieurs ECG dans un même cas"""
    
    pass

def page_admin_settings():
    """Page de paramètres administrateur"""
    
    st.header("⚙️ Paramètres système")
    st.info("🚧 Configuration système en développement")

def count_total_cases():
    """Compte le nombre total de cas"""
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    if cases_dir.exists():
        return len([d for d in cases_dir.iterdir() if d.is_dir()])
    return 0

def count_annotated_cases():
    """Compte le nombre de cas annotés"""
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    count = 0
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        annotations = metadata.get('annotations', [])
                        if annotations:
                            count += 1
                    except Exception:
                        pass
    return count

def count_ecg_sessions():
    """Compte le nombre de sessions ECG"""
    sessions_dir = Path("data/ecg_sessions")
    if not sessions_dir.exists():
        return 0
    
    return len([f for f in sessions_dir.iterdir() if f.suffix == '.json'])

def delete_case(case_name):
    """Supprimer un cas ECG"""
    try:
        # Utilisation d'un chemin absolu pour éviter les problèmes
        base_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
        case_dir = base_dir / case_name
        
        if case_dir.exists():
            shutil.rmtree(case_dir)
            st.success(f"✅ Cas '{case_name}' supprimé avec succès")
            return True
        else:
            st.error(f"❌ Cas '{case_name}' non trouvé")
            return False
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression : {e}")
        return False

def rename_case(old_name, new_name):
    """Renommer un cas ECG"""
    try:
        base_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
        old_path = base_dir / old_name
        new_path = base_dir / new_name
        
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            
            # Mettre à jour l'ID dans les métadonnées
            metadata_file = new_path / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata['case_id'] = new_name
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Cas renommé de '{old_name}' vers '{new_name}'")
        else:
            st.error(f"❌ Impossible de renommer : le cas '{new_name}' existe déjà ou '{old_name}' n'existe pas")
    except Exception as e:
        st.error(f"❌ Erreur lors du renommage : {e}")

def show_case_details(case_dir):
    """Afficher les détails d'un cas"""
    st.markdown(f"### 🔍 Détails du cas: {case_dir.name}")
    
    # Métadonnées
    metadata_file = case_dir / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            st.json(metadata)
            
        except Exception as e:
            st.error(f"❌ Erreur lecture métadonnées: {e}")
    else:
        st.warning("⚠️ Aucune métadonnée trouvée")
    
    # Fichiers
    st.markdown("**📁 Fichiers dans le dossier:**")
    for file_path in case_dir.iterdir():
        if file_path.is_file():
            st.write(f"- {file_path.name} ({file_path.stat().st_size} bytes)")

def evaluate_student_exercise(case_data, user_input):
    """Évalue l'exercice d'un étudiant"""
    
    # Chargement des annotations expertes
    case_dir = Path(f"data/ecg_cases/{case_data['case_id']}")
    annotations_file = case_dir / "annotations.json"
    
    if not annotations_file.exists():
        st.error("❌ Annotations expertes non trouvées")
        return
    
    with open(annotations_file, 'r', encoding='utf-8') as f:
        expert_annotations = json.load(f)
    
    # Évaluation avec le moteur de correction
    if 'corrector' in st.session_state:
        total_score = 0
        max_score = 0
        
        for annotation in expert_annotations['annotations']:
            expected = annotation['concept']
            coefficient = annotation.get('coefficient', 1.0)
            
            score = st.session_state.corrector.get_score(expected, user_input)
            total_score += score * coefficient
            max_score += 100 * coefficient
        
        final_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Affichage du résultat
        st.markdown("### 📊 Résultat de l'évaluation")
        
        if final_score >= 80:
            st.success(f"🎉 Excellent ! Score : {final_score:.1f}%")
        elif final_score >= 60:
            st.warning(f"👍 Bien ! Score : {final_score:.1f}%")
        elif final_score >= 40:
            st.info(f"📚 À améliorer. Score : {final_score:.1f}%")
        else:
            st.error(f"❌ Insuffisant. Score : {final_score:.1f}%")

def count_ecg_sessions():
    """Compte le nombre de sessions ECG existantes"""
    sessions_dir = Path("data/ecg_sessions")
    if not sessions_dir.exists():
        return 0
    return len([d for d in sessions_dir.iterdir() if d.is_dir()])

def create_ecg_session_interface():
    """Interface de création et modification des sessions ECG"""
    
    # Onglets pour Créer / Modifier
    tab1, tab2 = st.tabs(["➕ Créer Session", "✏️ Modifier Session"])
    
    with tab1:
        create_new_session_form()
    
    with tab2:
        modify_existing_session_interface()

def create_new_session_form():
    """Formulaire de création d'une nouvelle session"""
    
    st.markdown("### ➕ Créer une nouvelle session d'exercices")
    
    with st.form("create_session_form"):
        # Informations de la session
        col1, col2 = st.columns(2)
        
        with col1:
            session_name = st.text_input(
                "Nom de la session *",
                placeholder="Ex: Troubles du Rythme - Niveau 1",
                help="Nom descriptif de la session d'exercices"
            )
            
            session_description = st.text_area(
                "Description",
                placeholder="Description de la session et objectifs pédagogiques...",
                help="Description détaillée pour les étudiants"
            )
        
        with col2:
            difficulty = st.selectbox(
                "Niveau de difficulté",
                ["🟢 Débutant", "🟡 Intermédiaire", "🔴 Avancé"],
                help="Niveau de difficulté pour guider les étudiants"
            )
            
            time_limit = st.number_input(
                "Temps limite (minutes)",
                min_value=5,
                max_value=120,
                value=30,
                help="Temps recommandé pour compléter la session"
            )
        
        st.markdown("---")
        
        # Sélection des cas ECG
        st.markdown("**📋 Sélection des cas ECG**")
        
        # Charger la liste des cas disponibles
        available_cases = get_available_ecg_cases()
        
        if available_cases:
            selected_cases = st.multiselect(
                "Choisissez les cas ECG pour cette session",
                options=[case['name'] for case in available_cases],
                help="Sélectionnez plusieurs cas pour créer un parcours d'exercices"
            )
            
            if selected_cases:
                st.info(f"✅ {len(selected_cases)} cas sélectionnés")
                
                # Aperçu des cas sélectionnés
                with st.expander("📖 Aperçu des cas sélectionnés"):
                    for case_name in selected_cases:
                        case_info = next((c for c in available_cases if c['name'] == case_name), None)
                        if case_info:
                            st.write(f"• **{case_name}** - {case_info.get('annotations_count', 0)} annotation(s)")
        else:
            st.warning("⚠️ Aucun cas ECG disponible. Importez des cas d'abord.")
        
        st.markdown("---")
        
        # Paramètres avancés
        with st.expander("⚙️ Paramètres avancés"):
            randomize_order = st.checkbox(
                "Ordre aléatoire des cas",
                value=False,
                help="Mélanger l'ordre des cas pour chaque étudiant"
            )
            
            show_feedback = st.checkbox(
                "Feedback immédiat",
                value=True,
                help="Afficher les corrections après chaque cas"
            )
            
            allow_retry = st.checkbox(
                "Autoriser les reprises",
                value=True,
                help="Permettre aux étudiants de refaire la session"
            )
        
        # Boutons de validation
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("✅ Créer la session", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Annuler")
        
        if cancelled:
            st.session_state['creating_session'] = False
            st.rerun()
        
        if submitted:
            if session_name and selected_cases:
                # Créer la session
                session_data = {
                    'name': session_name,
                    'description': session_description,
                    'difficulty': difficulty,
                    'time_limit': time_limit,
                    'cases': selected_cases,
                    'randomize_order': randomize_order,
                    'show_feedback': show_feedback,
                    'allow_retry': allow_retry,
                    'created_date': datetime.now().isoformat(),
                    'created_by': 'admin'  # TODO: gérer les utilisateurs
                }
                
                if create_ecg_session(session_data):
                    st.success(f"✅ Session '{session_name}' créée avec succès !")
                    st.session_state['creating_session'] = False
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la création de la session")
            else:
                st.error("⚠️ Veuillez remplir le nom et sélectionner au moins un cas ECG")

def modify_existing_session_interface():
    """Interface de modification des sessions existantes"""
    
    st.markdown("### ✏️ Modifier une session existante")
    
    # Charger les sessions existantes
    existing_sessions = get_existing_sessions()
    
    if not existing_sessions:
        st.info("📭 Aucune session créée pour le moment.")
        return
    
    # Sélection de la session à modifier
    col1, col2 = st.columns([2, 1])
    
    with col1:
        session_names = [session['name'] for session in existing_sessions]
        selected_session_name = st.selectbox(
            "Choisir une session à modifier",
            session_names,
            help="Sélectionnez la session que vous souhaitez modifier"
        )
    
    with col2:
        # Boutons d'action
        if st.button("🗑️ Supprimer", type="secondary"):
            if st.session_state.get('confirm_delete_session') != selected_session_name:
                st.session_state['confirm_delete_session'] = selected_session_name
                st.warning(f"⚠️ Cliquez à nouveau pour confirmer la suppression de '{selected_session_name}'")
            else:
                if delete_ecg_session(selected_session_name):
                    st.success(f"✅ Session '{selected_session_name}' supprimée")
                    del st.session_state['confirm_delete_session']
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la suppression")
    
    # Affichage et modification de la session sélectionnée
    if selected_session_name:
        selected_session = next((s for s in existing_sessions if s['name'] == selected_session_name), None)
        if selected_session:
            modify_session_form(selected_session)

def modify_session_form(session_data):
    """Formulaire de modification d'une session"""
    
    st.markdown("---")
    st.markdown(f"#### ✏️ Modification de la session : **{session_data['name']}**")
    
    # Informations actuelles
    with st.expander("📋 Informations actuelles", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nom :** {session_data['name']}")
            st.write(f"**Difficulté :** {session_data.get('difficulty', 'Non définie')}")
            st.write(f"**Temps limite :** {session_data.get('time_limit', 30)} minutes")
        with col2:
            st.write(f"**Cas ECG :** {len(session_data.get('cases', []))} cas")
            st.write(f"**Créée le :** {session_data.get('created_date', 'Date inconnue')[:10]}")
            st.write(f"**Créée par :** {session_data.get('created_by', 'Inconnu')}")
    
    # Formulaire de modification
    with st.form(f"modify_session_form_{session_data['name']}"):
        st.markdown("#### 📝 Nouvelles valeurs")
        
        # Informations de base
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input(
                "Nouveau nom de la session",
                value=session_data['name'],
                help="Modifiez le nom de la session"
            )
            
            new_description = st.text_area(
                "Nouvelle description",
                value=session_data.get('description', ''),
                help="Description mise à jour"
            )
        
        with col2:
            new_difficulty = st.selectbox(
                "Nouveau niveau de difficulté",
                ["🟢 Débutant", "🟡 Intermédiaire", "🔴 Avancé"],
                index=["🟢 Débutant", "🟡 Intermédiaire", "🔴 Avancé"].index(session_data.get('difficulty', '🟢 Débutant')),
                help="Nouveau niveau de difficulté"
            )
            
            new_time_limit = st.number_input(
                "Nouveau temps limite (minutes)",
                min_value=5,
                max_value=120,
                value=session_data.get('time_limit', 30),
                help="Nouveau temps recommandé"
            )
        
        st.markdown("---")
        
        # Modification des cas ECG
        st.markdown("**📋 Modification des cas ECG**")
        
        available_cases = get_available_ecg_cases()
        
        if available_cases:
            current_cases = session_data.get('cases', [])
            new_selected_cases = st.multiselect(
                "Nouveaux cas ECG pour cette session",
                options=[case['name'] for case in available_cases],
                default=current_cases,
                help="Modifiez la sélection des cas ECG"
            )
            
            # Comparaison des changements
            added_cases = [c for c in new_selected_cases if c not in current_cases]
            removed_cases = [c for c in current_cases if c not in new_selected_cases]
            
            if added_cases or removed_cases:
                st.markdown("**🔄 Aperçu des changements :**")
                if added_cases:
                    st.success(f"➕ **Ajoutés :** {', '.join(added_cases)}")
                if removed_cases:
                    st.warning(f"➖ **Supprimés :** {', '.join(removed_cases)}")
        else:
            st.warning("⚠️ Aucun cas ECG disponible")
            new_selected_cases = []
        
        st.markdown("---")
        
        # Paramètres avancés
        with st.expander("⚙️ Nouveaux paramètres avancés"):
            new_randomize = st.checkbox(
                "Ordre aléatoire des cas",
                value=session_data.get('randomize_order', False)
            )
            
            new_show_feedback = st.checkbox(
                "Afficher les corrections",
                value=session_data.get('show_feedback', True)
            )
            
            new_allow_retry = st.checkbox(
                "Autoriser les tentatives multiples",
                value=session_data.get('allow_retry', True)
            )
        
        # Boutons de validation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            update_submitted = st.form_submit_button("✅ Sauvegarder", type="primary")
        
        with col2:
            duplicate_submitted = st.form_submit_button("📋 Dupliquer", type="secondary")
        
        with col3:
            cancel_submitted = st.form_submit_button("❌ Annuler")
        
        if cancel_submitted:
            st.rerun()
        
        if duplicate_submitted:
            # Créer une copie avec un nouveau nom
            duplicate_name = f"{new_name} - Copie"
            duplicate_data = {
                'name': duplicate_name,
                'description': new_description + "\n(Copie de la session originale)",
                'difficulty': new_difficulty,
                'time_limit': new_time_limit,
                'cases': new_selected_cases,
                'randomize_order': new_randomize,
                'show_feedback': new_show_feedback,
                'allow_retry': new_allow_retry,
                'created_date': datetime.now().isoformat(),
                'created_by': 'admin'
            }
            
            if create_ecg_session(duplicate_data):
                st.success(f"✅ Session dupliquée sous le nom '{duplicate_name}'")
                st.rerun()
            else:
                st.error("❌ Erreur lors de la duplication")
        
        if update_submitted:
            if new_name and new_selected_cases:
                # Préparer les nouvelles données
                updated_data = {
                    'name': new_name,
                    'description': new_description,
                    'difficulty': new_difficulty,
                    'time_limit': new_time_limit,
                    'cases': new_selected_cases,
                    'randomize_order': new_randomize,
                    'show_feedback': new_show_feedback,
                    'allow_retry': new_allow_retry,
                    'created_date': session_data.get('created_date', datetime.now().isoformat()),
                    'created_by': session_data.get('created_by', 'admin'),
                    'modified_date': datetime.now().isoformat(),
                    'modified_by': 'admin'
                }
                
                # Supprimer l'ancienne et créer la nouvelle (si le nom a changé)
                if new_name != session_data['name']:
                    if delete_ecg_session(session_data['name']) and create_ecg_session(updated_data):
                        st.success(f"✅ Session renommée de '{session_data['name']}' vers '{new_name}' et mise à jour")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la mise à jour")
                else:
                    # Mise à jour sur place
                    if update_ecg_session(session_data['name'], updated_data):
                        st.success(f"✅ Session '{new_name}' mise à jour avec succès")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la mise à jour")
            else:
                st.error("⚠️ Veuillez remplir le nom et sélectionner au moins un cas ECG")

def update_ecg_session(session_name, updated_data):
    """Met à jour une session ECG existante"""
    sessions_dir = os.path.abspath("data/ecg_sessions")
    
    try:
        # Créer le dossier s'il n'existe pas
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Chercher le fichier par nom de session
        for file in os.listdir(sessions_dir):
            if file.endswith('.json'):
                full_path = os.path.join(sessions_dir, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('name') == session_name:
                            # Mettre à jour le fichier
                            with open(full_path, 'w', encoding='utf-8') as f:
                                json.dump(updated_data, f, indent=2, ensure_ascii=False)
                            return True
                except (json.JSONDecodeError, KeyError) as e:
                    st.warning(f"Fichier session corrompu ignoré : {file}")
                    continue
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour : {e}")
        return False
    
    return False

def delete_ecg_session(session_name):
    """Supprime une session ECG"""
    sessions_dir = os.path.abspath("data/ecg_sessions")
    
    try:
        # Convertir le nom en nom de fichier sûr
        safe_filename = "".join(c for c in session_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        filepath = os.path.join(sessions_dir, f"{safe_filename}.json")
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        else:
            # Chercher par nom dans tous les fichiers
            for file in os.listdir(sessions_dir):
                if file.endswith('.json'):
                    full_path = os.path.join(sessions_dir, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get('name') == session_name:
                                os.remove(full_path)
                                return True
                    except (json.JSONDecodeError, KeyError):
                        continue
    except Exception as e:
        st.error(f"Erreur lors de la suppression : {e}")
        return False
    
    return False

def get_existing_sessions():
    """Récupère la liste des sessions existantes"""
    sessions_dir = os.path.abspath("data/ecg_sessions")
    sessions = []
    
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir, exist_ok=True)
        return sessions
    
    try:
        for filename in os.listdir(sessions_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(sessions_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        sessions.append(session_data)
                except (json.JSONDecodeError, KeyError) as e:
                    st.warning(f"Session corrompue ignorée : {filename}")
                    continue
    except Exception as e:
        st.error(f"Erreur lors du chargement des sessions : {e}")
    
    return sessions

def display_ecg_sessions():
    """Affiche la liste des sessions ECG existantes"""
    
    sessions = get_ecg_sessions()
    
    if sessions:
        st.markdown("**📚 Sessions existantes**")
        
        for session in sessions:
            with st.expander(f"📖 {session['name']} ({session['difficulty']})", expanded=False):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description :** {session.get('description', 'Aucune description')}")
                    st.write(f"**Cas inclus :** {len(session['cases'])} ECG")
                    st.write(f"**Temps limite :** {session['time_limit']} minutes")
                    
                    # Liste des cas
                    if session['cases']:
                        st.write("**📋 Cas ECG :**")
                        for i, case_name in enumerate(session['cases'], 1):
                            st.write(f"  {i}. {case_name}")
                
                with col2:
                    st.write(f"**📅 Créée :** {session.get('created_date', 'N/A')[:10]}")
                    
                    # Actions
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button("✏️ Modifier", key=f"edit_session_{session['name']}"):
                            st.info("🚧 Modification en développement")
                    
                    with col_delete:
                        if st.button("🗑️ Supprimer", key=f"delete_session_{session['name']}"):
                            if delete_ecg_session(session['name']):
                                st.success("✅ Session supprimée")
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la suppression")
    else:
        st.info("📚 Aucune session créée pour le moment")

def get_available_ecg_cases():
    """Récupère la liste des cas ECG disponibles"""
    
    cases = []
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Compter les annotations
                        annotations_count = len(metadata.get('annotations', []))
                        
                        cases.append({
                            'name': case_dir.name,
                            'case_id': metadata.get('case_id', case_dir.name),
                            'annotations_count': annotations_count
                        })
                    except Exception as e:
                        pass  # Ignorer les cas avec métadonnées corrompues
    
    return cases

def create_ecg_session(session_data):
    """Crée une nouvelle session ECG"""
    
    try:
        sessions_dir = Path("data/ecg_sessions")
        sessions_dir.mkdir(exist_ok=True)
        
        # Créer un nom de fichier sûr
        session_filename = session_data['name'].replace(' ', '_').replace('/', '_')
        session_file = sessions_dir / f"{session_filename}.json"
        
        # Vérifier que la session n'existe pas déjà
        if session_file.exists():
            return False
        
        # Sauvegarder la session
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        return False

def get_ecg_sessions():
    """Récupère toutes les sessions ECG"""
    
    sessions = []
    sessions_dir = Path("data/ecg_sessions")
    
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                sessions.append(session_data)
            except Exception as e:
                pass  # Ignorer les fichiers corrompus
    
    return sessions

def delete_ecg_session(session_name):
    """Supprime une session ECG"""
    
    try:
        sessions_dir = Path("data/ecg_sessions")
        session_filename = session_name.replace(' ', '_').replace('/', '_')
        session_file = sessions_dir / f"{session_filename}.json"
        
        if session_file.exists():
            session_file.unlink()
            return True
        
        return False
        
    except Exception as e:
        return False

def display_available_sessions():
    """Affiche les sessions ECG disponibles pour les étudiants"""
    
    sessions = get_ecg_sessions()
    
    if sessions:
        st.markdown("### 📚 Sessions d'exercices disponibles")
        
        # Filtres
        col1, col2 = st.columns(2)
        
        with col1:
            difficulty_filter = st.selectbox(
                "Filtrer par niveau :",
                ["Tous niveaux", "🟢 Débutant", "🟡 Intermédiaire", "🔴 Avancé"],
                help="Choisissez votre niveau pour filtrer les sessions"
            )
        
        with col2:
            sort_by = st.selectbox(
                "Trier par :",
                ["Date de création", "Nom", "Durée", "Nombre de cas"],
                help="Ordre d'affichage des sessions"
            )
        
        # Filtrer les sessions
        filtered_sessions = sessions
        
        if difficulty_filter != "Tous niveaux":
            filtered_sessions = [s for s in sessions if s.get('difficulty') == difficulty_filter]
        
        if not filtered_sessions:
            st.info("📭 Aucune session disponible selon vos critères.")
            return
        
        # Afficher les sessions
        for session in filtered_sessions:
            with st.expander(f"📚 {session['name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**📝 Description :** {session.get('description', 'Aucune description')}")
                    st.markdown(f"**🎯 Niveau :** {session.get('difficulty', 'Non spécifié')}")
                    st.markdown(f"**⏱️ Durée estimée :** {session.get('time_limit', 30)} minutes")
                    st.markdown(f"**📋 Nombre de cas :** {len(session.get('cases', []))}")
                
                with col2:
                    if st.button(f"▶️ Commencer", key=f"start_session_{session['name']}", type="primary"):
                        # Démarrer la session
                        session_instance = {
                            'session_data': session,
                            'cases': session['cases'],
                            'current_case_index': 0,
                            'responses': {},
                            'start_time': datetime.now().isoformat(),
                            'scores': {},
                            'individual_mode': False
                        }
                        st.session_state['current_session'] = session_instance
                        st.success(f"🎯 Session '{session['name']}' démarrée !")
                        st.rerun()
    else:
        st.info("📭 Aucune session d'exercices disponible pour le moment.")
        st.markdown("""
        **💡 Les enseignants peuvent créer des sessions d'exercices dans la section Administration.**
        
        En attendant, vous pouvez :
        - Explorer les cas ECG individuels
        - Vous exercer sur des cas spécifiques
        """)

def get_ecg_sessions():
    """Récupère la liste des sessions ECG disponibles"""
    sessions_dir = Path(__file__).parent.parent / "data" / "ecg_sessions"
    sessions = []
    
    if not sessions_dir.exists():
        return sessions
    
    try:
        for session_file in sessions_dir.glob("*.json"):
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                sessions.append(session_data)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des sessions : {e}")
    
    return sessions

def run_ecg_session():
    """Exécute une session d'exercices ECG"""
    
    if 'current_session' not in st.session_state:
        st.error("❌ Aucune session active")
        return

    session = st.session_state['current_session']
    session_data = session['session_data']
    current_index = session['current_case_index']
    total_cases = len(session['cases'])
    is_individual = session.get('individual_mode', False)
    
    # En-tête adapté selon le type d'exercice
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if is_individual:
            st.markdown(f"## 📖 {session_data['name']}")
            st.markdown("**🎯 Exercice individuel**")
        else:
            st.markdown(f"## 📖 {session_data['name']}")
            st.markdown(f"**Cas {current_index + 1} sur {total_cases}**")
    
    with col2:
        if not is_individual:
            progress = (current_index) / total_cases
            st.progress(progress, text=f"{progress*100:.0f}%")
        else:
            st.markdown("### 📝")
            st.markdown("Mode pratique")
    
    with col3:
        quit_label = "❌ Quitter l'exercice" if is_individual else "❌ Quitter la session"
        if st.button(quit_label):
            if st.session_state.get('confirm_quit'):
                del st.session_state['current_session']
                if 'confirm_quit' in st.session_state:
                    del st.session_state['confirm_quit']
                st.rerun()
            else:
                st.session_state['confirm_quit'] = True
                st.warning("Cliquez à nouveau pour confirmer")
                st.rerun()
    
    # Vérifier si la session est terminée
    if current_index >= total_cases:
        display_session_results(session)
        return
    
    # Récupérer le cas current
    current_case_name = session['cases'][current_index]
    current_case_data = load_case_for_exercise(current_case_name)
    
    if not current_case_data:
        st.error(f"❌ Cas '{current_case_name}' non trouvé")
        return
    
    st.markdown("---")
    
    # Affichage du cas ECG
    display_case_for_exercise(current_case_data)
    
    st.markdown("---")
    
    # Interface d'annotation pour l'exercice
    st.markdown("### 🏷️ Votre interprétation")
    st.markdown("*Saisissez votre interprétation de cet ECG*")
    
    # Utiliser le système d'annotation semi-automatique
    try:
        from annotation_components import smart_annotation_input
        student_annotations = smart_annotation_input(
            key_prefix=f"exercise_{current_case_name}",
            max_tags=10
        )
    except ImportError:
        # Fallback en cas d'erreur d'import
        student_annotations = []
        st.text_area(
            "💭 Votre interprétation",
            key=f"interpretation_{current_case_name}",
            height=150,
            placeholder="Décrivez ce que vous observez sur cet ECG..."
        )
    
    # Zone de commentaires
    student_comments = st.text_area(
        "💬 Commentaires supplémentaires",
        key=f"comments_{current_case_name}",
        height=100,
        placeholder="Ajoutez des commentaires ou questions..."
    )
    
    # Boutons d'action
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Sauvegarder", type="secondary"):
            save_exercise_response(session, current_case_name, student_annotations, student_comments)
            st.success("✅ Réponse sauvegardée")
    
    with col2:
        if st.button("➡️ Suivant", type="primary"):
            # Sauvegarder la réponse
            save_exercise_response(session, current_case_name, student_annotations, student_comments)
            
            # Passer au cas suivant
            st.session_state['current_session']['current_case_index'] += 1
            st.rerun()
    
    with col3:
        if session_data.get('show_feedback', True):
            if st.button("💡 Voir le feedback", help="Comparer avec l'annotation experte"):
                display_exercise_feedback(current_case_data, student_annotations)

def load_case_for_exercise(case_name):
    """Charge un cas pour un exercice"""
    cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
    case_dir = cases_dir / case_name
    
    if not case_dir.exists():
        return None
    
    metadata_file = case_dir / "metadata.json"
    if not metadata_file.exists():
        return None
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        # Ajouter les chemins des images
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(case_dir.glob(ext))
        
        if image_files:
            sorted_images = sorted(image_files, key=lambda x: x.name)
            case_data['image_paths'] = [str(img) for img in sorted_images]
            case_data['image_path'] = str(sorted_images[0])
        
        case_data['case_id'] = case_name
        return case_data
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du cas : {e}")
        return None

def display_case_for_exercise(case_data):
    """Affiche un cas ECG pour un exercice"""
    
    case_id = case_data.get('case_id', 'Cas ECG')
    
    # Informations du cas
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📋 {case_id}")
        
        # Affichage des ECG
        if 'image_paths' in case_data and case_data['image_paths']:
            total_images = len(case_data['image_paths'])
            
            if total_images > 1:
                st.info(f"📊 Ce cas contient **{total_images} ECG**")
                
                # Navigation entre les ECG
                ecg_index = st.selectbox(
                    "Sélectionner l'ECG :",
                    range(total_images),
                    format_func=lambda i: f"ECG {i+1}/{total_images}",
                    key=f"exercise_ecg_{case_id}"
                )
            else:
                ecg_index = 0
            
            # Affichage de l'ECG sélectionné
            image_path = Path(case_data['image_paths'][ecg_index])
            if image_path.exists():
                st.image(str(image_path), 
                       caption=f"ECG {ecg_index+1}/{total_images} - {case_id}",
                       use_container_width=True)
            else:
                st.warning(f"⚠️ ECG {ecg_index+1} non trouvé")
        
        elif 'image_path' in case_data:
            image_path = Path(case_data['image_path'])
            if image_path.exists():
                st.image(str(image_path), 
                       caption=f"ECG - {case_id}",
                       use_container_width=True)
            else:
                st.warning("⚠️ Image ECG non trouvée")
        else:
            st.info("📄 Cas ECG (format non-image)")
    
    with col2:
        st.markdown("**📋 Informations cliniques**")
        
        # Afficher les informations disponibles
        if case_data.get('age'):
            st.write(f"**Âge :** {case_data['age']} ans")
        if case_data.get('sexe'):
            st.write(f"**Sexe :** {case_data['sexe']}")
        if case_data.get('context'):
            st.write(f"**Contexte :** {case_data['context']}")
        
        # Indications supplémentaires
        st.markdown("---")
        st.markdown("**🎯 Instructions**")
        st.info("""
        Analysez cet ECG et proposez votre interprétation en utilisant les concepts médicaux appropriés.
        
        Points à considérer :
        - Rythme cardiaque
        - Morphologie des ondes
        - Intervalles et segments
        - Anomalies visibles
        """)

def save_exercise_response(session, case_name, annotations, comments):
    """Sauvegarde la réponse d'un exercice"""
    
    response = {
        'case_name': case_name,
        'annotations': annotations,
        'comments': comments,
        'timestamp': datetime.now().isoformat(),
        'session_type': 'individual' if session.get('individual_mode') else 'session'
    }
    
    # Ajouter à la session en cours
    if 'responses' not in session:
        session['responses'] = {}
    
    session['responses'][case_name] = response

def display_exercise_feedback(case_data, student_annotations):
    """Affiche le feedback d'un exercice"""
    
    st.markdown("### 💡 Feedback de l'exercice")
    
    # Charger les annotations expertes
    case_folder = Path("data/ecg_cases") / case_data['case_id']
    annotations_file = case_folder / "annotations.json"
    
    if annotations_file.exists():
        try:
            with open(annotations_file, 'r', encoding='utf-8') as f:
                expert_annotations = json.load(f)
            
            # Analyser et comparer
            if expert_annotations:
                st.success("✅ Annotations expertes disponibles")
                
                # Afficher les annotations expertes
                st.markdown("**🧠 Interprétation experte :**")
                for ann in expert_annotations[:3]:  # Limiter l'affichage
                    if ann.get('annotation_tags'):
                        for tag in ann['annotation_tags']:
                            st.markdown(f"- 🏷️ {tag}")
                    elif ann.get('interpretation_experte'):
                        st.info(ann['interpretation_experte'])
                
                # Comparaison simple
                if student_annotations:
                    st.markdown("**📊 Votre performance :**")
                    
                    # Calculer un score simple
                    expert_concepts = set()
                    for ann in expert_annotations:
                        if ann.get('annotation_tags'):
                            expert_concepts.update(ann['annotation_tags'])
                    
                    student_concepts = set(student_annotations)
                    
                    if expert_concepts:
                        overlap = expert_concepts.intersection(student_concepts)
                        score = len(overlap) / len(expert_concepts) * 100
                        
                        if score >= 70:
                            st.success(f"🏆 Excellent ! Score : {score:.0f}%")
                        elif score >= 50:
                            st.warning(f"👍 Bien ! Score : {score:.0f}%")
                        else:
                            st.error(f"📚 À améliorer. Score : {score:.0f}%")
                        
                        # Concepts manqués
                        missed = expert_concepts - student_concepts
                        if missed:
                            st.markdown("**💡 Concepts importants à considérer :**")
                            for concept in missed:
                                st.markdown(f"- 🔍 {concept}")
                    else:
                        st.info("✅ Votre interprétation a été enregistrée")
                else:
                    st.info("💭 Ajoutez des annotations pour voir la comparaison")
            else:
                st.info("💭 Pas d'annotation experte disponible pour ce cas")
                
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du feedback : {e}")
    else:
        st.info("💭 Feedback non disponible pour ce cas")

def display_session_results(session):
    """Affiche les résultats d'une session terminée"""
    
    st.markdown("## 🎉 Session terminée !")
    
    session_data = session['session_data']
    responses = session.get('responses', {})
    is_individual = session.get('individual_mode', False)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Cas traités", len(responses))
    
    with col2:
        total_time = "Non calculé"  # À implémenter si besoin
        st.metric("⏱️ Temps total", total_time)
    
    with col3:
        if is_individual:
            st.metric("🎯 Mode", "Exercice individuel")
        else:
            st.metric("🎯 Session", session_data['name'])
    
    st.markdown("---")
    
    # Affichage des réponses
    if responses:
        st.markdown("### 📝 Vos réponses")
        
        for case_name, response in responses.items():
            with st.expander(f"📋 {case_name}"):
                st.markdown(f"**🏷️ Annotations :** {', '.join(response.get('annotations', []))}")
                if response.get('comments'):
                    st.markdown(f"**💬 Commentaires :** {response['comments']}")
                st.caption(f"⏰ {response.get('timestamp', '')}")
    
    # Boutons d'action
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Nouvelle session", type="primary"):
            del st.session_state['current_session']
            st.rerun()
    
    with col2:
        if st.button("📚 Retour aux cas", type="secondary"):
            del st.session_state['current_session']
            st.session_state.selected_page = "cases"
            st.rerun()
        finish_ecg_session()
        return
    
    # Cas actuel
    current_case_name = session['cases'][current_index]
    case_data = load_case_data(current_case_name)
    
    if case_data:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"### 📋 {current_case_name}")
            
            # Affichage de tous les ECG du cas
            if 'image_paths' in case_data and case_data['image_paths']:
                total_images = len(case_data['image_paths'])
                
                if total_images > 1:
                    st.info(f"📊 Ce cas contient **{total_images} ECG** à analyser")
                    
                    # Navigation entre les ECG si plusieurs
                    ecg_index = st.selectbox(
                        "Sélectionner l'ECG à visualiser :",
                        range(total_images),
                        format_func=lambda i: f"ECG {i+1}/{total_images}",
                        key=f"ecg_selector_{current_case_name}_{current_index}"
                    )
                else:
                    ecg_index = 0
                
                # Affichage de l'ECG sélectionné
                image_path = Path(case_data['image_paths'][ecg_index])
                if image_path.exists():
                    st.image(str(image_path), 
                           caption=f"ECG {ecg_index+1}/{total_images} à analyser",
                           use_container_width=True)
                else:
                    st.error(f"❌ ECG {ecg_index+1} non trouvé")
                    
            elif 'image_path' in case_data:
                # Compatibilité avec l'ancien format (une seule image)
                image_path = Path(case_data['image_path'])
                if image_path.exists():
                    st.image(str(image_path), 
                           caption=f"ECG à analyser",
                           use_container_width=True)
            else:
                st.warning("⚠️ Aucun ECG trouvé pour ce cas")
            
            # Informations contextuelles
            if case_data.get('context'):
                st.info(f"**📋 Contexte :** {case_data['context']}")
        
        with col2:
            st.markdown("### ✍️ Votre interprétation")
            
            # Interface de saisie semi-automatique pour les étudiants
            student_annotations = smart_annotation_input(
                key_prefix=f"student_{current_case_name}_{current_index}", 
                max_tags=10
            )
            
            # Zone de saisie textuelle complémentaire
            st.markdown("### 📝 Observations complémentaires")
            user_response = st.text_area(
                "Description détaillée (optionnel) :",
                placeholder="Ajoutez vos observations textuelles...",
                height=100,
                key=f"response_{current_case_name}_{current_index}"
            )
            
            # Aperçu des annotations sélectionnées
            if student_annotations:
                display_annotation_summary(student_annotations, "📋 Vos annotations")
            
            col_validate, col_next = st.columns(2)
            
            with col_validate:
                if st.button("✅ Valider", type="primary"):
                    if student_annotations or user_response.strip():
                        # Enregistrer la réponse (annotations + texte)
                        response_data = {
                            'annotations': student_annotations,
                            'text_response': user_response.strip(),
                            'combined_response': student_annotations + [user_response.strip()] if user_response.strip() else student_annotations
                        }
                        session['responses'][current_case_name] = response_data
                        
                        # Feedback immédiat si activé
                        if session_data.get('show_feedback', True):
                            show_case_feedback(case_data, response_data)
                        
                        st.success("✅ Réponse enregistrée !")
                    else:
                        st.warning("⚠️ Veuillez saisir au moins une annotation ou observation")
            
            with col_next:
                if current_case_name in session.get('responses', {}):
                    if st.button("➡️ Cas suivant"):
                        session['current_case_index'] += 1
                        st.session_state['current_session'] = session
                        st.rerun()
    else:
        st.error(f"❌ Cas '{current_case_name}' non trouvé")
        if st.button("⏭️ Passer au suivant"):
            session['current_case_index'] += 1
            st.session_state['current_session'] = session
            st.rerun()

def load_case_data(case_name):
    """Charge les données d'un cas ECG"""
    
    case_dir = Path(__file__).parent.parent / "data" / "ecg_cases" / case_name
    metadata_file = case_dir / "metadata.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            
            # Ajouter tous les chemins d'images
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                image_files.extend(case_dir.glob(ext))
            
            if image_files:
                # Trier les images par nom pour un ordre cohérent
                sorted_images = sorted(image_files, key=lambda x: x.name)
                case_data['image_paths'] = [str(img) for img in sorted_images]
                # Garder l'ancienne clé pour la compatibilité
                case_data['image_path'] = str(sorted_images[0])
                case_data['total_images'] = len(sorted_images)
            
            return case_data
            
        except Exception as e:
            return None
    
    return None

def show_case_feedback(case_data, response_data):
    """Affiche le feedback pour un cas avec annotations semi-automatiques"""
    
    st.markdown("---")
    st.markdown("### 💡 Feedback")
    
    # Extraire les annotations de l'étudiant
    if isinstance(response_data, dict):
        student_annotations = response_data.get('annotations', [])
        student_text = response_data.get('text_response', '')
    else:
        # Compatibilité avec l'ancien format (string simple)
        student_annotations = []
        student_text = str(response_data)
    
    # Annotations expertes si disponibles
    expert_annotations = []
    case_annotations = case_data.get('annotations', [])
    
    # Extraire les annotations expertes selon différents formats
    for ann in case_annotations:
        if ann.get('type') == 'expert' or ann.get('annotation_type') == 'expert':
            if ann.get('expert_annotations'):
                expert_annotations.extend(ann['expert_annotations'])
            elif ann.get('concept'):
                expert_annotations.append(ann['concept'])
    
    if expert_annotations and student_annotations:
        # Comparaison intelligente avec l'ontologie
        try:
            from annotation_components import get_ontology_concepts
            concepts = get_ontology_concepts()
            
            # Analyser les correspondances
            matches = []
            missed = []
            
            for expert_ann in expert_annotations[:5]:  # Limiter à 5 annotations expertes
                found_match = False
                for student_ann in student_annotations:
                    if (expert_ann.lower() in student_ann.lower() or 
                        student_ann.lower() in expert_ann.lower() or
                        expert_ann.lower() == student_ann.lower()):
                        matches.append((expert_ann, student_ann))
                        found_match = True
                        break
                
                if not found_match:
                    missed.append(expert_ann)
            
            # Affichage des résultats
            if matches:
                st.success("🎯 **Bonnes observations :**")
                for expert, student in matches:
                    st.write(f"✅ {student} ↔ {expert}")
            
            if missed:
                st.info("💡 **Points à retenir :**")
                for miss in missed:
                    st.write(f"• {miss}")
            
            # Suggestions d'amélioration
            if len(missed) > len(matches):
                st.warning("📚 Pensez à utiliser l'ontologie médicale pour affiner vos observations")
        
        except ImportError:
            # Fallback simple
            st.info("📚 **Points clés à retenir :**")
            for ann in expert_annotations[:3]:
                st.write(f"• {ann}")
    
    elif expert_annotations:
        st.info("📚 **Points clés à retenir :**")
        for ann in expert_annotations[:3]:
            st.write(f"• {ann}")
    else:
        st.info("📚 Corrections détaillées disponibles avec votre enseignant")

def finish_ecg_session():
    """Termine une session ECG et affiche les résultats"""
    
    session = st.session_state['current_session']
    session_data = session['session_data']
    responses = session.get('responses', {})
    
    st.markdown("## 🎉 Session terminée !")
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Cas traités", len(responses))
    
    with col2:
        completion = len(responses) / len(session['cases'])
        st.metric("📈 Completion", f"{completion*100:.0f}%")
    
    with col3:
        # Calculer le temps écoulé
        start_time = datetime.fromisoformat(session['start_time'])
        duration = datetime.now() - start_time
        st.metric("⏱️ Durée", f"{duration.seconds//60} min")
    
    # Résumé des réponses
    st.markdown("### 📝 Vos réponses")
    
    for case_name, response in responses.items():
        with st.expander(f"📋 {case_name}"):
            if isinstance(response, dict):
                # Nouvelle format avec annotations semi-automatiques
                if response.get('annotations'):
                    st.markdown("**🏷️ Annotations sélectionnées :**")
                    for ann in response['annotations']:
                        st.write(f"• {ann}")
                
                if response.get('text_response'):
                    st.markdown("**📝 Observations textuelles :**")
                    st.write(response['text_response'])
            else:
                # Ancien format (texte simple)
                st.write(response)
    
    # Boutons d'action
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refaire la session", type="primary"):
            if session_data.get('allow_retry', True):
                # Redémarrer la session
                session_instance = {
                    'session_data': session_data,
                    'cases': session_data['cases'],
                    'current_case_index': 0,
                    'responses': {},
                    'start_time': datetime.now().isoformat(),
                    'scores': {},
                    'individual_mode': False
                }
                st.session_state['current_session'] = session_instance
                st.rerun()
            else:
                st.warning("⚠️ Les reprises ne sont pas autorisées pour cette session")
    
    with col2:
        if st.button("📚 Retour aux sessions"):
            del st.session_state['current_session']
            st.rerun()

def get_session_progress(session_name):
    """Récupère les progrès d'un étudiant sur une session"""
    # TODO: Implémenter la persistance des progrès
    return None

if __name__ == "__main__":
    main()
