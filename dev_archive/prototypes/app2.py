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

# Fonction de fallback pour create_advanced_ecg_viewer
def create_advanced_ecg_viewer_fallback(image_path, title):
    """Fallback simple pour l'affichage ECG"""
    return f"""
    <div style="text-align: center;">
        <h3>{title}</h3>
        <p>Visualiseur ECG avancé non disponible</p>
    </div>
    """

# Fonctions de fallback pour les annotations
def smart_annotation_input_fallback(key_prefix, max_tags=10):
    """Fallback pour l'interface d'annotation"""
    import streamlit as st
    
    # Interface simple sans autocomplétion
    if f'{key_prefix}_tags' not in st.session_state:
        st.session_state[f'{key_prefix}_tags'] = []
    
    # Zone de texte pour ajouter des tags
    new_tag = st.text_input("Ajouter une annotation:", key=f"{key_prefix}_input")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Ajouter", key=f"{key_prefix}_add"):
            if new_tag and new_tag not in st.session_state[f'{key_prefix}_tags']:
                if len(st.session_state[f'{key_prefix}_tags']) < max_tags:
                    st.session_state[f'{key_prefix}_tags'].append(new_tag)
                    st.rerun()
    
    # Afficher les tags existants
    if st.session_state[f'{key_prefix}_tags']:
        st.write("**Annotations actuelles:**")
        for i, tag in enumerate(st.session_state[f'{key_prefix}_tags']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {tag}")
            with col2:
                if st.button("❌", key=f"{key_prefix}_remove_{i}"):
                    st.session_state[f'{key_prefix}_tags'].pop(i)
                    st.rerun()
    
    return st.session_state[f'{key_prefix}_tags']

def display_annotation_summary_fallback(annotations, title="Résumé"):
    """Fallback pour l'affichage du résumé des annotations"""
    import streamlit as st
    
    if annotations:
        st.markdown(f"**{title}**")
        for ann in annotations:
            st.write(f"• {ann}")

# Variable globale qui sera mise à jour si le module est disponible
create_advanced_ecg_viewer = create_advanced_ecg_viewer_fallback
smart_annotation_input = smart_annotation_input_fallback
display_annotation_summary = display_annotation_summary_fallback

# Correction du chemin pour que data/ecg_cases soit à la racine du projet (et non dans frontend/)
# Définir le dossier data à la racine du projet
DATA_ROOT = Path(__file__).parent.parent / "data"
ECG_CASES_DIR = DATA_ROOT / "ecg_cases"
ECG_SESSIONS_DIR = DATA_ROOT / "ecg_sessions"

def load_ontology():
    """Chargement de l'ontologie ECG"""
    ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
    if 'corrector' not in st.session_state:
        try:
            from correction_engine import OntologyCorrector
            ontology_path = DATA_ROOT / "ontologie.owx"
            st.session_state.corrector = OntologyCorrector(str(ontology_path))
            st.session_state.concepts = list(st.session_state.corrector.concepts.keys())
            return True
        except ImportError as e:
            st.warning(f"⚠️ Module owlready2 non installé. Fonctionnalités d'ontologie désactivées.")
            st.session_state.concepts = []
            return False
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement de l'ontologie : {e}")
            return False
    return True

def count_ecg_sessions():
    """Compte le nombre de sessions ECG existantes"""
    sessions_dir = ECG_SESSIONS_DIR
    if not sessions_dir.exists():
        return 0
    
    return len([f for f in sessions_dir.iterdir() if f.suffix == '.json'])

def count_total_cases():
    """Compte le nombre total de cas ECG dans la base"""
    if not ECG_CASES_DIR.exists():
        return 0
    
    return len([d for d in ECG_CASES_DIR.iterdir() if d.is_dir()])

def count_annotated_cases():
    """Compte le nombre de cas ECG ayant des annotations expertes"""
    if not ECG_CASES_DIR.exists():
        return 0
    
    annotated = 0
    for case_dir in ECG_CASES_DIR.iterdir():
        if case_dir.is_dir():
            annotations_file = case_dir / "annotations.json"
            metadata_file = case_dir / "metadata.json"
            
            # Vérifier s'il y a des annotations dans le fichier annotations.json
            has_annotations = False
            if annotations_file.exists():
                try:
                    with open(annotations_file, 'r', encoding='utf-8') as f:
                        anns = json.load(f)
                        if anns and len(anns) > 0:
                            has_annotations = True
                except:
                    pass
            
            # Sinon vérifier dans metadata.json
            if not has_annotations and metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        anns = metadata.get('annotations', [])
                        if anns and len(anns) > 0:
                            has_annotations = True
                except:
                    pass
            
            if has_annotations:
                annotated += 1
    
    return annotated

def load_ontology():
    """Chargement de l'ontologie ECG"""
    ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
    if 'corrector' not in st.session_state:
        try:
            from correction_engine import OntologyCorrector
            ontology_path = DATA_ROOT / "ontologie.owx"
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
    else:
        # Application principale après authentification
        main_app_with_auth()

def main_app_with_auth():
    """Application principale après authentification"""

    # Définir ONTOLOGY_LOADED comme variable globale pour qu'elle soit accessible partout
    global ONTOLOGY_LOADED, ECG_READER_AVAILABLE, USER_MANAGEMENT_AVAILABLE
    global smart_annotation_input, display_annotation_summary, create_advanced_ecg_viewer
    global ecg_reader_interface, user_management_interface
    global admin_import_cases, admin_annotation_tool
    
    # Importer les modules critiques ici pour éviter de bloquer l'auth
    try:
        from correction_engine import OntologyCorrector
        from import_cases import admin_import_cases
        from annotation_tool import admin_annotation_tool
        ONTOLOGY_LOADED = True
    except ImportError as e:
        ONTOLOGY_LOADED = False
        st.warning(f"⚠️ Certains modules ne sont pas disponibles : {e}")
    
    # Essayer d'importer les composants d'annotation
    try:
        from annotation_components import smart_annotation_input as _smart_annotation_input
        from annotation_components import display_annotation_summary as _display_annotation_summary
        smart_annotation_input = _smart_annotation_input
        display_annotation_summary = _display_annotation_summary
    except ImportError:
        # Garder les fonctions de fallback
        st.info("💡 Module d'annotation avancé non disponible, utilisation de l'interface simplifiée")
    
    # Correction: importer create_advanced_ecg_viewer depuis le bon module
    try:
        from advanced_ecg_viewer import create_advanced_ecg_viewer as _create_advanced_ecg_viewer
        create_advanced_ecg_viewer = _create_advanced_ecg_viewer
    except ImportError:
        # Garder le fallback défini plus haut
        pass
    
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
        
        # Menu selon les permissions
        if user_role in ['admin', 'expert']:  # Utiliser les vrais noms de rôles
            st.markdown("### 📋 Gestion de Contenu")
            if st.button("📥 Import ECG", type="primary" if st.session_state.selected_page == 'import' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'import'
            
            
            # Menu Sessions pour experts et admins
            if check_permission('create_sessions') or check_permission('all'):
                if st.button("📚 Sessions ECG", type="primary" if st.session_state.selected_page == 'sessions' else "secondary", use_container_width=True):
                    st.session_state.selected_page = 'sessions'
        
        # Menu pour tous les utilisateurs
        st.markdown("### 📚 Formation")
        if st.button("📋 Cas ECG", type="primary" if st.session_state.selected_page == 'cases' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'cases'
        
        if st.button("🎯 Exercices", type="primary" if st.session_state.selected_page == 'exercises' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'exercises'
        
        if st.button("📊 Mes Sessions", type="primary" if st.session_state.selected_page == 'progress' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'progress'
        
        # Menu Admin uniquement
        if user_role == 'admin':  # Utiliser le vrai nom de rôle
            st.markdown("### ⚙️ Administration")
            if st.button("🗄️ Base de Données", type="primary" if st.session_state.selected_page == 'database' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'database'
            
            if st.button("👥 Utilisateurs", type="primary" if st.session_state.selected_page == 'users' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'users'
    
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
            
            # Boutons sidebar admin - SANS st.rerun() pour éviter double chargement
            if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True, key="admin_home_btn"):
                st.session_state.selected_page = 'home'
            
            if st.button("📥 Import ECG", type="primary" if st.session_state.selected_page == 'import' else "secondary", use_container_width=True, key="admin_import_btn"):
                st.session_state.selected_page = 'import'
            
            
            if st.button("👥 Utilisateurs", type="primary" if st.session_state.selected_page == 'users' else "secondary", use_container_width=True, key="admin_users_btn"):
                st.session_state.selected_page = 'users'
            
            if st.button("📊 Base de Données", type="primary" if st.session_state.selected_page == 'database' else "secondary", use_container_width=True, key="admin_database_btn"):
                st.session_state.selected_page = 'database'
            
        else:
            st.markdown("### 🎓 Menu Étudiant")
            
            # Boutons sidebar étudiant - SANS st.rerun() pour éviter double chargement
            if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True, key="student_home_btn"):
                st.session_state.selected_page = 'home'
            
            if st.button("📚 Cas ECG", type="primary" if st.session_state.selected_page == 'cases' else "secondary", use_container_width=True, key="student_cases_btn"):
                st.session_state.selected_page = 'cases'
            
            if st.button("🎯 Exercices", type="primary" if st.session_state.selected_page == 'exercises' else "secondary", use_container_width=True, key="student_exercises_btn"):
                st.session_state.selected_page = 'exercises'
            
            if st.button("📈 Mes Progrès", type="primary" if st.session_state.selected_page == 'progress' else "secondary", use_container_width=True, key="student_progress_btn"):
                st.session_state.selected_page = 'progress'
        
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
            from liseuse.liseuse_ecg_fonctionnelle import liseuse_ecg_fonctionnelle
            liseuse_ecg_fonctionnelle()
        except ImportError:
            try:
                from liseuse.liseuse_ecg_simple import liseuse_ecg_simple
                st.info("🔄 Liseuse standard (visualiseur avancé non disponible)")
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
        # Option pour choisir l'interface d'import
        st.subheader("🎯 Import Intelligent ECG")
        
        import_method = st.selectbox(
            "🎨 Choisir l'interface d'import",
            [
                "🚀 Import Amélioré (ep-cases style)",
                "📤 Import Standard", 
                "🔧 Import Classique"
            ],
            help="Interface d'import inspirée d'ep-cases avec drag-and-drop et validation intelligente"
        )
        
        if import_method == "🚀 Import Amélioré (ep-cases style)":
            try:
                from enhanced_import import enhanced_import_interface
                enhanced_import_interface()
            except ImportError as e:
                st.error(f"⚠️ Interface améliorée non disponible : {e}")
                st.info("🔄 Utilisation de l'interface standard...")
                # Fallback vers interface standard
                try:
                    from admin.smart_ecg_importer_simple import smart_ecg_importer_simple
                    smart_ecg_importer_simple()
                except ImportError:
                    from admin.smart_ecg_importer import smart_ecg_importer
                    smart_ecg_importer()
        elif import_method == "📤 Import Standard":
            try:
                from admin.smart_ecg_importer_simple import smart_ecg_importer_simple
                smart_ecg_importer_simple()
            except ImportError as e:
                # Fallback vers version avec onglets
                try:
                    from admin.smart_ecg_importer import smart_ecg_importer
                    smart_ecg_importer()
                except ImportError as e:
                    st.error(f"❌ Erreur d'import du module : {e}")
                    st.info("🔧 Utilisation de l'import simple en fallback")
                    admin_import_cases()
        else:  # Import Classique
            admin_import_cases()
    elif page == "📺 Liseuse ECG":
        try:
            from liseuse.liseuse_ecg_fonctionnelle import liseuse_ecg_fonctionnelle
            liseuse_ecg_fonctionnelle()
        except ImportError:
            try:
                from liseuse.liseuse_ecg_simple import liseuse_ecg_simple
                st.info("🔄 Liseuse standard (visualiseur avancé non disponible)")
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
    
    with col2:
        if st.button("📺 Liseuse ECG", use_container_width=True):
            st.session_state.selected_page = "reader"

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
    
    with col2:
        if st.button("🎯 Exercices", use_container_width=True):
            st.session_state.selected_page = "exercises"
    
    with col3:
        if st.button("📈 Mes progrès", use_container_width=True):
            st.session_state.selected_page = "progress"
    
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
    ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
    available_cases = []
    if ECG_CASES_DIR.exists():
        for case_dir in ECG_CASES_DIR.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(case_dir.glob(ext))
                if metadata_file.exists() and image_files:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        sorted_images = sorted(image_files, key=lambda x: x.name)
                        case_data['image_paths'] = [str(img) for img in sorted_images]
                        case_data['image_path'] = str(sorted_images[0])
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
                # --- NOUVEAU LAYOUT ---
                col_ecg, col_annot = st.columns([3, 2])
                with col_ecg:
                    # Affichage ECG(s)
                    if 'image_paths' in case_data and case_data['image_paths']:
                        total_images = len(case_data['image_paths'])
                        if total_images > 1:
                            st.info(f"📊 Ce cas contient **{total_images} ECG**")
                            ecg_preview_index = st.selectbox(
                                "Aperçu ECG :",
                                range(total_images),
                                format_func=lambda i: f"ECG {i+1}/{total_images}",
                                key=f"preview_ecg_{case_id}_{i}"
                            )
                        else:
                            ecg_preview_index = 0
                            st.info(f"📊 Ce cas contient **1 ECG**")
                        image_path = Path(case_data['image_paths'][ecg_preview_index])
                        if image_path.exists():
                            # Utiliser st.image directement - plus simple et plus fiable
                            st.image(str(image_path), 
                                   caption=f"ECG {ecg_preview_index+1}/{total_images} - {case_id}",
                                   use_container_width=True)
                        else:
                            st.warning(f"⚠️ ECG {ecg_preview_index+1} non trouvé")
                    elif 'image_path' in case_data:
                        image_path = Path(case_data['image_path'])
                        if image_path.exists():
                            # Utiliser st.image directement
                            st.image(str(image_path), 
                                   caption=f"ECG - {case_id}",
                                   use_container_width=True)
                        else:
                            st.warning("⚠️ Image ECG non trouvée")
                    else:
                        st.info("📄 Cas ECG (format non-image)")

                with col_annot:
                    st.markdown("### 📝 Vos annotations")
                    # --- Interface d'annotation avec autocomplétion ---
                    key_prefix = f"student_{case_id}_annotations"
                    # Charger/sauver les annotations de l'étudiant (session + fichier)
                    if 'student_annotations' not in st.session_state:
                        st.session_state['student_annotations'] = {}
                    # Charger depuis fichier si dispo
                    student_file = Path(case_data['case_folder']) / "student_annotations.json"
                    if key_prefix not in st.session_state['student_annotations']:
                        if student_file.exists():
                            try:
                                with open(student_file, 'r', encoding='utf-8') as f:
                                    st.session_state['student_annotations'][key_prefix] = json.load(f)
                            except Exception:
                                st.session_state['student_annotations'][key_prefix] = []
                        else:
                            st.session_state['student_annotations'][key_prefix] = []
                    # Interface
                    annotations = smart_annotation_input(
                        key_prefix=key_prefix,
                        max_tags=15
                    )
                    # Sauvegarde bouton
                    if st.button("💾 Sauvegarder mes annotations", key=f"save_{case_id}"):
                        st.session_state['student_annotations'][key_prefix] = annotations
                        try:
                            # Créer le chemin si case_folder existe, sinon le créer
                            if 'case_folder' in case_data:
                                student_folder = Path(case_data['case_folder'])
                            else:
                                student_folder = ECG_CASES_DIR / str(case_id)
                                student_folder.mkdir(parents=True, exist_ok=True)
                            student_file = student_folder / "student_annotations.json"
                            with open(student_file, 'w', encoding='utf-8') as f:
                                json.dump(annotations, f, ensure_ascii=False, indent=2)
                            st.success("✅ Sauvegardé !")
                        except Exception as e:
                            st.error(f"Erreur : {e}")
                    # Résumé structuré
                    if annotations:
                        display_annotation_summary(annotations, title="📊 Résumé de vos observations")
                    # Option voir la correction
                    show_correction = st.checkbox("Voir la correction experte", key=f"show_corr_{case_id}")
                    if show_correction:
                        # Affichage des annotations expertes
                        expert_annots = []
                        # Recherche dans metadata ou annotations.json
                        expert_file = Path(case_data['case_folder']) / "annotations.json"
                        if expert_file.exists():
                            try:
                                with open(expert_file, 'r', encoding='utf-8') as f:
                                    expert_annots = json.load(f)
                            except Exception:
                                expert_annots = []
                        else:
                            expert_annots = case_data.get('annotations', [])
                        expert_tags = []
                        for ann in expert_annots:
                            if ann.get('type') == 'expert' or ann.get('auteur') == 'expert':
                                if ann.get('annotation_tags'):
                                    expert_tags.extend(ann['annotation_tags'])
                                elif ann.get('concept'):
                                    expert_tags.append(ann['concept'])
                        if expert_tags:
                            st.markdown("**🧠 Concepts experts :**")
                            display_annotation_summary(expert_tags, title="🧠 Concepts experts")
                            # Comparaison simple
                            if annotations:
                                overlap = set(expert_tags).intersection(set(annotations))
                                score = len(overlap) / len(expert_tags) * 100 if expert_tags else 0
                                st.markdown(f"**Votre score de recoupement :** {score:.0f}%")
                                if overlap:
                                    st.success("✅ Points communs : " + ", ".join(overlap))
                                missed = set(expert_tags) - set(annotations)
                                if missed:
                                    st.info("💡 Concepts manqués : " + ", ".join(missed))
                        else:
                            st.info("Aucune annotation experte disponible pour ce cas.")
                    st.markdown("---")
                    # Option secondaire : passer en mode exercice
                    if st.button("🎯 Passer en mode exercice complet", key=f"to_ex_{case_id}"):
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
                            'individual_mode': True
                        }
                        st.session_state['current_session'] = individual_session
                        st.session_state.selected_page = "exercises"
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
        # Exécuter la session directement sans messages parasites
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
                    help="Sélectionnez plusieurs cas pour créer un parcours d'exercices"
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
    ECG_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_file = ECG_SESSIONS_DIR / f"{session_id}.json"
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

def load_case_for_exercise(case_name):
    """Charge un cas pour un exercice"""
    case_dir = ECG_CASES_DIR / case_name
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
            case_data['total_images'] = len(sorted_images)
        
        case_data['case_folder'] = str(case_dir)
        return case_data
    
    except Exception as e:
        st.error(f"Erreur lors du chargement du cas {case_name}: {e}")
        return None

def display_case_for_exercise(case_data):
    """Affiche un cas ECG pendant un exercice"""
    case_id = case_data.get('case_id', 'Cas ECG')
    
    col_ecg, col_annotations = st.columns([3, 2])
    
    with col_ecg:
        # Affichage des ECG
        if 'image_paths' in case_data and case_data['image_paths']:
            total_images = len(case_data['image_paths'])
            
            if total_images > 1:
                ecg_index = st.selectbox(
                    "Sélectionner l'ECG :",
                    range(total_images),
                    format_func=lambda i: f"ECG {i+1}/{total_images}",
                    key=f"exercise_ecg_select_{case_id}"
                )
            else:
                ecg_index = 0
                st.info(f"📊 Ce cas contient **1 ECG**")
            
            # Affichage de l'ECG sélectionné avec le visualiseur avancé
            image_path = Path(case_data['image_paths'][ecg_index])
            if image_path.exists():
                # Utiliser la liseuse avancée si disponible
                try:
                    from advanced_ecg_viewer import create_advanced_ecg_viewer
                    viewer_html = create_advanced_ecg_viewer(
                        image_path=str(image_path),
                        title=f"ECG {ecg_index+1} - {case_id}",
                        container_width=None
                    )
                    st.components.v1.html(
                        viewer_html,
                        height=800,
                        scrolling=False
                    )
                except Exception as e:
                    st.warning(f"Visualiseur avancé indisponible : {e}")
                    st.image(str(image_path), 
                             caption=f"ECG {ecg_index+1} - {case_id}",
                             use_container_width=True)
            else:
                st.warning(f"⚠️ ECG {ecg_index+1} non trouvé")
        
        elif 'image_path' in case_data:
            image_path = Path(case_data['image_path'])
            if image_path.exists():
                try:
                    from advanced_ecg_viewer import create_advanced_ecg_viewer
                    viewer_html = create_advanced_ecg_viewer(
                        image_path=str(image_path),
                        title=f"ECG - {case_id}",
                        container_width=None
                    )
                    st.components.v1.html(
                        viewer_html,
                        height=800,
                        scrolling=False
                    )
                except Exception as e:
                    st.warning(f"Visualiseur avancé indisponible : {e}")
                    st.image(str(image_path), 
                             caption=f"ECG - {case_id}",
                             use_container_width=True)
            else:
                st.warning("⚠️ Image ECG non trouvée")
        else:
            st.info("📄 Cas ECG (format non-image)")

    with col_annotations:
        st.markdown("#### 📝 Vos annotations")
        
        # Initialiser student_annotations si nécessaire
        if 'student_annotations' not in st.session_state:
            st.session_state['student_annotations'] = {}
        
        # Utiliser le nom du cas comme identifiant unique pour la clé
        key_prefix = f"student_{case_data.get('case_id', 'unknown')}_annotations"
        
        # Interface d'annotation avec autocomplétion
        annotations = smart_annotation_input(
            key_prefix=key_prefix,
            max_tags=15
        )
        
        # Bouton de sauvegarde
        if st.button("💾 Sauvegarder", key=f"save_{case_id}", use_container_width=True):
            st.session_state['student_annotations'][key_prefix] = annotations
            try:
                # Créer le chemin si case_folder existe, sinon le créer
                if 'case_folder' in case_data:
                    student_folder = Path(case_data['case_folder'])
                else:
                    student_folder = ECG_CASES_DIR / str(case_id)
                    student_folder.mkdir(parents=True, exist_ok=True)
                
                student_file = student_folder / "student_annotations.json"
                with open(student_file, 'w', encoding='utf-8') as f:
                    json.dump(annotations, f, ensure_ascii=False, indent=2)
                st.success("✅ Sauvegardé !")
            except Exception as e:
                st.error(f"Erreur : {e}")
        
        # Résumé structuré
        if annotations:
            st.markdown("---")
            display_annotation_summary(annotations, title="📊 Résumé")
        
        # Feedback
        st.markdown("---")
        st.markdown("#### 💡 Feedback")
        
        # Option pour voir/masquer le feedback
        show_feedback = st.checkbox("Voir le feedback expert", key=f"feedback_{case_id}")
        
        if show_feedback:
            # Charger les annotations expertes
            try:
                case_folder = ECG_CASES_DIR / case_data.get('case_id', '')
                annotations_file = case_folder / "annotations.json"
                
                if annotations_file.exists():
                    with open(annotations_file, 'r', encoding='utf-8') as f:
                        expert_annotations = json.load(f)
                    
                    if expert_annotations:
                        # Extraire les concepts experts
                        expert_concepts = set()
                        for ann in expert_annotations:
                            if ann.get('annotation_tags'):
                                expert_concepts.update(ann['annotation_tags'])
                        
                        if expert_concepts:
                            st.markdown("**🧠 Concepts experts :**")
                            for concept in list(expert_concepts)[:5]:
                                st.markdown(f"• {concept}")
                            
                            if len(expert_concepts) > 5:
                                st.caption(f"... et {len(expert_concepts) - 5} autres")
                            
                            # Score simple si l'étudiant a annoté
                            if annotations:
                                student_concepts = set(annotations)
                                overlap = expert_concepts.intersection(student_concepts)
                                score = len(overlap) / len(expert_concepts) * 100 if expert_concepts else 0
                                
                                st.markdown("---")
                                if score >= 70:
                                    st.success(f"🏆 Score : {score:.0f}%")
                                elif score >= 50:
                                    st.warning(f"👍 Score : {score:.0f}%")
                                else:
                                    st.error(f"📚 Score : {score:.0f}%")
                                
                                # Concepts manqués
                                missed = expert_concepts - student_concepts
                                if missed and score < 100:
                                    st.caption("💡 À considérer :")
                                    for concept in list(missed)[:3]:
                                        st.caption(f"• {concept}")
                        else:
                            st.info("Pas d'annotation experte")
                else:
                    st.info("Feedback non disponible")
            except Exception as e:
                st.error(f"Erreur : {e}")

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
                    
                    # Navigation entre les ECG si plusieurs
                    ecg_preview_index = st.selectbox(
                        "Aperçu ECG :",
                        range(total_images),
                        format_func=lambda i: f"ECG {i+1}/{total_images}",
                        key=f"admin_preview_ecg_{case_id}"
                    )
                else:
                    ecg_preview_index = 0
                    st.info(f"📊 Ce cas contient **1 ECG**")
                
                # Affichage de l'ECG sélectionné avec le visualiseur avancé
                image_path = Path(case['image_paths'][ecg_preview_index])
                if image_path.exists():
                    st.image(str(image_path), 
                           caption=f"📋 Admin - ECG {ecg_preview_index+1}/{total_images} - {case_id}",
                           use_container_width=True)
                else:
                    st.warning(f"⚠️ ECG {ecg_preview_index+1} non trouvé")
                    
            elif 'image_path' in case:
                # Compatibilité avec l'ancien format
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

    # En-tête minimaliste
    col1, col2 = st.columns([3, 1])
    with col1:
        if is_individual:
            st.markdown(f"## 🎯 {session_data['name']}")
        else:
            st.markdown(f"## 📚 {session_data['name']} - Cas {current_index + 1}/{total_cases}")
    with col2:
        quit_label = "✖ Quitter"
        if st.button(quit_label, type="secondary"):
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

    # Récupérer le cas actuel
    current_case_name = session['cases'][current_index]
    current_case_data = load_case_for_exercise(current_case_name)

    if not current_case_data:
        st.error(f"❌ Cas '{current_case_name}' non trouvé")
        return

    st.markdown("---")
    display_case_for_exercise(current_case_data)

    # Navigation entre les cas
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if current_index > 0:
            if st.button("◀ Cas précédent", use_container_width=True):
                session['current_case_index'] -= 1
                st.rerun()
    with col2:
        st.markdown(f"<center>Cas {current_index + 1} sur {total_cases}</center>", unsafe_allow_html=True)
    with col3:
        key_prefix = f"student_{current_case_data.get('case_id', 'unknown')}_annotations"
        current_annotations = st.session_state.get('student_annotations', {}).get(key_prefix, [])
        if current_annotations:
            if current_index < total_cases - 1:
                if st.button("Cas suivant ▶", type="primary", use_container_width=True):
                    session['responses'][current_case_name] = current_annotations
                    session['current_case_index'] += 1
                    st.rerun()
            else:
                if st.button("✅ Terminer", type="primary", use_container_width=True):
                    session['responses'][current_case_name] = current_annotations
                    session['current_case_index'] += 1
                    st.rerun()
        else:
            st.info("💡 Ajoutez des annotations avant de continuer")

def display_session_results(session):
    """Affiche les résultats d'une session terminée"""
    
    session_data = session['session_data']
    responses = session.get('responses', {})
    scores = session.get('scores', {})
    
    st.markdown("## 🎉 Session terminée !")
    
    # Calculer le temps écoulé
    start_time = datetime.fromisoformat(session['start_time'])
    duration = datetime.now() - start_time
    
    # Statistiques générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Cas complétés", f"{len(responses)}/{len(session['cases'])}")
    
    with col2:
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        st.metric("📊 Score moyen", f"{avg_score:.0f}%")
    
    with col3:
        st.metric("⏱️ Durée", f"{duration.seconds//60} min")
    
    with col4:
        completion_rate = len(responses) / len(session['cases']) * 100
        st.metric("✅ Complétion", f"{completion_rate:.0f}%")
    
    st.markdown("---")
    
    # Détails par cas
    st.markdown("### 📊 Détails par cas")
    
    for case_name in session['cases']:
        if case_name in responses:
            score = scores.get(case_name, 0)
            with st.expander(f"📋 {case_name} - Score: {score:.0f}%"):
                response = responses[case_name]
                
                if isinstance(response, list):  # Annotations
                    st.markdown("**Vos annotations:**")
                    for ann in response:
                        st.write(f"• {ann}")
                else:
                    st.write(response)
    
    # Actions finales
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Télécharger le rapport", type="primary", use_container_width=True):
            st.info("🚧 Fonction en développement")
    
    with col2:
        if st.button("📚 Retour aux sessions", use_container_width=True):
            del st.session_state['current_session']
            st.rerun()

def display_available_sessions():
    """Affiche les sessions ECG disponibles pour les étudiants"""
    
    sessions_dir = ECG_SESSIONS_DIR
    
    if not sessions_dir.exists():
        st.info("📭 Aucune session disponible pour le moment")
        return
    
    sessions = []
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                sessions.append(session_data)
        except Exception:
            continue
    
    if sessions:
        st.success(f"📚 {len(sessions)} session(s) disponible(s)")
        
        for session in sessions:
            with st.expander(f"📖 {session['name']} - {session.get('difficulty', '🟢 Débutant')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Description:** {session.get('description', 'Aucune description')}")
                    st.markdown(f"**Nombre de cas:** {len(session.get('cases', []))}")
                    st.markdown(f"**Durée estimée:** {session.get('time_limit', 30)} minutes")
                    
                    if session.get('created_by'):
                        st.caption(f"Créé par: {session['created_by']}")
                
                with col2:
                    if st.button("▶️ Commencer", key=f"start_{session['session_id']}", type="primary", use_container_width=True):
                        # Initialiser la session d'exercices
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
                        st.rerun()
    else:
        st.info("📭 Aucune session créée par vos enseignants")
        st.markdown("""
        **💡 En attendant, vous pouvez :**
        - Explorer les cas ECG individuellement
        - Vous exercer sur chaque cas séparément
        - Prendre des notes personnelles
        """)

def display_backup_management_tab():
    """Onglet gestion des sauvegardes"""
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

def page_database_management():
    """Page de gestion de la base de données"""
    st.header("🗄️ Gestion de la Base de Données")
    
    # Onglets pour organiser les fonctionnalités
    tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "🔧 Maintenance", "💾 Sauvegardes"])
    
    with tab1:
        display_database_overview()
    
    with tab2:
        display_database_maintenance()
    
    with tab3:
        display_backup_management_tab()

def display_database_overview():
    """Affiche une vue d'ensemble de la base de données"""
    st.markdown("### 📊 Vue d'ensemble de la base")
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cases_count = count_total_cases()
        st.metric("📋 Cas ECG", cases_count)
    
    with col2:
        sessions_count = count_ecg_sessions()
        st.metric("📚 Sessions", sessions_count)
    
    with col3:
        # Compter les annotations
        annotations_count = 0
        if ECG_CASES_DIR.exists():
            for case_dir in ECG_CASES_DIR.iterdir():
                if case_dir.is_dir():
                    ann_file = case_dir / "annotations.json"
                    if ann_file.exists():
                        try:
                            with open(ann_file, 'r', encoding='utf-8') as f:
                                anns = json.load(f)
                                annotations_count += len(anns)
                        except:
                            pass
        st.metric("🏷️ Annotations", annotations_count)
    
    with col4:
        # Taille de la base
        total_size = 0
        if DATA_ROOT.exists():
            for path in DATA_ROOT.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
        size_mb = total_size / (1024 * 1024)
        st.metric("💾 Taille", f"{size_mb:.1f} MB")

def display_database_maintenance():
    """Affiche les outils de maintenance de la base"""
    st.markdown("### 🔧 Maintenance de la base")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🧹 Nettoyage")
        if st.button("🗑️ Nettoyer les fichiers temporaires", use_container_width=True):
            clean_temp_files()
        
        if st.button("🔄 Réparer les métadonnées", use_container_width=True):
            repair_metadata()
    
    with col2:
        st.markdown("#### 📦 Export/Import")
        if st.button("📤 Exporter la base complète", use_container_width=True):
            export_database()
        
        if st.button("📥 Importer une base", use_container_width=True):
            st.info("🚧 Fonction en développement")

def clean_temp_files():
    """Nettoie les fichiers temporaires"""
    try:
        cleaned = 0
        # Nettoyer les fichiers temporaires
        for temp_file in DATA_ROOT.rglob("*.tmp"):
            temp_file.unlink()
            cleaned += 1
        
        for temp_file in DATA_ROOT.rglob("*~"):
            temp_file.unlink()
            cleaned += 1
        
        st.success(f"✅ {cleaned} fichiers temporaires supprimés")
    except Exception as e:
        st.error(f"❌ Erreur lors du nettoyage : {e}")

def repair_metadata():
    """Répare les métadonnées manquantes ou corrompues"""
    try:
        repaired = 0
        if ECG_CASES_DIR.exists():
            for case_dir in ECG_CASES_DIR.iterdir():
                if case_dir.is_dir():
                    metadata_file = case_dir / "metadata.json"
                    
                    # Si le fichier n'existe pas, le créer
                    if not metadata_file.exists():
                        metadata = {
                            "case_id": case_dir.name,
                            "created_date": datetime.now().isoformat(),
                            "annotations": []
                        }
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2, ensure_ascii=False)
                        repaired += 1
                    else:
                        # Vérifier et réparer le contenu
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            # Ajouter les champs manquants
                            updated = False
                            if "case_id" not in metadata:
                                metadata["case_id"] = case_dir.name
                                updated = True
                            
                            if "created_date" not in metadata:
                                metadata["created_date"] = datetime.now().isoformat()
                                updated = True
                            
                            if updated:
                                with open(metadata_file, 'w', encoding='utf-8') as f:
                                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                                repaired += 1
                        
                        except json.JSONDecodeError:
                            # Fichier corrompu, recréer
                            metadata = {
                                "case_id": case_dir.name,
                                "created_date": datetime.now().isoformat(),
                                "annotations": []
                            }
                            with open(metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, indent=2, ensure_ascii=False)
                            repaired += 1
        
        st.success(f"✅ {repaired} métadonnées réparées")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la réparation : {e}")

def export_database():
    """Exporte la base de données complète"""
    try:
        import zipfile
        from io import BytesIO
        
        # Créer un fichier ZIP en mémoire
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Ajouter tous les fichiers de data/
            if DATA_ROOT.exists():
                for file_path in DATA_ROOT.rglob('*'):
                    if file_path.is_file():
                        arcname = str(file_path.relative_to(DATA_ROOT.parent))
                        zip_file.write(file_path, arcname)
        
        # Proposer le téléchargement
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%S')
        
        st.download_button(
            label="💾 Télécharger l'export",
            data=zip_buffer,
            file_name=f"ecg_database_export_{timestamp}.zip",
            mime="application/zip"
        )
        
        st.success("✅ Export prêt au téléchargement")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'export : {e}")

def display_user_sessions():
    """Affiche les sessions créées par l'utilisateur actuel"""
    sessions = get_ecg_sessions()
    
    # Filtrer par créateur si nécessaire
    user_name = st.session_state.user_info.get('name', 'Unknown')
    user_sessions = [s for s in sessions if s.get('created_by') == user_name]
    
    if user_sessions:
        st.info(f"📚 Vous avez créé {len(user_sessions)} session(s)")
        
        for session in user_sessions:
            with st.expander(f"📖 {session['name']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Description:** {session.get('description', 'Aucune')}")
                    st.write(f"**Difficulté:** {session.get('difficulty', 'Non spécifiée')}")
                    st.write(f"**Nombre de cas:** {len(session.get('cases', []))}")
                    st.write(f"**Créée le:** {session.get('created_date', 'Date inconnue')[:10]}")
                
                with col2:
                    if st.button("✏️ Modifier", key=f"edit_{session['session_id']}"):
                        st.session_state['editing_session'] = session
                        st.rerun()
                    
                    if st.button("🗑️ Supprimer", key=f"delete_{session['session_id']}"):
                        if delete_ecg_session(session['name']):
                            st.success("✅ Session supprimée")
                            st.rerun()
    else:
        st.info("📭 Vous n'avez pas encore créé de session")

def display_sessions_statistics():
    """Affiche les statistiques des sessions"""
    sessions = get_ecg_sessions()
    
    if sessions:
        # Statistiques générales
        st.markdown("#### 📊 Statistiques générales")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📚 Total sessions", len(sessions))
        
        with col2:
            # Nombre moyen de cas par session
            avg_cases = sum(len(s.get('cases', [])) for s in sessions) / len(sessions)
            st.metric("📋 Moyenne cas/session", f"{avg_cases:.1f}")
        
        with col3:
            # Répartition par difficulté
            difficulties = {}
            for s in sessions:
                diff = s.get('difficulty', 'Non spécifiée')
                difficulties[diff] = difficulties.get(diff, 0) + 1
            
            st.metric("🎯 Difficulté la plus fréquente", 
                     max(difficulties.items(), key=lambda x: x[1])[0] if difficulties else "N/A")
        
        # Graphiques
        st.markdown("#### 📈 Visualisations")
        
        # Répartition par difficulté
        if difficulties:
            st.bar_chart(difficulties)
    else:
        st.info("📊 Aucune statistique disponible (pas de sessions créées)")

def display_case_edit_form(case):
    """Formulaire d'édition d'un cas ECG"""
    st.markdown("### ✏️ Édition du cas")
    
    with st.form(f"edit_case_{case['name']}"):
        # Champs éditables
        new_name = st.text_input("Nom du cas", value=case.get('case_id', case['name']))
        new_description = st.text_area("Description", value=case.get('description', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            new_age = st.number_input("Âge", value=case.get('age', 0), min_value=0, max_value=120)
        with col2:
            new_sexe = st.selectbox("Sexe", ["M", "F"], index=0 if case.get('sexe', 'M') == 'M' else 1)
        
        # Boutons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.form_submit_button("💾 Sauvegarder", type="primary"):
                # Mettre à jour les métadonnées
                update_case_metadata(case['name'], {
                    'case_id': new_name,
                    'description': new_description,
                    'age': new_age,
                    'sexe': new_sexe
                })
                st.session_state[f"editing_{case['name']}"] = False
                st.success("✅ Cas mis à jour")
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Annuler"):
                st.session_state[f"editing_{case['name']}"] = False
                st.rerun()

def update_case_metadata(case_name, updates):
    """Met à jour les métadonnées d'un cas"""
    try:
        case_dir = ECG_CASES_DIR / case_name
        metadata_file = case_dir / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Mettre à jour
            metadata.update(updates)
            metadata['last_modified'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return True
    except Exception as e:
        st.error(f"❌ Erreur lors de la mise à jour : {e}")
        return False

def count_ecg_sessions():
    """Compte le nombre de sessions ECG existantes"""
    sessions_dir = ECG_SESSIONS_DIR
    if not sessions_dir.exists():
        return 0
    
    return len([f for f in sessions_dir.iterdir() if f.suffix == '.json'])

def count_total_cases():
    """Compte le nombre total de cas ECG dans la base"""
    if not ECG_CASES_DIR.exists():
        return 0
    
    return len([d for d in ECG_CASES_DIR.iterdir() if d.is_dir()])

def count_annotated_cases():
    """Compte le nombre de cas ECG ayant des annotations expertes"""
    if not ECG_CASES_DIR.exists():
        return 0
    
    annotated = 0
    for case_dir in ECG_CASES_DIR.iterdir():
        if case_dir.is_dir():
            annotations_file = case_dir / "annotations.json"
            metadata_file = case_dir / "metadata.json"
            
            # Vérifier s'il y a des annotations dans le fichier annotations.json
            has_annotations = False
            if annotations_file.exists():
                try:
                    with open(annotations_file, 'r', encoding='utf-8') as f:
                        anns = json.load(f)
                        if anns and len(anns) > 0:
                            has_annotations = True
                except:
                    pass
            
            # Sinon vérifier dans metadata.json
            if not has_annotations and metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        anns = metadata.get('annotations', [])
                        if anns and len(anns) > 0:
                            has_annotations = True
                except:
                    pass
            
            if has_annotations:
                annotated += 1
    
    return annotated

def modify_session_form(session_data):
    """Formulaire de modification d'une session"""
    
    st.markdown("---")
    st.markdown(f"#### ✏️ Modification de la session : **{session_data['name']}**")
    
    # Informations actuelles
    with st.expander("📋 Informations actuelles", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nom :** {session_data['name']}")
            st.write(f"**Difficulté :** {session_data.get('difficulty', 'Non spécifiée')}")
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
                'time_limit': new_time_limit,
                'cases': new_selected_cases,
                'randomize_order': new_randomize,
                'show_feedback': new_show_feedback,
                'allow_retry': new_allow_retry,
                'created_date': datetime.now().isoformat(),
                'created_by': 'admin'
            }
            
            if create_ecg_session_from_dict(duplicate_data):
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
                    if delete_ecg_session(session_data['name']) and create_ecg_session_from_dict(updated_data):
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
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Description :** {session.get('description', 'Aucune description')}")
                    st.markdown(f"**Cas inclus :** {len(session['cases'])} ECG")
                    st.markdown(f"**Temps limite :** {session['time_limit']} minutes")
                    
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
                            st.session_state['editing_session'] = session
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ Supprimer", key=f"delete_session_{session['name']}"):
                            if delete_ecg_session(session['name']):
                                st.success("✅ Session supprimée")
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la suppression")
    else:
        st.info("📚 Aucune session créée pour le moment")

def get_ecg_sessions():
    """Récupère la liste des sessions ECG disponibles"""
    
    sessions = []
    sessions_dir = Path("data/ecg_sessions")
    
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

def get_available_ecg_cases():
    """Récupère la liste des cas ECG disponibles avec leurs métadonnées"""
    
    cases = []
    
    if ECG_CASES_DIR.exists():
        for case_dir in ECG_CASES_DIR.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Compter les annotations
                        annotations_file = case_dir / "annotations.json"
                        annotations_count = 0
                        if annotations_file.exists():
                            try:
                                with open(annotations_file, 'r', encoding='utf-8') as f:
                                    annotations = json.load(f)
                                    annotations_count = len(annotations)
                            except:
                                pass
                        
                        cases.append({
                            'name': case_dir.name,
                            'case_id': metadata.get('case_id', case_dir.name),
                            'annotations_count': annotations_count,
                            'metadata': metadata
                        })
                    except Exception:
                        continue
    
    return sorted(cases, key=lambda x: x['name'])

def create_ecg_session_from_dict(session_data):
    """Crée une session ECG à partir d'un dictionnaire"""
    try:
        ECG_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Générer un nom de fichier unique basé sur le nom de la session
        safe_name = "".join(c for c in session_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        # Ajouter un timestamp si le fichier existe déjà
        session_file = ECG_SESSIONS_DIR / f"{safe_name}.json"
        if session_file.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_file = ECG_SESSIONS_DIR / f"{safe_name}_{timestamp}.json"
        
        # Ajouter un ID unique si absent
        if 'session_id' not in session_data:
            session_data['session_id'] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
           

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"Erreur lors de la création de la session : {e}")
        return False

if __name__ == "__main__":
    main()