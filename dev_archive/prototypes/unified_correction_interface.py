"""
🎓 Interface Unifiée - Annotation + Correction LLM
Combine ECG viewer, annotation, et correction automatique en un seul workflow

Auteur: Edu-ECG Team  
Date: 2026-01-11
Version: 1.1 - Intégré dans app.py
"""

import streamlit as st
import sys
from pathlib import Path
import json
import os
from typing import List, Dict, Optional

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Import components - utilise ceux de app.py si disponibles
try:
    from annotation_components import smart_annotation_input, get_ontology_concepts
except ImportError:
    # Fallback simple si annotation_components n'est pas disponible
    def smart_annotation_input(key_prefix, max_tags=10):
        st.warning("⚠️ Annotation components non disponible")
        return []
    def get_ontology_concepts():
        return []

try:
    from advanced_ecg_viewer import create_advanced_ecg_viewer
except ImportError:
    # Fallback simple pour l'affichage ECG
    def create_advanced_ecg_viewer(image_path, title, container_width=None):
        return f"""
        <div style="text-align: center;">
            <h3>{title}</h3>
            <img src="{image_path}" style="max-width: 100%; height: auto;">
        </div>
        """

# Import backend services
try:
    from backend.services.llm_service import LLMService
    from backend.scoring_service_llm import SemanticScorer
    from backend.feedback_service import FeedbackService
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    import_error = str(e)

# Load OWL ontology mapping
WEIGHTED_ONTOLOGY = None
owl_mapping_file = project_root / "data" / "ontology_from_owl.json"
if owl_mapping_file.exists():
    with open(owl_mapping_file, 'r', encoding='utf-8') as f:
        WEIGHTED_ONTOLOGY = json.load(f)


def student_practice_interface():
    """
    Interface Étudiant: Pratique ECG avec correction automatique
    
    Flow:
    1. Sélectionner un cas ECG
    2. Afficher l'ECG avec viewer avancé
    3. Étudiant écrit sa réponse (texte libre)
    4. Soumission → LLM extraction + correction
    5. Affichage feedback pédagogique
    """
    st.title("🎓 Pratique ECG - Mode Étudiant")
    
    # Check dependencies
    if not LLM_AVAILABLE:
        st.error(f"""
        ❌ **Services backend non disponibles**
        
        Détails: {import_error}
        
        Vérifiez l'installation: `pip install openai`
        """)
        return
    
    # Load available cases
    ecg_cases_dir = project_root / "data" / "ecg_cases"
    
    if not ecg_cases_dir.exists():
        st.warning("📂 Aucun cas ECG trouvé. Créez des cas via l'interface Admin.")
        return
    
    # List cases
    case_dirs = [d for d in ecg_cases_dir.iterdir() if d.is_dir()]
    
    if not case_dirs:
        st.info("💡 Aucun cas disponible. Importez des ECGs pour commencer.")
        return
    
    # Case selection
    st.sidebar.header("📚 Sélection du Cas")
    
    case_options = {}
    for case_dir in sorted(case_dirs):
        metadata_file = case_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                case_id = metadata.get('case_id', case_dir.name)
                title = metadata.get('diagnostic_principal', case_id)
                case_options[f"{case_id}: {title}"] = case_dir
    
    if not case_options:
        st.warning("⚠️ Aucun cas valide trouvé (metadata.json manquants)")
        return
    
    selected_label = st.sidebar.selectbox("Choisir un cas ECG", list(case_options.keys()))
    selected_case_dir = case_options[selected_label]
    
    # Load case metadata
    with open(selected_case_dir / "metadata.json", 'r', encoding='utf-8') as f:
        case_metadata = json.load(f)
    
    case_id = case_metadata['case_id']
    
    # Display ECG
    st.header(f"📄 {case_metadata.get('diagnostic_principal', case_id)}")
    
    # Find ECG image
    ecg_image_path = None
    for ext in ['.png', '.jpg', '.jpeg', '.pdf']:
        candidate = selected_case_dir / f"{case_id}{ext}"
        if candidate.exists():
            ecg_image_path = candidate
            break
    
    if ecg_image_path:
        # Display with advanced viewer
        viewer_html = create_advanced_ecg_viewer(
            str(ecg_image_path),
            title=case_metadata.get('diagnostic_principal', 'ECG'),
            container_width=1200
        )
        st.components.v1.html(viewer_html, height=600, scrolling=True)
    else:
        st.warning("⚠️ Image ECG non trouvée")
    
    # Clinical context
    if case_metadata.get('clinical_context'):
        with st.expander("🩺 Contexte Clinique"):
            st.info(case_metadata['clinical_context'])
    
    st.divider()
    
    # Student answer input
    st.subheader("✍️ Votre Interprétation")
    
    st.markdown("""
    **Instructions:**
    - Décrivez ce que vous voyez sur l'ECG
    - Mentionnez: rythme, fréquence, intervalles, anomalies
    - Proposez un diagnostic si possible
    """)
    
    student_answer = st.text_area(
        "Écrivez votre interprétation (texte libre):",
        height=200,
        placeholder="Exemple: Rythme sinusal, fréquence normale, PR normal, QRS fins, pas d'anomalie de repolarisation...",
        key=f"answer_{case_id}"
    )
    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        submit_clicked = st.button(
            "🚀 Soumettre et Corriger",
            type="primary",
            use_container_width=True,
            disabled=not student_answer or len(student_answer.strip()) < 10
        )
    
    if submit_clicked:
        st.divider()
        process_student_submission(student_answer, case_metadata)


