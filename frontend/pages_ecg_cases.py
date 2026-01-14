import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import sys
from config import ECG_CASES_DIR  # Import depuis config.py
from advanced_ecg_viewer import create_advanced_ecg_viewer

# Ajouter backend au path pour imports LLM
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

# Import des composants nécessaires
try:
    from annotation_components import smart_annotation_input, display_annotation_summary
except ImportError:
    # Fonctions de fallback si le module n'est pas disponible
    def smart_annotation_input(key_prefix, max_tags=10):
        if f'{key_prefix}_tags' not in st.session_state:
            st.session_state[f'{key_prefix}_tags'] = []
        
        new_tag = st.text_input("Ajouter une annotation:", key=f"{key_prefix}_input")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Ajouter", key=f"{key_prefix}_add"):
                if new_tag and new_tag not in st.session_state[f'{key_prefix}_tags']:
                    if len(st.session_state[f'{key_prefix}_tags']) < max_tags:
                        st.session_state[f'{key_prefix}_tags'].append(new_tag)
                        st.rerun()
        
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

    def display_annotation_summary(annotations, title="Résumé"):
        if annotations:
            st.markdown(f"**{title}**")
            for ann in annotations:
                st.write(f"• {ann}")

# Import services LLM pour correction automatique
try:
    from backend.services.llm_service import LLMService
    from backend.scoring_service_llm import SemanticScorer
    from backend.feedback_service import FeedbackService
    LLM_CORRECTION_AVAILABLE = True
except ImportError as e:
    LLM_CORRECTION_AVAILABLE = False
    llm_import_error = str(e)

