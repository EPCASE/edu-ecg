"""
🔍 Module de Correction LLM - Version Intégrée
Adapté depuis correction_llm_poc.py pour intégration dans app.py

Auteur: Edu-ECG Team + BMAD Agents (Party Mode)
Date: 2026-01-11
Version: 2.0 - Production Ready
"""

import streamlit as st
import sys
from pathlib import Path
import json
import os

# Ajouter project root au path pour imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Imports backend services
try:
    from backend.services.llm_service import LLMService
    from backend.scoring_service_llm import SemanticScorer
    from backend.feedback_service import FeedbackService
    from backend.services.llm_semantic_matcher import semantic_match, get_match_type_emoji, get_match_type_label
    LLM_AVAILABLE = True
    LLM_SEMANTIC_MATCHER_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    LLM_SEMANTIC_MATCHER_AVAILABLE = False
    import_error = str(e)

# Charger ontologie pondérée OWL (prioritaire) ou fallback sur ancienne version
ONTOLOGY_MAPPING = None
WEIGHTED_ONTOLOGY = None

# 1. Charger ontologie OWL pondérée (source de vérité)
owl_mapping_file = project_root / "data" / "ontology_from_owl.json"
if owl_mapping_file.exists():
    with open(owl_mapping_file, 'r', encoding='utf-8') as f:
        WEIGHTED_ONTOLOGY = json.load(f)
        ONTOLOGY_MAPPING = WEIGHTED_ONTOLOGY  # Utiliser comme mapping principal

# 2. Fallback sur ancienne ontologie si OWL non disponible
if not ONTOLOGY_MAPPING:
    mapping_file = project_root / "data" / "epic1_ontology_mapping.json"
    if mapping_file.exists():
        with open(mapping_file, 'r', encoding='utf-8') as f:
            ONTOLOGY_MAPPING = json.load(f)


# ============================================================================
# HELPER FUNCTIONS - Copiées depuis POC
# ============================================================================

def find_owl_concept(concept_text):
    """
    Cherche un concept dans l'ontologie OWL pondérée par son label français
    
    Args:
        concept_text: Le texte du concept (ex: "nstemi", "bav 2 mobitz 1")
        
    Returns:
        dict ou None: {
            'ontology_id': str,
            'concept_name': str,
            'poids': int,
            'categorie': str,
            'synonymes': list,
            'implications': list
        }
    """
    if not WEIGHTED_ONTOLOGY:
        return None
        
    concept_lower = concept_text.lower().strip()
    
    # Chercher dans concept_mappings
    concept_mappings = WEIGHTED_ONTOLOGY.get('concept_mappings', {})
    
    # 1. Recherche exacte par concept_name (case-insensitive)
    for ontology_id, mapping in concept_mappings.items():
        concept_name = mapping.get('concept_name', '').lower()
        if concept_name == concept_lower:
            return {
                'ontology_id': ontology_id,
                'concept_name': mapping.get('concept_name'),
                'poids': mapping.get('poids', 1),
                'categorie': mapping.get('categorie', 'DESCRIPTEUR_ECG'),
                'synonymes': mapping.get('synonymes', []),
                'implications': mapping.get('implications', [])
            }
    
    # 2. Recherche par synonymes
    for ontology_id, mapping in concept_mappings.items():
        synonymes = [s.lower() for s in mapping.get('synonymes', [])]
        if concept_lower in synonymes:
            return {
                'ontology_id': ontology_id,
                'concept_name': mapping.get('concept_name'),
                'poids': mapping.get('poids', 1),
                'categorie': mapping.get('categorie', 'DESCRIPTEUR_ECG'),
                'synonymes': mapping.get('synonymes', []),
                'implications': mapping.get('implications', [])
            }
    
    # 3. Recherche partielle (contient)
    for ontology_id, mapping in concept_mappings.items():
        concept_name = mapping.get('concept_name', '').lower()
        if concept_lower in concept_name or concept_name in concept_lower:
            return {
                'ontology_id': ontology_id,
                'concept_name': mapping.get('concept_name'),
                'poids': mapping.get('poids', 1),
                'categorie': mapping.get('categorie', 'DESCRIPTEUR_ECG'),
                'synonymes': mapping.get('synonymes', []),
                'implications': mapping.get('implications', [])
            }
    
    # Pas trouvé - retourner poids par défaut
    return {
        'ontology_id': concept_text.upper().replace(' ', '_'),
        'concept_name': concept_text,
        'poids': 1,  # Par défaut: descripteur
        'categorie': 'DESCRIPTEUR_ECG',
        'synonymes': [],
        'implications': []
    }


