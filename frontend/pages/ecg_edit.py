"""
✏️ ECG Case Editor - Interface d'édition standalone
Interface dédiée pour éditer les cas ECG existants

Author: BMad Team
Date: 2026-01-14
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "frontend"))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from unidecode import unidecode
import json
from datetime import datetime
from PIL import Image
import shutil

from backend.services.llm_semantic_matcher import get_llm_stats
from backend.services.llm_service import LLMService
from backend.services.concept_decomposer import create_decomposer
from backend.territory_resolver import get_territory_config, resolve_territories
from components.territory_selector_ui import render_territory_selectors, check_territory_completeness

# Configuration
ECG_CASES_DIR = Path("data/ecg_cases")
ONTOLOGY_PATH = Path("data/ontology_from_owl.json")


def load_ontology():
    """Charge l'ontologie ECG"""
    try:
        with open(ONTOLOGY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning("⚠️ Ontologie non trouvée")
        return {}


def normalize_search(text):
    """Normalise le texte pour la recherche"""
    return unidecode(text.lower())


def get_ontology_concepts():
    """Récupère tous les concepts de l'ontologie avec synonymes"""
    ontology = load_ontology()
    concepts = []
    
    if 'concept_mappings' in ontology:
        for concept_id, concept_data in ontology['concept_mappings'].items():
            if isinstance(concept_data, dict):
                concept_name = concept_data.get('concept_name', '')
                if concept_name and not concept_name.startswith('Localisation'):
                    concepts.append({
                        'name': concept_name,
                        'category': concept_data.get('categorie', concept_data.get('category', 'AUTRE')),
                        'ontology_id': concept_id,
                        'synonyms': concept_data.get('synonymes', concept_data.get('synonyms', [])),
                        'territoires_possibles': concept_data.get('territoires_possibles', [])
                    })
    
    return concepts


def save_case_to_disk(case_data, images, case_dir):
    """Sauvegarde un cas ECG sur le disque"""
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder les images
    ecg_files = []
    for idx, img_data in enumerate(images):
        img_filename = f"ecg_{idx + 1}.png"
        img_path = case_dir / img_filename
        img_data['image'].save(img_path)
        
        ecg_files.append({
            'filename': img_filename,
            'index': idx + 1,
            'type': 'image/png',
            'label': img_data.get('label', f"ECG_{idx + 1}")
        })
    
    case_data['ecgs'] = ecg_files
    case_data['num_ecg'] = len(ecg_files)
    
    # Sauvegarder les métadonnées
    metadata_path = case_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)
    
    return case_dir


def _display_territory_selectors_for_annotations():
    """Affiche les sélecteurs de territoire pour les annotations qui en ont besoin"""
    if 'edit_annotations' not in st.session_state or not st.session_state.edit_annotations:
        return
    
    if 'edit_territory_selections' not in st.session_state:
        st.session_state.edit_territory_selections = {}
    
    ontology = load_ontology()
    if not ontology:
        return
    
    concepts_with_territory = []
    for annotation in st.session_state.edit_annotations:
        concept_name = annotation['concept']
        config = get_territory_config(concept_name, ontology)
        if config and config['show_territory_selector']:
            concepts_with_territory.append((concept_name, config))
    
    if concepts_with_territory:
        st.markdown("---")
        st.markdown("### 🗺️ Précision des Territoires")
        st.success(f"📍 {len(concepts_with_territory)} concept(s) nécessitent une précision de territoire")
        
        for concept_name, config in concepts_with_territory:
            with st.expander(f"🗺️ {concept_name}", expanded=True):
                importance = config.get('importance', 'optionnelle')
                importance_emoji = {'critique': '🔴', 'importante': '🟠', 'optionnelle': '🟢'}
                emoji = importance_emoji.get(importance, '⚪')
                
                st.caption(f"{emoji} Importance: **{importance}**")
                
                territories, mirrors = render_territory_selectors(
                    concept_name,
                    ontology,
                    key_prefix=f"ecg_edit_{concept_name.replace(' ', '_')}"
                )
                
                is_complete, error_msg = check_territory_completeness(
                    concept_name,
                    territories,
                    ontology
                )
                
                if not is_complete:
                    st.warning(error_msg)
                else:
                    if territories:
                        territory_str = ", ".join(territories)
                        mirror_str = f" + {', '.join(mirrors)}" if mirrors else ""
                        st.success(f"✅ Territoire: {territory_str}{mirror_str}")
                
                st.session_state.edit_territory_selections[concept_name] = {
                    'territories': territories,
                    'mirrors': mirrors,
                    'importance': importance
                }


