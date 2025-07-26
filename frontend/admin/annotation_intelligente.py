#!/usr/bin/env python3
"""
Composant d'annotation intelligent avec autocomplétion basée sur l'ontologie ECG
Interface moderne avec tags cliquables et saisie prédictive
"""

import streamlit as st
import json
from pathlib import Path
import sys

# Ajout des chemins pour l'ontologie
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "backend"))

try:
    from correction_engine import OntologyCorrector
    ONTOLOGY_AVAILABLE = True
except ImportError:
    ONTOLOGY_AVAILABLE = False

def load_ontology_concepts():
    """Charge les concepts de l'ontologie ECG"""
    if not ONTOLOGY_AVAILABLE:
        return []
    
    try:
        if 'ontology_concepts' not in st.session_state:
            ontology_path = project_root / "data" / "ontologie.owx"
            corrector = OntologyCorrector(str(ontology_path))
            st.session_state.ontology_concepts = corrector.get_concept_names()
            st.session_state.ontology_corrector = corrector
        
        return st.session_state.ontology_concepts
    except Exception as e:
        st.error(f"❌ Erreur chargement ontologie : {e}")
        return []

def filter_concepts(query, concepts_list):
    """Filtre les concepts selon la requête de l'utilisateur"""
    if not query:
        return []
    
    query_lower = query.lower()
    
    # Recherche exacte d'abord
    exact_matches = [concept for concept in concepts_list 
                    if concept.lower().startswith(query_lower)]
    
    # Puis recherche partielle
    partial_matches = [concept for concept in concepts_list 
                      if query_lower in concept.lower() and concept not in exact_matches]
    
    # Limiter à 10 suggestions max
    return (exact_matches + partial_matches)[:10]

def annotation_intelligente_admin(key_suffix="", initial_tags=None):
    """
    Interface d'annotation intelligente pour administrateur/expert
    
    Args:
        key_suffix: Suffixe pour les clés Streamlit (éviter conflits)
        initial_tags: Liste des tags initiaux à afficher
    
    Returns:
        Liste des tags sélectionnés
    """
    
    # Initialisation
    concepts_list = load_ontology_concepts()
    if not concepts_list:
        st.warning("⚠️ Ontologie non disponible - mode saisie libre")
        return st.text_area("Annotation libre :", key=f"annotation_libre_{key_suffix}")
    
    # État des tags sélectionnés
    tags_key = f"selected_tags_{key_suffix}"
    if tags_key not in st.session_state:
        st.session_state[tags_key] = initial_tags or []
    
    st.markdown("#### 🏷️ Annotation par mots-clés intelligents")
    
    # Zone de saisie avec autocomplétion
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Vérifier si on doit vider l'input
        clear_flag_key = f"clear_input_flag_{key_suffix}"
        input_value = ""
        if clear_flag_key in st.session_state and st.session_state[clear_flag_key]:
            input_value = ""
            st.session_state[clear_flag_key] = False
        
        # Input pour nouveau concept
        query = st.text_input(
            "Ajouter un concept ECG :",
            value=input_value,
            placeholder="Tapez pour rechercher dans l'ontologie...",
            key=f"concept_input_{key_suffix}",
            help="🔍 Saisissez quelques lettres pour voir les suggestions de l'ontologie"
        )
        
        # Suggestions en temps réel
        if query:
            suggestions = filter_concepts(query, concepts_list)
            if suggestions:
                st.markdown("**💡 Suggestions :**")
                cols = st.columns(min(3, len(suggestions)))
                
                for i, suggestion in enumerate(suggestions[:6]):  # Max 6 suggestions visibles
                    with cols[i % 3]:
                        if st.button(
                            f"+ {suggestion}", 
                            key=f"add_suggestion_{suggestion}_{key_suffix}_{i}",
                            help=f"Ajouter '{suggestion}' aux annotations"
                        ):
                            if suggestion not in st.session_state[tags_key]:
                                st.session_state[tags_key].append(suggestion)
                                # Ne pas modifier l'input directement - utiliser un flag
                                st.session_state[f"clear_input_flag_{key_suffix}"] = True
                                st.rerun()
    
    with col2:
        if st.button("🗑️ Tout effacer", key=f"clear_all_{key_suffix}"):
            st.session_state[tags_key] = []
            st.rerun()
    
    # Affichage des tags sélectionnés
    if st.session_state[tags_key]:
        st.markdown("**🏷️ Concepts annotés :**")
        
        # Créer des colonnes pour afficher les tags
        tag_cols = st.columns(min(4, len(st.session_state[tags_key])))
        
        for i, tag in enumerate(st.session_state[tags_key]):
            with tag_cols[i % 4]:
                # Bouton-tag cliquable pour suppression
                if st.button(
                    f"❌ {tag}", 
                    key=f"remove_tag_{tag}_{i}_{key_suffix}",
                    help=f"Cliquer pour supprimer '{tag}'"
                ):
                    st.session_state[tags_key].remove(tag)
                    st.rerun()
    else:
        st.info("💭 Aucun concept sélectionné. Commencez à taper pour voir les suggestions.")
    
    return st.session_state[tags_key]