def match_concept_with_ontology(student_text, expected_concept, use_llm_semantic=True):
    """
    Vérifie si le texte étudiant correspond au concept attendu
    en utilisant l'ontologie OWL pondérée (synonymes + labels)
    
    Returns: (match_found, match_type, matched_text, owl_concept, llm_result, score_percentage)
    """
    student_lower = student_text.lower()
    concept_lower = expected_concept.lower()
    
    # Dictionnaire de synonymes supplémentaires
    EXTRA_SYNONYMS = {
        "BAV 2 Mobitz 1": ["BAV2M1", "BAV 2 M1", "bav2 mobitz 1", "bav 2m1", "mobitz 1", "mobitz I", "wenckebach"],
        "BAV 2 Mobitz 2": ["BAV2M2", "BAV 2 M2", "bav2 mobitz 2", "bav 2m2", "mobitz 2", "mobitz II"],
        "BAV de type 1": ["BAV1", "BAV 1", "bav de type 1", "bav i", "bav premier degré"],
        "Rythme sinusal": ["sinusal", "RS", "rythme sinus", "sinusale"],
        "QRS fins": ["QRS fin", "QRS normal", "qrs normaux"],
        "QRS normal": ["QRS fins", "QRS fin", "qrs normaux"],
        "Bloc de branche gauche": ["BBG", "bbg complet"],
        "Bloc de branche droit": ["BBD", "bbd complet"],
        "Bloc fasciculaire antérieur gauche": ["HBAG", "hémibloc antérieur gauche", "hemibloc antérieur gauche"],
    }
    
    # Trouver le concept dans l'ontologie OWL
    owl_concept = find_owl_concept(expected_concept)
    
    # PHASE 0 : UTILISER SemanticScorer pour scoring hiérarchique
    try:
        scorer = SemanticScorer()
        student_concept_dict = {'text': student_text, 'category': 'unknown'}
        expected_concept_dict = {'text': expected_concept, 'category': owl_concept.get('categorie', 'unknown') if owl_concept else 'unknown'}
        
        match_result = scorer._compare_concepts_llm(student_concept_dict, expected_concept_dict)
        
        if match_result.score > 0:
            match_type_map = {
                'exact': 'exact',
                'child': 'implication',
                'partial': 'partial',
                'parent': 'parent_concept',
                'sibling': 'semantic_sibling'
            }
            
            return (
                True,
                match_type_map.get(match_result.match_type.value, 'semantic'),
                match_result.student_concept,
                owl_concept,
                {'explanation': match_result.explanation, 'score': match_result.score},
                match_result.score
            )
    except Exception as e:
        print(f"⚠️ SemanticScorer error: {e}, falling back to legacy matching")
    
    # PHASE 1 : MATCHING DÉTERMINISTE
    if concept_lower in student_lower:
        return (True, 'exact', expected_concept, owl_concept, None, 100.0)
    
    # Vérifier synonymes supplémentaires
    if expected_concept in EXTRA_SYNONYMS:
        for syn in EXTRA_SYNONYMS[expected_concept]:
            if syn.lower() in student_lower:
                return (True, 'synonyme', syn, owl_concept, None, 100.0)
    
    # Vérifier synonymes de l'ontologie OWL
    if owl_concept and owl_concept.get('synonymes'):
        for synonyme in owl_concept['synonymes']:
            if synonyme.lower() in student_lower:
                return (True, 'synonyme', synonyme, owl_concept, None, 100.0)
    
    # Vérifier ontology_id
    if owl_concept:
        ontology_id = owl_concept.get('ontology_id', '').lower().replace('_', ' ')
        if ontology_id in student_lower:
            return (True, 'ontology_id', owl_concept.get('ontology_id'), owl_concept, None, 100.0)
    
    # PHASE 2 : MATCHING SÉMANTIQUE LLM
    if use_llm_semantic and LLM_SEMANTIC_MATCHER_AVAILABLE:
        try:
            ontology_context = None
            if owl_concept:
                ontology_context = {
                    'id': owl_concept.get('ontology_id'),
                    'name': owl_concept.get('concept_name'),
                    'synonyms': owl_concept.get('synonymes', []),
                    'category': owl_concept.get('categorie'),
                    'implications': owl_concept.get('implications', []),
                    'weight': owl_concept.get('poids', 1)
                }
            
            llm_result = semantic_match(student_text, expected_concept, ontology_context)
            
            if llm_result.get('match'):
                return (
                    True, 
                    f"semantic_{llm_result.get('match_type')}", 
                    student_text, 
                    owl_concept, 
                    llm_result,
                    100.0
                )
        
        except Exception as e:
            print(f"⚠️ Erreur LLM semantic matcher : {e}")
            pass
    
    return (False, None, None, owl_concept, None, 0.0)