def process_student_submission(student_answer: str, case_metadata: dict):
    """
    Process student submission through LLM correction pipeline
    
    Args:
        student_answer: Student's text answer
        case_metadata: Case metadata with expected_concepts
    """
    with st.spinner("🤖 Correction en cours..."):
        
        # Step 1: Extract concepts from student answer
        st.info("🔍 Étape 1/3: Extraction des concepts avec LLM...")
        
        try:
            llm_service = LLMService()
            extraction_result = llm_service.extract_concepts(student_answer)
            student_concepts = extraction_result.get('concepts', [])
            
            st.success(f"✅ {len(student_concepts)} concepts extraits")
            
        except Exception as e:
            st.error(f"❌ Erreur extraction: {e}")
            return
        
        # Step 2: Semantic scoring
        st.info("📊 Étape 2/3: Scoring sémantique avec ontologie...")
        
        try:
            scorer = SemanticScorer()
            
            # Get expected concepts
            expected_concepts = case_metadata.get('expected_concepts', [])
            
            if not expected_concepts:
                st.warning("⚠️ Aucun concept attendu défini pour ce cas")
                return
            
            # Score the answer
            scoring_result = scorer.score(
                student_concepts=student_concepts,
                expected_concepts=expected_concepts,
                student_answer_full=student_answer
            )
            
            st.success(f"✅ Score: {scoring_result.percentage:.1f}%")
            
        except Exception as e:
            st.error(f"❌ Erreur scoring: {e}")
            return
        
        # Step 3: Generate pedagogical feedback
        st.info("💬 Étape 3/3: Génération du feedback pédagogique...")
        
        try:
            feedback_service = FeedbackService()
            feedback = feedback_service.generate_feedback(
                case_title=case_metadata.get('diagnostic_principal', 'ECG'),
                student_answer=student_answer,
                scoring_result=scoring_result,
                student_level='intermediate'
            )
            
            st.success("✅ Feedback généré!")
            
        except Exception as e:
            st.warning(f"⚠️ Feedback non disponible: {e}")
            feedback = None
        
        # Display results
        display_correction_results(scoring_result, feedback, case_metadata)


