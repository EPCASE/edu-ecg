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

# Import de la configuration
from config import ECG_CASES_DIR, ECG_SESSIONS_DIR, DATA_ROOT, ONTOLOGY_FILE

# Import du visualiseur ECG avancé
try:
    from advanced_ecg_viewer import create_advanced_ecg_viewer
except ImportError:
    # Fonction de fallback si le module n'est pas disponible
    def create_advanced_ecg_viewer(image_path, title, container_width=None):
        """Fallback simple pour l'affichage ECG"""
        return f"""
        <div style="text-align: center;">
            <h3>{title}</h3>
            <p>Visualiseur ECG avancé non disponible</p>
        </div>
        """

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

# Import de la correction LLM intégrée (NOUVEAU - Party Mode Integration!)
try:
    from pages.correction_llm import page_correction_llm
    CORRECTION_LLM_AVAILABLE = True
except ImportError as e:
    CORRECTION_LLM_AVAILABLE = False
    correction_llm_error = str(e)

# Import du module Import ECG (NOUVEAU - Party Mode Integration!)
try:
    from pages.ecg_import import page_ecg_import
    ECG_IMPORT_AVAILABLE = True
except ImportError as e:
    ECG_IMPORT_AVAILABLE = False
    ecg_import_error = str(e)

# Import du module Edit ECG (NOUVEAU - Standalone Editor!)
try:
    from pages.ecg_edit import page_ecg_edit
    ECG_EDIT_AVAILABLE = True
except ImportError as e:
    ECG_EDIT_AVAILABLE = False
    ecg_edit_error = str(e)

# Import des interfaces de correction LLM (LEGACY - SUPPRIMÉ)
# Ces fonctions sont maintenant dans pages/correction_llm.py et pages/ecg_import.py
LLM_CORRECTION_AVAILABLE = False  # Legacy module désactivé

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
create_advanced_ecg_viewer = create_advanced_ecg_viewer
smart_annotation_input = smart_annotation_input_fallback
display_annotation_summary = display_annotation_summary_fallback

def load_ontology():
    """Chargement de l'ontologie ECG depuis JSON (converti depuis OWL)"""
    ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
    
    if 'ontology_loaded' not in st.session_state:
        try:
            # Charger ontologie depuis JSON (converti depuis OWL avec simple_owl_converter.py)
            ontology_json = DATA_ROOT / "ontology_from_owl.json"
            
            if ontology_json.exists():
                with open(ontology_json, 'r', encoding='utf-8') as f:
                    ontology_data = json.load(f)
                
                # Extraire concepts depuis concept_mappings
                concepts = list(ontology_data.get('concept_mappings', {}).keys())
                st.session_state.concepts = concepts
                st.session_state.ontology_data = ontology_data
                st.session_state.ontology_loaded = True
                return True
            else:
                st.warning(f"⚠️ Fichier ontologie JSON introuvable: {ontology_json}")
                st.info("💡 Générez-le avec: python backend/simple_owl_converter.py")
                st.session_state.concepts = []
                st.session_state.ontology_loaded = False
                return False
                
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement de l'ontologie : {e}")
            st.session_state.concepts = []
            st.session_state.ontology_loaded = False
            return False
    
    return st.session_state.ontology_loaded

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

# FONCTION SUPPRIMÉE - Voir reload_ontology() plus bas qui utilise load_ontology()

def main():
    """Application principale Edu-CG - Mode Admin Direct"""
    
    # Mode admin permanent - pas d'authentification
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
        st.session_state.user_role = 'admin'
        st.session_state.user_info = {
            'username': 'admin',
            'name': 'Administrateur',
            'role': 'admin',
            'permissions': ['all']
        }
    
    # Application principale
    main_app_with_auth()

