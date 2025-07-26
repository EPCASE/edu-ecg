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

@require_auth
def main_app():
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
        user_role = st.session_state.user_info['role']
        
        # Pages communes à tous
        if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'home'
            st.rerun()
        
        # Menu selon les permissions
        if user_role in ['Admin', 'Expert']:
            st.markdown("### 📋 Gestion de Contenu")
            if st.button("📥 Import ECG", type="primary" if st.session_state.selected_page == 'import' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'import'
                st.rerun()
            
            if st.button("📖 Liseuse ECG", type="primary" if st.session_state.selected_page == 'reader' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'reader'
                st.rerun()
        
        # Menu pour tous les utilisateurs
        st.markdown("### 📚 Formation")
        if st.button("📋 Cas ECG", type="primary" if st.session_state.selected_page == 'cases' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'cases'
            st.rerun()
        
        if st.button("🎯 Exercices", type="primary" if st.session_state.selected_page == 'exercises' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'exercises'
            st.rerun()
        
        if st.button("� Mes Sessions", type="primary" if st.session_state.selected_page == 'sessions' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'sessions'
            st.rerun()
        
        # Menu Admin uniquement
        if user_role == 'Admin':
            st.markdown("### ⚙️ Administration")
            if st.button("🗄️ Base de Données", type="primary" if st.session_state.selected_page == 'database' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'database'
                st.rerun()
            
            if st.button("👥 Utilisateurs", type="primary" if st.session_state.selected_page == 'users' else "secondary", use_container_width=True):
                st.session_state.selected_page = 'users'
                st.rerun()
    
    # Routage des pages selon les permissions
    route_pages(st.session_state.selected_page)

def route_pages(page):
    """Routage des pages selon les permissions utilisateur"""
    
    if page == 'home':
        display_home_page()
    
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
    
    elif page == 'sessions':
        page_student_progress()
    
    elif page == 'database':
        if check_permission('all'):
            page_database_management()
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'users':
        if check_permission('all'):
            page_users_management()
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'analytics':
        if check_permission('all'):
            page_analytics()
        else:
            st.error("❌ Accès non autorisé")
    
    elif page == 'configuration':
        if check_permission('all'):
            page_configuration()
        else:
            st.error("❌ Accès non autorisé")
    
    else:
        display_home_page()

def display_home_page():
    """Page d'accueil adaptée selon le rôle utilisateur"""
    user_role = st.session_state.user_info['role']
    
    if user_role == 'Étudiant':
        page_student_home()
    elif user_role in ['Expert', 'Admin']:
        page_admin_home()
    else:
        # Page d'accueil générique
        st.markdown("## 🫀 Bienvenue sur Edu-CG")
        st.markdown("Plateforme d'apprentissage de l'électrocardiogramme")

def count_total_cases():
    """Compte le nombre total de cas ECG"""
    try:
        cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
        if cases_dir.exists():
            return len([d for d in cases_dir.iterdir() if d.is_dir()])
        return 0
    except:
        return 0

def count_annotated_cases():
    """Compte le nombre de cas annotés"""
    try:
        cases_dir = Path(__file__).parent.parent / "data" / "ecg_cases"
        annotated = 0
        if cases_dir.exists():
            for case_dir in cases_dir.iterdir():
                if case_dir.is_dir():
                    metadata_file = case_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            if data.get('annotations'):
                                annotated += 1
                        except:
                            continue
        return annotated
    except:
        return 0

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
    
    # Actions principales
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
    st.markdown("## � Formation à l'ECG")
    
    st.markdown("""
    Bienvenue dans **Edu-CG**, votre plateforme d'apprentissage de l'électrocardiogramme !
    
    **Votre parcours d'apprentissage :**
    - 📚 **Consultez les cas ECG** pour découvrir différentes pathologies
    - 🎯 **Pratiquez avec les exercices** d'annotation interactive
    - 📈 **Suivez vos progrès** avec des analytics détaillés
    - 🧠 **Bénéficiez de corrections intelligentes** basées sur l'ontologie médicale
    """)
    
    st.markdown("---")
    
    # Actions principales
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
            st.session_state.selected_page = "sessions"
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

def display_student_quick_stats():
    """Statistiques rapides pour étudiants"""
    st.markdown("#### 📊 Vos Statistiques Rapides")
    
    # Mock data - à remplacer par de vraies données
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cas Consultés", "12", "2")
    with col2:
        st.metric("Score Moyen", "78%", "5%")
    with col3:
        st.metric("Sessions", "24", "3")

def display_expert_quick_stats():
    """Statistiques rapides pour experts"""
    st.markdown("#### 📊 Vos Statistiques Rapides")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cas Créés", "8", "1")
    with col2:
        st.metric("Sessions Actives", "15", "2")
    with col3:
        st.metric("Étudiants", "42", "4")
    with col4:
        st.metric("Annotations", "156", "12")

def display_admin_dashboard():
    """Dashboard administrateur complet"""
    st.markdown("#### 📊 Vue d'Ensemble du Système")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Utilisateurs", "127", "8")
    with col2:
        st.metric("Cas ECG", "45", "3")
    with col3:
        st.metric("Sessions Actives", "89", "12")
    with col4:
        st.metric("Annotations", "1,234", "67")
    with col5:
        st.metric("Taux Activité", "92%", "3%")

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

def page_sessions():
    st.markdown("## 📝 Sessions")
    st.info("Gestion des sessions d'apprentissage")

def page_mes_sessions():
    st.markdown("## 📝 Mes Sessions")
    st.info("Historique de vos sessions personnelles")

def page_mes_statistiques():
    st.markdown("## 📊 Mes Statistiques")
    st.info("Suivi de votre progression personnelle")

def page_database_management():
    st.markdown("## 🗄️ Base de Données")
    st.info("Gestion avancée de la base de données")

def page_users_management():
    st.markdown("## 👥 Gestion des Utilisateurs")
    
    tab1, tab2 = st.tabs(["👤 Liste des Utilisateurs", "➕ Créer Utilisateur"])
    
    with tab1:
        list_users_interface()
    
    with tab2:
        create_user_interface()

def page_analytics():
    st.markdown("## 📊 Analytics")
    st.info("Analyses avancées du système")

def page_configuration():
    st.markdown("## ⚙️ Configuration")
    st.info("Configuration du système")

def main():
    """Point d'entrée principal de l'application"""
    
    # Initialiser le système d'authentification
    init_auth_system()
    
    # Vérifier si l'utilisateur est connecté
    if not st.session_state.authenticated:
        login_interface()
    else:
        main_app()

if __name__ == "__main__":
    main()