def display_correction_results(scoring_result, feedback, case_metadata):
    """Display correction results with feedback"""
    
    st.header("📊 Résultats de la Correction")
    
    # Score card
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_color = "🟢" if scoring_result.percentage >= 80 else "🟡" if scoring_result.percentage >= 60 else "🔴"
        st.metric(
            label="Score Global",
            value=f"{scoring_result.percentage:.1f}%",
            delta=None
        )
        st.markdown(f"{score_color} **{get_score_label(scoring_result.percentage)}**")
    
    with col2:
        st.metric(
            label="Concepts Corrects",
            value=f"{scoring_result.exact_matches + scoring_result.partial_matches}/{scoring_result.max_score}"
        )
    
    with col3:
        st.metric(
            label="Concepts Manquants",
            value=scoring_result.missing_concepts
        )
    
    st.divider()
    
    # Feedback section
    if feedback:
        st.subheader("💬 Feedback Pédagogique")
        
        # Summary
        st.markdown(f"**Résumé:** {feedback.summary}")
        
        # Strengths
        if feedback.strengths:
            with st.expander("✅ Points Forts", expanded=True):
                for strength in feedback.strengths:
                    st.success(strength)
        
        # Missing concepts
        if feedback.missing_concepts:
            with st.expander("❌ Concepts Manquants", expanded=True):
                for missing in feedback.missing_concepts:
                    st.warning(missing)
        
        # Errors
        if feedback.errors:
            with st.expander("🔴 Erreurs à Corriger", expanded=True):
                for error in feedback.errors:
                    st.error(error)
        
        # Advice
        with st.expander("💡 Conseils pour Progresser"):
            st.info(feedback.advice)
            st.markdown(f"**Prochaines étapes:** {feedback.next_steps}")
    
    # Detailed matches
    st.divider()
    st.subheader("🔍 Analyse Détaillée")
    
    with st.expander("📋 Correspondance des Concepts", expanded=False):
        for match in scoring_result.matches:
            match_type = match.match_type.value
            
            if match_type == 'exact':
                st.success(f"✅ **{match.expected_concept}** - Correspondance exacte")
            elif match_type == 'partial':
                st.warning(f"⚠️ **{match.expected_concept}** - Correspondance partielle: {match.student_concept}")
            elif match_type == 'missing':
                st.error(f"❌ **{match.expected_concept}** - Non mentionné")
            elif match_type == 'child':
                st.info(f"🔹 **{match.expected_concept}** - Implication validée via: {match.student_concept}")


