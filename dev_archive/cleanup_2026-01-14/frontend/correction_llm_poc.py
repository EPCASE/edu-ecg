"""
🧪 POC - Interface de Test Correction LLM
Interface Streamlit standalone pour tester le pipeline de correction

Auteur: Edu-ECG Team  
Date: 2026-01-10
Usage: streamlit run frontend/correction_llm_poc.py
"""

import streamlit as st
import sys
from pathlib import Path
import json
import os

# Charger variables d'environnement depuis .env
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Ajouter project root au path pour imports
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

# Helper: Trouver un concept dans l'ontologie OWL par son label français
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

# Helper: Matching avec ontologie et synonymes
def match_concept_with_ontology(student_text, expected_concept, use_llm_semantic=True):
    """
    Vérifie si le texte étudiant correspond au concept attendu
    en utilisant l'ontologie OWL pondérée (synonymes + labels)
    
    NOUVELLE ARCHITECTURE (2026-01-11) :
    Utilise SemanticScorer pour scoring hiérarchique directionnel
    - Diagnostic → Signe = 100% (implication validée)
    - Signe → Diagnostic = 40% (incomplet)
    
    Returns: (match_found, match_type, matched_text, owl_concept, llm_result, score_percentage)
    - match_found: bool
    - match_type: 'exact'|'synonyme'|'implication'|'semantic'|'parent_concept'|'partial'
    - matched_text: le texte qui a matché
    - owl_concept: dict avec poids et catégorie
    - llm_result: dict résultat LLM si utilisé, None sinon
    - score_percentage: float (0-100) - score partiel si signe incomplet
    """
    student_lower = student_text.lower()
    concept_lower = expected_concept.lower()
    
    # Dictionnaire de synonymes supplémentaires (en attendant enrichissement OWL)
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
    
    # ====================================================================
    # PHASE 0 : UTILISER SemanticScorer pour scoring hiérarchique
    # ====================================================================
    
    try:
        scorer = SemanticScorer()
        student_concept_dict = {'text': student_text, 'category': 'unknown'}
        expected_concept_dict = {'text': expected_concept, 'category': owl_concept.get('categorie', 'unknown') if owl_concept else 'unknown'}
        
        match_result = scorer._compare_concepts_llm(student_concept_dict, expected_concept_dict)
        
        # Si le score est > 0, c'est un match (même partiel)
        if match_result.score > 0:
            match_type_map = {
                'exact': 'exact',
                'child': 'implication',  # Diagnostic → Signe (100%)
                'partial': 'partial',     # Signe → Diagnostic (40%)
                'parent': 'parent_concept',
                'sibling': 'semantic_sibling'
            }
            
            return (
                True,
                match_type_map.get(match_result.match_type.value, 'semantic'),
                match_result.student_concept,
                owl_concept,
                {'explanation': match_result.explanation, 'score': match_result.score},
                match_result.score  # Score partiel (0-100)
            )
    except Exception as e:
        print(f"⚠️ SemanticScorer error: {e}, falling back to legacy matching")
    
    # ====================================================================
    # PHASE 1 : MATCHING DÉTERMINISTE (rapide, gratuit, reproductible)
    # ====================================================================
    
    # Match exact direct
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
    
    # Vérifier ontology_id (ex: "NSTEMI" pour "syndrome coronarien...")
    if owl_concept:
        ontology_id = owl_concept.get('ontology_id', '').lower().replace('_', ' ')
        if ontology_id in student_lower:
            return (True, 'ontology_id', owl_concept.get('ontology_id'), owl_concept, None, 100.0)
    
    # Vérifier si l'étudiant a utilisé un concept parent du concept attendu
    # Ex: étudiant dit "QRS normal" pour concept attendu "QRS fins"
    # DÉSACTIVÉ: Cette logique est maintenant gérée par SemanticScorer
    # if WEIGHTED_ONTOLOGY:
    #     concept_mappings = WEIGHTED_ONTOLOGY.get('concept_mappings', {})
    #     
    #     # Chercher le concept attendu dans les implications d'autres concepts
    #     for concept_id, concept_data in concept_mappings.items():
    #         concept_name = concept_data.get('concept_name', '')
    #         
    #         # Si ce concept a le concept attendu dans ses implications (enfants)
    #         if expected_concept in concept_data.get('implications', []):
    #             # Vérifier si l'étudiant a mentionné ce concept parent
    #             if concept_name.lower() in student_lower:
    #                 return (True, 'parent_concept', concept_name, owl_concept, None, 100.0)
    
    # ====================================================================
    # PHASE 2 : MATCHING SÉMANTIQUE LLM (si disponible et activé)
    # ====================================================================
    
    if use_llm_semantic and LLM_SEMANTIC_MATCHER_AVAILABLE:
        try:
            # Préparer contexte ontologique pour le LLM
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
            
            # Appeler le matching sémantique LLM
            llm_result = semantic_match(student_text, expected_concept, ontology_context)
            
            # Si LLM trouve un match, le retourner
            if llm_result.get('match'):
                return (
                    True, 
                    f"semantic_{llm_result.get('match_type')}", 
                    student_text, 
                    owl_concept, 
                    llm_result,
                    100.0  # LLM legacy donne toujours 100%
                )
        
        except Exception as e:
            # En cas d'erreur LLM, continuer sans (fallback gracieux)
            print(f"⚠️ Erreur LLM semantic matcher : {e}")
            pass
    
    # Pas de match trouvé (ni déterministe ni LLM)
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
    
    # Pour chaque concept matché par l'étudiant
    for matched_concept in matched_concepts:
        # Trouver son mapping
        mapping_key = None
        for k in concept_mappings.keys():
            if k.lower() == matched_concept.lower():
                mapping_key = k
                break
        
        if not mapping_key:
            continue
            
        mapping = concept_mappings[mapping_key]
        ontology_id = mapping.get('ontology_id', '')
        
        # Si ce concept a des règles d'implication
        if ontology_id in implication_rules:
            rule = implication_rules[ontology_id]
            auto_validate_ids = rule.get('auto_validate', [])
            
            # Pour chaque ID à auto-valider, trouver les concepts correspondants
            for auto_id in auto_validate_ids:
                # Chercher dans les expected_concepts lesquels correspondent à cet ID
                for expected in all_expected_concepts:
                    expected_mapping_key = None
                    for k in concept_mappings.keys():
                        if k.lower() == expected.lower():
                            expected_mapping_key = k
                            break
                    
                    if expected_mapping_key:
                        expected_mapping = concept_mappings[expected_mapping_key]
                        if expected_mapping.get('ontology_id', '') == auto_id:
                            auto_validated.add(expected)
    
    return auto_validated

