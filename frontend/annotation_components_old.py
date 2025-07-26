#!/usr/bin/env python3
"""
Composants d'annotation semi-automatique avec ontologie ECG
"""

import streamlit as st
from pathlib import Path
import json

def smart_annotation_input(key_prefix="annotation", max_tags=10):
    """
    Interface de saisie semi-automatique d'annotations avec l'ontologie
    
    Args:
        key_prefix: Préfixe pour les clés de session
        max_tags: Nombre maximum de tags autorisés
    
    Returns:
        list: Liste des annotations sélectionnées
    """
    
    # Initialiser les annotations dans la session
    if f'{key_prefix}_tags' not in st.session_state:
        st.session_state[f'{key_prefix}_tags'] = []
    
    # Récupérer les concepts de l'ontologie
    concepts = get_ontology_concepts()
    
    st.markdown("### 🏷️ Annotations ECG")
    st.markdown("*Saisissez des mots-clés pour rechercher dans l'ontologie médicale*")
    
    # Zone de saisie avec autocomplétion
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Input pour rechercher dans l'ontologie
        search_term = st.text_input(
            "🔍 Rechercher un concept médical",
            placeholder="Ex: rythme, tachycardie, fibrillation...",
            key=f"{key_prefix}_search",
            help="Tapez pour rechercher dans l'ontologie de 281 concepts ECG"
        )
    
    with col2:
        # Bouton pour ajouter le terme personnalisé
        if st.button("➕ Ajouter", key=f"{key_prefix}_add_custom"):
            if search_term and search_term not in st.session_state[f'{key_prefix}_tags']:
                if len(st.session_state[f'{key_prefix}_tags']) < max_tags:
                    st.session_state[f'{key_prefix}_tags'].append(search_term)
                    # Rerun pour rafraîchir l'interface
                    st.rerun()
                else:
                    st.warning(f"⚠️ Maximum {max_tags} annotations autorisées")
    
    # Suggestions basées sur la recherche
    if search_term:
        suggestions = search_ontology_concepts(concepts, search_term)
        
        if suggestions:
            st.markdown("**💡 Suggestions de l'ontologie :**")
            
            # Afficher les suggestions en colonnes
            cols = st.columns(min(3, len(suggestions)))
            
            for i, suggestion in enumerate(suggestions[:6]):  # Limiter à 6 suggestions
                col_idx = i % len(cols)
                with cols[col_idx]:
                    if st.button(
                        f"✨ {suggestion}", 
                        key=f"{key_prefix}_suggestion_{i}",
                        help=f"Ajouter '{suggestion}' aux annotations"
                    ):
                        if suggestion not in st.session_state[f'{key_prefix}_tags']:
                            if len(st.session_state[f'{key_prefix}_tags']) < max_tags:
                                st.session_state[f'{key_prefix}_tags'].append(suggestion)
                                st.rerun()
                            else:
                                st.warning(f"⚠️ Maximum {max_tags} annotations autorisées")
        else:
            st.info("💭 Aucun concept trouvé dans l'ontologie - vous pouvez ajouter ce terme personnalisé")
    
    # Affichage des annotations actuelles
    current_tags = st.session_state[f'{key_prefix}_tags']
    
    if current_tags:
        st.markdown("**🏷️ Annotations sélectionnées :**")
        
        # Afficher les tags avec boutons de suppression
        cols = st.columns(min(4, len(current_tags)))
        
        for i, tag in enumerate(current_tags):
            col_idx = i % len(cols)
            with cols[col_idx]:
                col_tag, col_del = st.columns([3, 1])
                
                with col_tag:
                    # Vérifier si c'est un concept de l'ontologie
                    is_ontology = tag.lower() in [c.lower() for c in concepts]
                    icon = "🧠" if is_ontology else "📝"
                    st.markdown(f"{icon} **{tag}**")
                
                with col_del:
                    if st.button("❌", key=f"{key_prefix}_remove_{i}", help=f"Supprimer '{tag}'"):
                        st.session_state[f'{key_prefix}_tags'].remove(tag)
                        st.rerun()
        
        # Statistiques
        ontology_count = sum(1 for tag in current_tags if tag.lower() in [c.lower() for c in concepts])
        custom_count = len(current_tags) - ontology_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🧠 Ontologie", ontology_count)
        with col2:
            st.metric("📝 Personnalisés", custom_count)
        with col3:
            st.metric("📊 Total", len(current_tags))
        
        # Bouton pour vider toutes les annotations
        if st.button("🗑️ Vider toutes les annotations", key=f"{key_prefix}_clear_all"):
            st.session_state[f'{key_prefix}_tags'] = []
            st.rerun()
    
    else:
        st.info("💡 Aucune annotation ajoutée. Utilisez la recherche pour commencer.")
    
    return current_tags