def annotation_intelligente_etudiant(key_suffix="", max_suggestions=8):
    """
    Interface d'annotation intelligente pour étudiant
    Plus guidée et pédagogique
    
    Args:
        key_suffix: Suffixe pour les clés Streamlit
        max_suggestions: Nombre max de suggestions à afficher
    
    Returns:
        Liste des concepts sélectionnés par l'étudiant
    """
    
    concepts_list = load_ontology_concepts()
    if not concepts_list:
        st.warning("⚠️ Ontologie non disponible")
        return []
    
    # État des réponses de l'étudiant
    student_key = f"student_answers_{key_suffix}"
    if student_key not in st.session_state:
        st.session_state[student_key] = []
    
    st.markdown("#### 🎓 Votre interprétation de l'ECG")
    st.caption("💡 Tapez quelques lettres et sélectionnez les concepts appropriés")
    
    # Zone de saisie étudiante 
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Vérifier si on doit vider l'input étudiant
        clear_student_flag_key = f"clear_student_input_flag_{key_suffix}"
        student_input_value = ""
        if clear_student_flag_key in st.session_state and st.session_state[clear_student_flag_key]:
            student_input_value = ""
            st.session_state[clear_student_flag_key] = False
        
        student_query = st.text_input(
            "Que voyez-vous sur cet ECG ?",
            value=student_input_value,
            placeholder="Ex: rythrme, frequence, axe...",
            key=f"student_input_{key_suffix}",
            help="🔤 Commencez à taper un concept médical"
        )
        
        # Menu de sélection intelligent pour étudiants
        if student_query:
            suggestions = filter_concepts(student_query, concepts_list)
            if suggestions:
                st.markdown("**🎯 Concepts possibles :**")
                
                # Affichage sous forme de sélecteur
                selected_suggestion = st.selectbox(
                    "Choisissez le concept approprié :",
                    [""] + suggestions,  # Option vide en premier
                    key=f"student_select_{key_suffix}",
                    help="Sélectionnez le concept qui correspond à votre observation"
                )
                
                if selected_suggestion and st.button(
                    f"✅ Ajouter '{selected_suggestion}'", 
                    key=f"confirm_student_{key_suffix}"
                ):
                    if selected_suggestion not in st.session_state[student_key]:
                        st.session_state[student_key].append(selected_suggestion)
                        # Utiliser un flag au lieu de modifier directement l'input
                        st.session_state[f"clear_student_input_flag_{key_suffix}"] = True
                        st.rerun()
    
    with col2:
        if st.button("🔄 Recommencer", key=f"restart_student_{key_suffix}"):
            st.session_state[student_key] = []
            st.rerun()
    
    # Affichage des réponses de l'étudiant
    if st.session_state[student_key]:
        st.markdown("**✅ Vos observations :**")
        
        for i, answer in enumerate(st.session_state[student_key]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.success(f"🩺 {answer}")
            with col2:
                if st.button("❌", key=f"remove_student_{i}_{key_suffix}"):
                    st.session_state[student_key].remove(answer)
                    st.rerun()
    else:
        st.info("🔍 Commencez votre analyse en tapant vos premières observations")
    
    return st.session_state[student_key]

def compare_annotations(expert_tags, student_tags):
    """
    Compare les annotations expertes et étudiantes
    Utilise l'ontologie pour un scoring intelligent
    """
    
    if not ONTOLOGY_AVAILABLE or 'ontology_corrector' not in st.session_state:
        return {"score": 0, "feedback": "Ontologie non disponible"}
    
    corrector = st.session_state.ontology_corrector
    
    # Calcul du score global
    total_score = 0
    detailed_feedback = []
    
    if not student_tags:
        return {
            "score": 0, 
            "feedback": "❌ Aucune réponse fournie",
            "details": []
        }
    
    # Comparaison concept par concept
    for student_concept in student_tags:
        best_match_score = 0
        best_match_expert = ""
        
        for expert_concept in expert_tags:
            score = corrector.get_score(expert_concept, student_concept)
            if score > best_match_score:
                best_match_score = score
                best_match_expert = expert_concept
        
        total_score += best_match_score
        
        if best_match_score >= 80:
            detailed_feedback.append(f"✅ '{student_concept}' : Excellent ({best_match_score}%)")
        elif best_match_score >= 50:
            detailed_feedback.append(f"🟡 '{student_concept}' : Bien, proche de '{best_match_expert}' ({best_match_score}%)")
        else:
            detailed_feedback.append(f"❌ '{student_concept}' : À revoir ({best_match_score}%)")
    
    # Score final
    final_score = total_score / len(student_tags) if student_tags else 0
    
    return {
        "score": round(final_score),
        "feedback": f"Score global : {round(final_score)}%",
        "details": detailed_feedback
    }

# Test du composant
if __name__ == "__main__":
    st.set_page_config(
        page_title="Test Annotation Intelligente",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 Test d'Annotation Intelligente")
    
    tab1, tab2 = st.tabs(["👨‍⚕️ Mode Expert", "🎓 Mode Étudiant"])
    
    with tab1:
        st.header("Interface Administrateur/Expert")
        expert_tags = annotation_intelligente_admin("test_admin")
        st.write("**Tags sélectionnés :**", expert_tags)
    
    with tab2:
        st.header("Interface Étudiant")
        student_tags = annotation_intelligente_etudiant("test_student")
        st.write("**Réponses étudiant :**", student_tags)
        
        if expert_tags and student_tags:
            st.markdown("---")
            st.header("🎯 Correction Automatique")
            comparison = compare_annotations(expert_tags, student_tags)
            
            st.metric("Score", f"{comparison['score']}%")
            st.info(comparison['feedback'])
            
            for detail in comparison.get('details', []):
                st.write(detail)
