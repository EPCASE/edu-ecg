"""
🎓 Interface Complète de Correction ECG
Interface professionnelle pour la correction interactive d'ECG avec LLM

Auteur: BMAD Party Mode Team
Date: 2026-01-11
Version: 1.0

Features:
- Sélection de cas/sessions
- Affichage ECG interactif
- Correction temps réel avec scoring hiérarchique
- Feedback pédagogique enrichi
- Tableau de bord et statistiques
- Export PDF des résultats
- Historique des corrections

Usage: streamlit run frontend/interface_correction_complete.py --server.port 8503
"""

import streamlit as st
import sys
from pathlib import Path
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import base64

# Configuration de la page (DOIT être en premier)
st.set_page_config(
    page_title="🎓 Edu-ECG - Correction Interactive",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger variables d'environnement
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Ajouter project root au path
sys.path.insert(0, str(project_root))

# Imports backend
try:
    from backend.services.llm_service import LLMService
    from backend.scoring_service_llm import SemanticScorer
    from backend.feedback_service import FeedbackService
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    import_error = str(e)

# Charger ontologie OWL
WEIGHTED_ONTOLOGY = None
owl_mapping_file = project_root / "data" / "ontology_from_owl.json"
if owl_mapping_file.exists():
    with open(owl_mapping_file, 'r', encoding='utf-8') as f:
        WEIGHTED_ONTOLOGY = json.load(f)

# ============================================================================
# UTILITAIRES
# ============================================================================

def load_image_as_base64(image_path: Path) -> Optional[str]:
    """Charge une image et la convertit en base64 pour affichage"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None


def find_owl_concept(concept_text: str) -> Optional[Dict]:
    """Cherche un concept dans l'ontologie OWL"""
    if not WEIGHTED_ONTOLOGY:
        return None
    
    concept_lower = concept_text.lower().strip()
    concept_mappings = WEIGHTED_ONTOLOGY.get('concept_mappings', {})
    
    # Recherche exacte
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
    
    # Recherche par synonymes
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
    
    return None


def load_sessions() -> List[Dict]:
    """Charge toutes les sessions disponibles"""
    sessions_dir = project_root / "data" / "ecg_sessions"
    sessions = []
    
    if sessions_dir.exists():
        for session_file in sorted(sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    session_data['file_path'] = str(session_file)
                    sessions.append(session_data)
            except:
                pass
    
    return sessions


def load_case_metadata(case_id: str) -> Optional[Dict]:
    """Charge les métadonnées d'un cas"""
    case_dir = project_root / "data" / "ecg_cases" / case_id
    metadata_file = case_dir / "metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return None


def get_case_image_path(case_id: str) -> Optional[Path]:
    """Récupère le chemin de l'image ECG d'un cas"""
    case_dir = project_root / "data" / "ecg_cases" / case_id
    
    # Chercher l'image (plusieurs formats possibles)
    for ext in ['.png', '.jpg', '.jpeg', '.pdf']:
        image_file = case_dir / f"ecg{ext}"
        if image_file.exists():
            return image_file
    
    return None


def save_correction_history(case_id: str, student_answer: str, score: float, details: Dict):
    """Sauvegarde l'historique des corrections"""
    history_dir = project_root / "data" / "correction_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    
    history_file = history_dir / f"{case_id}_history.json"
    
    # Charger historique existant
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    # Ajouter nouvelle entrée
    history.append({
        'timestamp': datetime.now().isoformat(),
        'student_answer': student_answer,
        'score': score,
        'details': details
    })
    
    # Sauvegarder
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

def main():
    """Interface principale"""
    
    # ========================================================================
    # SIDEBAR - NAVIGATION
    # ========================================================================
    
    with st.sidebar:
        st.title("🫀 Edu-ECG")
        st.markdown("### Correction Interactive")
        
        # Menu de navigation
        page = st.radio(
            "Navigation",
            ["📝 Correction", "📊 Tableau de bord", "📚 Historique", "⚙️ Paramètres"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Sélection de session/cas
        st.subheader("🗂️ Sélection")
        
        sessions = load_sessions()
        
        selection_mode = st.radio(
            "Mode",
            ["Session complète", "Cas individuel"],
            horizontal=True
        )
        
        selected_case = None
        selected_session = None
        
        if selection_mode == "Session complète" and sessions:
            session_options = [f"📁 {s.get('name', s.get('nom', 'Session'))} ({len(s.get('cases', s.get('cas_ids', [])))} cas)" for s in sessions]
            selected_idx = st.selectbox("Session", range(len(sessions)), format_func=lambda i: session_options[i])
            selected_session = sessions[selected_idx]
            
            # Sélection du cas dans la session
            case_list = selected_session.get('cases', selected_session.get('cas_ids', []))
            case_idx = st.selectbox(
                "Cas",
                range(len(case_list)),
                format_func=lambda i: f"Cas {i+1}/{len(case_list)}"
            )
            case_id = case_list[case_idx]
            selected_case = load_case_metadata(case_id)
            
        elif selection_mode == "Cas individuel":
            # Liste tous les cas disponibles
            cases_dir = project_root / "data" / "ecg_cases"
            if cases_dir.exists():
                case_ids = [d.name for d in cases_dir.iterdir() if d.is_dir()]
                if case_ids:
                    case_id = st.selectbox("Cas", case_ids)
                    selected_case = load_case_metadata(case_id)
        
        st.divider()
        
        # Informations sur le cas sélectionné
        if selected_case:
            st.subheader("📋 Informations")
            st.markdown(f"**Diagnostic :** {selected_case.get('diagnostic_principal', 'N/A')}")
            st.markdown(f"**Concepts :** {len(selected_case.get('expected_concepts', []))}")
            
            # Afficher catégories des concepts
            categories = set()
            for concept in selected_case.get('expected_concepts', []):
                owl_concept = find_owl_concept(concept)
                if owl_concept:
                    categories.add(owl_concept['categorie'])
            
            if categories:
                st.markdown(f"**Catégories :** {', '.join(categories)}")
        
        st.divider()
        
        # Statistiques rapides
        st.subheader("📈 Stats")
        if WEIGHTED_ONTOLOGY:
            total_concepts = len(WEIGHTED_ONTOLOGY.get('concept_mappings', {}))
            st.metric("Concepts dans l'ontologie", total_concepts)
        
        if LLM_AVAILABLE:
            st.success("✅ LLM actif")
        else:
            st.error("❌ LLM indisponible")
    
    # ========================================================================
    # CONTENU PRINCIPAL
    # ========================================================================
    
    if page == "📝 Correction":
        show_correction_page(selected_case)
    elif page == "📊 Tableau de bord":
        show_dashboard_page()
    elif page == "📚 Historique":
        show_history_page()
    elif page == "⚙️ Paramètres":
        show_settings_page()


def show_correction_page(selected_case: Optional[Dict]):
    """Page de correction"""
    
    st.title("📝 Correction Interactive ECG")
    
    if not selected_case:
        st.info("👈 Sélectionnez un cas dans la barre latérale pour commencer")
        return
    
    # ========================================================================
    # AFFICHAGE ECG
    # ========================================================================
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🫀 ECG à analyser")
        
        # Afficher l'image ECG
        case_id = selected_case.get('case_id')
        image_path = get_case_image_path(case_id)
        
        if image_path and image_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            st.image(str(image_path), use_container_width=True)
        elif image_path:
            st.info(f"📄 Fichier : {image_path.name}")
        else:
            st.warning("⚠️ Image ECG non disponible")
    
    with col2:
        st.subheader("ℹ️ Contexte clinique")
        
        # Afficher le contexte
        context = selected_case.get('clinical_context', selected_case.get('description', ''))
        if context:
            st.info(context)
        else:
            st.warning("Aucun contexte clinique")
        
        # Informations sur les concepts attendus
        st.markdown("**Concepts à identifier :**")
        expected_concepts = selected_case.get('expected_concepts', [])
        
        with st.expander(f"Voir les {len(expected_concepts)} concepts", expanded=False):
            for concept in expected_concepts:
                owl_concept = find_owl_concept(concept)
                if owl_concept:
                    poids = owl_concept['poids']
                    emoji = "🚨" if poids >= 3 else "📌" if poids == 2 else "📝"
                    st.markdown(f"{emoji} {concept} (poids: {poids})")
                else:
                    st.markdown(f"📝 {concept}")
    
    st.divider()
    
    # ========================================================================
    # ZONE DE RÉPONSE
    # ========================================================================
    
    st.subheader("✍️ Votre réponse")
    
    student_answer = st.text_area(
        "Décrivez ce que vous observez sur cet ECG",
        height=150,
        placeholder="Ex: Rythme sinusal, PR allongé à 240ms, QRS fins, absence d'onde P...",
        key="student_answer"
    )
    
    # Boutons d'aide
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💡 Astuce", use_container_width=True):
            st.info("Analysez systématiquement : Rythme → Fréquence → Axes → Intervalles → Ondes")
    
    with col2:
        if st.button("📖 Exemple", use_container_width=True):
            st.info("Ex: 'Rythme sinusal régulier, FC 75 bpm, PR allongé 250ms, QRS fins, pas d'onde Q pathologique'")
    
    with col3:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.student_answer = ""
            st.rerun()
    
    with col4:
        correct_button = st.button(
            "🚀 Corriger",
            type="primary",
            use_container_width=True,
            disabled=not student_answer or len(student_answer.strip()) < 5
        )
    
    # ========================================================================
    # CORRECTION
    # ========================================================================
    
    if correct_button and student_answer:
        with st.spinner("🤖 Correction en cours..."):
            try:
                # Étape 1: Extraction
                st.info("🔍 Extraction des concepts...")
                llm_service = LLMService()
                extraction_result = llm_service.extract_concepts(student_answer)
                student_concepts = extraction_result['concepts']
                
                # Étape 2: Scoring
                st.info("📊 Scoring avec ontologie...")
                scorer = SemanticScorer()
                
                expected_list = selected_case.get('expected_concepts', [])
                
                matched_details = []
                total_score = 0
                total_weight = 0
                
                for expected in expected_list:
                    owl_concept = find_owl_concept(expected)
                    weight = owl_concept['poids'] if owl_concept else 1
                    total_weight += weight
                    
                    # Comparer avec SemanticScorer
                    best_match = None
                    best_score = 0
                    
                    for student_concept in student_concepts:
                        student_dict = {'text': student_concept['text'], 'category': 'unknown'}
                        expected_dict = {'text': expected, 'category': owl_concept['categorie'] if owl_concept else 'unknown'}
                        
                        match_result = scorer._compare_concepts_llm(student_dict, expected_dict)
                        
                        if match_result.score > best_score:
                            best_score = match_result.score
                            best_match = match_result
                    
                    if best_match:
                        total_score += weight * (best_match.score / 100)
                        matched_details.append({
                            'expected': expected,
                            'match': best_match,
                            'weight': weight,
                            'owl_concept': owl_concept
                        })
                    else:
                        matched_details.append({
                            'expected': expected,
                            'match': None,
                            'weight': weight,
                            'owl_concept': owl_concept
                        })
                
                # Score final
                final_score = (total_score / total_weight * 100) if total_weight > 0 else 0
                
                # Sauvegarder historique
                save_correction_history(case_id, student_answer, final_score, {
                    'matched_details': [
                        {
                            'expected': d['expected'],
                            'score': d['match'].score if d['match'] else 0,
                            'type': d['match'].match_type.value if d['match'] else 'missing'
                        }
                        for d in matched_details
                    ]
                })
                
                st.success("✅ Correction terminée !")
                
                # ============================================================
                # AFFICHAGE RÉSULTATS
                # ============================================================
                
                st.divider()
                st.header("📊 Résultats")
                
                # Score global
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score_color = "🟢" if final_score >= 80 else "🟠" if final_score >= 60 else "🔴"
                    st.metric("Score Global", f"{final_score:.1f}%", delta=None)
                    st.markdown(f"{score_color} **{'Excellent !' if final_score >= 80 else 'Bien' if final_score >= 60 else 'À améliorer'}**")
                
                with col2:
                    exact_matches = sum(1 for d in matched_details if d['match'] and d['match'].score == 100)
                    st.metric("Concepts exacts", f"{exact_matches}/{len(expected_list)}")
                
                with col3:
                    partial_matches = sum(1 for d in matched_details if d['match'] and 0 < d['match'].score < 100)
                    st.metric("Concepts partiels", partial_matches)
                
                st.divider()
                
                # Détails par concept
                st.subheader("🔍 Détails par concept")
                
                for detail in matched_details:
                    expected = detail['expected']
                    match = detail['match']
                    weight = detail['weight']
                    owl_concept = detail['owl_concept']
                    
                    with st.expander(f"{'✅' if match and match.score >= 80 else '⚠️' if match and match.score > 0 else '❌'} {expected} - Poids: {weight}"):
                        if match:
                            st.markdown(f"**Score :** {match.score:.0f}%")
                            st.markdown(f"**Type :** {match.match_type.value}")
                            st.markdown(f"**Explication :** {match.explanation}")
                            
                            if owl_concept:
                                st.markdown(f"**Catégorie :** {owl_concept['categorie']}")
                                if owl_concept.get('synonymes'):
                                    st.markdown(f"**Synonymes :** {', '.join(owl_concept['synonymes'][:3])}")
                        else:
                            st.error("❌ Concept non identifié")
                            if owl_concept and owl_concept.get('implications'):
                                st.info(f"💡 Astuce : Ce concept peut impliquer : {', '.join(owl_concept['implications'][:2])}")
                
                st.divider()
                
                # Feedback pédagogique
                st.subheader("💬 Feedback pédagogique")
                
                if final_score >= 80:
                    st.success("🎉 Excellente analyse ! Vous maîtrisez bien l'interprétation ECG.")
                elif final_score >= 60:
                    st.info("👍 Bonne analyse, mais quelques points à revoir.")
                else:
                    st.warning("💪 Continuez à pratiquer, vous progresserez !")
                
                # Points forts et à améliorer
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### ✅ Points forts")
                    strong_points = [d for d in matched_details if d['match'] and d['match'].score >= 80]
                    if strong_points:
                        for point in strong_points[:3]:
                            st.markdown(f"- {point['expected']}")
                    else:
                        st.markdown("_Aucun concept parfaitement identifié_")
                
                with col2:
                    st.markdown("#### 📚 À améliorer")
                    weak_points = [d for d in matched_details if not d['match'] or d['match'].score < 60]
                    if weak_points:
                        for point in weak_points[:3]:
                            st.markdown(f"- {point['expected']}")
                    else:
                        st.markdown("_Rien à signaler !_")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la correction : {e}")
                import traceback
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())


def show_dashboard_page():
    """Page tableau de bord"""
    st.title("📊 Tableau de bord")
    st.info("🚧 Tableau de bord en construction...")
    
    # TODO: Statistiques globales, progression, etc.


def show_history_page():
    """Page historique"""
    st.title("📚 Historique des corrections")
    st.info("🚧 Historique en construction...")
    
    # TODO: Afficher l'historique des corrections


def show_settings_page():
    """Page paramètres"""
    st.title("⚙️ Paramètres")
    
    st.subheader("Configuration")
    
    # Paramètres LLM
    with st.expander("🤖 Paramètres LLM", expanded=True):
        st.checkbox("Utiliser matching sémantique LLM", value=True, key="use_llm")
        st.slider("Seuil de confiance", 0.0, 1.0, 0.7, 0.05, key="confidence_threshold")
    
    # Paramètres scoring
    with st.expander("📊 Paramètres de scoring", expanded=True):
        st.slider("Score partiel (signe incomplet)", 0, 100, 40, 5, key="partial_score")
        st.checkbox("Appliquer bonus diagnostic", value=True, key="apply_bonus")
    
    # Informations système
    with st.expander("ℹ️ Informations système"):
        st.markdown(f"**Version :** 1.0")
        st.markdown(f"**LLM disponible :** {'✅ Oui' if LLM_AVAILABLE else '❌ Non'}")
        if WEIGHTED_ONTOLOGY:
            total_concepts = len(WEIGHTED_ONTOLOGY.get('concept_mappings', {}))
            st.markdown(f"**Concepts ontologie :** {total_concepts}")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()