def apply_implication_rules(matched_concepts, all_expected_concepts):
    """
    Applique les règles d'implication automatique
    Si un diagnostic est identifié, valide automatiquement ses implications
    
    Returns: set of auto-validated concept names
    """
    auto_validated = set()
    
    if not ONTOLOGY_MAPPING:
        return auto_validated
    
    implication_rules = ONTOLOGY_MAPPING.get('implication_rules', {})
    concept_mappings = ONTOLOGY_MAPPING.get('concept_mappings', {})
    
    for matched_concept in matched_concepts:
        mapping_key = None
        for ontology_id, mapping in concept_mappings.items():
            if mapping.get('concept_name', '').lower() == matched_concept.lower():
                mapping_key = ontology_id
                break
        
        if mapping_key and mapping_key in implication_rules:
            implications = implication_rules[mapping_key]
            for implied_concept in implications:
                if implied_concept in all_expected_concepts and implied_concept not in matched_concepts:
                    auto_validated.add(implied_concept)
    
    return auto_validated


def check_if_child_concept_used(expected_concept, student_answer):
    """Vérifie si l'étudiant a utilisé un concept enfant au lieu du concept attendu"""
    if not WEIGHTED_ONTOLOGY:
        return False, []
    
    concept_mappings = WEIGHTED_ONTOLOGY.get('concept_mappings', {})
    owl_concept = find_owl_concept(expected_concept)
    
    if not owl_concept:
        return False, []
    
    implications = owl_concept.get('implications', [])
    student_lower = student_answer.lower()
    
    found_children = []
    for implied in implications:
        if implied.lower() in student_lower:
            found_children.append(implied)
    
    return len(found_children) > 0, found_children


def load_available_ecg_cases():
    """Charge les cas ECG disponibles depuis data/cases/ ou data/ecg_cases/"""
    cases_dir = project_root / "data" / "ecg_cases"
    if not cases_dir.exists():
        cases_dir = project_root / "data" / "cases"
    
    if not cases_dir.exists():
        return {}
    
    available_cases = {}
    
    for case_dir in cases_dir.iterdir():
        if not case_dir.is_dir():
            continue
        
        case_id = case_dir.name
        metadata_file = case_dir / "metadata.json"
        
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
                available_cases[case_id] = {
                    'id': case_id,
                    'title': metadata.get('diagnostic_principal', case_id),
                    'diagnosis': metadata.get('expected_concepts', []),
                    'ecgs': metadata.get('ecgs', []),
                    'case_folder': str(case_dir),
                    'metadata': metadata
                }
        except Exception as e:
            st.warning(f"Erreur chargement cas {case_id}: {e}")
            continue
    
    return available_cases


# ============================================================================
# PAGE PRINCIPALE
# ============================================================================

