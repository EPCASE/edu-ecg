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
    else:
        st.info("💭 Aucune annotation sélectionnée")
    
    return st.session_state[f'{key_prefix}_tags']

def search_ontology_concepts(concepts, search_term):
    """
    Recherche dans les concepts de l'ontologie
    
    Args:
        concepts: Liste des concepts disponibles
        search_term: Terme à rechercher
    
    Returns:
        list: Liste des concepts correspondants
    """
    if not search_term or len(search_term) < 2:
        return []
    
    search_lower = search_term.lower()
    matches = []
    
    # Recherche exacte en priorité
    for concept in concepts:
        if search_lower in concept.lower():
            matches.append(concept)
    
    # Trier par pertinence (correspondance au début du mot en premier)
    matches.sort(key=lambda x: (
        not x.lower().startswith(search_lower),  # Commence par le terme
        not search_lower in x.lower().split()[0],  # Premier mot contient le terme
        len(x)  # Plus court en premier
    ))
    
    return matches[:10]  # Limiter à 10 suggestions


def get_ontology_concepts():
    """
    Récupère la liste des concepts de l'ontologie depuis la session ou charge depuis le fichier
    
    Returns:
        list: Liste des concepts ECG
    """
    
    # Essayer de récupérer depuis la session state
    if 'concepts' in st.session_state:
        return st.session_state.concepts
    
    # Charger depuis le fichier ontologie si disponible
    try:
        ontology_path = Path(__file__).parent.parent / "data" / "ontologie.owx"
        if ontology_path.exists():
            # Si on a un corrector en session, utiliser ses concepts
            if 'corrector' in st.session_state:
                return list(st.session_state.corrector.concepts.keys())
    except Exception:
        pass
    
    # Fallback : concepts de base
    return [
        "Rythme sinusal", "Tachycardie", "Bradycardie", "Fibrillation atriale",
        "Flutter atrial", "Extrasystole", "Bloc AV", "QRS large", "QRS fin",
        "Onde P", "Intervalle PR", "Segment ST", "Onde T", "Intervalle QT",
        "Axe normal", "Déviation axiale gauche", "Déviation axiale droite",
        "Hypertrophie VG", "Hypertrophie VD", "Ischémie", "Lésion", "Nécrose"
    ]


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
    
    # Affichage des annotations ontologiques
    if ontology_annotations:
        st.markdown("**🧠 Concepts ontologiques :**")
        for annotation in ontology_annotations:
            st.markdown(f"- 🧠 {annotation}")
    
    # Affichage des annotations personnalisées
    if custom_annotations:
        st.markdown("**📝 Annotations personnalisées :**")
        for annotation in custom_annotations:
            st.markdown(f"- 📝 {annotation}")
    
    # Statistiques
    total = len(annotations)
    ontology_count = len(ontology_annotations)
    custom_count = len(custom_annotations)
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total", total)
    
    with col2:
        st.metric("🧠 Ontologie", ontology_count)
    
    with col3:
        st.metric("📝 Personnalisé", custom_count)


def validate_annotations(annotations):
    """
    Valide et nettoie une liste d'annotations
    
    Args:
        annotations: Liste des annotations à valider
    
    Returns:
        tuple: (annotations_valides, annotations_invalides)
    """
    
    valid_annotations = []
    invalid_annotations = []
    
    for annotation in annotations:
        # Nettoyage basique
        cleaned = annotation.strip()
        
        # Validation
        if len(cleaned) >= 2 and len(cleaned) <= 100:
            valid_annotations.append(cleaned)
        else:
            invalid_annotations.append(annotation)
    
    return valid_annotations, invalid_annotations


def export_annotations_to_json(annotations, metadata=None):
    """
    Exporte les annotations au format JSON
    
    Args:
        annotations: Liste des annotations
        metadata: Métadonnées additionnelles
    
    Returns:
        str: JSON formaté
    """
    
    export_data = {
        "annotations": annotations,
        "count": len(annotations),
        "export_date": str(st.session_state.get('current_time', 'unknown')),
        "metadata": metadata or {}
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def import_annotations_from_json(json_data):
    """
    Importe des annotations depuis du JSON
    
    Args:
        json_data: Données JSON à importer
    
    Returns:
        list: Liste des annotations importées
    """
    
    try:
        data = json.loads(json_data) if isinstance(json_data, str) else json_data
        return data.get('annotations', [])
    except Exception as e:
        st.error(f"❌ Erreur lors de l'import : {e}")
        return []