def professor_validation_interface():
    """
    Interface Professeur: Validation des concepts extraits par LLM
    
    Flow:
    1. Importer ECG + rédiger correction manuscrite
    2. LLM extrait concepts de la correction
    3. Professeur valide/édite les concepts
    4. Sauvegarde comme ground truth
    """
    st.title("👨‍🏫 Import & Validation - Mode Professeur")
    
    st.markdown("""
    **Workflow:**
    1. **Uploadez un ECG** (PDF/Image)
    2. **Rédigez votre correction** (texte libre, comme vous l'écririez à un étudiant)
    3. **L'IA extrait les concepts** médicaux de votre texte
    4. **Vous validez** les concepts détectés (cocher/décocher)
    5. **Sauvegarde** comme référence pour correction automatique
    """)
    
    st.divider()
    
    # Check dependencies
    if not LLM_AVAILABLE:
        st.error(f"❌ Services LLM non disponibles: {import_error}")
        return
    
    # Step 1: Upload ECG
    st.header("1️⃣ Upload ECG")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_id = st.text_input(
            "ID du cas*",
            placeholder="Ex: BAV1_001, FA_RAPIDE_002",
            help="Identifiant unique pour ce cas"
        )
    
    with col2:
        diagnostic = st.text_input(
            "Diagnostic principal*",
            placeholder="Ex: BAV 1er degré avec BBG",
            help="Diagnostic médical principal"
        )
    
    uploaded_file = st.file_uploader(
        "Sélectionnez l'ECG (PDF ou Image)",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Image de l'ECG 12 dérivations"
    )
    
    # Step 2: Write correction
    st.header("2️⃣ Rédaction de Votre Correction")
    
    st.markdown("**Écrivez votre correction comme vous l'expliqueriez à un étudiant:**")
    
    teacher_correction = st.text_area(
        "Correction manuscrite (texte libre):",
        height=250,
        placeholder="""Exemple:
        
Il s'agit d'un rythme sinusal régulier. La fréquence cardiaque est normale (70 bpm).

L'intervalle PR est allongé à 240ms, ce qui signe un BAV du 1er degré.

Les QRS sont élargis (140ms) avec un aspect rSR' en V1 et des ondes S larges en V6, caractéristiques d'un bloc de branche gauche complet.

Pas d'anomalie de repolarisation. L'axe est normal.

Diagnostic: BAV 1er degré associé à un BBG complet.""",
        help="Décrivez l'ECG comme vous le feriez dans un compte-rendu"
    )
    
    # Step 3: Extract concepts with LLM
    if teacher_correction and len(teacher_correction) > 50:
        
        if st.button("🤖 Extraire les Concepts avec IA", type="primary"):
            with st.spinner("🔍 Analyse de votre correction avec GPT-4o..."):
                try:
                    llm_service = LLMService()
                    extraction_result = llm_service.extract_concepts(teacher_correction)
                    
                    extracted_concepts = extraction_result.get('concepts', [])
                    
                    # Store in session state for validation
                    st.session_state.extracted_concepts = extracted_concepts
                    st.session_state.extraction_done = True
                    
                    st.success(f"✅ {len(extracted_concepts)} concepts extraits!")
                    
                except Exception as e:
                    st.error(f"❌ Erreur extraction: {e}")
    
    # Step 4: Validate extracted concepts
    if st.session_state.get('extraction_done'):
        st.header("3️⃣ Validation des Concepts")
        
        st.markdown("**Concepts détectés par l'IA - Cochez ceux qui sont corrects:**")
        
        extracted_concepts = st.session_state.extracted_concepts
        
        validated_concepts = []
        
        for i, concept in enumerate(extracted_concepts):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                is_valid = st.checkbox(
                    concept,
                    value=True,  # Par défaut, tous cochés
                    key=f"concept_validate_{i}"
                )
                
                if is_valid:
                    validated_concepts.append(concept)
            
            with col2:
                # Show category from ontology
                if WEIGHTED_ONTOLOGY:
                    concept_data = find_concept_in_ontology(concept)
                    if concept_data:
                        st.caption(f"📁 {concept_data.get('categorie', 'N/A')}")
        
        # Add manual concepts
        st.subheader("➕ Ajouter des Concepts Manuellement")
        
        manual_concept = st.text_input(
            "Concept médical supplémentaire:",
            placeholder="Ex: Ondes T inversées en V1-V3"
        )
        
        if manual_concept:
            if st.button("➕ Ajouter"):
                validated_concepts.append(manual_concept)
                st.success(f"✅ Ajouté: {manual_concept}")
        
        # Clinical context (optional)
        st.subheader("🩺 Contexte Clinique (optionnel)")
        clinical_context = st.text_area(
            "Informations cliniques du patient:",
            placeholder="Patient de 65 ans, diabétique, douleur thoracique...",
            height=100
        )
        
        # Step 5: Save
        st.divider()
        st.header("4️⃣ Sauvegarde")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            save_clicked = st.button(
                "💾 Sauvegarder le Cas ECG",
                type="primary",
                use_container_width=True,
                disabled=not (case_id and diagnostic and uploaded_file and validated_concepts)
            )
        
        if save_clicked:
            save_ecg_case(
                case_id=case_id,
                diagnostic=diagnostic,
                uploaded_file=uploaded_file,
                teacher_correction=teacher_correction,
                validated_concepts=validated_concepts,
                clinical_context=clinical_context
            )