def main_app_with_auth():
    """Application principale après authentification"""

    # Définir variables globales pour qu'elles soient accessibles partout
    global ONTOLOGY_LOADED, ECG_READER_AVAILABLE, USER_MANAGEMENT_AVAILABLE
    global smart_annotation_input, display_annotation_summary, create_advanced_ecg_viewer
    global ecg_reader_interface, user_management_interface
    
    # Charger ontologie JSON (pas besoin d'import correction_engine)
    ONTOLOGY_LOADED = load_ontology()
    
    # Essayer d'importer les composants d'annotation (optionnels - fallback existe)
    # Ces imports sont en try/except pour graceful degradation
    try:
        from annotation_components import smart_annotation_input as _smart_annotation_input
        from annotation_components import display_annotation_summary as _display_annotation_summary
        smart_annotation_input = _smart_annotation_input
        display_annotation_summary = _display_annotation_summary
    except ImportError:
        # Garder les fonctions de fallback définies plus haut - mode silencieux
        pass
    
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
        st.markdown("**Mode Admin**")
    
    # Navigation selon les permissions utilisateur
    with st.sidebar:
        
        st.markdown("## 🔧 Navigation")
        
        # Initialiser la page sélectionnée
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'home'
        
        # Menu complet en mode admin
        if st.button("🏠 Accueil", type="primary" if st.session_state.selected_page == 'home' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'home'
        
        st.markdown("### 📋 Gestion de Contenu")
        if st.button("📥 Import ECG", type="primary" if st.session_state.selected_page == 'import' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'import'
        
        if st.button("📚 Sessions ECG", type="primary" if st.session_state.selected_page == 'sessions' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'sessions'
        
        st.markdown("### 🎓 Formation")
        if st.button("📋 Cas ECG", type="primary" if st.session_state.selected_page == 'cases' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'cases'
        
        if st.button("🎯 Exercices", type="primary" if st.session_state.selected_page == 'exercises' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'exercises'
        
        if st.button("📊 Mes Sessions", type="primary" if st.session_state.selected_page == 'progress' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'progress'
        
        st.markdown("### ⚙️ Administration")
        
        if st.button("🔧 Ontologie OWL", type="primary" if st.session_state.selected_page == 'admin_ontology' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'admin_ontology'
        
        if st.button("🗄️ Base de Données", type="primary" if st.session_state.selected_page == 'database' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'database'
        
        if st.button("👥 Utilisateurs", type="primary" if st.session_state.selected_page == 'users' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'users'
        
        st.markdown("### 🧪 Tests & Dev")
        
        if st.button("🗺️ Territory Selector", type="primary" if st.session_state.selected_page == 'territory_demo' else "secondary", use_container_width=True):
            st.session_state.selected_page = 'territory_demo'
    
    # Routage des pages selon les permissions
    route_pages_with_auth(st.session_state.selected_page)

def route_pages_with_auth(page):
    """Routage des pages - Mode Admin complet"""
    
    if page == 'home':
        page_admin_home()
    
    elif page == 'import':
        if ECG_IMPORT_AVAILABLE:
            page_ecg_import()
        else:
            st.error("❌ Module Import ECG non disponible")
            st.info(f"💡 Erreur d'import: {ecg_import_error if 'ecg_import_error' in dir() else 'Module non trouvé'}")
    
    elif page == 'cases':
        page_ecg_cases()
    
    elif page == 'edit':
        if ECG_EDIT_AVAILABLE:
            page_ecg_edit()
        else:
            st.error("❌ Module d'édition ECG non disponible")
            st.info(f"💡 Erreur d'import: {ecg_edit_error if 'ecg_edit_error' in dir() else 'Module non trouvé'}")
    
    elif page == 'correction_llm':
        if CORRECTION_LLM_AVAILABLE:
            page_correction_llm()
        else:
            st.error("❌ Module de correction LLM non disponible")
            st.info(f"Erreur: {correction_llm_error if 'correction_llm_error' in dir() else 'Module non trouvé'}")
    
    elif page == 'exercises':
        page_exercises()
    
    elif page == 'progress':
        page_student_progress()
    
    elif page == 'sessions':
        page_sessions_management()
    
    elif page == 'database':
        page_database_management()
    
    elif page == 'admin_ontology':
        page_admin_ontology()
    
    elif page == 'users':
        page_users_management_with_auth()
    
    elif page == 'territory_demo':
        page_territory_demo()


def page_users_management_with_auth():
    """Page de gestion des utilisateurs avec l'interface d'authentification"""
    st.markdown("## 👥 Gestion des Utilisateurs")
    
    tab1, tab2 = st.tabs(["👤 Liste des Utilisateurs", "➕ Créer Utilisateur"])
    
    with tab1:
        list_users_interface()
    
    with tab2:
        create_user_interface()


def route_student_sidebar_pages(page):
    """Routage des pages étudiant avec sidebar"""
    
    if page == 'home':
        page_student_home()
    elif page == 'cases':
        page_ecg_cases()  # Utilise maintenant la fonction importée
    elif page == 'exercises':
        page_exercises()
    elif page == 'progress':
        page_student_progress()


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


def page_exercises():
    """Page d'exercices pour étudiants avec sessions ECG"""
        
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

def page_ecg_cases():
    """
    📚 Bibliothèque de Cas ECG - Simple Gallery
    Browse all created ECG cases with practice button
    """
    st.title("📚 Bibliothèque de Cas ECG")
    st.markdown("*Parcourez tous les cas ECG créés et entraînez-vous*")
    
    cases_dir = Path("data/ecg_cases")
    
    if not cases_dir.exists():
        st.info("📁 Aucun cas disponible. Créez-en via **Import ECG**.")
        if st.button("➕ Aller à Import ECG"):
            st.session_state.selected_page = 'import'
            st.rerun()
        return
    
    # List all case directories
    case_dirs = [d for d in cases_dir.iterdir() if d.is_dir()]
    
    if not case_dirs:
        st.info("📁 Aucun cas disponible. Créez-en via **Import ECG**.")
        if st.button("➕ Aller à Import ECG"):
            st.session_state.selected_page = 'import'
            st.rerun()
        return
    
    st.markdown(f"**{len(case_dirs)} cas disponibles**")
    st.divider()
    
    # Display as 3-column grid
    cols = st.columns(3)
    
    for idx, case_dir in enumerate(sorted(case_dirs, key=lambda x: x.name, reverse=True)):
        metadata_file = case_dir / "metadata.json"
        
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            
            # Add case_folder path for correction_llm
            case_data['case_folder'] = str(case_dir)
            case_data['case_id'] = case_data.get('case_id', case_dir.name)
            
        except Exception as e:
            st.error(f"Erreur lecture {case_dir.name}: {e}")
            continue
        
        with cols[idx % 3]:
            # Card display
            with st.container():
                st.markdown(f"### {case_data.get('name', case_dir.name)}")
                
                # Display category and difficulty with icons
                category = case_data.get('category', 'N/A')
                difficulty = case_data.get('difficulty', 'N/A')
                
                category_icons = {
                    'Rythme': '🫀',
                    'Conduction': '⚡',
                    'Repolarisation': '📈',
                    'Arythmie': '💓',
                    'Ischémie': '🚨',
                    'SCA': '🆘'
                }
                
                difficulty_icons = {
                    'Débutant': '🟢',
                    'Intermédiaire': '🟡',
                    'Avancé': '🔴'
                }
                
                cat_icon = category_icons.get(category, '📁')
                diff_icon = difficulty_icons.get(difficulty, '⚪')
                
                st.markdown(f"{cat_icon} **Catégorie:** {category}")
                st.markdown(f"{diff_icon} **Difficulté:** {difficulty}")
                
                # Show creation date
                created = case_data.get('created_date', 'N/A')
                if created != 'N/A':
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created)
                        st.caption(f"📅 Créé le {dt.strftime('%d/%m/%Y')}")
                    except:
                        st.caption(f"📅 {created}")
                
                # Thumbnail preview if exists
                ecg_files = case_data.get('ecgs', [])
                image_displayed = False
                
                # Try new format: ecgs array
                if ecg_files and len(ecg_files) > 0:
                    first_ecg = ecg_files[0]
                    image_path = case_dir / first_ecg.get('filename', '')
                    if image_path.exists():
                        try:
                            from PIL import Image
                            img = Image.open(str(image_path))
                            st.image(img, use_container_width=True)
                            image_displayed = True
                        except Exception as e:
                            pass
                
                # Try old format: image_path
                if not image_displayed and case_data.get('image_path'):
                    image_path = case_dir / case_data['image_path']
                    if image_path.exists():
                        try:
                            from PIL import Image
                            img = Image.open(str(image_path))
                            st.image(img, use_container_width=True)
                            image_displayed = True
                        except:
                            pass
                
                # Try to find any image in directory
                if not image_displayed:
                    for ext in ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']:
                        images = list(case_dir.glob(ext))
                        if images:
                            try:
                                from PIL import Image
                                img = Image.open(str(images[0]))
                                st.image(img, use_container_width=True)
                                image_displayed = True
                                break
                            except:
                                pass
                
                if not image_displayed:
                    st.caption("📷 Aperçu non disponible")
                
                st.divider()
                
                # Action buttons
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("🎯 Pratiquer", key=f"practice_{case_dir.name}", use_container_width=True, type="primary"):
                        # Redirect to correction_llm (unified page)
                        st.session_state.selected_practice_case = case_data
                        st.session_state.selected_page = 'correction_llm'
                        st.rerun()
                
                with col_b:
                    if st.button("✏️ Éditer", key=f"edit_{case_dir.name}", use_container_width=True):
                        # Charger le cas pour édition dans ecg_edit
                        st.session_state.editing_case_id = case_dir.name
                        st.session_state.selected_page = 'edit'
                        st.rerun()
                
                # Bouton de suppression avec confirmation
                if st.button("🗑️ Supprimer", key=f"delete_{case_dir.name}", use_container_width=True):
                    st.session_state.confirm_delete_case = str(case_dir)
                    st.rerun()
                
                # Popup de confirmation de suppression
                if st.session_state.get('confirm_delete_case') == str(case_dir):
                    st.warning("⚠️ Confirmer la suppression ?")
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("✅ Oui", key=f"confirm_yes_{case_dir.name}", use_container_width=True):
                            try:
                                # Supprimer le dossier et tout son contenu
                                shutil.rmtree(case_dir)
                                st.success(f"✅ Cas supprimé: {case_data.get('name', case_dir.name)}")
                                st.session_state.confirm_delete_case = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erreur lors de la suppression: {str(e)}")
                    
                    with col_no:
                        if st.button("❌ Non", key=f"confirm_no_{case_dir.name}", use_container_width=True):
                            st.session_state.confirm_delete_case = None
                            st.rerun()
                
                st.markdown("---")
    
    # Plus de sidebar avec détails des cas - supprimé

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

def page_admin_ontology():
    """
    🔧 Administration - Rechargement Ontologie OWL
    Page réservée aux administrateurs pour recharger l'ontologie
    depuis un fichier .owl/.owx
    
    Use cases:
    - Mode hors ligne (pas d'accès GitHub)
    - Itérations de développement ontologie
    """
    st.title("🔧 Administration - Ontologie OWL")
    st.markdown("*Rechargez l'ontologie depuis un fichier .owl (offline ou dev)*")
    
    st.info("""
    **Cas d'usage :**
    - 🌐 **Mode hors ligne** : Environnements sans accès GitHub
    - 🔬 **Développement** : Itérations rapides d'ontologie
    - 🏥 **Hôpitaux** : Déploiements avec restrictions internet
    """)
    
    st.markdown("---")
    
    # Status actuel
    st.subheader("📊 Status Actuel")
    
    owl_file = Path("data/ontologie.owx")
    json_file = Path("data/ontology_from_owl.json")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if owl_file.exists():
            st.success(f"✅ Fichier OWL: `{owl_file.name}`")
            try:
                size_mb = owl_file.stat().st_size / (1024 * 1024)
                st.caption(f"Taille: {size_mb:.2f} MB")
            except:
                pass
        else:
            st.warning("⚠️ Fichier OWL non trouvé")
    
    with col2:
        if json_file.exists():
            st.success(f"✅ Ontologie JSON: `{json_file.name}`")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    ontology_data = json.load(f)
                    concept_count = len(ontology_data.get('concept_mappings', {}))
                    st.caption(f"Concepts: {concept_count}")
            except Exception as e:
                st.error(f"Erreur lecture: {e}")
        else:
            st.warning("⚠️ Ontologie JSON non trouvée")
    
    st.markdown("---")
    
    # Upload et extraction
    st.subheader("📤 Upload et Extraction")
    
    uploaded_file = st.file_uploader(
        "Sélectionnez un fichier .owl ou .owx",
        type=['owl', 'owx'],
        help="Fichier ontologie Protégé (format OWL/RDF)"
    )
    
    if uploaded_file:
        st.success(f"✅ Fichier chargé: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
        
        # Preview first few lines
        with st.expander("👁️ Aperçu du fichier"):
            try:
                content_preview = uploaded_file.getvalue().decode('utf-8')[:1000]
                st.code(content_preview, language='xml')
                uploaded_file.seek(0)  # Reset pour utilisation ultérieure
            except Exception as e:
                st.warning(f"Impossible d'afficher l'aperçu: {e}")
        
        st.markdown("---")
        
        # Extraction button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            extract_button = st.button(
                "🔄 Extraire vers JSON et Recharger",
                type="primary",
                use_container_width=True
            )
        
        if extract_button:
            with st.spinner("🔄 Extraction en cours..."):
                try:
                    # Step 1: Save uploaded file to data/ontologie.owx
                    st.info("📝 Étape 1/3: Sauvegarde du fichier OWL...")
                    with open(owl_file, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.success(f"✅ Fichier sauvegardé: {owl_file}")
                    
                    # Step 2: Convert OWL to JSON
                    st.info("🔄 Étape 2/3: Extraction ontologie...")
                    
                    try:
                        # ✅ UTILISATION DU BON EXTRACTEUR (rdf_owl_extractor, pas owl_to_json_converter!)
                        from backend.rdf_owl_extractor import RDFOWLExtractor
                        
                        # Extraction complète avec RDFOWLExtractor
                        extractor = RDFOWLExtractor(str(owl_file))
                        extractor.load()
                        extractor.extract_labels()
                        extractor.extract_weight_classes()
                        extractor.extract_weights()
                        extractor.inherit_weights()
                        extractor.extract_territoires()
                        extractor.extract_concept_territoires()
                        extractor.extract_requires_findings()
                        ontology_data = extractor.generate_json(str(json_file))
                        
                        st.success(f"✅ Ontologie extraite: {json_file}")
                        
                        # Show detailed stats
                        concept_count = len(ontology_data.get('concept_mappings', {}))
                        territory_count = len(ontology_data.get('territoires_ecg', {}))
                        
                        # Compter concepts avec synonymes
                        concepts_with_synonyms = sum(
                            1 for concept_data in ontology_data.get('concept_mappings', {}).values()
                            if concept_data.get('synonymes', [])
                        )
                        total_synonyms = sum(
                            len(concept_data.get('synonymes', []))
                            for concept_data in ontology_data.get('concept_mappings', {}).values()
                        )
                        
                        # Compter par catégorie
                        nb_urgent = len(ontology_data.get('concept_categories', {}).get('DIAGNOSTIC_URGENT', {}).get('concepts', []))
                        nb_majeur = len(ontology_data.get('concept_categories', {}).get('DIAGNOSTIC_MAJEUR', {}).get('concepts', []))
                        nb_signe = len(ontology_data.get('concept_categories', {}).get('SIGNE_ECG_PATHOLOGIQUE', {}).get('concepts', []))
                        nb_desc = len(ontology_data.get('concept_categories', {}).get('DESCRIPTEUR_ECG', {}).get('concepts', []))
                        
                        st.info(f"""
                        📊 **Statistiques d'extraction:**
                        - **{concept_count} concepts** au total
                        - **{territory_count} territoires** ECG
                        - **{concepts_with_synonyms} concepts** avec synonymes ({total_synonyms} synonymes totaux)
                        
                        **Répartition par catégorie:**
                        - 🚨 Diagnostic URGENT: {nb_urgent}
                        - ⚠️ Diagnostic MAJEUR: {nb_majeur}
                        - 🔍 Signe ECG: {nb_signe}
                        - 📝 Descripteur ECG: {nb_desc}
                        """)
                        
                    except ImportError as e:
                        st.error(f"❌ Module rdf_owl_extractor non disponible: {e}")
                        st.info("Vérifiez que backend/rdf_owl_extractor.py existe")
                        return
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'extraction: {e}")
                        import traceback
                        with st.expander("🐛 Détails de l'erreur"):
                            st.code(traceback.format_exc())
                        return
                    
                    # Step 3: Reload instruction
                    st.info("🔄 Étape 3/3: Rechargement...")
                    st.warning("""
                    ⚠️ **Action requise:**
                    
                    L'ontologie a été extraite avec succès !
                    
                    Pour appliquer les changements, **rechargez l'application** :
                    - Cliquez sur le bouton ci-dessous
                    - Ou appuyez sur **R** dans votre navigateur
                    """)
                    
                    if st.button("🔄 Recharger l'application maintenant", type="primary"):
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'extraction: {e}")
                    
                    import traceback
                    with st.expander("🐛 Détails de l'erreur"):
                        st.code(traceback.format_exc())
    
    else:
        st.info("💡 Uploadez un fichier .owl pour commencer")
    
    st.markdown("---")
    
    # Section alternative: Chemin externe
    st.subheader("📂 Ou charger depuis un chemin externe")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        external_path = st.text_input(
            "Chemin complet vers le fichier OWL",
            value=r"C:\Users\Administrateur\bmad\BrYOzRZIu7jQTwmfcGsi35.owl",
            help="Chemin absolu vers votre fichier .owl (ex: C:\\path\\to\\file.owl)"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        load_external_button = st.button("🔄 Charger", type="primary", use_container_width=True)
    
    if load_external_button:
        external_owl = Path(external_path)
        
        if not external_owl.exists():
            st.error(f"❌ Fichier introuvable: {external_path}")
        else:
            with st.spinner("🔄 Chargement et extraction en cours..."):
                try:
                    st.info(f"📥 Chargement depuis: {external_owl}")
                    
                    # Extraction directe sans copie
                    from backend.rdf_owl_extractor import RDFOWLExtractor
                    
                    extractor = RDFOWLExtractor(str(external_owl))
                    extractor.load()
                    extractor.extract_labels()
                    extractor.extract_weight_classes()
                    extractor.extract_weights()
                    extractor.inherit_weights()
                    extractor.extract_territoires()
                    extractor.extract_concept_territoires()
                    extractor.extract_requires_findings()
                    ontology_data = extractor.generate_json(str(json_file))
                    
                    st.success(f"✅ Ontologie extraite vers: {json_file}")
                    
                    # Show detailed stats
                    concept_count = len(ontology_data.get('concept_mappings', {}))
                    territory_count = len(ontology_data.get('territoires_ecg', {}))
                    
                    concepts_with_synonyms = sum(
                        1 for concept_data in ontology_data.get('concept_mappings', {}).values()
                        if concept_data.get('synonymes', [])
                    )
                    total_synonyms = sum(
                        len(concept_data.get('synonymes', []))
                        for concept_data in ontology_data.get('concept_mappings', {}).values()
                    )
                    
                    nb_urgent = len(ontology_data.get('concept_categories', {}).get('DIAGNOSTIC_URGENT', {}).get('concepts', []))
                    nb_majeur = len(ontology_data.get('concept_categories', {}).get('DIAGNOSTIC_MAJEUR', {}).get('concepts', []))
                    nb_signe = len(ontology_data.get('concept_categories', {}).get('SIGNE_ECG_PATHOLOGIQUE', {}).get('concepts', []))
                    nb_desc = len(ontology_data.get('concept_categories', {}).get('DESCRIPTEUR_ECG', {}).get('concepts', []))
                    
                    st.success(f"""
                    🎉 **EXTRACTION RÉUSSIE !**
                    
                    📊 **Statistiques:**
                    - **{concept_count} concepts** au total
                    - **{territory_count} territoires** ECG
                    - **{concepts_with_synonyms} concepts** avec synonymes ({total_synonyms} synonymes totaux)
                    
                    **Répartition par catégorie:**
                    - 🚨 Diagnostic URGENT: {nb_urgent}
                    - ⚠️ Diagnostic MAJEUR: {nb_majeur}
                    - 🔍 Signe ECG: {nb_signe}
                    - 📝 Descripteur ECG: {nb_desc}
                    """)
                    
                    st.warning("⚠️ **Rechargez l'application** pour utiliser la nouvelle ontologie (touche R)")
                    
                    if st.button("🔄 Recharger maintenant", type="primary", key="reload_after_external"):
                        # Reset ontology cache
                        if 'ontology_loaded' in st.session_state:
                            del st.session_state['ontology_loaded']
                        if 'ontology_data' in st.session_state:
                            del st.session_state['ontology_data']
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'extraction: {e}")
                    import traceback
                    with st.expander("🐛 Détails de l'erreur"):
                        st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # Documentation
    with st.expander("📚 Documentation"):
        st.markdown("""
        ### 🔍 Comment ça marche?
        
        1. **Upload** : Sélectionnez votre fichier .owl/.owx
        2. **Sauvegarde** : Le fichier est sauvegardé dans `data/ontologie.owx`
        3. **Extraction** : Le convertisseur extrait les concepts vers JSON
        4. **Rechargement** : L'application recharge la nouvelle ontologie
        
        ### 📁 Fichiers générés
        
        - `data/ontologie.owx` : Fichier OWL source
        - `data/ontology_from_owl.json` : Ontologie au format JSON
        
        ### ⚠️ Précautions
        
        - Testez d'abord en environnement de développement
        - Faites une sauvegarde avant de remplacer
        - Vérifiez les logs après rechargement
        
        ### 🔧 Dépannage
        
        Si l'extraction échoue :
        - Vérifiez le format du fichier OWL (doit être OWL/XML ou RDF/XML)
        - Consultez les logs de l'extracteur
        - Vérifiez que tous les concepts ont des labels français
        """)

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
                try:
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
        # 🎯 UTILISER LE MODULE DE CORRECTION LLM UNIFIÉ
        st.markdown("#### 🔍 Correction Automatique LLM")
        
        # Préparer les données du cas pour correction_llm
        if 'case_folder' not in case_data:
            case_folder = ECG_CASES_DIR / case_data.get('case_id', '')
            case_data['case_folder'] = str(case_folder)
        
        # Rediriger vers la page de correction LLM pour ce cas
        if st.button("🎯 Ouvrir le module de correction", key=f"open_correction_{case_id}", type="primary", use_container_width=True):
            # Sauvegarder le cas dans session_state pour correction_llm
            st.session_state.selected_practice_case = case_data
            st.session_state.selected_page = 'correction_llm'
            st.rerun()
        
        st.info("💡 Utilisez le module de correction pour une analyse complète avec IA")
        
        # Aperçu du diagnostic attendu
        with st.expander("📋 Voir le diagnostic de référence"):
            diagnosis = case_data.get('expected_concepts', case_data.get('annotations', []))
            if diagnosis:
                if isinstance(diagnosis, list):
                    for diag in diagnosis[:5]:
                        concept_text = diag if isinstance(diag, str) else diag.get('concept', diag.get('text', str(diag)))
                        st.write(f"• {concept_text}")
                else:
                    st.write(diagnosis)
            else:
                st.info("Pas de diagnostic de référence disponible")

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


def page_territory_demo():
    """Page de démonstration du Territory Selector"""
    st.title("🗺️ Démonstration Territory Selector")
    st.markdown("Test interactif du sélecteur de territoire contextuel")
    
    # Import des composants
    try:
        from components.territory_selector_ui import (
            render_territory_selectors,
            check_territory_completeness,
            get_territory_selection_summary,
            calculate_territory_bonus
        )
        from backend.territory_resolver import get_territory_config
    except ImportError as e:
        st.error(f"❌ Erreur d'import: {e}")
        st.info("💡 Vérifiez que backend/territory_resolver.py et frontend/components/territory_selector_ui.py existent")
        return
    
    # Charger l'ontologie
    ontology_path = project_root / "data" / "ontology_from_owl.json"
    if not ontology_path.exists():
        st.error("❌ Ontologie non trouvée")
        st.info(f"💡 Chemin attendu: {ontology_path}")
        return
    
    with open(ontology_path, 'r', encoding='utf-8') as f:
        ontology = json.load(f)
    
    st.markdown("---")
    
    # Sélection du concept à tester
    st.markdown("### 1️⃣ Sélectionnez un concept")
    
    test_concepts = [
        "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST",
        "STEMI",
        "NSTEMI",
        "Hypertrophie VG",
        "BAV 1"
    ]
    
    selected_concept = st.selectbox(
        "Concept à tester:",
        options=test_concepts,
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 2️⃣ Sélecteur de territoire")
    
    # Afficher le sélecteur
    territories, mirrors = render_territory_selectors(
        selected_concept,
        ontology,
        key_prefix="demo"
    )
    
    # Afficher ce qui a été capturé
    st.markdown("---")
    st.markdown("### 3️⃣ Résultats")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Territoires sélectionnés:**")
        if territories:
            for terr in territories:
                st.write(f"📍 {terr}")
        else:
            st.info("Aucun territoire sélectionné")
    
    with col2:
        st.markdown("**Miroirs sélectionnés:**")
        if mirrors:
            for mirr in mirrors:
                st.write(f"🪞 {mirr}")
        else:
            st.info("Aucun miroir sélectionné")
    
    # Check complétude
    st.markdown("---")
    st.markdown("### 4️⃣ Validation")
    
    is_complete, error_msg = check_territory_completeness(
        selected_concept,
        territories,
        ontology
    )
    
    if is_complete:
        st.success("✅ Sélection complète")
    else:
        st.error(f"❌ {error_msg}")
    
    # Résumé
    summary = get_territory_selection_summary(selected_concept, territories, mirrors)
    if summary:
        st.info(f"📝 Résumé: {summary}")
    
    # Test scoring (simulation)
    st.markdown("---")
    st.markdown("### 5️⃣ Simulation Scoring")
    
    with st.expander("🧪 Simuler un matching avec réponse de référence"):
        st.markdown("**Définir les territoires attendus:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            config = get_territory_config(selected_concept, ontology)
            
            if config and config['territories']:
                expected_terr = st.multiselect(
                    "Territoires attendus:",
                    options=config['territories'],
                    default=config['territories'][:1],
                    key="expected_territories"
                )
            else:
                expected_terr = []
                st.info("Pas de territoires disponibles")
        
        with col2:
            if config and config['mirrors']:
                expected_mirr = st.multiselect(
                    "Miroirs attendus:",
                    options=config['mirrors'],
                    key="expected_mirrors"
                )
            else:
                expected_mirr = []
                st.info("Pas de miroirs disponibles")
        
        if expected_terr or expected_mirr:
            bonus, explanation = calculate_territory_bonus(
                selected_concept,
                territories,
                mirrors,
                expected_terr,
                expected_mirr,
                ontology
            )
            
            st.markdown("---")
            st.markdown("**Résultat du scoring:**")
            st.metric("Bonus territoire", f"+{bonus*100:.1f}%")
            st.markdown(f"**Explication:** {explanation}")
    
    # Debug info
    with st.expander("🔍 Debug - Configuration complète"):
        config = get_territory_config(selected_concept, ontology)
        if config:
            st.json(config)
        else:
            st.info("Pas de configuration territoire pour ce concept")


if __name__ == '__main__':
    main()