def page_correction_llm():
    """
    Page principale de correction LLM intégrée dans app.py
    Interface de test de correction automatique avec LLM
    """
    st.title("🔍 Correction Automatique LLM")
    st.markdown("### Testez la correction automatique de vos interprétations ECG")
    
    # Vérifier disponibilité LLM
    if not LLM_AVAILABLE:
        st.error("❌ Services LLM non disponibles")
        st.info(f"Erreur: {import_error}")
        return
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ Clé API OpenAI non configurée")
        st.info("💡 Ajoutez OPENAI_API_KEY dans votre fichier .env")
        return
    
    # Vérifier ontologie
    if not ONTOLOGY_MAPPING:
        st.error("❌ Ontologie non chargée")
        st.info("Vérifiez que data/ontology_from_owl.json existe")
        return
    
    st.success("✅ Système de correction opérationnel")
    st.markdown("---")
    
    # CHECK: Cas sélectionné depuis la galerie?
    selected_case_data = None
    selected_case_id = None
    
    if 'selected_practice_case' in st.session_state:
        # Mode: Venant de la galerie de cas
        selected_case_data = st.session_state.selected_practice_case
        selected_case_id = selected_case_data.get('case_id') or selected_case_data.get('id')
        
        st.info(f"📚 Cas sélectionné depuis la galerie: **{selected_case_data.get('title', selected_case_id)}**")
        
        if st.button("🔄 Choisir un autre cas"):
            del st.session_state.selected_practice_case
            st.session_state.selected_page = 'cases'
            st.rerun()
    
    else:
        # Mode: Sélection manuelle
        available_cases = load_available_ecg_cases()
        
        if not available_cases:
            st.warning("⚠️ Aucun cas ECG disponible")
            st.info("💡 Importez des cas ECG d'abord via la page 'Import ECG'")
            return
        
        st.markdown("#### 1️⃣ Sélectionnez un cas ECG")
        
        case_options = {
            case_id: f"{case_data['title']} ({case_id})"
            for case_id, case_data in available_cases.items()
        }
        
        selected_case_id = st.selectbox(
            "Choisir un cas:",
            options=list(case_options.keys()),
            format_func=lambda x: case_options[x],
            key="correction_case_select"
        )
        
        if not selected_case_id:
            return
        
        selected_case_data = available_cases[selected_case_id]
    
    # Afficher image ECG si disponible
    st.markdown("#### 2️⃣ Cas ECG")
    
    # Try to find ECG image - MULTIPLE FALLBACKS
    image_path = None
    case_folder = Path(selected_case_data.get('case_folder', ''))
    
    # Method 1: 'ecgs' array (new format)
    if 'ecgs' in selected_case_data and len(selected_case_data['ecgs']) > 0:
        first_ecg = selected_case_data['ecgs'][0]
        image_path = case_folder / first_ecg.get('filename', '')
    
    # Method 2: 'image_paths' array (from pages_ecg_cases)
    elif 'image_paths' in selected_case_data and selected_case_data['image_paths']:
        image_path = Path(selected_case_data['image_paths'][0])
    
    # Method 3: 'image_path' single (old format)
    elif 'image_path' in selected_case_data:
        image_path = case_folder / selected_case_data['image_path']
    
    # Method 4: Search for any ECG image in folder
    elif case_folder.exists():
        for pattern in ['ecg_*.png', 'ecg_*.jpg', '*.png', '*.jpg']:
            images = list(case_folder.glob(pattern))
            if images:
                image_path = images[0]
                break
    
    # Display ECG with advanced viewer
    if image_path and image_path.exists():
        try:
            from advanced_ecg_viewer import create_advanced_ecg_viewer
            st.success("🔍 **Visualiseur Avancé** - Zoom (molette) | Caliper (clic gauche) | Drag (clic droit)")
            viewer_html = create_advanced_ecg_viewer(
                image_path=str(image_path),
                title=selected_case_data.get('title', selected_case_data.get('name', 'ECG'))
            )
            st.components.v1.html(viewer_html, height=800, scrolling=False)
        except ImportError:
            # Fallback to simple image display
            st.image(str(image_path), caption=selected_case_data.get('title', 'ECG'), use_column_width=True)
    else:
        st.warning(f"⚠️ Image ECG non trouvée")
        if case_folder.exists():
            st.caption(f"📁 Dossier: {case_folder}")
            st.caption(f"📄 Fichiers: {list(case_folder.glob('*'))[:5]}")
    
    # Afficher diagnostic de référence (optionnel)
    with st.expander("📋 Voir le diagnostic de référence"):
        diagnosis = selected_case_data.get('diagnosis', selected_case_data.get('expected_concepts', []))
        if diagnosis:
            for diag in diagnosis:
                concept_text = diag if isinstance(diag, str) else diag.get('text', str(diag))
                st.write(f"• {concept_text}")
        else:
            st.info("Pas de diagnostic de référence")
    
    st.markdown("---")
    
    # Zone de réponse étudiant
    st.markdown("#### 3️⃣ Votre interprétation")
    
    student_answer = st.text_area(
        "Décrivez ce que vous observez sur cet ECG:",
        height=200,
        placeholder="Ex: Rythme sinusal régulier à 75 bpm. PR normal. QRS fins. Pas d'anomalie ST-T...",
        key="correction_student_answer"
    )
    
    # Bouton de correction
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        correct_button = st.button(
            "🚀 Corriger avec LLM",
            type="primary",
            use_container_width=True,
            disabled=not student_answer.strip()
        )
    
    if not student_answer.strip():
        st.info("💡 Entrez votre interprétation pour lancer la correction")
    
    # Traitement de la correction
    if correct_button and student_answer.strip():
        perform_correction(selected_case_data, student_answer)