def get_ontology_concepts():
    """Récupère la liste des concepts de l'ontologie"""
    
    if 'concepts' in st.session_state:
        return st.session_state.concepts
    
    # Fallback avec concepts de base si l'ontologie n'est pas chargée
    basic_concepts = [
        "rythme sinusal", "tachycardie", "bradycardie", "fibrillation auriculaire",
        "extrasystole", "bloc auriculoventriculaire", "onde P", "complexe QRS", "onde T",
        "intervalle PR", "intervalle QT", "axe électrique", "ischémie", "infarctus",
        "hypertrophie ventriculaire", "troubles de la repolarisation", "arythmie",
        "flutter auriculaire", "tachycardie ventriculaire", "bradycardie sinusale",
        "tachycardie sinusale", "bigéminisme", "trigéminisme", "pause sinusale",
        "bloc de branche", "hémibloc", "préexcitation", "syndrome de Wolff-Parkinson-White"
    ]
    
    return basic_concepts

def search_ontology_concepts(concepts, search_term, max_results=6):
    """
    Recherche des concepts dans l'ontologie
    
    Args:
        concepts: Liste des concepts de l'ontologie
        search_term: Terme de recherche
        max_results: Nombre maximum de résultats
    
    Returns:
        list: Liste des concepts correspondants
    """
    
    if not search_term or not concepts:
        return []
    
    search_lower = search_term.lower().strip()
    
    # Recherche exacte en premier
    exact_matches = [c for c in concepts if search_lower == c.lower()]
    
    # Recherche qui commence par le terme
    starts_with = [c for c in concepts if c.lower().startswith(search_lower) and c not in exact_matches]
    
    # Recherche qui contient le terme
    contains = [c for c in concepts if search_lower in c.lower() and c not in exact_matches and c not in starts_with]
    
    # Combiner les résultats par priorité
    results = exact_matches + starts_with + contains
    
    return results[:max_results]

def display_annotation_summary(annotations, title="📋 Résumé des annotations"):
    """
    Affiche un résumé des annotations avec classification
    
    Args:
        annotations: Liste des annotations
        title: Titre de la section
    """
    
    if not annotations:
        st.info("💭 Aucune annotation disponible")
        return
    
    st.markdown(f"### {title}")
    
    concepts = get_ontology_concepts()
    
    # Classifier les annotations
    ontology_annotations = []
    custom_annotations = []
    
    for annotation in annotations:
        if annotation.lower() in [c.lower() for c in concepts]:
            ontology_annotations.append(annotation)
        else:
            custom_annotations.append(annotation)
    
    # Affichage par catégorie
    col1, col2 = st.columns(2)
    
    with col1:
        if ontology_annotations:
            st.markdown("**🧠 Concepts de l'ontologie :**")
            for annotation in ontology_annotations:
                st.markdown(f"• {annotation}")
        else:
            st.markdown("**🧠 Concepts de l'ontologie :** *Aucun*")
    
    with col2:
        if custom_annotations:
            st.markdown("**📝 Annotations personnalisées :**")
            for annotation in custom_annotations:
                st.markdown(f"• {annotation}")
        else:
            st.markdown("**📝 Annotations personnalisées :** *Aucune*")
    
    # Statistiques globales
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🧠 Ontologie", len(ontology_annotations))
    with col2:
        st.metric("📝 Personnalisées", len(custom_annotations))
    with col3:
        st.metric("📊 Total", len(annotations))

def export_annotations_format(annotations, format_type="list"):
    """
    Exporte les annotations dans différents formats
    
    Args:
        annotations: Liste des annotations
        format_type: Type de format ('list', 'dict', 'json')
    
    Returns:
        Annotations formatées
    """
    
    if format_type == "list":
        return annotations
    
    elif format_type == "dict":
        concepts = get_ontology_concepts()
        return {
            'ontology_concepts': [a for a in annotations if a.lower() in [c.lower() for c in concepts]],
            'custom_annotations': [a for a in annotations if a.lower() not in [c.lower() for c in concepts]],
            'total_count': len(annotations)
        }
    
    elif format_type == "json":
        concepts = get_ontology_concepts()
        data = {
            'annotations': annotations,
            'ontology_concepts': [a for a in annotations if a.lower() in [c.lower() for c in concepts]],
            'custom_annotations': [a for a in annotations if a.lower() not in [c.lower() for c in concepts]],
            'metadata': {
                'total_count': len(annotations),
                'ontology_count': len([a for a in annotations if a.lower() in [c.lower() for c in concepts]]),
                'custom_count': len([a for a in annotations if a.lower() not in [c.lower() for c in concepts]])
            }
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    return annotations
