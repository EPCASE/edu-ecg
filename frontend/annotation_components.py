#!/usr/bin/env python3
"""
Composants d'annotation semi-automatique avec ontologie ECG
"""

import streamlit as st
from pathlib import Path
import json
from typing import List, Dict, Set

# Ontologie ECG structurée pour l'autocomplétion
ECG_ONTOLOGY = {
    "rythme": [
        "Rythme sinusal", "Fibrillation auriculaire", "Flutter auriculaire", 
        "Tachycardie sinusale", "Bradycardie sinusale", "Arythmie sinusale",
        "Tachycardie supraventriculaire", "Tachycardie ventriculaire",
        "Fibrillation ventriculaire", "Rythme jonctionnel", "Rythme idioventriculaire"
    ],
    "conduction": [
        "BAV 1er degré", "BAV 2ème degré Mobitz 1", "BAV 2ème degré Mobitz 2",
        "BAV 3ème degré", "Bloc de branche droit", "Bloc de branche gauche",
        "Hémibloc antérieur gauche", "Hémibloc postérieur gauche",
        "Préexcitation", "Syndrome de Wolff-Parkinson-White"
    ],
    "morphologie": [
        "Onde P normale", "Onde P bifide", "Onde P ample", "Absence d'onde P",
        "QRS fin", "QRS large", "QRS fragmenté", "Onde Q pathologique",
        "Onde R prédominante", "Onde T inversée", "Onde T ample", "Onde T plate",
        "Sus-décalage ST", "Sous-décalage ST", "Onde U présente"
    ],
    "intervalles": [
        "PR court", "PR long", "PR normal", "QT court", "QT long", "QT normal",
        "QRS < 120ms", "QRS > 120ms", "Intervalle RR régulier", "Intervalle RR irrégulier"
    ],
    "pathologie": [
        "Infarctus aigu", "Infarctus ancien", "Ischémie myocardique", "Péricardite",
        "Myocardite", "Hypertrophie ventriculaire gauche", "Hypertrophie ventriculaire droite",
        "Hypertrophie auriculaire gauche", "Hypertrophie auriculaire droite",
        "Syndrome coronarien aigu", "STEMI", "NSTEMI"
    ],
    "électrolytes": [
        "Hyperkaliémie", "Hypokaliémie", "Hypercalcémie", "Hypocalcémie",
        "Hypermagnésémie", "Hypomagnésémie"
    ],
    "autres": [
        "Pacemaker", "Défibrillateur implantable", "Artéfacts", "Mauvaise qualité du tracé",
        "Extrasystoles auriculaires", "Extrasystoles ventriculaires", "Bigéminisme",
        "Trigéminisme", "Torsade de pointes", "Syndrome du QT long congénital"
    ]
}

def get_ontology_concepts() -> List[str]:
    """Retourne tous les concepts de l'ontologie ECG"""
    all_concepts = []
    for category, concepts in ECG_ONTOLOGY.items():
        all_concepts.extend(concepts)
    return sorted(all_concepts)

def get_filtered_suggestions(search_term: str, selected_tags: Set[str], max_suggestions: int = 10) -> List[Dict[str, str]]:
    """
    Retourne des suggestions filtrées basées sur le terme de recherche
    
    Args:
        search_term: Terme recherché par l'utilisateur
        selected_tags: Tags déjà sélectionnés (pour les exclure)
        max_suggestions: Nombre maximum de suggestions
    
    Returns:
        Liste de dictionnaires avec 'concept' et 'category'
    """
    if not search_term or len(search_term) < 2:
        return []
    
    search_lower = search_term.lower()
    suggestions = []
    
    for category, concepts in ECG_ONTOLOGY.items():
        for concept in concepts:
            # Exclure les concepts déjà sélectionnés
            if concept in selected_tags:
                continue
                
            # Recherche flexible
            concept_lower = concept.lower()
            if (search_lower in concept_lower or 
                concept_lower.startswith(search_lower) or
                any(word.startswith(search_lower) for word in concept_lower.split())):
                
                suggestions.append({
                    'concept': concept,
                    'category': category,
                    'score': calculate_relevance_score(search_lower, concept_lower)
                })
    
    # Trier par score de pertinence
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    
    return suggestions[:max_suggestions]

def calculate_relevance_score(search: str, concept: str) -> int:
    """Calcule un score de pertinence pour le tri des suggestions"""
    score = 0
    
    # Correspondance exacte
    if search == concept:
        score += 100
    # Commence par le terme
    elif concept.startswith(search):
        score += 80
    # Mot complet qui commence par le terme
    elif any(word.startswith(search) for word in concept.split()):
        score += 60
    # Contient le terme
    elif search in concept:
        score += 40
    
    # Bonus pour les termes courts (plus spécifiques)
    score += max(0, 20 - len(concept))
    
    return score