def page_ecg_cases():
    """Page de consultation des cas ECG pour étudiants"""
    
    # Si un cas est sélectionné, afficher le détail
    if 'selected_case' in st.session_state and st.session_state.selected_case:
        display_case_detail(st.session_state.selected_case)
        return
    
    # Sinon, afficher la liste des cas
    st.markdown("## 📚 Cas ECG disponibles")
    
    ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
    available_cases = []
    
    if ECG_CASES_DIR.exists():
        for case_dir in ECG_CASES_DIR.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(case_dir.glob(ext))
                if metadata_file.exists() and image_files:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        sorted_images = sorted(image_files, key=lambda x: x.name)
                        case_data['image_paths'] = [str(img) for img in sorted_images]
                        case_data['image_path'] = str(sorted_images[0])
                        case_data['total_images'] = len(sorted_images)
                        case_data['case_folder'] = str(case_dir)
                        case_id = case_data.get('case_id', case_dir.name)
                        case_data['case_id'] = case_id
                        available_cases.append(case_data)
                    except Exception as e:
                        st.warning(f"⚠️ Erreur lecture métadonnées {case_dir.name}: {e}")

    if available_cases:
        st.success(f"✅ {len(available_cases)} cas disponibles")
        
        # Affichage en grille avec 3 colonnes
        cols_per_row = 3
        for i in range(0, len(available_cases), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(available_cases):
                    case_data = available_cases[i + j]
                    with cols[j]:
                        display_case_thumbnail(case_data)
    else:
        st.warning("⚠️ Aucun cas ECG disponible")
        st.info("""
        **💡 Pour avoir des cas disponibles :**
        1. Passez en mode Administrateur/Expert
        2. Utilisez l'Import Intelligent pour ajouter des ECG
        3. Annotez les cas dans la Liseuse ECG
        4. Les cas annotés apparaîtront ici pour les étudiants
        """)

def display_case_thumbnail(case_data):
    """Affiche une vignette pour un cas ECG"""
    case_id = case_data.get('case_id', 'Cas ECG')
    
    # Container pour la vignette
    with st.container():
        # Afficher la première image comme vignette
        if 'image_paths' in case_data and case_data['image_paths']:
            image_path = Path(case_data['image_paths'][0])
            if image_path.exists():
                st.image(str(image_path), use_container_width=True)
            else:
                st.info("📄 Image non disponible")
        
        # Informations du cas
        st.markdown(f"**{case_id}**")
        
        # Nombre d'ECG dans le cas
        if case_data.get('total_images', 1) > 1:
            st.caption(f"📊 {case_data['total_images']} ECG")
        
        # Bouton pour ouvrir le cas
        if st.button("📋 CAS ECG", key=f"open_{case_id}", use_container_width=True, type="primary"):
            st.session_state.selected_case = case_data
            st.rerun()

def display_case_detail(case_data):
    """Affiche le détail d'un cas ECG avec interface d'annotation"""
    case_id = case_data.get('case_id', 'Cas ECG')
    
    # Bouton retour
    if st.button("◀ Retour à la liste", key="back_to_list"):
        st.session_state.selected_case = None
        st.rerun()
    
    st.markdown(f"## 📋 Cas ECG: {case_id}")
    
    # Section 1: Affichage ECG (pleine largeur)
    st.markdown("### 📊 ECG")
    
    # Affichage ECG(s)
    if 'image_paths' in case_data and case_data['image_paths']:
        total_images = len(case_data['image_paths'])
        
        # Navigation entre les ECG avec flèches
        col_nav1, col_select, col_nav2 = st.columns([1, 3, 1])
        
        # Initialiser l'index si nécessaire
        if f'ecg_index_{case_id}' not in st.session_state:
            st.session_state[f'ecg_index_{case_id}'] = 0
        
        current_index = st.session_state[f'ecg_index_{case_id}']
        
        with col_nav1:
            if st.button("◀", key=f"prev_ecg_{case_id}", disabled=(current_index == 0)):
                st.session_state[f'ecg_index_{case_id}'] = current_index - 1
                st.rerun()
        
        with col_select:
            if total_images > 1:
                ecg_index = st.selectbox(
                    "Sélectionner l'ECG :",
                    range(total_images),
                    format_func=lambda i: f"ECG {i+1}/{total_images}",
                    key=f"detail_ecg_select_{case_id}",
                    index=current_index
                )
                if ecg_index != current_index:
                    st.session_state[f'ecg_index_{case_id}'] = ecg_index
                    st.rerun()
            else:
                ecg_index = 0
                st.info(f"📊 Ce cas contient **1 ECG**")
        
        with col_nav2:
            if st.button("▶", key=f"next_ecg_{case_id}", disabled=(current_index >= total_images - 1)):
                st.session_state[f'ecg_index_{case_id}'] = current_index + 1
                st.rerun()
        
        # Bouton pour basculer vers affichage simple/avancé
        col_tools1, col_tools2 = st.columns([3, 1])
        with col_tools2:
            # Texte du bouton selon état actuel
            viewer_key = f'advanced_viewer_{case_id}'
            is_advanced = st.session_state.get(viewer_key, True)  # Default TRUE
            button_text = "📷 Vue Simple" if is_advanced else "🔍 Vue Avancée"
            button_help = "Désactiver zoom/caliper" if is_advanced else "Activer zoom/caliper"
            
            if st.button(button_text, key=f"tools_{case_id}", type="secondary", help=button_help):
                # Basculer l'état du visualiseur avancé
                st.session_state[viewer_key] = not is_advanced
                st.rerun()
        
        # Affichage de l'image - normale ou avec visualiseur avancé
        image_path = Path(case_data['image_paths'][current_index])
        
        if image_path.exists():
            # Vérifier si le visualiseur avancé est activé (DEFAULT: TRUE - Party Mode v2.0)
            if st.session_state.get(f'advanced_viewer_{case_id}', True):
                try:
                    from advanced_ecg_viewer import create_advanced_ecg_viewer
                    st.success("🔍 **Visualiseur Avancé Actif** - Zoom (molette souris) | Caliper (clic gauche) | Drag (clic droit)")
                    viewer_html = create_advanced_ecg_viewer(
                        image_path=str(image_path),
                        title=f"ECG {current_index+1}/{total_images} - {case_id}"
                    )
                    st.components.v1.html(
                        viewer_html,
                        height=800,
                        scrolling=False
                    )
                except ImportError:
                    st.warning("⚠️ Module advanced_ecg_viewer non disponible - Affichage simple")
                    st.image(str(image_path), 
                           caption=f"ECG {current_index+1}/{total_images} - {case_id}",
                           use_container_width=True)
            else:
                # Affichage normal (simple)
                st.info("📷 **Affichage Simple** - Pour zoom et mesures, cliquez sur '🔍 Vue Avancée'")
                st.image(str(image_path), 
                       caption=f"ECG {current_index+1}/{total_images} - {case_id}",
                       use_container_width=True)
        else:
            st.warning(f"⚠️ ECG {current_index+1} non trouvé")
    
    # Section 2: Zone d'interprétation (sous l'ECG)
    st.markdown("---")
    st.markdown("### 🎓 Votre Interprétation ECG")
    
    # Initialisation session state
    answer_key = f"student_answer_{case_id}"
    correction_key = f"correction_result_{case_id}"
    
    if answer_key not in st.session_state:
        # Charger depuis fichier si disponible
        student_file = Path(case_data['case_folder']) / "student_answer.json"
        if student_file.exists():
            try:
                with open(student_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    st.session_state[answer_key] = saved_data.get('answer', '')
            except Exception:
                st.session_state[answer_key] = ''
        else:
            st.session_state[answer_key] = ''
    
    # Instructions
    st.markdown("""
    **📋 Instructions:**
    - Décrivez ce que vous observez sur l'ECG (rythme, fréquence, intervalles, anomalies)
    - Proposez un diagnostic si possible
    - Écrivez en texte libre comme dans un compte-rendu
    """)
    
    # Zone de texte pour réponse libre
    student_answer = st.text_area(
        "✍️ Écrivez votre interprétation :",
        value=st.session_state[answer_key],
        height=250,
        placeholder="""Exemple:
        
Rythme sinusal régulier, fréquence cardiaque à 75 bpm.

L'intervalle PR est normal (160ms). Les QRS sont fins (90ms).

Pas d'onde Q pathologique. Segment ST isoélectrique.

Ondes T positives et symétriques dans toutes les dérivations.

Diagnostic: ECG normal.""",
        key=f"answer_input_{case_id}"
    )
    
    # Sauvegarder dans session state
    st.session_state[answer_key] = student_answer
    
    # Boutons d'action
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 Sauvegarder", key=f"save_answer_{case_id}", use_container_width=True):
            try:
                student_folder = Path(case_data['case_folder'])
                student_file = student_folder / "student_answer.json"
                save_data = {
                    'answer': student_answer,
                    'case_id': case_id,
                    'timestamp': str(Path(__file__).stat().st_mtime)
                }
                with open(student_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                st.success("✅ Sauvegardé !")
            except Exception as e:
                st.error(f"❌ Erreur sauvegarde: {e}")
    
    with col_btn2:
        # Bouton correction LLM
        can_correct = LLM_CORRECTION_AVAILABLE and student_answer and len(student_answer.strip()) > 20
        
        if st.button(
            "🤖 Corriger avec IA",
            key=f"llm_corr_{case_id}",
            type="primary",
            disabled=not can_correct,
            use_container_width=True
        ):
            st.session_state[correction_key] = perform_llm_correction(case_data, student_answer)
        
        if not can_correct:
            if not LLM_CORRECTION_AVAILABLE:
                st.caption("⚠️ LLM non disponible")
            elif not student_answer or len(student_answer.strip()) <= 20:
                st.caption("Écrivez votre interprétation d'abord")
    
    # Affichage des résultats de correction (si disponible)
    if correction_key in st.session_state and st.session_state[correction_key]:
        st.markdown("---")
        display_llm_correction_results(st.session_state[correction_key])
    
    # Option pour voir correction experte
    st.markdown("---")
    show_expert = st.checkbox("👨‍🏫 Voir la correction experte", key=f"show_expert_{case_id}")
    
    if show_expert:
        display_expert_correction(case_data)


def perform_llm_correction(case_data, student_text):
    """
    Effectue une correction automatique avec LLM et retourne les résultats
    
    Args:
        case_data: Métadonnées du cas ECG
        student_text: Texte de la réponse étudiant
        
    Returns:
        dict: Résultats de correction avec scoring_result et feedback
    """
    case_id = case_data.get('case_id', 'unknown')
    
    results = {
        'success': False,
        'scoring_result': None,
        'feedback': None,
        'student_concepts': [],
        'error': None
    }
    
    with st.spinner("🤖 Correction en cours..."):
        
        try:
            # Étape 1: Extraction concepts LLM
            st.info("🔍 Étape 1/3: Extraction des concepts...")
            llm_service = LLMService()
            extraction_result = llm_service.extract_concepts(student_text)
            student_concepts_llm = extraction_result.get('concepts', [])
            results['student_concepts'] = student_concepts_llm
            
            st.success(f"✅ {len(student_concepts_llm)} concepts extraits")
            
            # Étape 2: Scoring sémantique
            st.info("📊 Étape 2/3: Scoring avec ontologie...")
            
            # 🆕 VÉRIFIER LES EXCLUSIONS D'ABORD
            has_exclusions = case_data.get('has_exclusions', False)
            
            # Vérifier aussi dans les annotations (fallback pour anciens cas)
            if not has_exclusions and 'annotations' in case_data:
                for ann in case_data['annotations']:
                    if ann.get('annotation_role') == '❌ Exclusion' or ann.get('is_exclusion', False):
                        has_exclusions = True
                        break
            
            if has_exclusions:
                # Si exclusion présente → Note automatique = 0
                st.error("❌ EXCLUSION DÉTECTÉE - Note automatique: 0/20")
                st.warning("⚠️ Ce cas contient une annotation marquée comme 'Exclusion' (faute grave). La note est automatiquement 0.")
                
                # Créer un scoring_result avec score 0
                from backend.scoring_service_llm import ScoringResult, ConceptMatch, MatchType
                results['scoring_result'] = ScoringResult(
                    total_score=0.0,
                    max_score=20.0,
                    percentage=0.0,
                    matches=[],
                    exact_matches=0,
                    partial_matches=0,
                    missing_concepts=0,
                    extra_concepts=0,
                    contradictions=0,
                    category_scores={}
                )
                results['exclusion_penalty'] = True
                results['success'] = True
                return results
            
            # Récupérer concepts attendus
            expected_concepts_raw = case_data.get('expected_concepts', [])
            
            if not expected_concepts_raw:
                # Fallback: utiliser annotations expertes
                expert_file = Path(case_data['case_folder']) / "annotations.json"
                if expert_file.exists():
                    try:
                        with open(expert_file, 'r', encoding='utf-8') as f:
                            expert_annots = json.load(f)
                            for ann in expert_annots:
                                if ann.get('annotation_tags'):
                                    expected_concepts_raw.extend(ann['annotation_tags'])
                    except Exception:
                        pass
            
            if not expected_concepts_raw:
                results['error'] = "no_expected_concepts"
                st.warning("⚠️ Aucun concept attendu défini pour ce cas. Impossible de corriger automatiquement.")
                st.info("💡 Demandez à un enseignant de valider ce cas avec des concepts attendus.")
                return results
            
            # Convertir expected_concepts en format dict si nécessaire
            expected_concepts = []
            for concept in expected_concepts_raw:
                if isinstance(concept, str):
                    # Convertir string en dict
                    expected_concepts.append({
                        'text': concept,
                        'category': 'general',
                        'confidence': 1.0
                    })
                elif isinstance(concept, dict):
                    # Déjà au bon format
                    expected_concepts.append(concept)
            
            # Récupérer les annotations avec leurs territoires pour appliquer la pénalité
            annotations = case_data.get('annotations', [])
            territory_selections = case_data.get('territory_selections', {})
            
            # Scoring
            scorer = SemanticScorer()
            scoring_result = scorer.score(
                student_concepts=student_concepts_llm,
                expected_concepts=expected_concepts,
                annotations=annotations,  # 🆕 Passer les annotations
                territory_selections=territory_selections  # 🆕 Passer les territoires
            )
            results['scoring_result'] = scoring_result
            results['annotations'] = annotations  # 🆕 Garder les annotations pour affichage
            
            st.success(f"✅ Score: {scoring_result.percentage:.1f}%")
            
            # Étape 3: Feedback pédagogique
            st.info("💬 Étape 3/3: Génération du feedback...")
            
            feedback_service = FeedbackService()
            feedback = feedback_service.generate_feedback(
                case_title=case_data.get('diagnostic_principal', 'ECG'),
                student_answer=student_text,
                scoring_result=scoring_result,
                student_level='intermediate'
            )
            results['feedback'] = feedback
            
            st.success("✅ Feedback généré!")
            results['success'] = True
            
        except Exception as e:
            st.error(f"❌ Erreur correction: {e}")
            results['error'] = str(e)
            return results
    
    return results


def display_llm_correction_results(results):
    """
    Affiche les résultats de la correction LLM
    
    Args:
        results: dict avec scoring_result et feedback
    """
    if not results.get('success'):
        st.error("❌ La correction n'a pas abouti")
        if results.get('error'):
            st.info(f"Erreur: {results['error']}")
        return
    
    scoring_result = results['scoring_result']
    feedback = results['feedback']
    
    st.markdown("## 📊 Résultats de la Correction")
    
    # Score cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_color = "🟢" if scoring_result.percentage >= 80 else "🟡" if scoring_result.percentage >= 60 else "🔴"
        st.metric("Score Global", f"{scoring_result.percentage:.1f}%")
        
        if scoring_result.percentage >= 90:
            st.markdown(f"{score_color} **Excellent**")
        elif scoring_result.percentage >= 80:
            st.markdown(f"{score_color} **Très bien**")
        elif scoring_result.percentage >= 70:
            st.markdown(f"{score_color} **Bien**")
        elif scoring_result.percentage >= 60:
            st.markdown(f"{score_color} **Passable**")
        else:
            st.markdown(f"{score_color} **À améliorer**")
    
    with col2:
        st.metric(
            "Concepts Corrects",
            f"{scoring_result.exact_matches + scoring_result.partial_matches}/{scoring_result.max_score}"
        )
    
    with col3:
        st.metric("Concepts Manquants", scoring_result.missing_concepts)
    
    st.divider()
    
    # Feedback pédagogique
    if feedback:
        st.subheader("💬 Feedback Pédagogique")
        
        st.markdown(f"**Résumé:** {feedback.summary}")
        
        # Points forts
        if feedback.strengths:
            with st.expander("✅ Points Forts", expanded=True):
                for strength in feedback.strengths:
                    st.success(strength)
        
        # Concepts manquants
        if feedback.missing_concepts:
            with st.expander("❌ Concepts Manquants", expanded=True):
                for missing in feedback.missing_concepts:
                    st.warning(missing)
        
        # Erreurs
        if feedback.errors:
            with st.expander("🔴 Erreurs à Corriger", expanded=True):
                for error in feedback.errors:
                    st.error(error)
        
        # Conseils
        with st.expander("💡 Conseils pour Progresser", expanded=False):
            st.info(feedback.advice)
            st.markdown(f"**Prochaines étapes:** {feedback.next_steps}")
    
    # Analyse détaillée
    st.divider()
    
    with st.expander("🔍 Analyse Détaillée des Concepts", expanded=False):
        st.markdown("#### 🎯 Diagnostics validants (comptent dans la note)")
        
        for match in scoring_result.matches:
            match_type = match.match_type.value
            
            if match_type == 'exact':
                st.success(f"✅ **{match.expected_concept}** - Correspondance exacte ({match.score:.0f} points)")
            elif match_type == 'partial':
                st.warning(f"⚠️ **{match.expected_concept}** - Correspondance partielle: {match.student_concept} ({match.score:.0f} points)")
            elif match_type == 'missing':
                st.error(f"❌ **{match.expected_concept}** - Non mentionné (0 points)")
            elif match_type == 'child':
                st.info(f"🔹 **{match.expected_concept}** - Implication validée via: {match.student_concept} ({match.score:.0f} points)")
        
        # 🆕 AFFICHER LES DESCRIPTIONS (ne comptent pas dans la note)
        if 'annotations' in correction_result:
            description_annotations = [
                ann for ann in correction_result['annotations']
                if ann.get('annotation_role', '📝 Description') == '📝 Description'
            ]
            
            if description_annotations:
                st.markdown("---")
                st.markdown("#### 📝 Descriptions (pour information, ne comptent pas dans la note)")
                
                for ann in description_annotations:
                    # Vérifier si l'étudiant a mentionné ce concept
                    concept_name = ann['concept']
                    student_mentioned = False
                    
                    # Chercher dans les concepts extraits de l'étudiant
                    if 'student_concepts' in correction_result:
                        for student_concept in correction_result['student_concepts']:
                            # Match simple (peut être amélioré)
                            if concept_name.lower() in student_concept.get('text', '').lower():
                                student_mentioned = True
                                break
                    
                    if student_mentioned:
                        st.info(f"ℹ️ **{concept_name}** - Mentionné (descriptif, pas de points)")
                    else:
                        st.caption(f"ℹ️ **{concept_name}** - Non mentionné (descriptif, pas obligatoire)")


def display_expert_correction(case_data):
    """
    Affiche la correction experte pour comparaison
    
    Args:
        case_data: Métadonnées du cas ECG
    """
    st.markdown("### 👨‍🏫 Correction Experte")
    
    # Charger les annotations expertes
    expert_annots = []
    expert_file = Path(case_data['case_folder']) / "annotations.json"
    
    if expert_file.exists():
        try:
            with open(expert_file, 'r', encoding='utf-8') as f:
                expert_annots = json.load(f)
        except Exception:
            expert_annots = []
    else:
        expert_annots = case_data.get('annotations', [])
    
    # Extraire concepts experts
    expert_tags = []
    for ann in expert_annots:
        if ann.get('type') == 'expert' or ann.get('auteur') == 'expert':
            if ann.get('annotation_tags'):
                expert_tags.extend(ann['annotation_tags'])
            elif ann.get('concept'):
                expert_tags.append(ann['concept'])
    
    if expert_tags:
        st.markdown("**🧠 Concepts Clés :**")
        display_annotation_summary(expert_tags, title="")
        
        # Afficher texte de correction si disponible
        teacher_correction_file = Path(case_data['case_folder']) / "metadata.json"
        if teacher_correction_file.exists():
            try:
                with open(teacher_correction_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    teacher_text = metadata.get('teacher_correction_text', '')
                    
                    if teacher_text:
                        st.markdown("---")
                        st.markdown("**📝 Correction Rédigée :**")
                        st.info(teacher_text)
            except Exception:
                pass
    else:
        st.info("💡 Aucune annotation experte disponible pour ce cas.")

