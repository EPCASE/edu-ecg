"""
🎓 ECG Session Builder - Interface POC
Interface complète pour importer, annoter des ECG et créer des sessions de formation

Workflow:
1. 📤 Import ECG (simple ou multiple)
2. 🏷️ Annotation intelligente (ontologie + LLM)
3. ✅ Validation du cas
4. 📚 Création de session

Author: BMad Team
Date: 2026-01-11
"""

# Configuration du PYTHONPATH AVANT tous les imports
import sys
from pathlib import Path
# Ajouter le root du projet (2 niveaux au-dessus de ce fichier)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
# Ajouter aussi frontend/ pour les components
sys.path.insert(0, str(project_root / "frontend"))

# 🔧 CHARGER .env AVANT tous les autres imports
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from unidecode import unidecode
import json
from datetime import datetime
import uuid
from PIL import Image
import io
import base64

# Imports backend (après configuration sys.path)
from backend.services.llm_semantic_matcher import semantic_match, get_llm_stats
from backend.services.llm_service import LLMService
from backend.services.concept_decomposer import create_decomposer
from backend.territory_resolver import get_territory_config, resolve_territories
from components.territory_selector_ui import render_territory_selectors, check_territory_completeness

# Configuration
ECG_CASES_DIR = Path("data/ecg_cases")
ECG_SESSIONS_DIR = Path("data/ecg_sessions")
ANNOTATION_TEMPLATES_PATH = Path("data/annotation_templates.json")
ONTOLOGY_PATH = Path("data/ontology_from_owl.json")

ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
ECG_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# UTILITIES
# =====================================================================

