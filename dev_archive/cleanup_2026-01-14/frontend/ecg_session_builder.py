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
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    for idx, img_data in enumerate(images):
        img_path = case_dir / f"ecg_{idx + 1}.png"
        img_data['image'].save(img_path)
    
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
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Formats supportés: PNG, JPG, JPEG, PDF"
        )
        
        if uploaded_file:
            # Traiter l'image
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                
                # Afficher prévisualisation
                st.image(image, caption="Prévisualisation", use_container_width=True)
                
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
            
            elif uploaded_file.type == 'application/pdf':
                st.warning("📄 Support PDF en cours de développement - Veuillez utiliser une image")
    
    else:  # Multi-ECG
        st.info("💡 Vous pouvez ajouter plusieurs ECG pour créer un cas complexe")
        
        # Initialiser la liste des images
        if 'uploaded_images' not in st.session_state:
            st.session_state.uploaded_images = []
        
        # Uploader un nouvel ECG
        uploaded_file = st.file_uploader(
            f"Ajouter un ECG ({len(st.session_state.uploaded_images) + 1})",
            type=['png', 'jpg', 'jpeg'],
            key=f"upload_{len(st.session_state.uploaded_images)}"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            
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
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
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
                if st.button("🗑️", key=f"delete_ann_{idx}"):
                    st.session_state.case_annotations.pop(idx)
                    st.rerun()
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("◀ Retour à l'upload", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    with col2:
        if st.session_state.case_annotations:
            if st.button("Valider le cas ▶", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()
        else:
            st.button("Valider le cas ▶", disabled=True, use_container_width=True)
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
    
    for annotation in st.session_state.case_annotations:
        st.markdown(f"- **{annotation['concept']}** ({annotation['category']}) - Coeff: {annotation['coefficient']}")
    
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
            # Créer le cas
            case_id = generate_case_id()
            
            # Extraire les concepts des annotations pour expected_concepts
            expected_concepts = [ann['concept'] for ann in st.session_state.case_annotations]
            
            # Déterminer le diagnostic principal (premier concept ou concept avec plus grand coefficient)
            diagnostic_principal = st.session_state.case_name
            if st.session_state.case_annotations:
                # Prendre le concept avec le plus grand coefficient
                main_annotation = max(st.session_state.case_annotations, key=lambda x: x.get('coefficient', 1))
                diagnostic_principal = main_annotation['concept']
            
            case_data = {
                'case_id': case_id,
                'name': st.session_state.case_name,
                'category': st.session_state.case_category,
                'difficulty': st.session_state.case_difficulty,
                'description': st.session_state.case_description,
                'annotations': st.session_state.case_annotations,
                'expected_concepts': expected_concepts,  # 🆕 Pour la correction
                'diagnostic_principal': diagnostic_principal,  # 🆕 Pour affichage
                'clinical_context': st.session_state.case_description,  # 🆕 Alias
                'num_ecg': len(st.session_state.uploaded_images),
                'created_date': datetime.now().isoformat(),
                'type': 'multi_ecg' if len(st.session_state.uploaded_images) > 1 else 'simple',
                'metadata': {
                    'created_by': 'ecg_session_builder',
                    'version': '1.0'
                }
            }
            
            # Sauvegarder
            case_dir = save_case_to_disk(case_data, st.session_state.uploaded_images)
            
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

def ecg_session_builder():
    """Interface principale du Session Builder"""
    
    st.title("🎓 ECG Session Builder")
    st.markdown("*Créez des sessions de formation complètes en important et annotant vos ECG*")
    
    # Initialiser l'étape
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Barre de progression
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
    ecg_session_builder()