def smart_annotation_input(key_prefix: str = "annotation", max_tags: int = 10) -> List[str]:
    """
    Interface de saisie d'annotations avec autocomplétion intelligente
    
    Args:
        key_prefix: Préfixe pour les clés Streamlit
        max_tags: Nombre maximum de tags
    
    Returns:
        Liste des annotations sélectionnées
    """
    
    # Initialiser l'état si nécessaire
    if f'{key_prefix}_selected_tags' not in st.session_state:
        st.session_state[f'{key_prefix}_selected_tags'] = []
    if f'{key_prefix}_search_term' not in st.session_state:
        st.session_state[f'{key_prefix}_search_term'] = ""
    
    selected_tags = st.session_state[f'{key_prefix}_selected_tags']
    
    # Afficher les tags déjà sélectionnés
    if selected_tags:
        st.markdown("**🏷️ Annotations sélectionnées:**")
        
        # Afficher les tags avec possibilité de suppression
        cols = st.columns(min(len(selected_tags), 4))
        for idx, tag in enumerate(selected_tags):
            with cols[idx % len(cols)]:
                if st.button(f"❌ {tag}", key=f"{key_prefix}_remove_{idx}"):
                    st.session_state[f'{key_prefix}_selected_tags'].remove(tag)
                    st.rerun()
    
    # Zone de recherche avec autocomplétion
    if len(selected_tags) < max_tags:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Rechercher une annotation",
                value=st.session_state[f'{key_prefix}_search_term'],
                placeholder="Tapez au moins 2 caractères...",
                key=f"{key_prefix}_search_input",
                help="Commencez à taper pour voir les suggestions de l'ontologie ECG"
            )
            
            # Mettre à jour le terme de recherche dans session_state
            if search_term != st.session_state[f'{key_prefix}_search_term']:
                st.session_state[f'{key_prefix}_search_term'] = search_term
        
        with col2:
            if st.button("➕ Texte libre", key=f"{key_prefix}_free_text"):
                if search_term and search_term not in selected_tags:
                    st.session_state[f'{key_prefix}_selected_tags'].append(search_term)
                    st.session_state[f'{key_prefix}_search_term'] = ""
                    st.rerun()
        
        # Afficher les suggestions
        if search_term and len(search_term) >= 2:
            suggestions = get_filtered_suggestions(
                search_term, 
                set(selected_tags),
                max_suggestions=8
            )
            
            if suggestions:
                st.markdown("**💡 Suggestions de l'ontologie:**")
                
                # Afficher les suggestions groupées par catégorie
                categories_shown = set()
                for suggestion in suggestions:
                    category = suggestion['category']
                    concept = suggestion['concept']
                    
                    # Afficher la catégorie si c'est la première fois
                    if category not in categories_shown:
                        st.caption(f"**{category.upper()}**")
                        categories_shown.add(category)
                    
                    # Bouton pour ajouter le concept
                    if st.button(
                        f"➕ {concept}",
                        key=f"{key_prefix}_add_{concept}",
                        help=f"Ajouter '{concept}' aux annotations"
                    ):
                        st.session_state[f'{key_prefix}_selected_tags'].append(concept)
                        st.session_state[f'{key_prefix}_search_term'] = ""
                        st.rerun()
            else:
                st.info("💡 Aucune suggestion trouvée. Utilisez 'Texte libre' pour ajouter votre propre annotation.")
    else:
        st.warning(f"⚠️ Limite de {max_tags} annotations atteinte")
    
    return selected_tags

def display_annotation_summary(annotations: List[str], title: str = "Résumé des annotations"):
    """
    Affiche un résumé visuel des annotations sélectionnées
    
    Args:
        annotations: Liste des annotations
        title: Titre de la section
    """
    if annotations:
        st.markdown(f"### {title}")
        
        # Grouper par catégorie
        categorized = {}
        uncategorized = []
        
        for annotation in annotations:
            found = False
            for category, concepts in ECG_ONTOLOGY.items():
                if annotation in concepts:
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(annotation)
                    found = True
                    break
            
            if not found:
                uncategorized.append(annotation)
        
        # Afficher par catégorie
        for category, items in categorized.items():
            st.markdown(f"**{category.upper()}**")
            for item in items:
                st.markdown(f"• {item}")
        
        # Afficher les annotations libres
        if uncategorized:
            st.markdown("**AUTRES**")
            for item in uncategorized:
                st.markdown(f"• {item}")

def export_annotations_to_json(annotations: List[str], case_id: str) -> str:
    """
    Exporte les annotations au format JSON
    
    Args:
        annotations: Liste des annotations
        case_id: Identifiant du cas
    
    Returns:
        JSON string des annotations
    """
    export_data = {
        'case_id': case_id,
        'annotations': annotations,
        'timestamp': st.session_state.get('annotation_timestamp', ''),
        'annotator': st.session_state.get('user_info', {}).get('name', 'Unknown')
    }
    
    return json.dumps(export_data, ensure_ascii=False, indent=2)

# Pour compatibilité avec l'ancien code
def get_annotation_suggestions(search_term: str) -> List[str]:
    """Fonction de compatibilité pour l'ancien code"""
    suggestions = get_filtered_suggestions(search_term, set(), max_suggestions=10)
    return [s['concept'] for s in suggestions]