def save_ecg_case(case_id, diagnostic, uploaded_file, teacher_correction, validated_concepts, clinical_context):
    """Save ECG case with validated concepts"""
    
    ecg_cases_dir = project_root / "data" / "ecg_cases"
    ecg_cases_dir.mkdir(parents=True, exist_ok=True)
    
    case_dir = ecg_cases_dir / case_id
    
    if case_dir.exists():
        if not st.warning(f"⚠️ Le cas {case_id} existe déjà. Écraser?"):
            return
    
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Save ECG file
    file_ext = Path(uploaded_file.name).suffix
    ecg_file_path = case_dir / f"{case_id}{file_ext}"
    
    with open(ecg_file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    # Save metadata
    metadata = {
        'case_id': case_id,
        'diagnostic_principal': diagnostic,
        'expected_concepts': validated_concepts,
        'teacher_correction_text': teacher_correction,
        'clinical_context': clinical_context,
        'created_at': str(Path(__file__).stat().st_mtime),
        'validated_by_professor': True
    }
    
    with open(case_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    st.success(f"""
    ✅ **Cas sauvegardé avec succès!**
    
    - **ID:** {case_id}
    - **Diagnostic:** {diagnostic}
    - **Concepts validés:** {len(validated_concepts)}
    - **Fichier:** {ecg_file_path.name}
    
    Le cas est maintenant disponible pour la pratique étudiante! 🎓
    """)
    
    # Reset form
    st.session_state.extraction_done = False


def find_concept_in_ontology(concept_text: str) -> Optional[dict]:
    """Find concept in OWL ontology"""
    if not WEIGHTED_ONTOLOGY:
        return None
    
    concept_lower = concept_text.lower().strip()
    concept_mappings = WEIGHTED_ONTOLOGY.get('concept_mappings', {})
    
    for ontology_id, mapping in concept_mappings.items():
        concept_name = mapping.get('concept_name', '').lower()
        if concept_name == concept_lower:
            return mapping
    
    return None


def get_score_label(percentage: float) -> str:
    """Get label for score percentage"""
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 80:
        return "Très bien"
    elif percentage >= 70:
        return "Bien"
    elif percentage >= 60:
        return "Passable"
    else:
        return "À améliorer"


def main():
    """
    Main application with role selection
    
    NOTE: Cette fonction n'est utilisée QUE si le fichier est exécuté directement.
    Quand intégré dans app.py, les fonctions student_practice_interface() et
    professor_validation_interface() sont appelées directement.
    """
    
    st.set_page_config(
        page_title="🫀 Edu-ECG - Correction LLM",
        page_icon="🫀",
        layout="wide"
    )
    
    # Sidebar role selection
    st.sidebar.title("🫀 Edu-ECG")
    st.sidebar.divider()
    
    role = st.sidebar.radio(
        "Mode:",
        ["🎓 Étudiant - Pratique", "👨‍🏫 Professeur - Import"],
        key="role_selection"
    )
    
    st.sidebar.divider()
    st.sidebar.info("""
    **Interface Unifiée v1.1**
    
    Combine:
    - Annotation intelligente
    - Correction LLM automatique
    - Feedback pédagogique
    
    **Note:** Cette interface est intégrée dans app.py principal.
    Pour l'utiliser, lancez app.py et cliquez sur "🤖 Pratique avec IA".
    """)
    
    # Initialize session state
    if 'extraction_done' not in st.session_state:
        st.session_state.extraction_done = False
    
    # Route to interface
    if role.startswith("🎓"):
        student_practice_interface()
    else:
        professor_validation_interface()


if __name__ == "__main__":
    # Ce bloc n'est exécuté QUE si on lance directement ce fichier
    # Quand importé par app.py, il est ignoré
    main()
