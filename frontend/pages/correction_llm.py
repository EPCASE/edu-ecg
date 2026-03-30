"""
🔍 Module de Correction LLM - Version Neurosymbolique (RAG)
Refactorisé pour utiliser l'architecture RAG Ontologique (Briques 2-3-4)
au lieu de l'ancien SemanticScorer + matching itératif.

Auteur: Edu-ECG Team + BMAD Agents
Date: 2026-02-25
Version: 3.0 - RAG Neurosymbolique
"""

import streamlit as st
import sys
from pathlib import Path
import json
import os

# Ajouter project root et RAG ontologique au path pour imports
project_root = Path(__file__).parent.parent.parent
rag_root = project_root.parent / "RAG ontologique"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(rag_root))

# Imports RAG Neurosymbolique (Briques 2, 3, 4)
try:
    from ner_extractor import extract_clinical_terms, NERExtraction
    from hybrid_search import HybridSearchEngine
    from neurosymbolic_judge import resolve_term_to_ontology
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
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


# match_concept_with_ontology — SUPPRIMÉE (remplacée par le pipeline RAG Neurosymbolique)
# L'ancien matching itératif (EXTRA_SYNONYMS, SemanticScorer, LLM semantic_match)
# est remplacé par : extract_clinical_terms → HybridSearchEngine → resolve_term_to_ontology



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


