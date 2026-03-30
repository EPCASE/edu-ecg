#!/usr/bin/env python3
"""
Version simplifiée de l'Import Intelligent ECG
Interface linéaire plus intuitive sans onglets
"""

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw
import base64
import json
import os
from pathlib import Path
import io
import uuid
from datetime import datetime
import sys

# Ajouter backend au path pour imports LLM
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

# Import services LLM pour validation automatique
try:
    from backend.services.llm_service import LLMService
    from backend.scoring_service_llm import SemanticScorer
    from backend.feedback_service import FeedbackService
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    llm_import_error = str(e)

def smart_ecg_importer_simple():
    """Interface d'import ECG simplifiée et linéaire avec support multi-ECG"""
    
    st.header("📥 Import ECG Intelligent")
    
    # Sélection du mode d'import
    st.markdown("### 🎯 Choisir le Mode d'Import")
    
    mode_col1, mode_col2, mode_col3 = st.columns(3)
    
    with mode_col1:
        if st.button("⚡ Recherche Rapide", type="primary", use_container_width=True):
            st.session_state.import_mode = 'quick'
            st.rerun()
        st.caption("Import ultra-rapide sans annotation")
    
    with mode_col2:
        if st.button("🤖 Mode IA (Auto)", type="primary", use_container_width=True):
            st.session_state.import_mode = 'ai'
            st.rerun()
        st.caption("Validation automatique avec LLM")
    
    with mode_col3:
        if st.button("✍️ Mode Manuel", type="primary", use_container_width=True):
            st.session_state.import_mode = 'manual'
            st.rerun()
        st.caption("Annotation manuelle avec tags")
    
    st.markdown("---")
    
    # Initialiser le mode par défaut
    if 'import_mode' not in st.session_state:
        st.session_state.import_mode = 'ai'
    
    # Afficher le mode actuel
    mode_icons = {'quick': '⚡', 'ai': '🤖', 'manual': '✍️'}
    mode_names = {'quick': 'Recherche Rapide', 'ai': 'Mode IA', 'manual': 'Mode Manuel'}
    
    st.info(f"{mode_icons[st.session_state.import_mode]} **Mode actif:** {mode_names[st.session_state.import_mode]}")
    
    # Workflow selon le mode
    import_multiple_workflow()