def load_ontology():
    """Charge l'ontologie ECG"""
    try:
        with open(ONTOLOGY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning("⚠️ Ontologie non trouvée")
        return {}


def normalize_search(text):
    """Normalise le texte pour la recherche (insensible casse + accents)"""
    return unidecode(text.lower())


def load_annotation_templates():
    """Charge les templates d'annotation"""
    try:
        with open(ANNOTATION_TEMPLATES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_ontology_concepts():
    """Récupère tous les concepts de l'ontologie avec synonymes"""
    ontology = load_ontology()
    
    concepts = []
    
    # PRIORITÉ: Utiliser concept_mappings qui contient les synonymes
    if 'concept_mappings' in ontology:
        for concept_id, concept_data in ontology['concept_mappings'].items():
            if isinstance(concept_data, dict):
                concept_name = concept_data.get('concept_name', '')
                
                # 🚫 FILTRER les concepts "Localisation" parents (non sélectionnables)
                if concept_name and not concept_name.startswith('Localisation') and not concept_name.startswith('localisation'):
                    concepts.append({
                        'name': concept_name,
                        'category': concept_data.get('categorie', concept_data.get('category', 'AUTRE')),
                        'ontology_id': concept_id,
                        'synonyms': concept_data.get('synonymes', concept_data.get('synonyms', [])),
                        'territoires_possibles': concept_data.get('territoires_possibles', [])  # 🆕 NOUVEAU
                    })
    
    # Fallback: concept_categories (sans synonymes)
    elif 'concept_categories' in ontology:
        for category, data in ontology['concept_categories'].items():
            if isinstance(data, dict) and 'concepts' in data:
                for concept_data in data['concepts']:
                    if isinstance(concept_data, dict):
                        concept_name = concept_data.get('concept_name', concept_data.get('name', ''))
                        if concept_name:
                            concepts.append({
                                'name': concept_name,
                                'category': category,
                                'ontology_id': concept_data.get('ontology_id', ''),
                                'synonyms': concept_data.get('synonyms', [])
                            })
    
    return concepts


def _display_territory_selectors_for_annotations():
    """Affiche les sélecteurs de territoire pour les annotations qui en ont besoin"""
    if 'case_annotations' not in st.session_state or not st.session_state.case_annotations:
        return
    
    # Initialiser territoire_selections si nécessaire
    if 'territory_selections' not in st.session_state:
        st.session_state.territory_selections = {}
    
    # Charger l'ontologie
    ontology = load_ontology()
    if not ontology:
        return
    
    # Vérifier quels concepts nécessitent un territoire
    concepts_with_territory = []
    for annotation in st.session_state.case_annotations:
        concept_name = annotation['concept']
        config = get_territory_config(concept_name, ontology)
        if config and config['show_territory_selector']:
            concepts_with_territory.append((concept_name, config))
    
    # Afficher la section territoires si nécessaire
    if concepts_with_territory:
        st.markdown("---")
        st.markdown("### 🗺️ Précision des Territoires")
        st.success(f"📍 {len(concepts_with_territory)} concept(s) nécessitent une précision de territoire")
        
        # Afficher un sélecteur pour chaque concept
        for concept_name, config in concepts_with_territory:
            is_required = config.get('is_required', False)
            required_label = " (obligatoire)" if is_required else ""
            with st.expander(f"🗺️ {concept_name}{required_label}", expanded=True):
                
                # Afficher les sélecteurs
                territories, mirrors = render_territory_selectors(
                    concept_name,
                    ontology,
                    key_prefix=f"ecg_import_{concept_name.replace(' ', '_')}"
                )
                
                # Valider
                is_complete, error_msg = check_territory_completeness(
                    concept_name,
                    territories,
                    ontology
                )
                
                if not is_complete:
                    st.warning(error_msg)
                else:
                    # Afficher résumé si complet
                    if territories:
                        territory_str = ", ".join(territories)
                        mirror_str = f" + {', '.join(mirrors)}" if mirrors else ""
                        st.success(f"✅ Territoire: {territory_str}{mirror_str}")
                
                # Stocker dans session_state
                st.session_state.territory_selections[concept_name] = {
                    'territories': territories,
                    'mirrors': mirrors
                }


def _display_structure_selectors_for_annotations():
    """Affiche les sélecteurs de structure anatomique pour échappement ventriculaire"""
    if 'case_annotations' not in st.session_state or not st.session_state.case_annotations:
        return
    
    # Initialiser structure_selections si nécessaire
    if 'structure_selections' not in st.session_state:
        st.session_state.structure_selections = {}
    
    # Charger l'ontologie
    ontology = load_ontology()
    if not ontology:
        return
    
    concept_mappings = ontology.get('concept_mappings', {})
    
    # Vérifier quels concepts nécessitent une structure anatomique
    concepts_with_structure = []
    for annotation in st.session_state.case_annotations:
        concept_name = annotation['concept']
        concept_id = concept_name.upper().replace(' ', '_').replace('-', '_').replace("'", '_')
        concept_data = concept_mappings.get(concept_id, {})
        
        # Vérifier si le concept a des origin_structures ET requires_morphology_inversion
        has_origins = len(concept_data.get('origin_structures', [])) > 0
        requires_inversion = concept_data.get('requires_morphology_inversion', False)
        
        if has_origins and requires_inversion:
            concepts_with_structure.append((concept_name, concept_data))
    
    # Afficher la section structures si nécessaire
    if concepts_with_structure:
        st.markdown("---")
        st.markdown("### 🏗️ Origine Anatomique & Morphologie")
        st.success(f"⚡ {len(concepts_with_structure)} concept(s) nécessitent une précision d'origine")
        
        # Afficher un sélecteur pour chaque concept
        for concept_name, concept_data in concepts_with_structure:
            with st.expander(f"🏗️ {concept_name}", expanded=True):
                st.caption("⚡ Ce concept nécessite une inversion de morphologie")
                
                # Importer le sélecteur de structure
                try:
                    from components.structure_selector import structure_selector_interface
                    
                    result = structure_selector_interface(
                        concept_name=concept_name,
                        key_prefix=f"ecg_import_{concept_name.replace(' ', '_')}",
                        auto_add_morphology=True
                    )
                    
                    if result:
                        # Stocker dans session_state
                        st.session_state.structure_selections[concept_name] = {
                            'structure': result['selected_structure'],
                            'morphology': result['calculated_morphology'],
                            'explanation': result['explanation']
                        }
                        
                        # Ajouter automatiquement la morphologie aux annotations
                        if result['calculated_morphology']:
                            # Vérifier si la morphologie n'est pas déjà dans les annotations
                            morphology_exists = any(
                                ann['concept'] == result['calculated_morphology']
                                for ann in st.session_state.case_annotations
                            )
                            
                            if not morphology_exists:
                                st.info(f"💡 Annotation auto-ajoutée: **{result['calculated_morphology']}**")
                                # Ajouter à la session pour sauvegarde
                                if st.button(
                                    f"➕ Ajouter '{result['calculated_morphology']}'",
                                    key=f"add_morpho_{concept_name.replace(' ', '_')}"
                                ):
                                    st.session_state.case_annotations.append({
                                        'concept': result['calculated_morphology'],
                                        'type': 'auto_morphology',
                                        'parent_concept': concept_name
                                    })
                                    st.rerun()
                
                except ImportError as e:
                    st.error(f"❌ Module structure_selector non disponible: {e}")
                    # Fallback simple
                    origin_structures = concept_data.get('origin_structures', [])
                    if origin_structures:
                        selected = st.selectbox(
                            "Origine anatomique:",
                            options=origin_structures,
                            key=f"fallback_structure_{concept_name.replace(' ', '_')}"
                        )
                        st.session_state.structure_selections[concept_name] = {
                            'structure': selected,
                            'morphology': None,
                            'explanation': None
                        }


def generate_case_id():
    """Génère un ID unique pour un cas"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"case_{timestamp}_{unique_id}"


def save_case_to_disk(case_data, images):
    """Sauvegarde un cas ECG sur le disque"""
    case_id = case_data['case_id']
    case_dir = ECG_CASES_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder les images
    ecg_files = []
    for idx, img_data in enumerate(images):
        img_filename = f"ecg_{idx + 1}.png"
        img_path = case_dir / img_filename
        img_data['image'].save(img_path)
        
        # Ajouter à la liste des ECGs
        ecg_files.append({
            'filename': img_filename,
            'index': idx + 1,
            'type': 'image/png'
        })
    
    # Ajouter la liste des ECGs au metadata
    case_data['ecgs'] = ecg_files
    case_data['num_ecg'] = len(ecg_files)
    
    # Sauvegarder les métadonnées
    metadata_path = case_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    
    return case_dir


def create_session_from_cases(session_name, description, difficulty, cases, time_limit=30):
    """Crée une session à partir de cas annotés"""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    session_data = {
        'session_id': session_id,
        'name': session_name,
        'description': description,
        'difficulty': difficulty,
        'time_limit': time_limit,
        'cases': [case['case_id'] for case in cases],
        'created_date': datetime.now().isoformat(),
        'status': 'active',
        'show_feedback': True,
        'allow_retry': True,
        'participants': []
    }
    
    session_file = ECG_SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    return session_id


# =====================================================================
# STEP 1: UPLOAD ECG
# =====================================================================

def step_upload_ecg():
    """Étape 1: Upload des ECG"""
    st.markdown("### 📤 Étape 1: Importer les ECG")
    
    # Info formats supportés
    st.info("📷 **Formats supportés**: Images (PNG, JPG, JPEG, BMP, TIFF, WebP), PDF, captures d'écran mobile")
    
    # Mode d'import
    import_mode = st.radio(
        "Mode d'import",
        ["📄 ECG Unique", "📁 Cas Multi-ECG"],
        horizontal=True,
        help="Choisissez d'importer un seul ECG ou plusieurs ECG pour un même cas"
    )
    
    if import_mode == "📄 ECG Unique":
        uploaded_file = st.file_uploader(
            "Choisir un fichier ECG",
            type=['png', 'jpg', 'jpeg', 'pdf', 'bmp', 'tiff', 'tif', 'webp', 'heic'],
            help="Tous formats d'images et PDF acceptés (y compris captures d'écran mobile)"
        )
        
        if uploaded_file:
            # Traiter l'image
            if uploaded_file.type.startswith('image') or uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.heic')):
                try:
                    image = Image.open(uploaded_file)
                    # Convertir en RGB si nécessaire (pour compatibilité)
                    if image.mode not in ('RGB', 'L'):
                        image = image.convert('RGB')
                    
                    # Afficher prévisualisation avec info dimensions
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.image(image, caption="Prévisualisation", use_container_width=True)
                    with col2:
                        st.metric("Largeur", f"{image.width}px")
                        st.metric("Hauteur", f"{image.height}px")
                        st.metric("Format", image.format or "Inconnu")
                    
                    # Sauvegarder dans session state
                    if 'uploaded_images' not in st.session_state:
                        st.session_state.uploaded_images = []
                    
                    if st.button("✅ Valider cet ECG", type="primary"):
                        st.session_state.uploaded_images = [{
                            'image': image,
                            'filename': uploaded_file.name,
                            'label': 'ECG_01'
                        }]
                        st.session_state.current_step = 2
                        st.success("✅ ECG chargé avec succès!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'ouverture de l'image: {str(e)}")
                    st.info("💡 Essayez de convertir votre image en PNG ou JPEG")
            
            elif uploaded_file.type == 'application/pdf':
                try:
                    # Essayer d'extraire les images du PDF avec pdf2image
                    try:
                        from pdf2image import convert_from_bytes
                        
                        # Convertir le PDF en images
                        images = convert_from_bytes(uploaded_file.read(), dpi=300)
                        
                        if images:
                            st.success(f"✅ {len(images)} page(s) extraite(s) du PDF")
                            
                            # Afficher toutes les pages
                            for idx, img in enumerate(images):
                                st.image(img, caption=f"Page {idx + 1}", use_container_width=True)
                            
                            # Sélectionner quelle page utiliser
                            if len(images) > 1:
                                page_num = st.selectbox(
                                    "Sélectionner la page à utiliser",
                                    range(1, len(images) + 1),
                                    format_func=lambda x: f"Page {x}"
                                )
                                selected_image = images[page_num - 1]
                            else:
                                selected_image = images[0]
                            
                            if st.button("✅ Valider cet ECG", type="primary"):
                                st.session_state.uploaded_images = [{
                                    'image': selected_image,
                                    'filename': uploaded_file.name.replace('.pdf', '.png'),
                                    'label': 'ECG_01'
                                }]
                                st.session_state.current_step = 2
                                st.success("✅ ECG extrait du PDF avec succès!")
                                st.rerun()
                        else:
                            st.error("❌ Aucune image trouvée dans le PDF")
                            
                    except ImportError:
                        st.error("❌ Le module pdf2image n'est pas installé")
                        st.info("💡 Installez-le avec: `pip install pdf2image poppler-utils`")
                        st.warning("📄 En attendant, exportez votre PDF en image (PNG/JPEG)")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du traitement du PDF: {str(e)}")
                    st.info("💡 Essayez d'exporter le PDF en image PNG ou JPEG")
    
    else:  # Multi-ECG
        st.info("💡 Vous pouvez ajouter plusieurs ECG pour créer un cas complexe (différents moments, dérivations, etc.)")
        
        # Initialiser la liste des images
        if 'uploaded_images' not in st.session_state:
            st.session_state.uploaded_images = []
        
        # Uploader un nouvel ECG
        uploaded_file = st.file_uploader(
            f"Ajouter un ECG ({len(st.session_state.uploaded_images) + 1})",
            type=['png', 'jpg', 'jpeg', 'pdf', 'bmp', 'tiff', 'tif', 'webp', 'heic'],
            key=f"upload_{len(st.session_state.uploaded_images)}",
            help="Tous formats d'images acceptés"
        )
        
        if uploaded_file:
            try:
                # Traiter selon le type
                if uploaded_file.type == 'application/pdf':
                    try:
                        from pdf2image import convert_from_bytes
                        images = convert_from_bytes(uploaded_file.read(), dpi=300)
                        image = images[0] if images else None
                        if not image:
                            st.error("❌ Impossible d'extraire l'image du PDF")
                    except ImportError:
                        st.error("❌ Module pdf2image non disponible - utilisez une image")
                        image = None
                else:
                    image = Image.open(uploaded_file)
                    if image.mode not in ('RGB', 'L'):
                        image = image.convert('RGB')
                
                if image:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.image(image, caption="Prévisualisation", use_container_width=True)
                    
                    with col2:
                        ecg_label = st.text_input(
                            "Libellé de cet ECG",
                            value=f"ECG_{len(st.session_state.uploaded_images) + 1:02d}",
                            key="ecg_label_input"
                        )
                        
                        ecg_timing = st.selectbox(
                            "Moment",
                            ["Initial", "Post-traitement", "Contrôle", "Suivi"],
                            key="ecg_timing_select"
                        )
                        
                        if st.button("➕ Ajouter cet ECG"):
                            st.session_state.uploaded_images.append({
                                'image': image,
                                'filename': uploaded_file.name,
                                'label': ecg_label,
                                'timing': ecg_timing
                            })
                            st.success(f"✅ {ecg_label} ajouté!")
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")
                st.info("💡 Essayez de convertir votre fichier en PNG ou JPEG")
        
        # Afficher les ECG ajoutés
        if st.session_state.uploaded_images:
            st.markdown("---")
            st.markdown(f"**📋 ECG ajoutés: {len(st.session_state.uploaded_images)}**")
            
            for idx, img_data in enumerate(st.session_state.uploaded_images):
                with st.expander(f"📄 {img_data['label']}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.image(img_data['image'], use_container_width=True)
                    with col2:
                        st.write(f"**Fichier:** {img_data['filename']}")
                        st.write(f"**Moment:** {img_data.get('timing', 'N/A')}")
                        if st.button("🗑️ Supprimer", key=f"delete_{idx}"):
                            st.session_state.uploaded_images.pop(idx)
                            st.rerun()
            
            st.markdown("---")
            if st.button("✅ Passer à l'annotation", type="primary", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()


# =====================================================================
# STEP 2: ANNOTATION
# =====================================================================

def step_annotation():
    """Étape 2: Annotation intelligente"""
    st.markdown("### 🏷️ Étape 2: Annoter le cas ECG")
    
    if 'uploaded_images' not in st.session_state or not st.session_state.uploaded_images:
        st.error("❌ Aucun ECG chargé. Retournez à l'étape 1.")
        if st.button("◀ Retour"):
            st.session_state.current_step = 1
            st.rerun()
        return
    
    # 📷 AFFICHAGE DES ECG IMPORTÉS
    st.markdown("#### 📷 ECG(s) importé(s)")
    
    # Si un seul ECG, l'afficher directement
    if len(st.session_state.uploaded_images) == 1:
        ecg_data = st.session_state.uploaded_images[0]
        st.image(ecg_data['image'], caption=ecg_data.get('label', 'ECG'), use_container_width=True)
    
    # Si plusieurs ECG, onglets pour les visualiser
    else:
        tab_labels = [img_data.get('label', f"ECG {i+1}") for i, img_data in enumerate(st.session_state.uploaded_images)]
        tabs = st.tabs(tab_labels)
        
        for tab, img_data in zip(tabs, st.session_state.uploaded_images):
            with tab:
                st.image(img_data['image'], use_container_width=True)
                if 'timing' in img_data:
                    st.caption(f"⏱️ Moment: {img_data['timing']}")
    
    st.markdown("---")
    
    # Informations du cas
    st.markdown("#### 📋 Informations du cas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_name = st.text_input(
            "Nom du cas",
            value=st.session_state.get('case_name', ''),
            placeholder="Ex: BAV 2 Mobitz 1 - Cas clinique",
            key="case_name_input"
        )
        st.session_state.case_name = case_name
        
        case_category = st.selectbox(
            "Catégorie",
            ["Troubles du Rythme", "Infarctus", "Bloc de Conduction", "Hypertrophie", "Normal", "Autre"],
            key="case_category_select"
        )
        st.session_state.case_category = case_category
    
    with col2:
        case_difficulty = st.select_slider(
            "Difficulté",
            options=["🟢 Débutant", "🟡 Intermédiaire", "🟠 Avancé", "🔴 Expert"],
            value=st.session_state.get('case_difficulty', "🟡 Intermédiaire"),
            key="case_difficulty_slider"
        )
        st.session_state.case_difficulty = case_difficulty
        
        case_description = st.text_area(
            "Description clinique",
            value=st.session_state.get('case_description', ''),
            placeholder="Contexte clinique du patient...",
            height=100,
            key="case_description_area"
        )
        st.session_state.case_description = case_description
    
    st.markdown("---")
    st.markdown("#### 🏷️ Annotations expertes")
    
    # Initialiser les annotations
    if 'case_annotations' not in st.session_state:
        st.session_state.case_annotations = []
    
    # Initialiser les sélections de territoires
    if 'territory_selections' not in st.session_state:
        st.session_state.territory_selections = {}
    
    # Deux modes d'annotation
    annotation_mode = st.radio(
        "Mode d'annotation",
        ["🔍 Recherche Rapide", "🤖 Assisté par LLM", "✍️ Manuel"],
        horizontal=True
    )
    
    if annotation_mode == "🔍 Recherche Rapide":
        st.info("💡 Recherche instantanée dans l'ontologie (sans LLM)")
        
        # Charger tous les concepts
        ontology_concepts = get_ontology_concepts()
        
        search_term = st.text_input(
            "🔍 Rechercher un concept",
            placeholder="Ex: BAV, mobitz, sinusal, normal...",
            key="search_concept_input"
        )
        
        if search_term and len(search_term) >= 2:
            # Recherche multi-termes (tous les mots doivent être présents)
            search_words = [normalize_search(word) for word in search_term.split() if len(word) >= 2]
            
            if search_words:
                matching_concepts = []
                
                for c in ontology_concepts:
                    # Texte à rechercher : nom + synonymes
                    search_text = normalize_search(c['name'])
                    for syn in c.get('synonyms', []):
                        search_text += " " + normalize_search(syn)
                    
                    # Tous les mots de recherche doivent être présents
                    if all(word in search_text for word in search_words):
                        matching_concepts.append(c)
            else:
                matching_concepts = []
            
            if matching_concepts:
                st.success(f"✅ {len(matching_concepts)} concepts trouvés")
                
                # Limiter l'affichage
                for idx, concept in enumerate(matching_concepts[:20]):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{concept['name']}**")
                        caption_parts = [f"Catégorie: {concept['category']}"]
                        
                        # 🆕 AFFICHER TERRITOIRES POSSIBLES
                        territoires = concept.get('territoires_possibles', [])
                        if territoires:
                            territoires_str = ", ".join(territoires)
                            caption_parts.append(f"🗺️ Territoire: {territoires_str}")
                        
                        st.caption(" | ".join(caption_parts))
                    
                    with col2:
                        # Clé unique avec index pour éviter les doublons
                        add_key = f"quick_add_{idx}_{concept['ontology_id']}"
                        if st.button("➕ Ajouter", key=add_key):
                            if concept['name'] not in [a['concept'] for a in st.session_state.case_annotations]:
                                st.session_state.case_annotations.append({
                                    'concept': concept['name'],
                                    'category': concept['category'],
                                    'type': 'expert',
                                    'coefficient': 1.0
                                })
                                st.success(f"✅ {concept['name']} ajouté!")
                                st.rerun()
                            else:
                                st.warning("Déjà ajouté")
            else:
                st.warning(f"⚠️ Aucun concept trouvé pour '{search_term}'")
                st.info("💡 Essayez d'autres termes ou utilisez le mode Manuel")
    
    elif annotation_mode == "🤖 Assisté par LLM":
        st.info("💡 Décrivez ce que vous voyez sur l'ECG, le LLM extraira et décomposera les concepts intelligemment")
        
        user_description = st.text_area(
            "Description de l'ECG",
            placeholder="Ex: STEMI antérieur, BAV du 2e degré Mobitz 1, fréquence à 60 bpm...",
            height=100,
            key="llm_description_area"
        )
        
        if st.button("🔍 Analyser avec LLM", type="primary") and user_description:
            with st.spinner("🤖 Extraction et décomposition intelligente..."):
                try:
                    # ÉTAPE 1: Extraire les concepts du texte avec le LLM
                    llm_service = LLMService(use_structured_output=True)
                    extraction_result = llm_service.extract_concepts(user_description)
                    
                    extracted_concepts = extraction_result.get('concepts', [])
                    
                    if not extracted_concepts:
                        st.warning("⚠️ Aucun concept médical détecté dans votre description")
                        st.info("💡 Essayez d'être plus précis (ex: 'STEMI antérieur', 'BAV 2 Mobitz 1')")
                    else:
                        st.success(f"✅ {len(extracted_concepts)} concepts extraits par le LLM!")
                        
                        # ÉTAPE 2: Décomposer chaque concept avec intelligence
                        with st.spinner("🧩 Décomposition et validation..."):
                            ontology_concepts = get_ontology_concepts()
                            decomposer = create_decomposer(ontology_concepts)
                            
                            all_matches = []
                            
                            for extracted in extracted_concepts:
                                concept_text = extracted['text']
                                confidence = extracted.get('confidence', 0.9)
                                
                                # Décomposer intelligemment
                                matches = decomposer.decompose(concept_text, confidence)
                                
                                # Convertir pour l'UI
                                for match in matches:
                                    match_dict = match.to_dict()
                                    match_dict['is_main'] = (match.relation == 'main')
                                    match_dict['is_territory'] = (match.relation == 'territory')
                                    match_dict['is_subtype'] = (match.relation == 'subtype')
                                    all_matches.append(match_dict)
                        
                        # Tri: principaux d'abord, puis par confiance
                        all_matches.sort(key=lambda x: (not x['is_main'], -x['confidence']))
                        
                        # Afficher les résultats
                        if all_matches:
                            validated_count = sum(1 for m in all_matches if m['validated'])
                            st.success(f"✅ {len(all_matches)} concepts annotés ({validated_count} validés) !")
                            
                            st.markdown("**📊 Concepts détectés:**")
                            
                            for mc in all_matches:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                
                                with col1:
                                    # Icône selon le type
                                    icon = "🎯" if mc['is_main'] else "🗺️" if mc['is_territory'] else "🔗"
                                    validated_icon = "✅" if mc['validated'] else "⚠️"
                                    
                                    st.write(f"{icon} **{mc['concept']}** {validated_icon}")
                                    
                                    caption_parts = []
                                    if mc['extracted_text'] and mc['extracted_text'] != mc['concept']:
                                        caption_parts.append(f"De: '{mc['extracted_text']}'")
                                    caption_parts.append(mc['category'])
                                    
                                    # Type de relation
                                    if mc['relation'] == 'territory':
                                        caption_parts.append("🗺️ Territoire")
                                    elif mc['relation'] == 'subtype':
                                        caption_parts.append("🔗 Sous-type")
                                    elif mc['relation'] == 'main':
                                        caption_parts.append("🎯 Principal")
                                    
                                    # Territoires possibles
                                    territoires = mc.get('territoires_possibles', [])
                                    if territoires:
                                        caption_parts.append(f"Zones: {', '.join(territoires)}")
                                    
                                    st.caption(" • ".join(caption_parts))
                                    
                                with col2:
                                    # Badge confiance
                                    conf = mc['confidence']
                                    if conf >= 85:
                                        st.markdown(f"🟢 **{conf}%**")
                                    elif conf >= 70:
                                        st.markdown(f"🟡 **{conf}%**")
                                    else:
                                        st.markdown(f"🟠 **{conf}%**")
                                        
                                with col3:
                                    add_key = f"add_llm_{mc['concept'].replace(' ', '_')[:20]}_{mc['confidence']}"
                                    if st.button("➕", key=add_key):
                                        if mc['concept'] not in [a['concept'] for a in st.session_state.case_annotations]:
                                            st.session_state.case_annotations.append({
                                                'concept': mc['concept'],
                                                'category': mc['category'],
                                                'confidence': mc['confidence'],
                                                'type': 'expert',
                                                'coefficient': 1.0 if mc['validated'] else 0.9
                                            })
                                            st.success(f"✅ {mc['concept']} ajouté!")
                                            st.rerun()
                        else:
                            st.warning(f"⚠️ Aucun concept matché dans l'ontologie")
                            st.info("💡 Essayez 'Recherche Rapide' ou 'Manuel'")
                
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
                    st.info("💡 Essayez un autre mode d'annotation")
    
    else:  # Mode manuel - Vue arborescente
        st.info("💡 Parcourez l'ontologie de manière hiérarchique (comme WebProtégé)")
        
        # Charger l'ontologie
        ontology_concepts = get_ontology_concepts()
        
        if not ontology_concepts:
            st.error("❌ Impossible de charger l'ontologie")
            st.info(f"📁 Vérifiez que le fichier existe: {ONTOLOGY_PATH}")
            return
        
        st.success(f"✅ {len(ontology_concepts)} concepts chargés")
        
        # Barre de recherche filtrante
        search_filter = st.text_input(
            "🔍 Filtrer les concepts",
            placeholder="Tapez pour filtrer (ex: 'bloc', 'tachycardie', 'onde')...",
            key="manual_search_filter"
        )
        
        # Grouper par catégorie et sous-groupes
        def group_concepts():
            """Groupe les concepts en hiérarchie"""
            grouped = {
                "🚨 DIAGNOSTICS URGENTS": {
                    "icon": "🚨",
                    "category": "DIAGNOSTIC_URGENT",
                    "concepts": []
                },
                "⚕️ DIAGNOSTICS MAJEURS": {
                    "icon": "⚕️",
                    "category": "DIAGNOSTIC_MAJEUR",
                    "concepts": [],
                    "subgroups": {
                        "Blocs de conduction": [],
                        "Troubles du rythme": [],
                        "Syndromes": [],
                        "Hypertrophies": [],
                        "Autres": []
                    }
                },
                "📊 SIGNES ECG PATHOLOGIQUES": {
                    "icon": "📊",
                    "category": "SIGNE_ECG_PATHOLOGIQUE",
                    "concepts": []
                },
                "📏 DESCRIPTEURS ECG": {
                    "icon": "📏",
                    "category": "DESCRIPTEUR_ECG",
                    "concepts": [],
                    "subgroups": {
                        "Ondes": [],
                        "Segments & Intervalles": [],
                        "Territoires": [],
                        "ESV & Arythmies": [],
                        "Autres": []
                    }
                }
            }
            
            # Remplir les groupes
            for concept in ontology_concepts:
                cat = concept['category']
                name_lower = concept['name'].lower()
                
                # Trouver le groupe principal
                main_group = None
                for group_name, group_data in grouped.items():
                    if group_data['category'] == cat:
                        main_group = group_data
                        break
                
                if not main_group:
                    continue
                
                # Si pas de sous-groupes, ajouter directement
                if 'subgroups' not in main_group:
                    main_group['concepts'].append(concept)
                    continue
                
                # Sinon, classifier dans un sous-groupe
                added = False
                
                if cat == "DIAGNOSTIC_MAJEUR":
                    if 'bloc' in name_lower:
                        main_group['subgroups']['Blocs de conduction'].append(concept)
                        added = True
                    elif any(w in name_lower for w in ['tachycardie', 'bradycardie', 'rythme', 'flutter', 'fibrillation']):
                        main_group['subgroups']['Troubles du rythme'].append(concept)
                        added = True
                    elif 'syndrome' in name_lower:
                        main_group['subgroups']['Syndromes'].append(concept)
                        added = True
                    elif 'hypertrophie' in name_lower:
                        main_group['subgroups']['Hypertrophies'].append(concept)
                        added = True
                
                elif cat == "DESCRIPTEUR_ECG":
                    if 'onde' in name_lower:
                        main_group['subgroups']['Ondes'].append(concept)
                        added = True
                    elif any(w in name_lower for w in ['segment', 'intervalle', 'espace']):
                        main_group['subgroups']['Segments & Intervalles'].append(concept)
                        added = True
                    elif any(w in name_lower for w in ['antérieur', 'postérieur', 'latéral', 'inférieur', 'septal', 'territoire', 'paroi']):
                        main_group['subgroups']['Territoires'].append(concept)
                        added = True
                    elif 'esv' in name_lower or 'extrasystole' in name_lower:
                        main_group['subgroups']['ESV & Arythmies'].append(concept)
                        added = True
                
                # Si non classé, mettre dans "Autres"
                if not added:
                    if 'subgroups' in main_group:
                        main_group['subgroups']['Autres'].append(concept)
                    else:
                        main_group['concepts'].append(concept)
            
            return grouped
        
        grouped_concepts = group_concepts()
        
        # Fonction d'affichage d'un concept
        def display_concept_card(concept, key_prefix, index):
            """Affiche une carte concept avec détails"""
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{concept['name']}**")
                
                # Détails
                details = []
                details.append(f"📁 {concept['category']}")
                
                if concept.get('synonyms'):
                    syn_str = ", ".join(concept['synonyms'][:3])
                    if len(concept['synonyms']) > 3:
                        syn_str += f" (+{len(concept['synonyms']) - 3})"
                    details.append(f"🔤 {syn_str}")
                
                if concept.get('territoires_possibles'):
                    terr_str = ", ".join(concept['territoires_possibles'])
                    details.append(f"🗺️ {terr_str}")
                
                st.caption(" • ".join(details))
            
            with col2:
                add_key = f"add_manual_{key_prefix}_{index}"
                if st.button("➕", key=add_key, use_container_width=True):
                    if concept['name'] not in [a['concept'] for a in st.session_state.case_annotations]:
                        st.session_state.case_annotations.append({
                            'concept': concept['name'],
                            'category': concept['category'],
                            'type': 'expert',
                            'coefficient': 1.0
                        })
                        st.success(f"✅ {concept['name'][:30]}... ajouté!", icon="✅")
                        st.rerun()
        
        # Fonction de filtrage
        def filter_concept(concept, search_text):
            """Vérifie si un concept matche le filtre"""
            if not search_text:
                return True
            
            search_lower = normalize_search(search_text)
            
            # Recherche dans nom
            if search_lower in normalize_search(concept['name']):
                return True
            
            # Recherche dans synonymes
            for syn in concept.get('synonyms', []):
                if search_lower in normalize_search(syn):
                    return True
            
            return False
        
        # Afficher l'arborescence
        st.markdown("---")
        st.markdown("### 🌳 Ontologie ECG Hiérarchique")
        
        for group_name, group_data in grouped_concepts.items():
            icon = group_data['icon']
            
            # Compter les concepts (avec filtre)
            if 'subgroups' in group_data:
                total_concepts = sum(len(concepts) for concepts in group_data['subgroups'].values())
                if search_filter:
                    filtered_total = sum(
                        len([c for c in concepts if filter_concept(c, search_filter)])
                        for concepts in group_data['subgroups'].values()
                    )
                else:
                    filtered_total = total_concepts
            else:
                total_concepts = len(group_data['concepts'])
                if search_filter:
                    filtered_total = len([c for c in group_data['concepts'] if filter_concept(c, search_filter)])
                else:
                    filtered_total = total_concepts
            
            # Afficher seulement si concepts filtrés
            if filtered_total == 0:
                continue
            
            with st.expander(f"{icon} **{group_name}** ({filtered_total}/{total_concepts})", expanded=False):
                if 'subgroups' in group_data:
                    # Afficher avec sous-groupes
                    for subgroup_name, concepts in group_data['subgroups'].items():
                        # Filtrer
                        if search_filter:
                            concepts = [c for c in concepts if filter_concept(c, search_filter)]
                        
                        if len(concepts) == 0:
                            continue
                        
                        st.markdown(f"##### 📁 {subgroup_name} ({len(concepts)})")
                        
                        for idx, concept in enumerate(sorted(concepts, key=lambda x: x['name'])):
                            display_concept_card(concept, f"{group_name}_{subgroup_name}", idx)
                            st.markdown("") # Espacement
                else:
                    # Afficher directement les concepts
                    concepts = group_data['concepts']
                    if search_filter:
                        concepts = [c for c in concepts if filter_concept(c, search_filter)]
                    
                    for idx, concept in enumerate(sorted(concepts, key=lambda x: x['name'])):
                        display_concept_card(concept, group_name, idx)
                        st.markdown("") # Espacement
    
    # Afficher les annotations ajoutées
    if st.session_state.case_annotations:
        st.markdown("---")
        st.markdown(f"**📋 Annotations ajoutées: {len(st.session_state.case_annotations)}**")
        
        for idx, annotation in enumerate(st.session_state.case_annotations):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 1])
            
            with col1:
                st.write(f"**{annotation['concept']}**")
                st.caption(f"Catégorie: {annotation['category']}")
            
            with col2:
                confidence = annotation.get('confidence', 'N/A')
                if confidence != 'N/A':
                    st.write(f"🎯 {confidence}%")
            
            with col3:
                st.write(f"⚖️ {annotation['coefficient']}")
            
            with col4:
                # Déterminer la valeur par défaut selon la catégorie
                category = annotation.get('category', '')
                if category in ['DIAGNOSTIC_URGENT', 'DIAGNOSTIC_MAJEUR']:
                    default_role = "🎯 Diagnostic validant"
                else:
                    default_role = "📝 Description"
                
                # Récupérer le rôle actuel ou utiliser le défaut
                current_role = annotation.get('annotation_role', default_role)
                
                # Sélecteur de rôle
                role = st.selectbox(
                    "Rôle",
                    ["🎯 Diagnostic validant", "📝 Description", "❌ Exclusion"],
                    index=["🎯 Diagnostic validant", "📝 Description", "❌ Exclusion"].index(current_role),
                    key=f"role_{idx}",
                    label_visibility="collapsed"
                )
                
                # Sauvegarder le rôle sélectionné
                st.session_state.case_annotations[idx]['annotation_role'] = role
                
                # Warning si exclusion
                if role == "❌ Exclusion":
                    st.session_state.case_annotations[idx]['is_exclusion'] = True
                else:
                    st.session_state.case_annotations[idx]['is_exclusion'] = False
            
            with col5:
                if st.button("🗑️", key=f"delete_ann_{idx}"):
                    st.session_state.case_annotations.pop(idx)
                    st.rerun()
        
        # 🆕 AFFICHER LES SÉLECTEURS DE TERRITOIRE
        _display_territory_selectors_for_annotations()
        
        # 🆕 AFFICHER LES SÉLECTEURS DE STRUCTURE ANATOMIQUE (échappement, etc.)
        _display_structure_selectors_for_annotations()
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    # Mode édition: navigation différente
    is_editing = 'editing_case' in st.session_state and st.session_state.editing_case
    
    with col1:
        if is_editing:
            # En mode édition, retour à la bibliothèque
            if st.button("◀ Annuler et retourner à la bibliothèque", use_container_width=True):
                st.session_state.editing_case = None
                st.session_state.editing_case_dir = None
                st.session_state.case_edit_loaded = None
                st.session_state.uploaded_images = []
                st.session_state.case_annotations = []
                st.session_state.selected_page = 'cases'  # Retour à la bibliothèque
                st.rerun()
        else:
            # En mode création, retour à l'upload
            if st.button("◀ Retour à l'upload", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
    
    with col2:
        if st.session_state.case_annotations:
            if is_editing:
                # En mode édition, sauvegarder directement
                if st.button("💾 Sauvegarder les modifications", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            else:
                # En mode création, aller à la validation
                if st.button("Valider le cas ▶", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
        else:
            button_label = "💾 Sauvegarder les modifications" if is_editing else "Valider le cas ▶"
            st.button(button_label, disabled=True, use_container_width=True)
            st.caption("⚠️ Ajoutez au moins une annotation")


# =====================================================================
# STEP 3: VALIDATION
# =====================================================================

def step_validation():
    """Étape 3: Validation du cas"""
    st.markdown("### ✅ Étape 3: Valider le cas")
    
    # Résumé du cas
    st.markdown("#### 📊 Résumé du cas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Nom:** {st.session_state.case_name}")
        st.markdown(f"**Catégorie:** {st.session_state.case_category}")
        st.markdown(f"**Difficulté:** {st.session_state.case_difficulty}")
    
    with col2:
        st.markdown(f"**ECG:** {len(st.session_state.uploaded_images)}")
        st.markdown(f"**Annotations:** {len(st.session_state.case_annotations)}")
    
    st.markdown("---")
    st.markdown("**Description:**")
    st.info(st.session_state.case_description or "Aucune description")
    
    # Annotations
    st.markdown("---")
    st.markdown("#### 🏷️ Annotations expertes")
    
    # Interface de classification des diagnostics
    st.markdown("##### 🎯 Classifiez vos diagnostics")
    st.caption("Sélectionnez les diagnostics principaux (ceux qui doivent être impérativement identifiés)")
    # Affichage groupé par rôle
    st.markdown("##### 📋 Liste des annotations")
    
    # Grouper par rôle
    validant_annotations = [ann for ann in st.session_state.case_annotations if ann.get('annotation_role', '📝 Description') == '🎯 Diagnostic validant']
    description_annotations = [ann for ann in st.session_state.case_annotations if ann.get('annotation_role', '📝 Description') == '📝 Description']
    exclusion_annotations = [ann for ann in st.session_state.case_annotations if ann.get('annotation_role', '📝 Description') == '❌ Exclusion']
    
    # Diagnostics validants
    if validant_annotations:
        st.markdown("**🎯 Diagnostics validants** (comptent pour 100% de la note)")
        for annotation in validant_annotations:
            # Vérifier si territoire manquant
            territory_info = ""
            if annotation.get('territoires_possibles'):
                territories = st.session_state.territory_selections.get(annotation['concept'], {}).get('territories', [])
                if territories:
                    territory_info = f" - 🗺️ {', '.join(territories)}"
                else:
                    territory_info = " - ⚠️ Territoire manquant (-50% points)"
            
            st.markdown(f"- ⭐ **{annotation['concept']}** ({annotation['category']}){territory_info}")
    
    # Descriptions
    if description_annotations:
        st.markdown("**📝 Descriptions** (ne comptent pas dans le scoring)")
        for annotation in description_annotations:
            st.markdown(f"- **{annotation['concept']}** ({annotation['category']})")
    
    # Exclusions
    if exclusion_annotations:
        st.error("**❌ EXCLUSIONS** (Note automatique = 0/20)")
        for annotation in exclusion_annotations:
            st.markdown(f"- 🚫 **{annotation['concept']}** - Faute grave")
    
    # ECG
    st.markdown("---")
    st.markdown("#### 📸 ECG")
    
    for img_data in st.session_state.uploaded_images:
        with st.expander(f"📄 {img_data['label']}"):
            st.image(img_data['image'], use_container_width=True)
    
    # Sauvegarder
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("◀ Retour à l'annotation", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    with col2:
        if st.button("💾 Sauvegarder le cas", type="primary", use_container_width=True):
            # Mode édition: réutiliser le case_id et le dossier existant
            if 'editing_case' in st.session_state and st.session_state.editing_case:
                case_id = st.session_state.editing_case.get('case_id')
                case_dir = Path(st.session_state.editing_case_dir)
                is_editing = True
            else:
                # Nouveau cas: générer un nouvel ID
                case_id = generate_case_id()
                is_editing = False
            
            # 🆕 FILTRER LES ANNOTATIONS PAR RÔLE
            # Seuls les diagnostics validants comptent dans expected_concepts
            validant_annotations = [
                ann for ann in st.session_state.case_annotations 
                if ann.get('annotation_role', '📝 Description') == '🎯 Diagnostic validant'
            ]
            
            exclusion_annotations = [
                ann for ann in st.session_state.case_annotations 
                if ann.get('annotation_role', '📝 Description') == '❌ Exclusion'
            ]
            
            # expected_concepts = UNIQUEMENT les diagnostics validants
            expected_concepts = [ann['concept'] for ann in validant_annotations]
            
            # Vérifier s'il y a des exclusions
            has_exclusions = len(exclusion_annotations) > 0
            
            # Déterminer le diagnostic principal pour l'affichage
            diagnostic_principal = st.session_state.case_name
            
            if validant_annotations:
                diagnostic_principal = validant_annotations[0]['concept']
            elif st.session_state.case_annotations:
                # Fallback: prendre le concept avec le plus grand coefficient
                main_annotation = max(st.session_state.case_annotations, key=lambda x: x.get('coefficient', 1))
                diagnostic_principal = main_annotation['concept']
            
            case_data = {
                'case_id': case_id,
                'name': st.session_state.case_name,
                'category': st.session_state.case_category,
                'difficulty': st.session_state.case_difficulty,
                'description': st.session_state.case_description,
                'annotations': st.session_state.case_annotations,  # Inclut annotation_role
                'expected_concepts': expected_concepts,  # 🆕 UNIQUEMENT les diagnostics validants
                'has_exclusions': has_exclusions,  # 🆕 Flag d'exclusion
                'diagnostic_principal': diagnostic_principal,  # 🆕 Pour affichage
                'clinical_context': st.session_state.case_description,  # 🆕 Alias
                'num_ecg': len(st.session_state.uploaded_images),
                'created_date': datetime.now().isoformat(),
                'type': 'multi_ecg' if len(st.session_state.uploaded_images) > 1 else 'simple',
                'territory_selections': st.session_state.get('territory_selections', {}),  # 🆕 TERRITOIRES
                'metadata': {
                    'created_by': 'ecg_session_builder',
                    'version': '1.0'
                }
            }
            
            # Sauvegarder
            case_dir = save_case_to_disk(case_data, st.session_state.uploaded_images)
            
            # Message de succès différent selon le mode
            if is_editing:
                st.success(f"✅ Cas mis à jour: {case_id}")
                st.info(f"📁 Dossier: {case_dir}")
                
                # Reset du mode édition
                st.session_state.editing_case = None
                st.session_state.editing_case_dir = None
                st.session_state.case_edit_loaded = None
                st.session_state.uploaded_images = []
                st.session_state.case_annotations = []
                st.session_state.case_name = ''
                st.session_state.case_description = ''
                
                # Auto-redirection vers la bibliothèque après 2 secondes
                st.info("🔄 Redirection vers la bibliothèque...")
                import time
                time.sleep(2)
                st.session_state.selected_page = 'cases'
                st.rerun()
            else:
                # Stocker dans session state pour la création de session
                if 'validated_cases' not in st.session_state:
                    st.session_state.validated_cases = []
                
                st.session_state.validated_cases.append(case_data)
                
                st.success(f"✅ Cas sauvegardé: {case_id}")
                st.info(f"📁 Dossier: {case_dir}")
                
                # Reset pour un nouveau cas
                st.session_state.uploaded_images = []
                st.session_state.case_annotations = []
                st.session_state.case_name = ''
                st.session_state.case_description = ''
                
                st.session_state.current_step = 4
            
            st.rerun()


# =====================================================================
# STEP 4: CREATE SESSION
# =====================================================================

def step_create_session():
    """Étape 4: Créer une session"""
    st.markdown("### 📚 Étape 4: Créer une session de formation")
    
    if 'validated_cases' not in st.session_state or not st.session_state.validated_cases:
        st.warning("⚠️ Aucun cas validé. Créez d'abord au moins un cas.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Créer un nouveau cas", type="primary", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
        with col2:
            if st.button("🏠 Retour à l'accueil", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
        
        return
    
    # Afficher les cas validés
    st.markdown(f"**📋 Cas validés: {len(st.session_state.validated_cases)}**")
    
    for case in st.session_state.validated_cases:
        with st.expander(f"📄 {case['name']}"):
            st.write(f"**ID:** {case['case_id']}")
            st.write(f"**Catégorie:** {case['category']}")
            st.write(f"**Difficulté:** {case['difficulty']}")
            st.write(f"**Annotations:** {len(case['annotations'])}")
    
    st.markdown("---")
    st.markdown("#### 🎓 Créer la session")
    
    session_name = st.text_input(
        "Nom de la session",
        placeholder="Ex: Troubles du Rythme - Niveau 1",
        key="session_name_input"
    )
    
    session_description = st.text_area(
        "Description de la session",
        placeholder="Objectifs pédagogiques de la session...",
        height=100,
        key="session_description_area"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        session_difficulty = st.selectbox(
            "Difficulté globale",
            ["🟢 Débutant", "🟡 Intermédiaire", "🔴 Avancé"],
            key="session_difficulty_select"
        )
    
    with col2:
        time_limit = st.number_input(
            "Temps limite (minutes)",
            min_value=5,
            max_value=180,
            value=30,
            key="session_time_limit"
        )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("◀ Créer un autre cas", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    with col2:
        if st.button("💾 Sauvegarder sans session", use_container_width=True):
            st.success("✅ Cas sauvegardés!")
            st.session_state.validated_cases = []
            st.session_state.current_step = 1
            st.rerun()
    
    with col3:
        if session_name and st.button("🚀 Créer la session", type="primary", use_container_width=True):
            session_id = create_session_from_cases(
                session_name=session_name,
                description=session_description,
                difficulty=session_difficulty,
                cases=st.session_state.validated_cases,
                time_limit=time_limit
            )
            
            st.success(f"✅ Session créée: {session_id}")
            st.balloons()
            
            # Reset
            st.session_state.validated_cases = []
            st.session_state.current_step = 1
            
            st.info("🎉 La session est maintenant disponible pour les étudiants!")
            
            if st.button("🏠 Retour à l'accueil"):
                st.rerun()


# =====================================================================
# MAIN INTERFACE
# =====================================================================

def page_ecg_import():
    """Interface principale du Session Builder - Page Import ECG"""
    
    st.title("🎓 ECG Session Builder")
    st.markdown("*Créez des sessions de formation complètes en important et annotant vos ECG*")
    
    # ✏️ MODE ÉDITION: Charger un cas existant
    is_editing_mode = ('editing_case' in st.session_state and 
                       st.session_state.editing_case is not None and
                       st.session_state.editing_case != {})
    
    if is_editing_mode:
        st.info("✏️ **Mode Édition** - Modification d'un cas existant")
        
        case_data = st.session_state.editing_case
        case_dir = Path(st.session_state.editing_case_dir)
        
        # Afficher un résumé du cas en cours d'édition
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nom du cas", case_data.get('name', 'N/A'))
        with col2:
            st.metric("Catégorie", case_data.get('category', 'N/A'))
        with col3:
            st.metric("Annotations", len(case_data.get('annotations', [])))
        
        # Charger les données dans session_state (une seule fois)
        if 'case_edit_loaded' not in st.session_state:
            st.session_state.case_name = case_data.get('name', '')
            st.session_state.case_category = case_data.get('category', 'Troubles du Rythme')
            st.session_state.case_difficulty = case_data.get('difficulty', '🟡 Intermédiaire')
            st.session_state.case_description = case_data.get('description', '')
            st.session_state.case_annotations = case_data.get('annotations', [])
            st.session_state.territory_selections = case_data.get('territory_selections', {})
            
            # S'assurer que toutes les annotations ont un annotation_role
            for ann in st.session_state.case_annotations:
                if 'annotation_role' not in ann:
                    # Définir par défaut selon la catégorie
                    if ann.get('category') in ['DIAGNOSTIC_URGENT', 'DIAGNOSTIC_MAJEUR']:
                        ann['annotation_role'] = '🎯 Diagnostic validant'
                    else:
                        ann['annotation_role'] = '📝 Description'
            
            # Charger les images ECG
            uploaded_images = []
            ecg_files = case_data.get('ecgs', [])
            
            for ecg_file in ecg_files:
                img_path = case_dir / ecg_file['filename']
                if img_path.exists():
                    try:
                        image = Image.open(img_path)
                        uploaded_images.append({
                            'image': image,
                            'filename': ecg_file['filename'],
                            'label': ecg_file.get('label', f"ECG_{ecg_file['index']}")
                        })
                    except Exception as e:
                        st.error(f"❌ Erreur chargement image: {e}")
            
            st.session_state.uploaded_images = uploaded_images
            st.session_state.case_edit_loaded = True
            st.success(f"✅ {len(uploaded_images)} ECG chargé(s) depuis le cas existant")
        
        # Afficher un aperçu des ECG chargés
        if st.session_state.get('uploaded_images'):
            with st.expander("📷 Aperçu des ECG chargés", expanded=False):
                for img_data in st.session_state.uploaded_images:
                    st.image(img_data['image'], caption=img_data.get('label', 'ECG'), use_container_width=True)
        
        # Bouton pour annuler l'édition
        if st.button("❌ Annuler l'édition et retourner à la bibliothèque"):
            st.session_state.editing_case = None
            st.session_state.editing_case_dir = None
            st.session_state.case_edit_loaded = None
            st.session_state.current_step = 1
            st.session_state.uploaded_images = []
            st.session_state.case_annotations = []
            st.rerun()
        
        st.markdown("---")
    
    # Initialiser l'étape
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # MODE ÉDITION: Affichage séparé sans workflow d'import
    if is_editing_mode:
        # Pas de barre de progression en mode édition
        # Afficher directement l'interface d'édition
        step_annotation()
        return  # Sortir de la fonction pour ne pas afficher le workflow normal
    
    # WORKFLOW NORMAL: Barre de progression
    progress_steps = ["📤 Upload", "🏷️ Annotation", "✅ Validation", "📚 Session"]
    
    cols = st.columns(4)
    for idx, (col, step_name) in enumerate(zip(cols, progress_steps), start=1):
        with col:
            if idx == st.session_state.current_step:
                st.markdown(f"**:blue[{step_name}]**")
            elif idx < st.session_state.current_step:
                st.markdown(f"~~{step_name}~~ ✅")
            else:
                st.markdown(f":gray[{step_name}]")
    
    st.markdown("---")
    
    # Afficher l'étape courante
    if st.session_state.current_step == 1:
        step_upload_ecg()
    elif st.session_state.current_step == 2:
        step_annotation()
    elif st.session_state.current_step == 3:
        step_validation()
    elif st.session_state.current_step == 4:
        step_create_session()
    
    # Sidebar: Stats
    with st.sidebar:
        st.markdown("### 📊 Statistiques")
        
        # Compter les cas existants
        if ECG_CASES_DIR.exists():
            case_folders = [d for d in ECG_CASES_DIR.iterdir() if d.is_dir()]
            st.metric("📁 Total Cas", len(case_folders))
        
        # Compter les sessions existantes
        if ECG_SESSIONS_DIR.exists():
            session_files = list(ECG_SESSIONS_DIR.glob("*.json"))
            st.metric("📚 Total Sessions", len(session_files))
        
        st.markdown("---")
        
        # Cache LLM stats
        try:
            llm_stats = get_llm_stats()
            if llm_stats and 'cache_stats' in llm_stats:
                cache_stats = llm_stats['cache_stats']
                st.markdown("### 🚀 Cache LLM")
                st.metric("Hit Rate", f"{cache_stats.get('hit_rate_percent', 0):.1f}%")
                st.metric("Hits", cache_stats.get('hits', 0))
                st.metric("Misses", cache_stats.get('misses', 0))
        except:
            pass


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    page_ecg_import()