def generate_pedagogical_feedback(
    case_title: str,
    student_answer: str,
    percentage: float,
    concepts_valides_attendus: list,
    missing_concepts: list,
    decouvertes_additionnelles: list,
    match_details: dict,
) -> dict:
    """
    Génère un feedback pédagogique structuré via GPT-4o.

    Injecte deux listes distinctes dans le prompt :
      - concepts_valides_attendus  → structure le feedback principal
      - decouvertes_additionnelles → section "✨ Découvertes additionnelles"

    Returns:
        dict avec clés : summary, strengths, missing, advice, decouvertes, raw
    """
    from openai import OpenAI
    import json as _json

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY non configurée", "raw": ""}

    client = OpenAI(api_key=api_key)

    # Formater les listes pour le prompt
    attendus_str = ", ".join(concepts_valides_attendus) if concepts_valides_attendus else "(aucun)"
    manquants_str = ", ".join(missing_concepts) if missing_concepts else "(aucun)"
    decouvertes_str = ", ".join(
        f"{d['concept_name']} ({d['categorie']})" for d in decouvertes_additionnelles
    ) if decouvertes_additionnelles else "(aucune)"

    system_prompt = f"""Tu es un enseignant en cardiologie, expert en ECG, bienveillant et pédagogue.

Ton rôle est de donner un feedback constructif sur l'interprétation ECG d'un étudiant en médecine.

Principes IMPÉRATIFS:
1. 🟢 TOUJOURS commencer par le POSITIF (ce qui est correct)
2. 📚 EXPLIQUER pourquoi un concept est important ou manquant
3. 🎯 GUIDER vers la bonne réponse (pas donner directement)
4. 💡 SUGGÉRER une méthode d'analyse pour éviter l'erreur future
5. 🌟 ENCOURAGER le progrès, valoriser l'effort

Voici les concepts que l'étudiant a correctement identifiés selon le barème du professeur : {attendus_str}. Tu dois structurer ton feedback autour de ces points.

Voici les concepts cliniques RÉELS que l'étudiant a trouvés sur l'ECG, mais qui n'étaient pas le focus principal de l'exercice : {decouvertes_str}. Tu DOIS créer une petite section finale intitulée '✨ Découvertes additionnelles' pour valoriser son sens de l'observation sans modifier sa note principale.

Ton TON : bienveillant mais rigoureux, encourageant mais honnête, pédagogique.

Format de réponse JSON :
{{
  "summary": "Résumé général en 1-2 phrases",
  "strengths": ["Point fort 1", "Point fort 2"],
  "missing_explanations": ["Explication pédagogique pour concept manquant 1", ...],
  "advice": "Conseil méthodologique principal",
  "decouvertes_section": "Texte de la section ✨ Découvertes additionnelles (2-4 phrases valorisant l'observation de l'étudiant)",
  "encouragement": "Message d'encouragement final"
}}"""

    user_prompt = f"""CAS ECG : {case_title}
Score : {percentage:.1f}%

RÉPONSE DE L'ÉTUDIANT :
{student_answer}

CONCEPTS CORRECTEMENT IDENTIFIÉS (barème prof) :
{attendus_str}

CONCEPTS MANQUANTS :
{manquants_str}

DÉCOUVERTES ADDITIONNELLES (hors barème, mais cliniquement justes) :
{decouvertes_str}

Génère le feedback pédagogique structuré en JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )

        raw_text = response.choices[0].message.content
        feedback = _json.loads(raw_text)
        feedback["raw"] = raw_text
        return feedback

    except Exception as e:
        return {
            "error": str(e),
            "raw": "",
            "summary": f"Score : {percentage:.1f}%. Feedback automatique indisponible.",
            "strengths": concepts_valides_attendus,
            "missing_explanations": [f"Concept manquant : {c}" for c in missing_concepts],
            "advice": "Revoir la méthodologie systématique de lecture ECG.",
            "decouvertes_section": (
                f"Vous avez également identifié : {decouvertes_str}. "
                "Bien que ces éléments ne fassent pas partie du barème, ils témoignent d'un bon sens clinique."
            ) if decouvertes_additionnelles else "",
            "encouragement": "Continuez vos efforts !",
        }


def perform_correction(case_data, student_answer):
    """Effectue la correction via le pipeline RAG Neurosymbolique et affiche les résultats"""
    
    with st.spinner("🤖 Correction Neurosymbolique en cours..."):
        try:
            # Initialiser le moteur de recherche hybride (Brique 3 — chargé une seule fois)
            moteur_recherche = HybridSearchEngine()

            # ─── Étape 1 : Extraction NER (Brique 2) ─────────────────────────
            st.info("🔍 Étape 1/3: Extraction des concepts (GPT-4o)...")
            extraction_result = extract_clinical_terms(student_answer)

            if not extraction_result.entites:
                st.error("❌ Aucun concept médical trouvé dans votre réponse")
                st.info("💡 Décrivez les éléments ECG observés (rythme, ondes, intervalles, etc.)")
                return

            st.success(f"✅ {len(extraction_result.entites)} concepts extraits")

            # ─── Étape 2 : Matching RAG (Briques 3 & 4) ──────────────────────
            st.info("📊 Étape 2/3: Recherche dans l'ontologie locale (RAG + QCM)...")

            student_matched_ids = {}     # {ontology_id: statut}
            student_match_details = {}   # {ontology_id: terme_brut}
            student_match_method = {}    # {ontology_id: method (coupe_circuit/juge_llm)}

            for entite in extraction_result.entites:
                candidats = moteur_recherche.search_top_k(entite.terme_brut)
                resolution = resolve_term_to_ontology(
                    entite.terme_brut, entite.contexte_phrase, candidats
                )

                matched_id = resolution["ontology_id"]
                if matched_id != "NONE":
                    student_matched_ids[matched_id] = entite.statut
                    student_match_details[matched_id] = entite.terme_brut
                    student_match_method[matched_id] = resolution["method"]

            # ─── Étape 3 : Le Pont avec l'ancien scoring (Adaptateur) ────────
            st.info("⚖️ Étape 3/3: Calcul du score...")

            expected_concepts_raw = case_data.get(
                'diagnosis', case_data.get('expected_concepts', [])
            )
            if not expected_concepts_raw:
                st.warning("⚠️ Aucun concept attendu défini pour ce cas")
                return

            expected_list = [
                c if isinstance(c, str) else c.get('text', '')
                for c in expected_concepts_raw
            ]

            matched_concepts = []
            match_details = {}
            concept_weights = {}
            concept_scores = {}
            llm_matches = {}   # Vide pour compatibilité display_results

            for expected in expected_list:
                owl_concept = find_owl_concept(expected)
                expected_id = owl_concept.get('ontology_id') if owl_concept else None

                # Préparer les poids
                concept_weights[expected] = {
                    'poids': owl_concept.get('poids', 1) if owl_concept else 1,
                    'categorie': owl_concept.get('categorie', 'DESCRIPTEUR_ECG') if owl_concept else 'DESCRIPTEUR_ECG',
                    'ontology_id': expected_id,
                }

                # Vérification du match via les IDs ontologiques
                if expected_id and expected_id in student_matched_ids:
                    statut = student_matched_ids[expected_id]

                    # PIÈGE DE LA NÉGATION : on ne valide que si l'étudiant
                    # affirme ("present") ou suspecte ("hypothese") le concept.
                    # Un statut "absent" signifie qu'il a explicitement nié
                    # ce concept → on ne donne PAS les points.
                    if statut in ("present", "hypothese"):
                        matched_concepts.append(expected)
                        method = student_match_method.get(expected_id, "rag")
                        match_details[expected] = {
                            'type': 'exact' if statut == "present" else 'hypothese',
                            'matched_text': student_match_details.get(expected_id, ''),
                            'poids': concept_weights[expected]['poids'],
                            'categorie': concept_weights[expected]['categorie'],
                        }
                        # Affirme → 100% | Hypothèse → 80%
                        concept_scores[expected] = 100.0 if statut == "present" else 80.0

            # ─── Règles d'implication (inchangé) ─────────────────────────────
            auto_validated = apply_implication_rules(matched_concepts, expected_list)
            all_validated = set(matched_concepts) | auto_validated

            # ─── Logique ensembliste : attendus vs découvertes ───────────────
            # 1. Ce que l'étudiant a validé ET qui était attendu par le prof
            expected_set = set(expected_list)
            concepts_valides_attendus = all_validated.intersection(expected_set)

            # 2. Ce que l'étudiant a trouvé de juste sur l'ECG MAIS non exigé
            #    → IDs trouvés par le pipeline RAG qui ne sont pas dans le golden set
            expected_ids = set()
            for exp in expected_list:
                owl_exp = find_owl_concept(exp)
                if owl_exp:
                    expected_ids.add(owl_exp.get('ontology_id'))

            decouvertes_additionnelles = []
            for sid, statut in student_matched_ids.items():
                if sid not in expected_ids and statut in ("present", "hypothese"):
                    # Retrouver le nom lisible
                    concept_mappings_data = ONTOLOGY_MAPPING.get('concept_mappings', {})
                    if sid in concept_mappings_data:
                        cname = concept_mappings_data[sid].get('concept_name', sid)
                        cat = concept_mappings_data[sid].get('categorie', 'DESCRIPTEUR_ECG')
                    else:
                        cname = student_match_details.get(sid, sid)
                        cat = 'DESCRIPTEUR_ECG'
                    decouvertes_additionnelles.append({
                        'ontology_id': sid,
                        'concept_name': cname,
                        'categorie': cat,
                        'statut': statut,
                        'terme_brut': student_match_details.get(sid, ''),
                    })

            # ─── Calcul du score STRICT (uniquement sur concepts attendus) ───
            # Les découvertes additionnelles ne rapportent ni ne retirent de points
            poids_valides = sum(
                concept_weights.get(concept, {}).get('poids', 1) * (concept_scores.get(concept, 100.0) / 100.0)
                for concept in concepts_valides_attendus
            )
            poids_attendus = sum(
                concept_weights.get(concept, {}).get('poids', 1)
                for concept in expected_list
            )

            base_percentage = (poids_valides / poids_attendus * 100) if poids_attendus > 0 else 0

            # Bonus diagnostic principal
            has_diagnostic_principal = any(
                concept_weights.get(c, {}).get('poids', 1) >= 3
                for c in all_validated
            )
            bonus_diagnostic = 0.15 if has_diagnostic_principal else 0
            percentage = min(100, base_percentage * (1 + bonus_diagnostic))

            st.success("✅ Correction terminée !")

            # ─── Feedback LLM (GPT-4o) avec concepts attendus + découvertes ─
            feedback_llm = generate_pedagogical_feedback(
                case_title=case_data.get('title', case_data.get('id', 'ECG')),
                student_answer=student_answer,
                percentage=percentage,
                concepts_valides_attendus=list(concepts_valides_attendus),
                missing_concepts=[c for c in expected_list if c not in concepts_valides_attendus],
                decouvertes_additionnelles=decouvertes_additionnelles,
                match_details=match_details,
            )

            # ─── Affichage (enrichi) ─────────────────────────────────────────
            display_results(
                percentage, base_percentage, bonus_diagnostic,
                poids_valides, poids_attendus,
                matched_concepts, auto_validated, expected_list,
                match_details, concept_weights, llm_matches,
                student_answer,
                concepts_valides_attendus=concepts_valides_attendus,
                decouvertes_additionnelles=decouvertes_additionnelles,
                feedback_llm=feedback_llm,
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
                    student_answer,
                    concepts_valides_attendus=None,
                    decouvertes_additionnelles=None,
                    feedback_llm=None):
    """Affiche les résultats de correction - Version enrichie avec feedback LLM"""
    
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
    
    # ─── Feedback LLM Pédagogique ──────────────────────────────────────
    if feedback_llm and not feedback_llm.get("error"):
        st.divider()
        st.subheader("💬 Feedback Pédagogique (GPT-4o)")

        # Résumé
        if feedback_llm.get("summary"):
            st.markdown(f"**{feedback_llm['summary']}**")

        # Points forts
        if feedback_llm.get("strengths"):
            st.markdown("##### ✅ Points forts")
            for s in feedback_llm["strengths"]:
                st.markdown(f"- 🟢 {s}")

        # Concepts manquants (explications pédagogiques)
        if feedback_llm.get("missing_explanations"):
            st.markdown("##### ❌ Concepts manquants — Explications")
            for m in feedback_llm["missing_explanations"]:
                st.markdown(f"- 📚 {m}")

        # Conseil méthodologique
        if feedback_llm.get("advice"):
            st.info(f"💡 **Conseil** : {feedback_llm['advice']}")

        # ✨ Découvertes additionnelles
        if feedback_llm.get("decouvertes_section"):
            st.markdown("##### ✨ Découvertes additionnelles")
            st.success(feedback_llm["decouvertes_section"])

        # Encouragement
        if feedback_llm.get("encouragement"):
            st.markdown(f"🌟 *{feedback_llm['encouragement']}*")

    elif feedback_llm and feedback_llm.get("error"):
        st.warning(f"⚠️ Feedback LLM indisponible : {feedback_llm['error']}")

    # ─── Section Découvertes Additionnelles (données brutes) ─────────
    if decouvertes_additionnelles:
        st.divider()
        st.subheader("✨ Découvertes Additionnelles (hors barème)")
        st.caption(
            "Concepts cliniques réels identifiés par l'étudiant mais non exigés dans le barème. "
            "Ils ne modifient pas la note mais témoignent d'un bon sens d'observation."
        )
        for d in decouvertes_additionnelles:
            cat = d.get('categorie', 'DESCRIPTEUR_ECG')
            categorie_colors_map = {
                'DIAGNOSTIC_URGENT': ('🚨', '#D32F2F'),
                'DIAGNOSTIC_MAJEUR': ('⚡', '#F57C00'),
                'SIGNE_ECG_PATHOLOGIQUE': ('⚠️', '#FFA726'),
                'DESCRIPTEUR_ECG': ('📝', '#66BB6A'),
            }
            icon, color = categorie_colors_map.get(cat, ('📝', '#66BB6A'))
            terme = d.get('terme_brut', '') or ''
            st.markdown(f"""
            <div style="background-color: #fffde7; border-left: 4px solid #FFD600; padding: 10px; margin: 6px 0; border-radius: 4px;">
                ✨ <strong>{d['concept_name']}</strong> {icon}
                <span style="color: {color}; font-size: 0.85em;">({cat.replace('_', ' ')})</span>
                {f'<br><small>Terme brut : "{terme}"</small>' if terme else ''}
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
    Uses the RAG Neurosymbolic pipeline (Briques 2-3-4).
    
    Args:
        student_annotations: List of student annotation strings
        expert_concepts: List of expert concept strings
        case_id: Case identifier
    
    Returns:
        dict with correction results (score, correct_concepts, missing_concepts, extra_concepts)
    """
    try:
        moteur = HybridSearchEngine()
        student_text = " ".join(student_annotations)
        
        # Extraction NER
        extraction = extract_clinical_terms(student_text)
        
        # Resolution RAG
        student_ids = set()
        for entite in extraction.entites:
            candidats = moteur.search_top_k(entite.terme_brut)
            resolution = resolve_term_to_ontology(
                entite.terme_brut, entite.contexte_phrase, candidats
            )
            if resolution["ontology_id"] != "NONE" and entite.statut in ("present", "hypothese"):
                student_ids.add(resolution["ontology_id"])
        
        # Resolution des concepts experts vers IDs
        expert_ids = set()
        for concept in expert_concepts:
            owl = find_owl_concept(concept)
            if owl:
                expert_ids.add(owl.get('ontology_id'))
        
        correct = list(student_ids & expert_ids)
        missing = list(expert_ids - student_ids)
        extra = list(student_ids - expert_ids)
        
        score = (len(correct) / len(expert_ids) * 100) if expert_ids else 0
        
        return {
            'score': score,
            'correct_concepts': correct,
            'missing_concepts': missing,
            'extra_concepts': extra,
        }
        
    except Exception as e:
        return {
            'score': 0,
            'error': str(e),
            'correct_concepts': [],
            'missing_concepts': [],
            'extra_concepts': [],
        }


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    # Pour test standalone
    st.set_page_config(page_title="Correction LLM", page_icon="🔍", layout="wide")
    page_correction_llm()