def import_multiple_workflow():
    """Workflow d'import multiple - plusieurs ECG pour un cas"""
    
    # État de session pour l'import multiple
    if 'multi_case' not in st.session_state:
        st.session_state.multi_case = None
    if 'multi_ecgs' not in st.session_state:
        st.session_state.multi_ecgs = []
    
    # Interface de debug et reset en cas de problème
    with st.expander("🔧 Debug & Reset (si problème)", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**État actuel:**")
            if st.session_state.multi_case:
                st.write(f"- Cas: {st.session_state.multi_case['name']}")
            else:
                st.write("- Cas: Aucun")
            st.write(f"- ECG: {len(st.session_state.multi_ecgs)}")
        
        with col2:
            if st.button("🗑️ Reset complet", type="secondary"):
                st.session_state.multi_case = None
                st.session_state.multi_ecgs = []
                st.success("✅ Réinitialisé !")
                st.rerun()
        
        with col3:
            if st.button("🔄 Rafraîchir page", type="secondary"):
                st.rerun()
    
    if st.session_state.multi_case is None:
        # Étape 1 : Création du cas
        create_multi_case_interface()
    else:
        # Étape 2 : Gestion progressive des ECG
        st.markdown(f"### 📋 Cas : **{st.session_state.multi_case['name']}**")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**ECG ajoutés :** {len(st.session_state.multi_ecgs)}")
        with col2:
            if st.button("🔄 Nouveau Cas", type="secondary"):
                if st.session_state.multi_ecgs:
                    st.warning("⚠️ Vous avez des ECG non sauvegardés !")
                    if st.button("✅ Confirmer nouveau cas"):
                        st.session_state.multi_case = None
                        st.session_state.multi_ecgs = []
                        st.rerun()
                else:
                    st.session_state.multi_case = None
                    st.session_state.multi_ecgs = []
                    st.rerun()
        
        # Tabs pour les actions
        tabs = st.tabs(["📥 Ajouter ECG", "✂️ Recadrer ECG", "👁️ Aperçu Final", "✅ Sauvegarder"])
        
        with tabs[0]:
            add_ecg_to_multi_case()
        
        with tabs[1]:
            crop_multi_ecg_interface()
        
        with tabs[2]:
            preview_multi_case()
        
        with tabs[3]:
            save_multi_case()

def create_multi_case_interface():
    """Interface de création d'un nouveau cas multi-ECG"""
    
    st.markdown("### 📋 Créer un Nouveau Cas ECG")
    
    with st.form("create_multi_case"):
        case_name = st.text_input("📝 Nom du cas", placeholder="Ex: Infarctus Antérieur - Patient 45 ans")
        
        col1, col2 = st.columns(2)
        with col1:
            case_category = st.selectbox("📂 Catégorie", [
                "Infarctus", "Arythmie", "Bloc de branche", "Normal", 
                "Péricardite", "Embolie pulmonaire", "Autre"
            ])
        
        with col2:
            case_difficulty = st.selectbox("🎯 Niveau", [
                "Débutant", "Intermédiaire", "Avancé", "Expert"
            ])
        
        case_description = st.text_area("📖 Description clinique", 
                                       placeholder="Contexte du patient, histoire clinique...")
        
        submitted = st.form_submit_button("✅ Créer le Cas", type="primary")
        
        if submitted:
            if case_name:
                st.session_state.multi_case = {
                    'name': case_name,
                    'category': case_category,
                    'difficulty': case_difficulty,
                    'description': case_description,
                    'created_date': datetime.now().isoformat(),
                    'case_id': f"multi_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
                }
                st.success(f"✅ Cas '{case_name}' créé !")
                st.rerun()
            else:
                st.error("❌ Le nom du cas est obligatoire")

def add_ecg_to_multi_case():
    """Ajouter un ECG au cas en cours"""
    
    st.markdown("### 📥 Ajouter un ECG au Cas")
    
    if len(st.session_state.multi_ecgs) > 0:
        st.info(f"📊 **{len(st.session_state.multi_ecgs)} ECG** déjà ajoutés à ce cas")
    
    uploaded_file = st.file_uploader(
        f"Sélectionnez l'ECG #{len(st.session_state.multi_ecgs) + 1}",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        key=f"upload_ecg_{len(st.session_state.multi_ecgs)}",
        help="Formats supportés : PDF, PNG, JPG, JPEG"
    )
    
    if uploaded_file is not None:
        # Traitement du fichier
        success, file_data = process_uploaded_file(uploaded_file)
        if success and file_data:
            with st.form("ecg_metadata"):
                col1, col2 = st.columns(2)
                with col1:
                    ecg_label = st.text_input("🏷️ Libellé", 
                        value=f"ECG_{len(st.session_state.multi_ecgs) + 1}",
                        placeholder="Ex: ECG_Initial, ECG_Post_Traitement")
                with col2:
                    ecg_timing = st.selectbox("⏰ Timing", [
                        "Initial", "Contrôle", "Post-traitement", "Suivi", 
                        "Admission", "Sortie", "J+1", "Autre"
                    ])
                ecg_notes = st.text_area("📝 Notes", 
                    placeholder="Notes particulières pour cet ECG...")

                col1, col2 = st.columns(2)
                with col1:
                    add_direct = st.form_submit_button("✅ Ajouter Direct", type="primary")
                with col2:
                    add_with_crop = st.form_submit_button("✂️ Ajouter + Recadrer", type="secondary")

                if add_direct or add_with_crop:
                    if ecg_label:
                        ecg_data = {
                            'file_data': file_data,
                            'label': ecg_label,
                            'timing': ecg_timing,
                            'notes': ecg_notes,
                            'annotations': [],  # annotation à faire après
                            'filename': uploaded_file.name,
                            'added_date': datetime.now().isoformat(),
                            'needs_crop': add_with_crop,
                            'cropped': False
                        }
                        st.session_state.multi_ecgs.append(ecg_data)
                        st.session_state.pending_annotation_idx = len(st.session_state.multi_ecgs) - 1
                        st.success(f"✅ ECG '{ecg_label}' ajouté au cas !")
                        if add_with_crop:
                            st.info("💡 Passez à l'onglet 'Recadrer ECG' pour traiter cet ECG")
                        st.rerun()
                    else:
                        st.error("❌ Le libellé est obligatoire")

    # Affichage du module de validation LLM après ajout
    if 'pending_annotation_idx' in st.session_state:
        idx = st.session_state['pending_annotation_idx']
        if 0 <= idx < len(st.session_state.multi_ecgs):
            ecg = st.session_state.multi_ecgs[idx]
            
            # Mode Recherche Rapide: pas d'annotation
            if st.session_state.get('import_mode') == 'quick':
                st.markdown(f"### ⚡ Mode Recherche Rapide - ECG : **{ecg['label']}**")
                st.info("✅ En mode recherche rapide, l'ECG est enregistré sans annotation")
                
                if st.button("✅ Continuer (sans annotation)", key=f"quick_continue_{idx}", type="primary"):
                    st.session_state.multi_ecgs[idx]['annotations'] = []
                    st.session_state.multi_ecgs[idx]['expected_concepts'] = []
                    st.session_state.multi_ecgs[idx]['teacher_correction_text'] = ""
                    st.session_state.multi_ecgs[idx]['mode'] = 'quick'
                    del st.session_state['pending_annotation_idx']
                    st.success("✅ ECG enregistré en mode rapide!")
                    st.rerun()
                return
            
            # Mode Manuel: annotation avec tags
            if st.session_state.get('import_mode') == 'manual':
                st.markdown(f"### ✍️ Mode Manuel - ECG : **{ecg['label']}**")
                st.info("📝 Annotez manuellement avec des tags (concepts clés)")
                
                # Charger annotation_components
                try:
                    import importlib.util
                    annopath = os.path.join(os.path.dirname(__file__), '..', 'annotation_components.py')
                    spec = importlib.util.spec_from_file_location("annotation_components", annopath)
                    annotation_components = importlib.util.module_from_spec(spec)
                    sys.modules["annotation_components"] = annotation_components
                    spec.loader.exec_module(annotation_components)
                    
                    annotations = annotation_components.smart_annotation_input(
                        key_prefix=f"manual_anno_{idx}",
                        max_tags=20
                    )
                    
                    col_save, col_skip = st.columns(2)
                    
                    with col_save:
                        if st.button("✅ Valider l'annotation", key=f"validate_manual_{idx}", type="primary",
                                    disabled=not annotations):
                            st.session_state.multi_ecgs[idx]['annotations'] = annotations
                            st.session_state.multi_ecgs[idx]['expected_concepts'] = annotations
                            st.session_state.multi_ecgs[idx]['teacher_correction_text'] = ""
                            st.session_state.multi_ecgs[idx]['mode'] = 'manual'
                            st.success(f"✅ {len(annotations)} concepts enregistrés!")
                            del st.session_state['pending_annotation_idx']
                            st.rerun()
                    
                    with col_skip:
                        if st.button("⏭️ Passer", key=f"skip_manual_{idx}"):
                            st.session_state.multi_ecgs[idx]['annotations'] = []
                            st.session_state.multi_ecgs[idx]['expected_concepts'] = []
                            st.session_state.multi_ecgs[idx]['mode'] = 'manual'
                            del st.session_state['pending_annotation_idx']
                            st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur chargement module annotation: {e}")
                    st.info("💡 Utilisez le mode IA à la place")
                
                return
            
            # Mode IA (par défaut)
            st.markdown(f"### 🤖 Validation IA pour l'ECG : **{ecg['label']}**")
            
            if not LLM_AVAILABLE:
                st.warning(f"⚠️ Module LLM non disponible: {llm_import_error}")
                st.info("💡 Utilisation du mode manuel (tags)")
                
                # Fallback: annotation manuelle
                import importlib.util
                annopath = os.path.join(os.path.dirname(__file__), '..', 'annotation_components.py')
                spec = importlib.util.spec_from_file_location("annotation_components", annopath)
                annotation_components = importlib.util.module_from_spec(spec)
                sys.modules["annotation_components"] = annotation_components
                spec.loader.exec_module(annotation_components)
                annotations = annotation_components.smart_annotation_input(
                    key_prefix=f"ecg_anno_{idx}",
                    max_tags=15
                )
                
                if st.button("✅ Valider l'annotation", key=f"validate_anno_{idx}"):
                    st.session_state.multi_ecgs[idx]['annotations'] = annotations
                    st.session_state.multi_ecgs[idx]['expected_concepts'] = annotations  # Pour compatibilité
                    st.success("Annotations enregistrées !")
                    del st.session_state['pending_annotation_idx']
                    st.rerun()
            else:
                # Mode LLM: Rédaction de correction + extraction automatique
                st.markdown("""
                **📝 Mode Validation IA:**
                1. Rédigez votre correction (minimum 10 caractères)
                2. L'IA extrait automatiquement les concepts médicaux
                3. Validez les concepts détectés
                """)
                
                # Clé pour stocker la correction temporaire
                correction_key = f"teacher_correction_{idx}"
                if correction_key not in st.session_state:
                    st.session_state[correction_key] = ""
                
                # Zone de texte pour correction du professeur
                teacher_correction = st.text_area(
                    "✍️ Rédigez votre correction (texte libre):",
                    value=st.session_state[correction_key],
                    height=200,
                    placeholder="""Exemple court:

Rythme sinusal régulier à 70 bpm.
PR allongé à 240ms → BAV 1er degré.
QRS élargis (140ms) avec rSR' en V1 et S larges en V6 → BBG complet.
Pas d'anomalie de repolarisation.

Diagnostic: BAV 1 + BBG complet.""",
                    key=f"correction_input_{idx}"
                )
                
                st.session_state[correction_key] = teacher_correction
                
                # Indicateur de caractères
                char_count = len(teacher_correction.strip())
                if char_count > 0:
                    if char_count < 10:
                        st.caption(f"⚠️ {char_count} caractères (minimum 10 pour extraction IA)")
                    else:
                        st.caption(f"✅ {char_count} caractères - Prêt pour extraction IA")
                
                # Bouton extraction LLM
                col_extract, col_skip = st.columns(2)
                
                with col_extract:
                    if st.button("🤖 Extraire les Concepts avec IA", type="primary", key=f"extract_{idx}", 
                                disabled=not teacher_correction or len(teacher_correction.strip()) < 10):
                        with st.spinner("🔍 Extraction en cours..."):
                            try:
                                llm_service = LLMService()
                                extraction_result = llm_service.extract_concepts(teacher_correction)
                                extracted_concepts = extraction_result.get('concepts', [])
                                
                                # Stocker résultats extraction
                                st.session_state[f'extracted_{idx}'] = extracted_concepts
                                st.session_state[f'correction_text_{idx}'] = teacher_correction
                                st.success(f"✅ {len(extracted_concepts)} concepts extraits!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erreur extraction: {e}")
                
                with col_skip:
                    if st.button("⏭️ Passer (sans validation)", key=f"skip_{idx}"):
                        st.session_state.multi_ecgs[idx]['annotations'] = []
                        st.session_state.multi_ecgs[idx]['expected_concepts'] = []
                        st.session_state.multi_ecgs[idx]['teacher_correction_text'] = ""
                        st.warning("ECG enregistré sans validation")
                        del st.session_state['pending_annotation_idx']
                        st.rerun()
                
                # Affichage résultats extraction et validation
                if f'extracted_{idx}' in st.session_state:
                    st.markdown("---")
                    st.markdown("### ✅ Validation des Concepts Extraits")
                    
                    extracted = st.session_state[f'extracted_{idx}']
                    
                    st.info(f"🎯 {len(extracted)} concepts détectés - Cochez ceux qui sont pertinents:")
                    
                    validated_concepts = []
                    
                    # Afficher chaque concept avec checkbox
                    for i, concept in enumerate(extracted):
                        col_check, col_concept, col_info = st.columns([1, 5, 2])
                        
                        with col_check:
                            is_valid = st.checkbox(
                                "",
                                value=True,  # Par défaut, tous cochés
                                key=f"concept_check_{idx}_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with col_concept:
                            # Afficher le texte du concept
                            concept_text = concept.get('text', concept) if isinstance(concept, dict) else concept
                            st.write(f"**{concept_text}**")
                        
                        with col_info:
                            # Afficher catégorie si disponible
                            if isinstance(concept, dict):
                                category = concept.get('category', 'N/A')
                                confidence = concept.get('confidence', 1.0)
                                st.caption(f"📁 {category} ({confidence:.0%})")
                        
                        if is_valid:
                            validated_concepts.append(concept_text if isinstance(concept_text, str) else concept)
                    
                    # Option ajout manuel
                    st.markdown("---")
                    st.markdown("**➕ Ajouter un concept manuellement:**")
                    
                    col_manual, col_add = st.columns([4, 1])
                    with col_manual:
                        manual_concept = st.text_input(
                            "Concept supplémentaire:",
                            key=f"manual_concept_{idx}",
                            placeholder="Ex: Onde T inversée en V1-V3",
                            label_visibility="collapsed"
                        )
                    
                    with col_add:
                        if st.button("➕", key=f"add_manual_{idx}"):
                            if manual_concept:
                                validated_concepts.append(manual_concept)
                                st.success(f"✅ Ajouté: {manual_concept}")
                    
                    # Sauvegarde finale
                    st.markdown("---")
                    
                    col_save, col_cancel = st.columns(2)
                    
                    with col_save:
                        if st.button("💾 Sauvegarder la Validation", type="primary", key=f"save_validation_{idx}",
                                    disabled=not validated_concepts):
                            # Sauvegarder tous les résultats
                            st.session_state.multi_ecgs[idx]['expected_concepts'] = validated_concepts
                            st.session_state.multi_ecgs[idx]['teacher_correction_text'] = st.session_state[f'correction_text_{idx}']
                            st.session_state.multi_ecgs[idx]['annotations'] = validated_concepts  # Pour compatibilité
                            
                            # Nettoyer états temporaires
                            del st.session_state[f'extracted_{idx}']
                            del st.session_state[f'correction_text_{idx}']
                            del st.session_state[correction_key]
                            del st.session_state['pending_annotation_idx']
                            
                            st.success(f"✅ Validation enregistrée: {len(validated_concepts)} concepts!")
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("🔄 Recommencer", key=f"restart_{idx}"):
                            del st.session_state[f'extracted_{idx}']
                            if f'correction_text_{idx}' in st.session_state:
                                del st.session_state[f'correction_text_{idx}']
                            st.rerun()

def crop_multi_ecg_interface():
    """Interface de recadrage pour les ECG du cas"""
    
    st.markdown("### ✂️ Recadrage des ECG")
    
    # Filtrer les ECG qui ont besoin de recadrage
    ecgs_to_crop = [ecg for ecg in st.session_state.multi_ecgs if ecg.get('needs_crop', False) and not ecg.get('cropped', False)]
    
    if not ecgs_to_crop:
        if any(ecg.get('cropped', False) for ecg in st.session_state.multi_ecgs):
            st.success("✅ Tous les ECG nécessitant un recadrage ont été traités !")
        else:
            st.info("📝 Aucun ECG en attente de recadrage")
        return
    
    st.write(f"**{len(ecgs_to_crop)} ECG** en attente de recadrage")
    
    # Sélection de l'ECG à recadrer
    ecg_labels = [f"{ecg['label']} ({ecg['timing']})" for ecg in ecgs_to_crop]
    selected_idx = st.selectbox("Choisir l'ECG à recadrer", range(len(ecg_labels)), 
                               format_func=lambda x: ecg_labels[x])
    
    if selected_idx is not None:
        current_ecg = ecgs_to_crop[selected_idx]
        
        st.markdown(f"#### ✂️ Recadrage : {current_ecg['label']}")
        
        # Interface de recadrage (réutilise la fonction existante)
        if current_ecg['file_data']['type'] in ['image', 'pdf_converted']:
            cropped_data = interface_recadrage_simple(current_ecg['file_data'])
            
            if cropped_data and st.button("✅ Valider le recadrage", type="primary", 
                                         key=f"validate_crop_{selected_idx}_{current_ecg['label']}"):
                # Marquer comme recadré et sauvegarder
                current_ecg['cropped'] = True
                current_ecg['cropped_data'] = cropped_data
                current_ecg['needs_crop'] = False
                
                st.success(f"✅ ECG '{current_ecg['label']}' recadré avec succès !")
                st.rerun()

def preview_multi_case():
    """Aperçu du cas complet avant sauvegarde"""
    
    st.markdown("### 👁️ Aperçu du Cas Complet")
    
    if not st.session_state.multi_ecgs:
        st.warning("⚠️ Aucun ECG ajouté à ce cas")
        return
    
    # Informations du cas
    case = st.session_state.multi_case
    st.markdown(f"#### 📋 {case['name']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Catégorie :** {case['category']}")
    with col2:
        st.write(f"**Niveau :** {case['difficulty']}")
    with col3:
        st.write(f"**ECG :** {len(st.session_state.multi_ecgs)}")
    
    if case['description']:
        st.write(f"**Description :** {case['description']}")
    
    st.markdown("---")
    
    # Liste des ECG
    st.markdown("#### 📄 ECG du Cas")
    
    for i, ecg in enumerate(st.session_state.multi_ecgs):
        with st.expander(f"📄 {ecg['label']} - {ecg['timing']}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Fichier :** {ecg['filename']}")
                st.write(f"**Timing :** {ecg['timing']}")
                if ecg['notes']:
                    st.write(f"**Notes :** {ecg['notes']}")
                
                # Status
                status = "✂️ Recadré" if ecg.get('cropped', False) else "📄 Original"
                st.write(f"**Status :** {status}")
            
            with col2:
                # Actions sur ECG individuel
                if st.button(f"🗑️ Supprimer", key=f"del_ecg_{i}"):
                    st.session_state.multi_ecgs.pop(i)
                    st.rerun()
                
                if not ecg.get('cropped', False):
                    if st.button(f"✂️ Recadrer", key=f"crop_ecg_{i}"):
                        ecg['needs_crop'] = True
                        st.info("💡 Passez à l'onglet 'Recadrer ECG'")

def save_multi_case():
    """Sauvegarder le cas multi-ECG complet"""
    
    st.markdown("### 💾 Sauvegarder le Cas")
    
    if not st.session_state.multi_ecgs:
        st.warning("⚠️ Aucun ECG à sauvegarder")
        return
    
    case = st.session_state.multi_case
    
    # Aperçu final
    st.write(f"**Cas :** {case['name']}")
    st.write(f"**Nombre d'ECG :** {len(st.session_state.multi_ecgs)}")
    
    # Options de sauvegarde
    with st.form("save_multi_case"):
        st.markdown("#### ⚙️ Options de Sauvegarde")
        
        col1, col2 = st.columns(2)
        with col1:
            generate_previews = st.checkbox("🖼️ Générer des aperçus", value=True)
            create_annotations = st.checkbox("📝 Créer template d'annotation", value=True)
        
        with col2:
            auto_publish = st.checkbox("📢 Publier automatiquement", value=False)
            create_session = st.checkbox("🎓 Créer session d'étude", value=False)
        
        if st.form_submit_button("💾 Sauvegarder le Cas", type="primary"):
            success = save_final_multi_case(
                case, st.session_state.multi_ecgs,
                generate_previews, create_annotations, auto_publish, create_session
            )
            
            if success:
                st.success("✅ Cas multi-ECG sauvegardé avec succès !")
                
                # Reset pour nouveau cas - marquer le succès
                st.session_state.save_success = True
            else:
                st.error("❌ Erreur lors de la sauvegarde")
    
    # Bouton pour nouveau cas - en dehors du formulaire
    if st.session_state.get('save_success', False):
        if st.button("🆕 Créer un Nouveau Cas"):
            st.session_state.multi_case = None
            st.session_state.multi_ecgs = []
            st.session_state.save_success = False
            st.rerun()

def save_final_multi_case(case, ecgs, generate_previews, create_annotations, auto_publish, create_session):
    """Sauvegarder effectivement le cas multi-ECG avec debugging amélioré"""
    
    try:
        # Debug : afficher les informations
        st.write("🔧 **Debug Sauvegarde :**")
        st.write(f"- Cas : {case['name']}")
        st.write(f"- Nombre d'ECG : {len(ecgs)}")
        st.write(f"- ID du cas : {case['case_id']}")
        
        # Créer le dossier du cas
        case_dir = Path("data/ecg_cases") / case['case_id']
        st.write(f"- Création dossier : {case_dir}")
        case_dir.mkdir(parents=True, exist_ok=True)
        
        # Vérifier que le dossier existe
        if not case_dir.exists():
            st.error(f"❌ Impossible de créer le dossier : {case_dir}")
            return False
        
        st.write("✅ Dossier créé avec succès")
        
        # Métadonnées du cas
        metadata = {
            'name': case['name'],
            'description': case['description'],
            'category': case['category'],
            'difficulty': case['difficulty'],
            'created_date': case['created_date'],
            'case_id': case['case_id'],
            'type': 'multi_ecg',
            'total_files': len(ecgs),
            'import_mode': st.session_state.get('import_mode', 'ai'),  # Mode d'import utilisé
            'options': {
                'generate_previews': generate_previews,
                'create_annotations': create_annotations,
                'auto_publish': auto_publish,
                'create_session': create_session
            },
            'ecgs': [],
            'expected_concepts': []  # Tous les concepts attendus du cas
        }
        
        # Collecter tous les concepts attendus
        all_expected_concepts = []
        for ecg in ecgs:
            concepts = ecg.get('expected_concepts', [])
            all_expected_concepts.extend(concepts)
        
        # Dédupliquer
        metadata['expected_concepts'] = list(set(all_expected_concepts))
        
        # Traiter chaque ECG
        for i, ecg in enumerate(ecgs):
            try:
                ecg_filename = f"ecg_{i+1:02d}_{ecg['label']}.png"
                ecg_path = case_dir / ecg_filename
                
                st.write(f"- Traitement ECG {i+1}: {ecg['label']}")
                
                # Vérifier que nous avons une image
                image = None
                if ecg.get('cropped', False) and 'cropped_data' in ecg:
                    image = ecg['cropped_data']['image']
                    st.write(f"  → Utilisation image recadrée")
                elif 'file_data' in ecg and 'image' in ecg['file_data']:
                    image = ecg['file_data']['image']
                    st.write(f"  → Utilisation image originale")
                else:
                    st.error(f"  ❌ Pas d'image trouvée pour ECG {i+1}")
                    continue
                
                # Sauvegarder l'image
                if image:
                    image.save(ecg_path, "PNG", optimize=True)
                    st.write(f"  ✅ Sauvé: {ecg_filename}")
                    
                    # Vérifier que le fichier existe
                    if not ecg_path.exists():
                        st.error(f"  ❌ Fichier non créé: {ecg_filename}")
                        continue
                    
                    file_size = ecg_path.stat().st_size
                    st.write(f"  📊 Taille: {file_size // 1024} KB")
                
                # Métadonnées de l'ECG
                ecg_meta = {
                    'filename': ecg_filename,
                    'label': ecg['label'],
                    'timing': ecg['timing'],
                    'notes': ecg['notes'],
                    'original_filename': ecg['filename'],
                    'cropped': ecg.get('cropped', False),
                    'added_date': ecg['added_date'],
                    'mode': ecg.get('mode', 'ai'),  # Mode d'annotation utilisé
                    'has_validation': len(ecg.get('expected_concepts', [])) > 0
                }
                
                metadata['ecgs'].append(ecg_meta)
                
            except Exception as ecg_error:
                st.error(f"❌ Erreur ECG {i+1}: {ecg_error}")
                continue
        
        # Sauvegarder les métadonnées
        try:
            metadata_path = case_dir / "metadata.json"
            st.write(f"- Sauvegarde métadonnées: {metadata_path}")
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Vérifier que le fichier existe
            if metadata_path.exists():
                st.write("✅ Métadonnées sauvées")
            else:
                st.error("❌ Fichier métadonnées non créé")
                return False
                
        except Exception as meta_error:
            st.error(f"❌ Erreur métadonnées: {meta_error}")
            return False
        
        # Créer template d'annotation si demandé
        if create_annotations:
            try:
                template_path = case_dir / "annotation_template.json"
                template = {
                    'case_id': case['case_id'],
                    'annotations': [],
                    'created_date': datetime.now().isoformat(),
                    'template_version': '1.0'
                }
                
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                
                st.write("✅ Template d'annotation créé")
                
            except Exception as template_error:
                st.warning(f"⚠️ Erreur template: {template_error}")
        
        # Résumé final
        st.success("🎉 **Sauvegarde terminée avec succès !**")
        st.write(f"📁 Dossier: {case_dir}")
        st.write(f"📄 ECG sauvés: {len(metadata['ecgs'])}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur générale lors de la sauvegarde : {e}")
        import traceback
        st.code(traceback.format_exc())
        return False

def process_uploaded_file(uploaded_file):
    """Traite le fichier uploadé selon son type"""
    
    file_extension = Path(uploaded_file.name).suffix.lower()
    
    # Affichage des informations
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("#### 📊 Informations")
        st.write(f"**Nom :** {uploaded_file.name}")
        st.write(f"**Type :** {file_extension.upper()}")
        st.write(f"**Taille :** {len(uploaded_file.getvalue()) / 1024:.1f} KB")
    
    with col1:
        if file_extension == '.pdf':
            return traiter_pdf_simple(uploaded_file)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            return traiter_image_simple(uploaded_file)
        elif file_extension == '.xml':
            return traiter_xml_simple(uploaded_file)
        else:
            st.error(f"❌ Format {file_extension} non supporté")
            return False, None

def traiter_image_simple(uploaded_file):
    """Traite les images de façon simple"""
    
    try:
        image = Image.open(uploaded_file)
        
        st.markdown("#### 🖼️ Image ECG chargée")
        st.image(image, caption=f"ECG - {uploaded_file.name}", use_container_width=True)
        
        st.write(f"**Dimensions :** {image.size[0]} × {image.size[1]} pixels")
        
        return True, {
            'type': 'image',
            'filename': uploaded_file.name,
            'image': image,
            'original_data': uploaded_file.getvalue()
        }
        
    except Exception as e:
        st.error(f"❌ Erreur lecture image : {e}")
        return False, None

def traiter_pdf_simple(uploaded_file):
    """Traite les PDFs avec alternatives simples"""
    
    st.markdown("#### 📄 PDF détecté")
    
    pdf_data = uploaded_file.getvalue()
    file_size_mb = len(pdf_data) / (1024 * 1024)
    
    # Détection du nombre de pages
    num_pages = get_pdf_page_count(pdf_data)
    
    if num_pages > 1:
        st.info(f"📄 PDF avec {num_pages} pages détecté")
        selected_page = st.selectbox(
            "Choisissez la page à importer :",
            range(1, num_pages + 1),
            index=0,
            key=f"pdf_page_select_{uploaded_file.name}_{len(uploaded_file.getvalue())}",
            help="Sélectionnez la page contenant l'ECG à analyser"
        )
        page_index = selected_page - 1  # Conversion en index 0-based
    else:
        st.info("📄 PDF mono-page détecté")
        page_index = 0
    
    # Tentative de conversion automatique
    with st.spinner(f"🔄 Conversion de la page {page_index + 1}..."):
        conversion_result = try_convert_pdf(pdf_data, page_index)
    
    if conversion_result['success']:
        st.success(f"✅ {conversion_result['message']}")
        st.image(conversion_result['image'], caption=f"PDF converti - Page {page_index + 1}", use_container_width=True)
        
        return True, {
            'type': 'pdf_converted',
            'filename': uploaded_file.name,
            'image': conversion_result['image'],
            'method': conversion_result['method'],
            'page': page_index + 1
        }
    else:
        st.warning("⚠️ Conversion automatique échouée")
        st.info("💡 Interface de capture disponible ci-dessous")
        
        return True, {
            'type': 'pdf_manual' if file_size_mb <= 2 else 'pdf_large',
            'filename': uploaded_file.name,
            'data': pdf_data,
            'size_mb': file_size_mb,
            'page': page_index + 1
        }

def get_pdf_page_count(pdf_data):
    """Obtient le nombre de pages d'un PDF"""
    
    # Essai PyMuPDF
    try:
        import fitz
        pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
        page_count = pdf_doc.page_count
        pdf_doc.close()
        return page_count
    except ImportError:
        pass
    except Exception:
        pass
    
    # Essai pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            return len(pdf.pages)
    except ImportError:
        pass
    except Exception:
        pass
    
    # Fallback - assumer 1 page
    return 1

def try_convert_pdf(pdf_data, page_index=0):
    """Essaie de convertir le PDF à la page spécifiée"""
    
    # Essai PyMuPDF
    try:
        import fitz
        
        pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Vérifier que la page existe
        if page_index >= pdf_doc.page_count:
            page_index = 0
        
        page = pdf_doc[page_index]
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        pdf_doc.close()
        
        return {
            'success': True,
            'image': image,
            'message': f'Conversion PyMuPDF réussie (page {page_index + 1})',
            'method': 'pymupdf'
        }
        
    except ImportError:
        pass
    except Exception:
        pass
    
    # Essai pdfplumber
    try:
        import pdfplumber
        
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            # Vérifier que la page existe
            if page_index >= len(pdf.pages):
                page_index = 0
            
            page = pdf.pages[page_index]
            image = page.to_image(resolution=200)
            pil_image = image.original
            
        return {
            'success': True,
            'image': pil_image,
            'message': f'Conversion pdfplumber réussie (page {page_index + 1})',
            'method': 'pdfplumber'
        }
        
    except ImportError:
        pass
    except Exception:
        pass
    
    return {'success': False}

def traiter_xml_simple(uploaded_file):
    """Traite les fichiers XML"""
    
    try:
        xml_content = uploaded_file.getvalue().decode('utf-8')
        
        st.markdown("#### 📋 XML ECG détecté")
        
        with st.expander("📄 Aperçu du contenu"):
            st.code(xml_content[:500], language='xml')
        
        return True, {
            'type': 'xml',
            'filename': uploaded_file.name,
            'content': xml_content,
            'original_data': uploaded_file.getvalue()
        }
        
    except Exception as e:
        st.error(f"❌ Erreur lecture XML : {e}")
        return False, None

def interface_recadrage_simple(file_data):
    """Interface de recadrage simplifiée"""
    
    if 'image' not in file_data:
        return None
    
    image = file_data['image']
    
    # Redimensionner pour l'affichage
    display_image = image.copy()
    max_width = 600
    
    if display_image.width > max_width:
        ratio = max_width / display_image.width
        new_height = int(display_image.height * ratio)
        display_image = display_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
    # Initialiser les valeurs par défaut si pas encore définies
    if "crop_x1" not in st.session_state:
        st.session_state.crop_x1 = 0
    if "crop_y1" not in st.session_state:
        st.session_state.crop_y1 = 0
    if "crop_x2" not in st.session_state:
        st.session_state.crop_x2 = display_image.width
    if "crop_y2" not in st.session_state:
        st.session_state.crop_y2 = display_image.height
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🎯 Aperçu et zone de recadrage")
        
        # Curseurs de recadrage avec valeurs de session state
        x1 = st.slider("🔹 X début", 0, display_image.width, st.session_state.crop_x1, key="x1")
        y1 = st.slider("🔹 Y début", 0, display_image.height, st.session_state.crop_y1, key="y1") 
        x2 = st.slider("🔹 X fin", x1, display_image.width, st.session_state.crop_x2, key="x2")
        y2 = st.slider("🔹 Y fin", y1, display_image.height, st.session_state.crop_y2, key="y2")
        
        # Mettre à jour les valeurs en session state
        st.session_state.crop_x1 = x1
        st.session_state.crop_y1 = y1
        st.session_state.crop_x2 = x2
        st.session_state.crop_y2 = y2
        
        # Aperçu de la zone recadrée
        if x2 > x1 and y2 > y1:
            cropped_preview = display_image.crop((x1, y1, x2, y2))
            st.image(cropped_preview, caption="Aperçu de la zone recadrée", use_container_width=True)
    
    with col2:
        st.markdown("#### ⚙️ Contrôles")
        
        # Présets
        if st.button("🫀 ECG Standard", type="secondary", key="preset_ecg_standard"):
            # Recadrage typique (centre avec marges)
            margin = 50
            st.session_state.crop_x1 = margin
            st.session_state.crop_y1 = margin
            st.session_state.crop_x2 = display_image.width - margin
            st.session_state.crop_y2 = display_image.height - margin
            st.rerun()
        
        if st.button("📄 Image complète", type="secondary", key="preset_full_image"):
            st.session_state.crop_x1 = 0
            st.session_state.crop_y1 = 0
            st.session_state.crop_x2 = display_image.width
            st.session_state.crop_y2 = display_image.height
            st.rerun()
        
        st.markdown("---")
        
        # Validation
        if st.button("✅ Valider le recadrage", type="primary", key="validate_simple_crop"):
            # Utiliser les valeurs actuelles des sliders
            x1 = st.session_state.crop_x1 
            y1 = st.session_state.crop_y1
            x2 = st.session_state.crop_x2
            y2 = st.session_state.crop_y2
            
            # Calculer les coordonnées sur l'image originale
            scale_x = image.width / display_image.width
            scale_y = image.height / display_image.height
            
            real_x1 = int(x1 * scale_x)
            real_y1 = int(y1 * scale_y)
            real_x2 = int(x2 * scale_x)
            real_y2 = int(y2 * scale_y)
            
            # Recadrer l'image originale
            cropped_original = image.crop((real_x1, real_y1, real_x2, real_y2))
            
            st.success("✅ Recadrage validé !")
            
            return {
                'type': 'image',
                'image': cropped_original,
                'coordinates': (real_x1, real_y1, real_x2, real_y2),
                'original_filename': file_data['filename']
            }
    
    return None

def guide_capture_pdf(file_data):
    """Guide pour capturer un PDF"""
    
    st.markdown("#### 📱 Guide de capture d'écran")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Viewer PDF.js avec page sélectionnée
        pdf_base64 = base64.b64encode(file_data['data']).decode()
        
        # Construire l'URL avec la page spécifiée
        page_num = file_data.get('page', 1)
        viewer_url = f"https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}#page={page_num}"
        
        viewer_html = f"""
        <div style="border: 2px solid #0066cc; border-radius: 10px; padding: 5px;">
            <iframe 
                src="{viewer_url}" 
                width="100%" 
                height="400" 
                style="border: none; border-radius: 5px;">
            </iframe>
        </div>
        """
        
        st.components.v1.html(viewer_html, height=420)
        
        if page_num > 1:
            st.info(f"📄 Affichage de la page {page_num}")
    
    with col2:
        st.markdown("#### 🎯 Instructions")
        st.markdown("1. 📱 **Windows+Shift+S**")
        st.markdown("2. 🎯 **Sélectionnez l'ECG**") 
        st.markdown("3. 💾 **Sauvegardez PNG/JPG**")
        st.markdown("4. 🔄 **Rechargez la page**")
        st.markdown("5. ⬆️ **Réimportez l'image**")
        
        if st.button("🔄 J'ai capturé, recharger", type="primary"):
            # Effacer la session pour recommencer
            for key in ['uploaded_file_data', 'cropped_ecg']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def interface_export_simple(cropped_data):
    """Interface d'export simplifiée"""
    
    # Métadonnées
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(cropped_data['image'], caption="ECG final à exporter", use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Métadonnées")
        
        case_id = st.text_input("ID du cas", value=f"ecg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
        age = st.number_input("Âge patient", min_value=0, max_value=120, value=65)
        sexe = st.selectbox("Sexe", ["M", "F", "Non spécifié"])
        contexte = st.text_area("Contexte", placeholder="Douleur thoracique...")
    
    if st.button("🚀 Exporter vers la liseuse", type="primary"):
        success = executer_export_simple(case_id, cropped_data, {
            'age': age,
            'sexe': sexe, 
            'contexte': contexte
        })
        
        if success:
            st.success("🎉 ECG exporté avec succès !")
            st.balloons()
            
            if st.button("➕ Importer un autre ECG"):
                for key in ['uploaded_file_data', 'cropped_ecg']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

def interface_export_xml_simple(file_data):
    """Export XML simple"""
    
    st.markdown("#### 📋 Export de données XML")
    
    case_id = st.text_input("ID du cas", value=f"xml_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    
    if st.button("💾 Exporter XML", type="primary"):
        success = executer_export_xml_simple(case_id, file_data)
        
        if success:
            st.success("🎉 XML exporté avec succès !")

def executer_export_simple(case_id, cropped_data, metadata):
    """Exécute l'export simple avec gestion d'erreur robuste"""
    
    try:
        # Vérifications préliminaires
        if not case_id or not case_id.strip():
            st.error("❌ ID du cas invalide")
            return False
            
        if not cropped_data:
            st.error("❌ Aucune donnée d'image à exporter")
            return False
            
        if 'image' not in cropped_data or cropped_data['image'] is None:
            st.error("❌ Image manquante dans les données")
            return False
        
        # Nettoyer l'ID du cas
        case_id = case_id.strip()
        
        # Créer le répertoire de destination
        export_dir = Path("data/ecg_cases") / case_id
        
        # S'assurer que le répertoire parent existe
        export_dir.parent.mkdir(parents=True, exist_ok=True)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        st.info(f"📁 Création du cas dans : {export_dir.absolute()}")
        
        # Sauvegarder l'image
        filename = f"{case_id}.png"
        image_path = export_dir / filename
        
        # Sauvegarder avec gestion d'erreur
        try:
            cropped_data['image'].save(image_path, 'PNG', optimize=True, quality=95)
            st.success(f"✅ Image sauvegardée : {filename}")
        except Exception as img_error:
            st.error(f"❌ Erreur sauvegarde image : {img_error}")
            return False
        
        # Préparer les métadonnées avec valeurs par défaut
        metadata_json = {
            'case_id': case_id,
            'filename': filename,
            'created_date': datetime.now().isoformat(),
            'type': 'image',
            'age': metadata.get('age', 0),
            'sexe': metadata.get('sexe', 'Non spécifié'),
            'contexte': metadata.get('contexte', 'ECG importé pour analyse'),
            'diagnostic': 'À analyser',
            'statut': 'imported',
            'metadata': {
                'source_file': cropped_data.get('original_filename', 'fichier_source_inconnu'),
                'import_method': 'smart_importer_simple',
                'crop_coordinates': cropped_data.get('coordinates', None),
                'image_size': [cropped_data['image'].width, cropped_data['image'].height]
            }
        }
        
        # Sauvegarder les métadonnées
        metadata_path = export_dir / 'metadata.json'
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_json, f, indent=2, ensure_ascii=False)
            st.success(f"✅ Métadonnées sauvegardées : metadata.json")
        except Exception as meta_error:
            st.error(f"❌ Erreur sauvegarde métadonnées : {meta_error}")
            return False
        
        # Vérifications finales
        if image_path.exists() and metadata_path.exists():
            st.success(f"🎉 Cas ECG créé avec succès !")
            st.info(f"🆔 ID du cas : **{case_id}**")
            st.info(f"📂 Emplacement : `data/ecg_cases/{case_id}/`")
            st.info(f"📋 Fichiers créés :")
            st.info(f"  • {filename} ({image_path.stat().st_size} bytes)")
            st.info(f"  • metadata.json ({metadata_path.stat().st_size} bytes)")
            return True
        else:
            st.error("❌ Échec de vérification des fichiers créés")
            return False
        
    except Exception as e:
        st.error(f"❌ Erreur générale export : {e}")
        st.error(f"🔍 Type d'erreur : {type(e).__name__}")
        # Afficher plus de détails en mode debug
        import traceback
        with st.expander("🐛 Détails de l'erreur (debug)"):
            st.code(traceback.format_exc())
        return False

def executer_export_xml_simple(case_id, file_data):
    """Export XML simple"""
    
    try:
        export_dir = Path("data/ecg_cases") / case_id
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder XML
        xml_path = export_dir / f"{case_id}.xml"
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(file_data['content'])
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur export XML : {e}")
        return False

if __name__ == "__main__":
    st.set_page_config(
        page_title="Import ECG Simple",
        page_icon="📥",
        layout="wide"
    )
    
    st.title("📥 Import ECG Intelligent - Version Simple")
    smart_ecg_importer_simple()
