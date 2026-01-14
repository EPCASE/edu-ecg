"""
Composant de sélection de structure anatomique
Réutilise la logique du territoire_selector pour les origines anatomiques

Auteur: Dr. Grégoire + GitHub Copilot
Date: 2026-01-14
"""

import streamlit as st
from typing import List, Optional, Dict
from pathlib import Path
import json
import sys

# Ajouter backend au path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from morphology_resolver import MorphologyResolver


def structure_selector_interface(
    concept_name: str,
    key_prefix: str = "structure",
    auto_add_morphology: bool = True
) -> Optional[Dict]:
    """
    Interface de sélection de structure anatomique (identique au territory_selector)
    
    Args:
        concept_name: Nom du concept (ex: "Échappement ventriculaire")
        key_prefix: Préfixe pour les clés Streamlit
        auto_add_morphology: Si True, calcule et retourne la morphologie inversée
        
    Returns:
        Dict avec:
        - selected_structure: Structure sélectionnée
        - calculated_morphology: Morphologie calculée (si auto_add_morphology=True)
        - explanation: Explication du calcul
    """
    # Initialiser le résolveur
    if 'morphology_resolver' not in st.session_state:
        try:
            st.session_state.morphology_resolver = MorphologyResolver()
        except Exception as e:
            st.warning(f"⚠️ Résolveur morphologie non disponible: {e}")
            return None
    
    resolver = st.session_state.morphology_resolver
    
    # Récupérer les structures possibles
    concept_info = resolver.get_concept_info(concept_name)
    
    if not concept_info:
        return None
    
    origin_structures = concept_info.get('origin_structures', [])
    
    if not origin_structures:
        # Pas de structure à sélectionner
        return None
    
    # Récupérer TOUTES les enfants de "Ventricule" depuis l'ontologie
    # (Branche droite, Branche gauche, Muscle papillaire, etc.)
    available_structures = get_ventricle_children()
    
    if not available_structures:
        # Fallback: toutes les structures par défaut
        available_structures = ['Branche droite', 'Branche gauche', 'Muscle papillaire', 'Bandelette modératrice', 'Réseau de purkinje']
    
    # Interface de sélection
    st.markdown("#### 🏗️ Origine anatomique")
    st.caption("Sélectionnez la structure d'origine de l'échappement")
    
    selected_structure = st.selectbox(
        "Structure:",
        options=available_structures,
        key=f"{key_prefix}_structure_select",
        help="La structure d'où provient l'échappement (détermine la morphologie inversée)"
    )
    
    if not selected_structure:
        return None
    
    result = {
        'selected_structure': selected_structure,
        'calculated_morphology': None,
        'explanation': None
    }
    
    # Calculer la morphologie si demandé
    if auto_add_morphology and concept_info.get('requires_morphology_inversion'):
        resolution = resolver.resolve_morphology(concept_name, selected_structure)
        
        result['calculated_morphology'] = resolution['morphology']
        result['explanation'] = resolution['explanation']
        
        # Afficher la morphologie calculée (sans expander imbriqué)
        if resolution['morphology']:
            st.success(f"⚡ **Morphologie calculée:** {resolution['morphology']}")
            st.caption("💡 Explication:")
            st.info(resolution['explanation'])
    
    return result


def get_ventricle_children() -> List[str]:
    """
    Récupère les enfants de "Ventricule" dans la hiérarchie ontologique
    (Branche droite, Branche gauche, etc.)
    EXCLUT les catégories génériques (Ventricule seul)
    
    Returns:
        Liste des structures anatomiques enfants de Ventricule
    """
    ontology_path = Path("data/ontology_from_owl.json")
    
    if not ontology_path.exists():
        return []
    
    try:
        with open(ontology_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Chercher dans concept_hierarchy les enfants de VENTRICULE
        hierarchy = data.get('concept_hierarchy', {})
        concept_mappings = data.get('concept_mappings', {})
        
        ventricle_children = []
        
        # Trouver tous les concepts dont le parent est VENTRICULE
        for child_id, parent_id in hierarchy.items():
            if parent_id == 'VENTRICULE':
                # Récupérer le nom français
                child_data = concept_mappings.get(child_id, {})
                child_name = child_data.get('concept_name')
                # Accepter TOUTES les structures (même sans latéralité)
                if child_name and child_name.lower() != 'ventricule':
                    ventricle_children.append(child_name)
        
        # Si rien trouvé, retourner liste par défaut (toutes les structures)
        if not ventricle_children:
            return ['Branche droite', 'Branche gauche', 'Muscle papillaire', 'Bandelette modératrice', 'Réseau de purkinje']
        
        return sorted(ventricle_children)
        
    except Exception as e:
        # Fallback avec toutes les structures
        return ['Branche droite', 'Branche gauche', 'Muscle papillaire', 'Bandelette modératrice', 'Réseau de purkinje']


def demo_structure_selector():
    """Interface de démonstration"""
    st.title("🏗️ Sélecteur de Structure Anatomique")
    
    st.markdown("""
    Interface identique au territoire_selector, mais pour les structures anatomiques.
    Utilisé pour les concepts comme **Échappement ventriculaire**.
    """)
    
    st.divider()
    
    # Test avec échappement
    st.markdown("### Test: Échappement ventriculaire")
    
    result = structure_selector_interface(
        concept_name="Echappement ventriculaire",
        key_prefix="demo",
        auto_add_morphology=True
    )
    
    if result:
        st.divider()
        st.markdown("### 📋 Résultat")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Structure sélectionnée", result['selected_structure'])
        
        with col2:
            if result['calculated_morphology']:
                st.metric("Morphologie calculée", result['calculated_morphology'])
        
        # Annotation complète
        st.info(f"""
        **Annotations à ajouter:**
        1. Échappement ventriculaire
        2. {result['calculated_morphology']}
        """)
        
        with st.expander("🔍 Données JSON"):
            st.json(result)


if __name__ == "__main__":
    demo_structure_selector()