def check_if_child_concept_used(expected_concept, student_answer):
    """
    Vérifie si l'étudiant a utilisé un concept enfant du concept attendu
    
    Args:
        expected_concept: Concept attendu (ex: "ECG normal")
        student_answer: Réponse complète de l'étudiant
    
    Returns:
        (bool, list[str]): (True/False, liste des concepts enfants trouvés)
    """
    if not WEIGHTED_ONTOLOGY:
        return (False, [])
    
    # Trouver le mapping du concept attendu
    concept_mappings = WEIGHTED_ONTOLOGY.get('concept_mappings', {})
    
    expected_owl = None
    for concept_id, concept_data in concept_mappings.items():
        if concept_data.get('concept_name', '').lower() == expected_concept.lower():
            expected_owl = concept_data
            break
    
    if not expected_owl:
        return (False, [])
    
    # Vérifier les implications (enfants dans la hiérarchie)
    implications = expected_owl.get('implications', [])
    if not implications:
        return (False, [])
    
    # Chercher si l'étudiant a mentionné un des enfants
    student_lower = student_answer.lower()
    found_children = []
    
    for child_name in implications:
        if child_name.lower() in student_lower:
            found_children.append(child_name)
            continue
        
        # Vérifier aussi les synonymes de l'enfant
        child_owl = None
        for concept_id, concept_data in concept_mappings.items():
            if concept_data.get('concept_name', '').lower() == child_name.lower():
                child_owl = concept_data
                break
        
        if child_owl:
            for synonyme in child_owl.get('synonymes', []):
                if synonyme.lower() in student_lower:
                    found_children.append(child_name)
                    break
    
    return (len(found_children) > 0, found_children)

# Configuration page
st.set_page_config(
    page_title="🧪 POC - Correction LLM ECG",
    page_icon="🫀",
    layout="wide"
)