def perform_correction(case_data, student_answer):
    """Effectue la correction et affiche les résultats"""
    
    with st.spinner("🤖 Correction en cours..."):
        try:
            # Étape 1: Extraction concepts LLM
            st.info("🔍 Étape 1/3: Extraction des concepts...")
            llm_service = LLMService()
            extraction_result = llm_service.extract_concepts(student_answer)
            student_concepts = extraction_result.get('concepts', [])
            
            if not student_concepts:
                st.error("❌ Aucun concept médical trouvé dans votre réponse")
                st.info("💡 Décrivez les éléments ECG observés (rythme, ondes, intervalles, etc.)")
                return
            
            st.success(f"✅ {len(student_concepts)} concepts extraits")
            
            # Étape 2: Récupérer concepts attendus
            st.info("📊 Étape 2/3: Scoring avec ontologie...")
            
            expected_concepts_raw = case_data.get('diagnosis', case_data.get('expected_concepts', []))
            
            if not expected_concepts_raw:
                st.warning("⚠️ Aucun concept attendu défini pour ce cas")
                return
            
            # Convertir en liste de strings
            expected_list = []
            for concept in expected_concepts_raw:
                if isinstance(concept, str):
                    expected_list.append(concept)
                elif isinstance(concept, dict):
                    expected_list.append(concept.get('text', ''))
            
            # Étape 3: Matching avec ontologie
            matched_concepts = []
            match_details = {}
            concept_weights = {}
            concept_scores = {}
            llm_matches = {}
            
            for expected in expected_list:
                match_found, match_type, matched_text, owl_concept, llm_result, score_pct = match_concept_with_ontology(
                    student_answer, expected, use_llm_semantic=True
                )
                
                # Stocker le poids du concept
                if owl_concept:
                    concept_weights[expected] = {
                        'poids': owl_concept.get('poids', 1),
                        'categorie': owl_concept.get('categorie', 'DESCRIPTEUR_ECG'),
                        'ontology_id': owl_concept.get('ontology_id', '')
                    }
                else:
                    concept_weights[expected] = {'poids': 1, 'categorie': 'DESCRIPTEUR_ECG', 'ontology_id': ''}
                
                if match_found:
                    matched_concepts.append(expected)
                    match_details[expected] = {
                        'type': match_type,
                        'matched_text': matched_text,
                        'poids': concept_weights[expected]['poids'],
                        'categorie': concept_weights[expected]['categorie']
                    }
                    concept_scores[expected] = score_pct
                    
                    if llm_result:
                        llm_matches[expected] = llm_result
            
            # Appliquer règles d'implication
            auto_validated = apply_implication_rules(matched_concepts, expected_list)
            all_validated = set(matched_concepts) | auto_validated
            
            # Calcul score pondéré
            poids_valides = sum(
                concept_weights.get(concept, {}).get('poids', 1) * (concept_scores.get(concept, 100.0) / 100.0)
                for concept in all_validated
            )
            
            poids_attendus = sum(
                concept_weights.get(concept, {}).get('poids', 1)
                for concept in expected_list
            )
            
            base_percentage = (poids_valides / poids_attendus * 100) if poids_attendus > 0 else 0
            
            # Bonus diagnostic
            has_diagnostic_principal = any(
                concept_weights.get(c, {}).get('poids', 1) >= 3 
                for c in all_validated
            )
            bonus_diagnostic = 0.15 if has_diagnostic_principal else 0
            percentage = min(100, base_percentage * (1 + bonus_diagnostic))
            
            st.success("✅ Correction terminée !")
            
            # Affichage résultats
            display_results(
                percentage, base_percentage, bonus_diagnostic,
                poids_valides, poids_attendus,
                matched_concepts, auto_validated, expected_list,
                match_details, concept_weights, llm_matches,
                student_answer
            )
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la correction: {e}")
            import traceback
            with st.expander("🔍 Détails de l'erreur"):
                st.code(traceback.format_exc())


