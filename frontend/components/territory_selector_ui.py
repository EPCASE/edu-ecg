"""
🎯 Territory Selector UI - Composant Streamlit pour sélection des territoires

Intégration Streamlit pour le territory_resolver
Affiche les sélecteurs multiselect pour territoires et miroirs

Auteur: Grégoire + BMAD
Date: 2026-01-13
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
from backend.territory_resolver import get_territory_config


def render_territory_selectors(
    concept_name: str,
    ontology: Dict,
    key_prefix: str = ""
) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    """
    Affiche les sélecteurs de territoires pour un concept donné
    
    Args:
        concept_name: Nom du concept (ex: "STEMI", "Syndrome coronarien...")
        ontology: Ontologie complète chargée
        key_prefix: Préfixe pour les clés Streamlit (éviter doublons)
        
    Returns:
        Tuple (selected_territories, selected_mirrors) ou (None, None) si pas de sélecteur
    """
    # Récupérer configuration territoire
    config = get_territory_config(concept_name, ontology)
    
    if not config:
        return None, None
    
    # Containers pour l'affichage
    selected_territories = None
    selected_mirrors = None
    
    is_required = config.get('is_required', False)
    
    # Affichage du sélecteur de territoire principal
    if config['show_territory_selector']:
        territories = config['territories']
        
        if territories:
            label = "🗺️ Territoire" + (" (obligatoire)" if is_required else "")
            help_text = f"Sélectionnez un ou plusieurs territoires touchés pour **{config['concept_name']}**"
            
            if is_required:
                help_text += "\n\n⚠️ La sélection d'au moins un territoire est **obligatoire**"
            
            selected_territories = st.multiselect(
                label,
                options=territories,
                help=help_text,
                key=f"{key_prefix}_territory_{concept_name}"
            )
            
            # Warning si required mais pas sélectionné
            if is_required and not selected_territories:
                st.warning(f"⚠️ Le territoire est **obligatoire** pour {config['concept_name']}")
    
    # Affichage du sélecteur de miroir
    if config['show_mirror_selector']:
        mirrors = config['mirrors']
        
        if mirrors:
            help_text = f"Sélectionnez le(s) territoire(s) miroir si observé(s) pour **{config['concept_name']}**"
            
            selected_mirrors = st.multiselect(
                "🪞 Territoire Miroir (optionnel)",
                options=mirrors,
                help=help_text,
                key=f"{key_prefix}_mirror_{concept_name}"
            )
    
    return selected_territories, selected_mirrors


def check_territory_completeness(
    concept_name: str,
    selected_territories: Optional[List[str]],
    ontology: Dict
) -> Tuple[bool, Optional[str]]:
    """
    Vérifie si les territoires requis sont bien sélectionnés
    
    Args:
        concept_name: Nom du concept
        selected_territories: Liste des territoires sélectionnés
        ontology: Ontologie
        
    Returns:
        Tuple (is_complete, error_message)
    """
    config = get_territory_config(concept_name, ontology)
    
    if not config:
        return True, None
    
    # Si territoire requis mais aucun sélectionné
    if config['is_required'] and not selected_territories:
        return False, f"⚠️ Le territoire est obligatoire pour **{config['concept_name']}**"
    
    return True, None


def get_territory_selection_summary(
    concept_name: str,
    selected_territories: Optional[List[str]],
    selected_mirrors: Optional[List[str]]
) -> Optional[str]:
    """
    Génère un résumé textuel de la sélection de territoire
    
    Args:
        concept_name: Nom du concept
        selected_territories: Territoires sélectionnés
        selected_mirrors: Miroirs sélectionnés
        
    Returns:
        Texte de résumé ou None
    """
    if not selected_territories and not selected_mirrors:
        return None
    
    parts = []
    
    if selected_territories:
        terr_str = ", ".join(selected_territories)
        parts.append(f"📍 Territoire: {terr_str}")
    
    if selected_mirrors:
        mirr_str = ", ".join(selected_mirrors)
        parts.append(f"🪞 Miroir: {mirr_str}")
    
    return " | ".join(parts)


def calculate_territory_bonus(
    concept_name: str,
    student_territories: Optional[List[str]],
    student_mirrors: Optional[List[str]],
    expected_territories: Optional[List[str]],
    expected_mirrors: Optional[List[str]],
    ontology: Dict
) -> Tuple[float, str]:
    """
    Calcule le bonus de scoring pour précision du territoire
    
    Args:
        concept_name: Nom du concept
        student_territories: Territoires sélectionnés par l'étudiant
        student_mirrors: Miroirs sélectionnés par l'étudiant
        expected_territories: Territoires attendus
        expected_mirrors: Miroirs attendus
        ontology: Ontologie
        
    Returns:
        Tuple (bonus_percentage, explanation)
        
    Exemple:
        - Territoire exact: +5%
        - Miroir exact: +3%
        - Territoire partiel: +2%
    """
    config = get_territory_config(concept_name, ontology)
    
    if not config:
        return 0.0, ""
    
    bonus = 0.0
    explanations = []
    
    # Bonus territoire principal
    if student_territories and expected_territories:
        # Match exact
        if set(student_territories) == set(expected_territories):
            bonus += 0.05
            explanations.append("✅ Territoire exact (+5%)")
        # Match partiel (au moins 1 commun)
        elif set(student_territories) & set(expected_territories):
            bonus += 0.02
            common = set(student_territories) & set(expected_territories)
            explanations.append(f"⚠️ Territoire partiel ({len(common)}/{len(expected_territories)}) (+2%)")
        else:
            explanations.append("❌ Territoire incorrect (0%)")
    
    # Bonus miroir
    if student_mirrors and expected_mirrors:
        # Match exact
        if set(student_mirrors) == set(expected_mirrors):
            bonus += 0.03
            explanations.append("✅ Miroir exact (+3%)")
        # Match partiel
        elif set(student_mirrors) & set(expected_mirrors):
            bonus += 0.01
            common = set(student_mirrors) & set(expected_mirrors)
            explanations.append(f"⚠️ Miroir partiel ({len(common)}/{len(expected_mirrors)}) (+1%)")
        else:
            explanations.append("❌ Miroir incorrect (0%)")
    
    explanation = " | ".join(explanations)
    
    return bonus, explanation