# Style CSS
st.markdown("""
<style>
    .success-box {
        padding: 20px;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        padding: 20px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        padding: 20px;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        padding: 20px;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 48px;
        font-weight: bold;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Titre
st.title("🧪 POC - Système de Correction LLM")
st.markdown("**Proof of Concept** - Pipeline de correction automatique avec feedback pédagogique")

# Vérifier dépendances
if not LLM_AVAILABLE:
    st.error(f"""
    ❌ **Erreur d'import des services backend**
    
    Détail: {import_error}
    
    **Solutions:**
    1. Vérifier que les fichiers existent:
       - `backend/services/llm_service.py`
       - `backend/scoring_service_llm.py`
       - `backend/feedback_service.py`
    
    2. Installer dépendances:
       ```bash
       pip install openai rdflib
       ```
    """)
    st.stop()

# Vérifier clé OpenAI
if 'OPENAI_API_KEY' not in os.environ:
    st.warning("""
    ⚠️ **OPENAI_API_KEY non configurée**
    
    Le feedback GPT-4o ne fonctionnera pas. Configurez dans `.env`:
    ```
    OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
    ```
    
    Le scoring hiérarchique fonctionnera quand même !
    """)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Sélection cas test
    st.subheader("📁 Cas Test")
    
    # 🆕 Charger cas disponibles - NOUVELLE PRIORITÉ: Sessions créées + Epic 1 + Legacy
    ecg_sessions_dir = project_root / "data" / "ecg_sessions"
    ecg_cases_dir = project_root / "data" / "ecg_cases"
    epic1_file = project_root / "data" / "case_templates_epic1.json"
    test_cases_file = project_root / "data" / "test_cases.json"
    
    test_cases = []
    
    # 🆕 1. PRIORITÉ: Charger sessions créées depuis ecg_session_builder
    if ecg_sessions_dir.exists():
        session_files = list(ecg_sessions_dir.glob("session_*.json"))
        for session_file in sorted(session_files, reverse=True):  # Plus récents d'abord
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    
                    # Charger chaque cas de la session
                    for case_id in session_data.get('cases', []):
                        case_metadata_file = ecg_cases_dir / case_id / "metadata.json"
                        if case_metadata_file.exists():
                            with open(case_metadata_file, 'r', encoding='utf-8') as cf:
                                case_data = json.load(cf)
                                
                                # Convertir au format test_cases
                                test_cases.append({
                                    'case_id': case_data['case_id'],
                                    'title': f"[SESSION {session_data['name']}] {case_data.get('diagnostic_principal', case_id)}",
                                    'expected_answer': ", ".join(case_data.get('expected_concepts', [])),
                                    'expected_concepts': case_data.get('expected_concepts', []),
                                    'context': case_data.get('clinical_context', ''),
                                    'metadata': case_data.get('metadata', {}),
                                    'session_name': session_data['name'],
                                    'session_id': session_data['session_id']
                                })
            except Exception as e:
                st.sidebar.warning(f"⚠️ Erreur chargement session {session_file.name}: {e}")
    
    # 2. Charger Epic 1 templates
    if epic1_file.exists():
        with open(epic1_file, 'r', encoding='utf-8') as f:
            epic1_data = json.load(f)
            for template in epic1_data.get('templates', []):
                test_cases.append({
                    'case_id': template['case_id'],
                    'title': f"[EPIC1] {template['diagnostic_principal']}",
                    'expected_answer': ", ".join(template['expected_concepts']),
                    'expected_concepts': template['expected_concepts'],
                    'context': template.get('notes_pedagogiques', ''),
                    'metadata': template.get('metadata', {}),
                    'implications': template.get('implications', {}),
                    'niveau_difficulte': template.get('niveau_difficulte', 'moyen')
                })
    
    # 3. Charger test_cases.json legacy
    if test_cases_file.exists():
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            legacy_cases = json.load(f)
            for case in legacy_cases:
                case['title'] = f"[LEGACY] {case.get('title', case['case_id'])}"
            test_cases.extend(legacy_cases)
    
    if test_cases:
        case_options = [case['case_id'] + ": " + case['title'] for case in test_cases]
        selected_case_idx = st.selectbox(
            "Choisir un cas",
            range(len(case_options)),
            format_func=lambda i: case_options[i]
        )
        
        selected_case = test_cases[selected_case_idx]
    else:
        st.info("""
        📝 Aucun cas test trouvé.
        
        Créez `data/test_cases.json` avec vos annotations.
        
        Template disponible dans `data/test_cases_template.json`
        """)
        selected_case = None
    
    st.divider()
    
    # Paramètres correction
    st.subheader("🎯 Paramètres")
    
    student_level = st.select_slider(
        "Niveau étudiant",
        options=['beginner', 'intermediate', 'advanced'],
        value='intermediate',
        help="Adapte le ton du feedback"
    )
    
    use_llm_feedback = st.checkbox(
        "Feedback GPT-4o",
        value=True,
        help="Désactiver si pas de clé OpenAI"
    )
    
    use_llm_semantic = st.checkbox(
        "🧠 Matching Sémantique LLM",
        value=LLM_SEMANTIC_MATCHER_AVAILABLE,
        disabled=not LLM_SEMANTIC_MATCHER_AVAILABLE,
        help="Utilise GPT-4o pour comprendre variations linguistiques (BAV2M1, Sinusal, etc.). Le scoring reste géré par l'ontologie."
    )
    
    if use_llm_semantic and not LLM_SEMANTIC_MATCHER_AVAILABLE:
        st.warning("⚠️ LLM Semantic Matcher non disponible. Installer backend/services/llm_semantic_matcher.py")
    
    st.divider()
    
    # Stats POC
    st.subheader("📊 Stats Session")
    
    if 'corrections_count' not in st.session_state:
        st.session_state.corrections_count = 0
    
    st.metric("Corrections testées", st.session_state.corrections_count)

# Zone principale
tab1, tab2, tab3 = st.tabs(["🧪 Test Correction", "📚 Guide", "⚙️ Diagnostic"])

with tab1:
    st.header("🧪 Tester la Correction")
    
    if selected_case:
        # Afficher infos cas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📄 Cas: {selected_case['title']}")
            st.markdown(f"**ID:** `{selected_case['case_id']}`")
            st.markdown(f"**Catégorie:** {selected_case.get('category', 'Non spécifiée')}")
            
            if 'description' in selected_case:
                with st.expander("📖 Description du cas"):
                    st.info(selected_case['description'])
        
        with col2:
            # Concepts attendus
            st.subheader("✅ Concepts Attendus")
            expected_concepts = selected_case['expected_concepts']
            
            for concept in expected_concepts:
                # Support both formats: string (Epic 1) or dict (legacy)
                if isinstance(concept, str):
                    # Format Epic 1: simple strings
                    st.markdown(f"📌 {concept}")
                else:
                    # Format legacy: dict with category
                    category_icon = {
                        'rhythm': '🫀',
                        'conduction': '⚡',
                        'morphology': '📈',
                        'measurement': '📏',
                        'pathology': '🩺'
                    }.get(concept.get('category', ''), '📌')
                    
                    st.markdown(f"{category_icon} {concept['text']}")
        
        st.divider()
        
        # Zone saisie réponse étudiant
        st.subheader("✍️ Réponse Étudiant")
        
        # Exemples de réponses rapides
        if selected_case['case_id'] == 'BAV1_BBG_002':
            st.caption("💡 Exemples de réponses à tester:")
            col_ex1, col_ex2, col_ex3 = st.columns(3)
            
            with col_ex1:
                if st.button("📝 Réponse complète", use_container_width=True):
                    st.session_state.example_answer = """Rythme sinusal
Onde P normale
BAV 1er degré
Bloc de branche gauche complet"""
            
            with col_ex2:
                if st.button("📝 Sans diagnostics", use_container_width=True):
                    st.session_state.example_answer = """Rythme sinusal
Onde P normale
PR allongé
QRS larges"""
            
            with col_ex3:
                if st.button("📝 Avec axe", use_container_width=True):
                    st.session_state.example_answer = """Rythme sinusal
Onde P normale
BAV 1er degré
Bloc de branche gauche complet
Axe normal"""
        
        elif selected_case['case_id'] == 'RYTHME_SINUSAL_001':
            st.caption("💡 Exemples de réponses à tester:")
            col_ex1, col_ex2 = st.columns(2)
            
            with col_ex1:
                if st.button("📝 ECG normal (global)", use_container_width=True):
                    st.session_state.example_answer = "ECG normal"
            
            with col_ex2:
                if st.button("📝 Détails complets", use_container_width=True):
                    st.session_state.example_answer = """Rythme sinusal
Fréquence cardiaque normale
PR normal
QRS fins
Axe normal
Pas d'anomalie de repolarisation"""
        
        # Zone de texte avec pré-remplissage si exemple sélectionné
        default_text = st.session_state.get('example_answer', '')
        student_answer = st.text_area(
            "Entrez votre interprétation de l'ECG",
            value=default_text,
            placeholder="Exemple: Rythme sinusal, BAV 1er degré, PR prolongé à 220ms, axe normal...",
            height=150,
            help="Décrivez tous les éléments ECG que vous identifiez",
            key="student_answer_input"
        )
        
        # Reset example après utilisation
        if 'example_answer' in st.session_state and student_answer != default_text:
            del st.session_state.example_answer
        
        # Bouton correction
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            correct_button = st.button(
                "🚀 Corriger avec IA",
                type="primary",
                use_container_width=True,
                disabled=not student_answer
            )
        
        # Validation réponse vide
        if correct_button:
            if not student_answer or len(student_answer.strip()) < 5:
                st.error("⚠️ **Veuillez entrer une réponse** (minimum 5 caractères)")
                st.info("💡 Décrivez ce que vous voyez sur l'ECG : rythme, intervalles, anomalies, etc.")
                st.stop()
        
        # Traitement correction
        if correct_button and student_answer:
            with st.spinner("🤖 Correction en cours..."):
                try:
                    # Étape 1: Extraction concepts LLM
                    st.info("🔍 Étape 1/3: Extraction concepts avec LLM...")
                    llm_service = LLMService()
                    extraction_result = llm_service.extract_concepts(student_answer)
                    
                    student_concepts = extraction_result['concepts']
                    
                    # Étape 2: Scoring avec ontologie
                    st.info("📊 Étape 2/3: Scoring avec mapping ontologie...")
                    
                    # Convertir expected_concepts en liste de strings si nécessaire
                    expected_list = []
                    for concept in expected_concepts:
                        if isinstance(concept, str):
                            expected_list.append(concept)
                        else:
                            expected_list.append(concept.get('text', ''))
                    
                    # Matching avec ontologie et synonymes
                    matched_concepts = []
                    match_details = {}
                    concept_weights = {}  # Stocker les poids de chaque concept
                    concept_scores = {}   # 🆕 Stocker les scores partiels
                    llm_matches = {}  # Stocker les résultats LLM pour affichage
                    
                    for expected in expected_list:
                        match_found, match_type, matched_text, owl_concept, llm_result, score_pct = match_concept_with_ontology(
                            student_answer, expected, use_llm_semantic=use_llm_semantic
                        )
                        
                        # Stocker le poids du concept (même si non matché)
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
                            
                            # 🆕 Stocker le score partiel (0-100)
                            concept_scores[expected] = score_pct
                            
                            # Stocker résultat LLM si utilisé
                            if llm_result:
                                llm_matches[expected] = llm_result
                    
                    # Appliquer règles d'implication automatique
                    auto_validated = apply_implication_rules(matched_concepts, expected_list)
                    
                    # Combiner concepts matchés + auto-validés
                    all_validated = set(matched_concepts) | auto_validated
                    
                    # 🆕 Calcul du score PONDÉRÉ avec scores partiels
                    # Calculer la somme des poids validés (pondérés par le score partiel)
                    poids_valides = 0
                    for concept in all_validated:
                        poids = concept_weights.get(concept, {}).get('poids', 1)
                        score_pct = concept_scores.get(concept, 100.0) / 100.0  # 🆕 Utiliser score partiel
                        poids_valides += poids * score_pct  # 🆕 Pondérer par le score
                    
                    # Calculer la somme des poids attendus
                    poids_attendus = 0
                    for concept in expected_list:
                        poids_attendus += concept_weights.get(concept, {}).get('poids', 1)
                    
                    # Calcul pourcentage de base
                    base_percentage = (poids_valides / poids_attendus * 100) if poids_attendus > 0 else 0
                    
                    # Bonus si diagnostic principal (poids ≥3) identifié
                    has_diagnostic_principal = any(
                        concept_weights.get(c, {}).get('poids', 1) >= 3 
                        for c in all_validated
                    )
                    bonus_diagnostic = 0.15 if has_diagnostic_principal else 0
                    
                    # Score final avec bonus
                    percentage = min(100, base_percentage * (1 + bonus_diagnostic))
                    
                    # Stats détaillées pour affichage
                    total_expected = len(expected_list)
                    total_matched = len(all_validated)
                    exact_matches = len([c for c in matched_concepts if match_details.get(c, {}).get('type') == 'exact'])
                    synonyme_matches = len([c for c in matched_concepts if match_details.get(c, {}).get('type') == 'synonyme'])
                    auto_matches = len(auto_validated)
                    missing_concepts = total_expected - total_matched
                    
                    # Créer un objet résultat compatible avec feedback_service
                    class MatchType:
                        def __init__(self, value):
                            self.value = value
                    
                    class ConceptMatch:
                        def __init__(self, student_concept, expected_concept, match_type):
                            self.student_concept = student_concept
                            self.expected_concept = expected_concept
                            self.match_type = MatchType(match_type)
                    
                    class ScoringResult:
                        def __init__(self):
                            # Score pondéré
                            self.percentage = percentage
                            self.base_percentage = base_percentage
                            self.bonus_diagnostic = bonus_diagnostic
                            self.poids_valides = poids_valides
                            self.poids_attendus = poids_attendus
                            
                            # Stats basiques
                            self.total_score = total_matched
                            self.max_score = total_expected
                            self.exact_matches = exact_matches
                            self.synonyme_matches = synonyme_matches
                            self.auto_validated_count = auto_matches
                            self.missing_concepts = missing_concepts
                            
                            # Données détaillées
                            self.matched_list = list(matched_concepts)
                            self.auto_validated_list = list(auto_validated)
                            self.match_details = match_details
                            self.concept_weights = concept_weights
                            self.expected_list = expected_list
                            
                            # Créer liste de matches pour feedback_service
                            self.matches = []
                            
                            # Ajouter matches exacts et synonymes
                            for concept in matched_concepts:
                                match_type = match_details.get(concept, {}).get('type', 'exact')
                                self.matches.append(
                                    ConceptMatch(concept, concept, match_type)
                                )
                            
                            # Ajouter auto-validés comme matches spéciaux
                            for concept in auto_validated:
                                self.matches.append(
                                    ConceptMatch(concept, concept, 'implication')
                                )
                            
                            # Ajouter concepts manquants
                            missing = set(expected_list) - all_validated
                            for concept in missing:
                                self.matches.append(
                                    ConceptMatch('', concept, 'missing')
                                )
                    
                    scoring_result = ScoringResult()
                    
                    # Étape 3: Feedback pédagogique
                    if use_llm_feedback and 'OPENAI_API_KEY' in os.environ:
                        st.info("💬 Étape 3/3: Génération feedback GPT-4o...")
                        feedback_service = FeedbackService()
                        feedback = feedback_service.generate_feedback(
                            case_title=selected_case['title'],
                            student_answer=student_answer,
                            scoring_result=scoring_result,
                            student_level=student_level
                        )
                    else:
                        feedback = None
                    
                    # Incrémenter compteur
                    st.session_state.corrections_count += 1
                    
                    # Affichage résultats
                    st.success("✅ Correction terminée !")
                    
                    st.divider()
                    
                    # Score global
                    st.subheader("📊 Résultat Global")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div>Score Global</div>
                            <div class="stat-value">{scoring_result.percentage:.1f}%</div>
                            <div>{scoring_result.poids_valides:.0f} / {scoring_result.poids_attendus:.0f} points pondérés</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        bonus_display = f"+{scoring_result.bonus_diagnostic*100:.0f}%" if scoring_result.bonus_diagnostic > 0 else "Aucun"
                        bonus_color = "#28a745" if scoring_result.bonus_diagnostic > 0 else "#6c757d"
                        st.markdown(f"""
                        <div class="stat-card" style="background: linear-gradient(135deg, {bonus_color} 0%, {bonus_color}dd 100%);">
                            <div>Bonus Diagnostic</div>
                            <div class="stat-value">{bonus_display}</div>
                            <div>{'🎯 Diagnostic identifié' if scoring_result.bonus_diagnostic > 0 else '⚪ Diagnostic manqué'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                            <div>Concepts Exacts</div>
                            <div class="stat-value">{scoring_result.exact_matches}</div>
                            <div>✅ Parfait</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="stat-card" style="background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);">
                            <div>Concepts Manquants</div>
                            <div class="stat-value">{scoring_result.missing_concepts}</div>
                            <div>❌ À revoir</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Détails concepts avec mapping ontologie
                    st.subheader("🔍 Détails par Concept (Scoring Pondéré)")
                    
                    # Couleurs par catégorie
                    categorie_colors = {
                        'DIAGNOSTIC_URGENT': ('#D32F2F', '🚨'),
                        'DIAGNOSTIC_MAJEUR': ('#F57C00', '⚡'),
                        'SIGNE_ECG_PATHOLOGIQUE': ('#FFA726', '⚠️'),
                        'DESCRIPTEUR_ECG': ('#66BB6A', '📝')
                    }
                    
                    # Afficher concepts matchés
                    for expected in scoring_result.expected_list:
                        weight_info = scoring_result.concept_weights.get(expected, {})
                        poids = weight_info.get('poids', 1)
                        categorie = weight_info.get('categorie', 'DESCRIPTEUR_ECG')
                        color, icon = categorie_colors.get(categorie, ('#66BB6A', '📝'))
                        
                        if expected in scoring_result.matched_list:
                            # Concept trouvé par l'étudiant
                            details = scoring_result.match_details.get(expected, {})
                            match_type = details.get('type', 'exact')
                            matched_text = details.get('matched_text', expected)
                            
                            check_icon = '✅' if match_type == 'exact' else '🔍'
                            type_label = {
                                'exact': 'Match exact',
                                'synonyme': 'Synonyme reconnu',
                                'ontology_id': 'ID ontologie',
                                'semantic': 'Match sémantique',
                                'semantic_exact': '🎯 Match sémantique exact (LLM)',
                                'semantic_synonym': '🔄 Synonyme sémantique (LLM)',
                                'semantic_abbreviation': '📝 Abréviation reconnue (LLM)',
                                'semantic_equivalent': '≈ Équivalent sémantique (LLM)',
                                'semantic_parent': '⬆️ Concept parent (LLM)',
                                'semantic_child': '⬇️ Concept enfant (LLM)',
                                'parent_concept': '⬆️ Concept parent (hiérarchie)'
                            }.get(match_type, 'Match')
                            
                            # Vérifier si matching LLM utilisé
                            llm_info = ""
                            if expected in llm_matches:
                                llm_result = llm_matches[expected]
                                llm_emoji = get_match_type_emoji(llm_result.get('match_type', ''))
                                llm_confidence = llm_result.get('confidence', 0)
                                llm_explanation = llm_result.get('explanation', '')
                                llm_info = f"""<br>
                                <div style="background-color: #e7f3ff; padding: 8px; margin-top: 6px; border-radius: 4px; border-left: 3px solid #17a2b8;">
                                    🧠 <strong>LLM Semantic Matcher</strong> ({llm_confidence}% confiance)<br>
                                    {llm_emoji} {llm_explanation}
                                </div>"""
                            
                            st.markdown(f"""
                            <div class="success-box" style="border-left-color: {color};">
                                {check_icon} <strong>{expected}</strong> - {poids} pts {icon}<br>
                                Type: {type_label} - Texte trouvé: "{matched_text}"<br>
                                <small>Catégorie: {categorie.replace('_', ' ')}</small>
                                {llm_info}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        elif expected in scoring_result.auto_validated_list:
                            # Concept auto-validé par implication
                            st.markdown(f"""
                            <div class="success-box" style="background-color: #e7f3ff; border-left-color: {color};">
                                🤖 <strong>{expected}</strong> - {poids} pts {icon} (Auto-validé)<br>
                                Validé automatiquement par règle d'implication diagnostique<br>
                                <small>Catégorie: {categorie.replace('_', ' ')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        else:
                            # Concept manquant
                            # Vérifier si l'étudiant a utilisé un concept enfant
                            has_child, child_concepts = check_if_child_concept_used(expected, student_answer)
                            
                            # Afficher suggestion de synonymes si mapping existe
                            suggestion = ""
                            owl_concept = find_owl_concept(expected)
                            if owl_concept and owl_concept.get('synonymes'):
                                synonymes = owl_concept['synonymes']
                                if synonymes:
                                    suggestion = f"<br><em>💡 Synonymes acceptés: {', '.join(synonymes[:3])}</em>"
                            
                            # Message pédagogique si concepts enfants trouvés
                            child_message = ""
                            if has_child and child_concepts:
                                child_list = ', '.join([f"<strong>{c}</strong>" for c in child_concepts[:3]])
                                child_message = f"""<br>
                                <div style="background-color: #fff3cd; padding: 10px; margin-top: 8px; border-radius: 4px; border-left: 3px solid #ffc107;">
                                    ⚠️ <strong>Attention pédagogique :</strong><br>
                                    Vous avez mentionné {child_list} qui {'font' if len(child_concepts) > 1 else 'fait'} partie de "<strong>{expected}</strong>".<br>
                                    Ces éléments sont corrects mais <strong>ne remplacent pas</strong> le diagnostic complet attendu.<br>
                                    💡 <em>Pensez à donner la réponse la plus complète et synthétique.</em>
                                </div>"""
                            
                            st.markdown(f"""
                            <div class="error-box" style="border-left-color: {color};">
                                ❌ <strong>{expected}</strong> - <span style="color: {color};">-{poids} pts {icon}</span><br>
                                Ce concept n'a pas été retrouvé dans votre réponse{suggestion}
                                {child_message}
                                <br><small>Catégorie: {categorie.replace('_', ' ')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Stats du matching ontologie
                    if WEIGHTED_ONTOLOGY:
                        llm_stats = ""
                        if llm_matches:
                            llm_count = len(llm_matches)
                            llm_avg_confidence = sum(r.get('confidence', 0) for r in llm_matches.values()) / llm_count if llm_count > 0 else 0
                            llm_stats = f"""
                        - 🧠 Matches LLM sémantiques: {llm_count} (confiance moyenne: {llm_avg_confidence:.0f}%)"""
                        
                        st.info(f"""
                        📚 **Scoring avec Ontologie OWL Pondérée**  
                        - ⚖️ Score: {scoring_result.base_percentage:.1f}% (base) + {scoring_result.bonus_diagnostic*100:.0f}% (bonus) = **{scoring_result.percentage:.1f}%**
                        - 🎯 Poids validés: {scoring_result.poids_valides:.0f} / {scoring_result.poids_attendus:.0f} points
                        - ✅ Match exacts: {scoring_result.exact_matches}  
                        - 🔍 Synonymes reconnus: {scoring_result.synonyme_matches}  
                        - 🤖 Auto-validés (implications): {scoring_result.auto_validated_count}{llm_stats}  
                        - 📊 Ontologie: {sum(len(cat['concepts']) for cat in WEIGHTED_ONTOLOGY['concept_categories'].values())} concepts avec poids
                        """)
                    elif ONTOLOGY_MAPPING:
                        st.info(f"""
                        📚 **Scoring avec ontologie activé**  
                        - Match exacts: {scoring_result.exact_matches}  
                        - Synonymes reconnus: {scoring_result.synonyme_matches}  
                        - Auto-validés (implications): {scoring_result.auto_validated_count}  
                        - Mapping: {len(ONTOLOGY_MAPPING.get('concept_mappings', {}))} concepts ontologie
                        """)
                    
                    
                    # Feedback pédagogique
                    if feedback:
                        st.divider()
                        st.subheader("💬 Feedback Pédagogique")
                        
                        st.markdown(f"**{feedback.summary}**")
                        
                        if feedback.strengths:
                            st.success("**✅ Points Forts**\n\n" + "\n".join(f"- {s}" for s in feedback.strengths))
                        
                        if feedback.missing_concepts:
                            st.warning("**📚 À Apprendre**\n\n" + "\n".join(f"- {m}" for m in feedback.missing_concepts))
                        
                        if feedback.errors:
                            st.error("**❌ Erreurs à Corriger**\n\n" + "\n".join(f"- {e}" for e in feedback.errors))
                        
                        st.info(f"**💡 Conseil**\n\n{feedback.advice}")
                        
                        st.markdown(f"**🎯 Prochaines Étapes**\n\n{feedback.next_steps}")
                    
                except Exception as e:
                    st.error(f"""
                    ❌ **Erreur lors de la correction**
                    
                    ```
                    {str(e)}
                    ```
                    
                    Vérifiez:
                    1. Clé OPENAI_API_KEY configurée
                    2. Services backend accessibles
                    3. Logs dans terminal
                    """)
                    
                    import traceback
                    with st.expander("🐛 Stack trace complète"):
                        st.code(traceback.format_exc())
    
    else:
        st.warning("Aucun cas test sélectionné. Chargez `data/test_cases.json` ou créez-en un.")

with tab2:
    st.header("📚 Guide d'Utilisation")
    
    st.markdown("""
    ## 🎯 Objectif du POC
    
    Ce POC permet de tester le **pipeline de correction automatique LLM** avant intégration complète.
    
    ### 🔄 Pipeline en 3 Étapes
    
    1. **Extraction Concepts (LLM)**
       - Utilise GPT-4o pour extraire concepts médicaux
       - Catégorise : rhythm, conduction, morphology, measurement, pathology
       - Fallback regex si API échoue
    
    2. **Scoring Hiérarchique**
       - Compare réponse étudiant vs attendu
       - Scores: Exact (100 pts), Child (85-90), Parent (60-80), Missing (0)
       - Pondération par catégorie (rhythm ×1.2, measurement ×0.8)
    
    3. **Feedback Pédagogique (GPT-4o)**
       - Génère feedback personnalisé et bienveillant
       - Adapte ton selon niveau (beginner/intermediate/advanced)
       - Structure: Points forts → À améliorer → Conseil → Prochaines étapes
    
    ### 📝 Comment Annoter un Cas
    
    1. Créez/éditez `data/test_cases.json`
    2. Format:
    ```json
    [
      {
        "case_id": "BAV1_001",
        "title": "BAV 1er degré simple",
        "category": "conduction",
        "description": "ECG montrant BAV 1er degré isolé",
        "expected_concepts": [
          {"text": "Rythme sinusal", "category": "rhythm"},
          {"text": "BAV 1er degré", "category": "conduction"},
          {"text": "PR > 200ms", "category": "measurement"}
        ]
      }
    ]
    ```
    
    ### ✅ Métriques de Validation
    
    - **Precision**: % concepts corrects parmi ceux identifiés
    - **Recall**: % concepts attendus trouvés
    - **F1-Score**: Moyenne harmonique Precision/Recall
    - **Cible POC**: F1 > 70%
    - **Cible Production**: F1 > 80%
    
    ### 🚀 Prochaines Étapes
    
    - **Semaine 1**: Test 3-5 cas, démo informelle
    - **Semaine 2**: 10 cas annotés, métriques, démo formelle
    - **Semaine 3-4**: Backend PostgreSQL, module progression
    """)

with tab3:
    st.header("⚙️ Diagnostic Système")
    
    # Vérifier services
    st.subheader("🔍 Services Backend")
    
    services_status = {
        "LLM Service": Path(project_root / "backend" / "services" / "llm_service.py").exists(),
        "Ontology Service": Path(project_root / "backend" / "ontology_service.py").exists(),
        "Scoring Service (LLM)": Path(project_root / "backend" / "scoring_service_llm.py").exists(),
        "Feedback Service": Path(project_root / "backend" / "feedback_service.py").exists()
    }
    
    for service, status in services_status.items():
        if status:
            st.success(f"✅ {service}")
        else:
            st.error(f"❌ {service}")
    
    st.divider()
    
    # Vérifier environnement
    st.subheader("🔐 Variables d'Environnement")
    
    env_vars = {
        "OPENAI_API_KEY": 'OPENAI_API_KEY' in os.environ,
        "REDIS_URL": 'REDIS_URL' in os.environ,
        "DATABASE_URL": 'DATABASE_URL' in os.environ
    }
    
    for var, status in env_vars.items():
        if status:
            st.success(f"✅ {var} configurée")
        else:
            st.warning(f"⚠️ {var} non configurée (optionnel pour POC)")
    
    st.divider()
    
    # Vérifier données
    st.subheader("📁 Fichiers de Données")
    
    data_files = {
        "test_cases.json": Path(project_root / "data" / "test_cases.json").exists(),
        "ontologie.owx": Path(project_root / "data" / "ontologie.owx").exists()
    }
    
    for file, status in data_files.items():
        if status:
            st.success(f"✅ {file}")
        else:
            st.info(f"ℹ️ {file} - Créer pour tester")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    🫀 <strong>Edu-ECG POC</strong> - Système de Correction LLM<br>
    Semaine 1 - Proof of Concept<br>
    <em>Développé avec BMad Method - Scénario C Hybride Pragmatique</em>
</div>
""", unsafe_allow_html=True)