def display_results(percentage, base_percentage, bonus_diagnostic,
                    poids_valides, poids_attendus,
                    matched_concepts, auto_validated, expected_list,
                    match_details, concept_weights, llm_matches,
                    student_answer):
    """Affiche les résultats de correction - Version POC enrichie"""
    
    # CSS pour cartes stylisées
    st.markdown("""
    <style>
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .stat-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📊 Résultat Global")
    
    # 4 cartes colorées style POC
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div>Score Global</div>
            <div class="stat-value">{percentage:.1f}%</div>
            <div>{poids_valides:.0f} / {poids_attendus:.0f} points pondérés</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        bonus_display = f"+{bonus_diagnostic*100:.0f}%" if bonus_diagnostic > 0 else "Aucun"
        bonus_color = "#28a745" if bonus_diagnostic > 0 else "#6c757d"
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, {bonus_color} 0%, {bonus_color}dd 100%);">
            <div>Bonus Diagnostic</div>
            <div class="stat-value">{bonus_display}</div>
            <div>{'🎯 Diagnostic identifié' if bonus_diagnostic > 0 else '⚪ Diagnostic manqué'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        exact_matches = len([c for c in matched_concepts if match_details.get(c, {}).get('type') == 'exact'])
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <div>Concepts Exacts</div>
            <div class="stat-value">{exact_matches}</div>
            <div>✅ Parfait</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_matched = len(set(matched_concepts) | auto_validated)
        missing = len(expected_list) - total_matched
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);">
            <div>Concepts Manquants</div>
            <div class="stat-value">{missing}</div>
            <div>❌ À revoir</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Détails par concept avec enrichissements POC
    st.subheader("🔍 Détails par Concept (Scoring Pondéré)")
    
    categorie_colors = {
        'DIAGNOSTIC_URGENT': ('#D32F2F', '🚨'),
        'DIAGNOSTIC_MAJEUR': ('#F57C00', '⚡'),
        'SIGNE_ECG_PATHOLOGIQUE': ('#FFA726', '⚠️'),
        'DESCRIPTEUR_ECG': ('#66BB6A', '📝')
    }
    
    for expected in expected_list:
        weight_info = concept_weights.get(expected, {})
        poids = weight_info.get('poids', 1)
        categorie = weight_info.get('categorie', 'DESCRIPTEUR_ECG')
        color, icon = categorie_colors.get(categorie, ('#66BB6A', '📝'))
        
        if expected in matched_concepts:
            # Concept trouvé
            details = match_details.get(expected, {})
            match_type = details.get('type', 'exact')
            matched_text = details.get('matched_text', expected)
            
            check_icon = '✅' if match_type == 'exact' else '🔍'
            type_label = {
                'exact': 'Match exact',
                'synonyme': 'Synonyme reconnu',
                'semantic': 'Match sémantique',
                'implication': 'Implication reconnue',
                'parent_concept': '⬆️ Concept parent (hiérarchie)'
            }.get(match_type, 'Match')
            
            # Info LLM si disponible
            llm_info = ""
            if expected in llm_matches:
                llm_result = llm_matches[expected]
                llm_confidence = llm_result.get('confidence', 0)
                llm_explanation = llm_result.get('explanation', '')
                llm_info = f"""<br>
                <div style="background-color: #e7f3ff; padding: 8px; margin-top: 6px; border-radius: 4px; border-left: 3px solid #17a2b8;">
                    🧠 <strong>LLM Semantic Matcher</strong> ({llm_confidence}% confiance)<br>
                    {llm_explanation}
                </div>"""
            
            st.markdown(f"""
            <div class="success-box" style="border-left-color: {color};">
                {check_icon} <strong>{expected}</strong> - {poids} pts {icon}<br>
                Type: {type_label} - Texte trouvé: "{matched_text}"<br>
                <small>Catégorie: {categorie.replace('_', ' ')}</small>
                {llm_info}
            </div>
            """, unsafe_allow_html=True)
            
        elif expected in auto_validated:
            # Concept auto-validé
            st.markdown(f"""
            <div class="success-box" style="background-color: #e7f3ff; border-left-color: {color};">
                🤖 <strong>{expected}</strong> - {poids} pts {icon} (Auto-validé)<br>
                Validé automatiquement par règle d'implication diagnostique<br>
                <small>Catégorie: {categorie.replace('_', ' ')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        else:
            # Concept manquant - avec suggestions
            owl_concept = find_owl_concept(expected)
            suggestion = ""
            if owl_concept and owl_concept.get('synonymes'):
                synonymes = owl_concept['synonymes']
                if synonymes:
                    suggestion = f"<br><em>💡 Synonymes acceptés: {', '.join(synonymes[:3])}</em>"
            
            st.markdown(f"""
            <div class="error-box" style="border-left-color: {color};">
                ❌ <strong>{expected}</strong> - <span style="color: {color};">-{poids} pts {icon}</span><br>
                Ce concept n'a pas été retrouvé dans votre réponse{suggestion}
                <br><small>Catégorie: {categorie.replace('_', ' ')}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Stats ontologie
    if WEIGHTED_ONTOLOGY:
        llm_stats = ""
        if llm_matches:
            llm_count = len(llm_matches)
            llm_avg_confidence = sum(r.get('confidence', 0) for r in llm_matches.values()) / llm_count if llm_count > 0 else 0
            llm_stats = f"""
        - 🧠 Matches LLM sémantiques: {llm_count} (confiance moyenne: {llm_avg_confidence:.0f}%)"""
        
        st.info(f"""
📚 **Scoring avec Ontologie OWL Pondérée**  
- ⚖️ Score: {base_percentage:.1f}% (base) + {bonus_diagnostic*100:.0f}% (bonus) = **{percentage:.1f}%**
- 🎯 Poids validés: {poids_valides:.0f} / {poids_attendus:.0f} points
- ✅ Match exacts: {exact_matches}
- 🔍 Synonymes reconnus: {len([c for c in matched_concepts if match_details.get(c, {}).get('type') == 'synonyme'])}
- 🤖 Auto-validés (implications): {len(auto_validated)}{llm_stats}
- 📊 Ontologie: {sum(len(cat['concepts']) for cat in WEIGHTED_ONTOLOGY['concept_categories'].values())} concepts avec poids
        """)


# ============================================================================
# HELPER FUNCTION FOR EXERCISE INTEGRATION
# ============================================================================

def run_correction_for_case(student_annotations, expert_concepts, case_id):
    """
    🎯 Helper function to run correction within exercise sessions
    
    Args:
        student_annotations: List of student annotation strings
        expert_concepts: List of expert concept strings
        case_id: Case identifier
    
    Returns:
        dict with correction results (score, correct_concepts, missing_concepts, extra_concepts)
    """
    try:
        from backend.services.llm_service import LLMService
        from backend.services.scoring_service_llm import SemanticScorer
        
        # Initialize services
        llm_service = LLMService()
        scorer = SemanticScorer()
        
        # Match student annotations to ontology
        matched_student = []
        for ann in student_annotations:
            match_result = match_concept_with_ontology(ann, ONTOLOGY_MAPPING, llm_service)
            if match_result and match_result.get('matched_concepts'):
                matched_student.extend(match_result['matched_concepts'])
        
        # Match expert concepts to ontology
        matched_expert = []
        for concept in expert_concepts:
            match_result = match_concept_with_ontology(concept, ONTOLOGY_MAPPING, llm_service)
            if match_result and match_result.get('matched_concepts'):
                matched_expert.extend(match_result['matched_concepts'])
        
        # Calculate score
        if not matched_expert:
            return {
                'score': 0,
                'correct_concepts': [],
                'missing_concepts': [],
                'extra_concepts': matched_student
            }
        
        # Find overlaps
        student_set = set(matched_student)
        expert_set = set(matched_expert)
        
        correct = list(student_set.intersection(expert_set))
        missing = list(expert_set - student_set)
        extra = list(student_set - expert_set)
        
        # Score = correct / total expected
        score = (len(correct) / len(expert_set)) * 100 if expert_set else 0
        
        return {
            'score': score,
            'correct_concepts': correct,
            'missing_concepts': missing,
            'extra_concepts': extra
        }
        
    except Exception as e:
        return {
            'score': 0,
            'error': str(e),
            'correct_concepts': [],
            'missing_concepts': [],
            'extra_concepts': []
        }


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    # Pour test standalone
    st.set_page_config(page_title="Correction LLM", page_icon="🔍", layout="wide")
    page_correction_llm()