def _display_structure_selectors_for_annotations_edit():
    """Affiche les sélecteurs de structure anatomique pour échappement ventriculaire (mode édition)"""
    if 'edit_annotations' not in st.session_state or not st.session_state.edit_annotations:
        return
    
    # Initialiser structure_selections si nécessaire
    if 'edit_structure_selections' not in st.session_state:
        st.session_state.edit_structure_selections = {}
    
    # Charger l'ontologie
    ontology = load_ontology()
    if not ontology:
        return
    
    concept_mappings = ontology.get('concept_mappings', {})
    
    # Vérifier quels concepts nécessitent une structure anatomique
    concepts_with_structure = []
    for annotation in st.session_state.edit_annotations:
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
                        key_prefix=f"ecg_edit_{concept_name.replace(' ', '_')}",
                        auto_add_morphology=True
                    )
                    
                    if result:
                        # Stocker dans session_state
                        st.session_state.edit_structure_selections[concept_name] = {
                            'structure': result['selected_structure'],
                            'morphology': result['calculated_morphology'],
                            'explanation': result['explanation']
                        }
                        
                        # Ajouter automatiquement la morphologie aux annotations
                        if result['calculated_morphology']:
                            # Vérifier si la morphologie n'est pas déjà dans les annotations
                            morphology_exists = any(
                                ann['concept'] == result['calculated_morphology']
                                for ann in st.session_state.edit_annotations
                            )
                            
                            if not morphology_exists:
                                st.info(f"💡 Annotation auto-ajoutée: **{result['calculated_morphology']}**")
                                # Ajouter à la session pour sauvegarde
                                if st.button(
                                    f"➕ Ajouter '{result['calculated_morphology']}'",
                                    key=f"add_morpho_edit_{concept_name.replace(' ', '_')}"
                                ):
                                    st.session_state.edit_annotations.append({
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
                            key=f"fallback_structure_edit_{concept_name.replace(' ', '_')}"
                        )
                        st.session_state.edit_structure_selections[concept_name] = {
                            'structure': selected,
                            'morphology': None,
                            'explanation': None
                        }


def page_ecg_edit():
    """Interface d'édition standalone pour les cas ECG"""
    
    st.title("✏️ Édition de Cas ECG")
    st.markdown("*Modifiez les informations et annotations d'un cas existant*")
    
    # Vérifier si un cas est sélectionné pour édition
    if 'editing_case_id' not in st.session_state or not st.session_state.editing_case_id:
        st.error("❌ Aucun cas sélectionné pour édition")
        st.info("💡 Retournez à la bibliothèque de cas et cliquez sur 'Éditer'")
        
        if st.button("📚 Retour à la bibliothèque"):
            st.session_state.selected_page = 'cases'
            st.rerun()
        return
    
    case_id = st.session_state.editing_case_id
    case_dir = ECG_CASES_DIR / case_id
    metadata_file = case_dir / "metadata.json"
    
    # Charger les métadonnées
    if not metadata_file.exists():
        st.error(f"❌ Cas introuvable: {case_id}")
        if st.button("📚 Retour à la bibliothèque"):
            st.session_state.editing_case_id = None
            st.session_state.selected_page = 'cases'
            st.rerun()
        return
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
    except Exception as e:
        st.error(f"❌ Erreur de chargement: {e}")
        return
    
    # Charger les données une seule fois
    if 'edit_loaded' not in st.session_state or st.session_state.edit_loaded != case_id:
        st.session_state.edit_name = case_data.get('name', '')
        st.session_state.edit_category = case_data.get('category', 'Troubles du Rythme')
        st.session_state.edit_difficulty = case_data.get('difficulty', '🟡 Intermédiaire')
        st.session_state.edit_description = case_data.get('description', '')
        st.session_state.edit_annotations = case_data.get('annotations', [])
        st.session_state.edit_territory_selections = case_data.get('territory_selections', {})
        
        # Charger les images
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
        
        st.session_state.edit_images = uploaded_images
        st.session_state.edit_loaded = case_id
    
    # En-tête avec résumé
    st.info(f"📝 **Modification du cas:** {case_data.get('name', case_id)}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ID du cas", case_id[:20] + "...")
    with col2:
        st.metric("ECG", len(st.session_state.edit_images))
    with col3:
        st.metric("Annotations", len(st.session_state.edit_annotations))
    
    st.markdown("---")
    
    # Afficher les ECG
    st.markdown("#### 📷 ECG du cas")
    
    if len(st.session_state.edit_images) == 1:
        ecg_data = st.session_state.edit_images[0]
        st.image(ecg_data['image'], caption=ecg_data.get('label', 'ECG'), use_container_width=True)
    else:
        tab_labels = [img_data.get('label', f"ECG {i+1}") for i, img_data in enumerate(st.session_state.edit_images)]
        tabs = st.tabs(tab_labels)
        
        for tab, img_data in zip(tabs, st.session_state.edit_images):
            with tab:
                st.image(img_data['image'], use_container_width=True)
    
    st.markdown("---")
    
    # Informations du cas
    st.markdown("#### 📋 Informations du cas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_name = st.text_input(
            "Nom du cas",
            value=st.session_state.edit_name,
            placeholder="Ex: BAV 2 Mobitz 1",
            key="edit_case_name_input"
        )
        st.session_state.edit_name = case_name
        
        case_category = st.selectbox(
            "Catégorie",
            ["Troubles du Rythme", "Infarctus", "Bloc de Conduction", "Hypertrophie", "Normal", "Autre"],
            index=["Troubles du Rythme", "Infarctus", "Bloc de Conduction", "Hypertrophie", "Normal", "Autre"].index(st.session_state.edit_category) if st.session_state.edit_category in ["Troubles du Rythme", "Infarctus", "Bloc de Conduction", "Hypertrophie", "Normal", "Autre"] else 0,
            key="edit_case_category_select"
        )
        st.session_state.edit_category = case_category
    
    with col2:
        case_difficulty = st.select_slider(
            "Difficulté",
            options=["🟢 Débutant", "🟡 Intermédiaire", "🟠 Avancé", "🔴 Expert"],
            value=st.session_state.edit_difficulty if st.session_state.edit_difficulty in ["🟢 Débutant", "🟡 Intermédiaire", "🟠 Avancé", "🔴 Expert"] else "🟡 Intermédiaire",
            key="edit_case_difficulty_slider"
        )
        st.session_state.edit_difficulty = case_difficulty
        
        case_description = st.text_area(
            "Description clinique",
            value=st.session_state.edit_description,
            placeholder="Contexte clinique du patient...",
            height=100,
            key="edit_case_description_area"
        )
        st.session_state.edit_description = case_description
    
    st.markdown("---")
    
    # Annotations
    st.markdown("#### 🏷️ Annotations expertes")
    
    # Mode d'ajout rapide
    with st.expander("➕ Ajouter une nouvelle annotation", expanded=False):
        ontology_concepts = get_ontology_concepts()
        
        search_term = st.text_input(
            "🔍 Rechercher un concept",
            placeholder="Ex: BAV, mobitz, STEMI...",
            key="edit_search_concept"
        )
        
        if search_term and len(search_term) >= 2:
            search_words = [normalize_search(word) for word in search_term.split() if len(word) >= 2]
            
            if search_words:
                matching_concepts = []
                for c in ontology_concepts:
                    search_text = normalize_search(c['name'])
                    for syn in c.get('synonyms', []):
                        search_text += " " + normalize_search(syn)
                    
                    if all(word in search_text for word in search_words):
                        matching_concepts.append(c)
                
                if matching_concepts:
                    st.success(f"✅ {len(matching_concepts)} concepts trouvés")
                    
                    for idx, concept in enumerate(matching_concepts[:10]):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{concept['name']}**")
                            st.caption(f"Catégorie: {concept['category']}")
                        
                        with col2:
                            if st.button("➕", key=f"edit_add_{idx}_{concept['ontology_id']}"):
                                if concept['name'] not in [a['concept'] for a in st.session_state.edit_annotations]:
                                    st.session_state.edit_annotations.append({
                                        'concept': concept['name'],
                                        'category': concept['category'],
                                        'type': 'expert',
                                        'coefficient': 1.0
                                    })
                                    st.success(f"✅ {concept['name']} ajouté!")
                                    st.rerun()
    
    # Liste des annotations
    if st.session_state.edit_annotations:
        st.markdown(f"**📋 {len(st.session_state.edit_annotations)} annotation(s)**")
        
        for idx, annotation in enumerate(st.session_state.edit_annotations):
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                st.write(f"**{annotation['concept']}**")
                st.caption(f"Catégorie: {annotation['category']}")
            
            with col2:
                st.write(f"⚖️ {annotation['coefficient']}")
            
            with col3:
                if st.button("🗑️", key=f"edit_delete_ann_{idx}"):
                    st.session_state.edit_annotations.pop(idx)
                    st.rerun()
        
        # Sélecteurs de territoire
        _display_territory_selectors_for_annotations()
        
        # 🆕 Sélecteurs de structure anatomique (échappement, etc.)
        _display_structure_selectors_for_annotations_edit()
    else:
        st.warning("⚠️ Aucune annotation. Ajoutez au moins un concept.")
    
    # Actions
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Annuler et retourner à la bibliothèque", use_container_width=True):
            st.session_state.editing_case_id = None
            st.session_state.edit_loaded = None
            st.session_state.selected_page = 'cases'
            st.rerun()
    
    with col2:
        if st.session_state.edit_annotations and st.button("💾 Sauvegarder les modifications", type="primary", use_container_width=True):
            # Mise à jour des métadonnées
            expected_concepts = [ann['concept'] for ann in st.session_state.edit_annotations]
            
            diagnostic_principal = st.session_state.edit_name
            if st.session_state.edit_annotations:
                main_annotation = max(st.session_state.edit_annotations, key=lambda x: x.get('coefficient', 1))
                diagnostic_principal = main_annotation['concept']
            
            updated_case_data = {
                'case_id': case_id,
                'name': st.session_state.edit_name,
                'category': st.session_state.edit_category,
                'difficulty': st.session_state.edit_difficulty,
                'description': st.session_state.edit_description,
                'annotations': st.session_state.edit_annotations,
                'expected_concepts': expected_concepts,
                'diagnostic_principal': diagnostic_principal,
                'clinical_context': st.session_state.edit_description,
                'num_ecg': len(st.session_state.edit_images),
                'created_date': case_data.get('created_date', datetime.now().isoformat()),
                'modified_date': datetime.now().isoformat(),
                'type': 'multi_ecg' if len(st.session_state.edit_images) > 1 else 'simple',
                'territory_selections': st.session_state.edit_territory_selections,
                'metadata': {
                    'created_by': case_data.get('metadata', {}).get('created_by', 'ecg_session_builder'),
                    'version': '1.0',
                    'last_modified': datetime.now().isoformat()
                }
            }
            
            # Sauvegarder
            save_case_to_disk(updated_case_data, st.session_state.edit_images, case_dir)
            
            st.success(f"✅ Cas mis à jour avec succès!")
            st.info("🔄 Redirection vers la bibliothèque...")
            
            # Nettoyage
            st.session_state.editing_case_id = None
            st.session_state.edit_loaded = None
            st.session_state.selected_page = 'cases'
            
            import time
            time.sleep(1.5)
            st.rerun()


if __name__ == "__main__":
    page_ecg_edit()
