#!/usr/bin/env python3
"""
Liseuse ECG Simple - Visualiseur avec annotation semi-automatique intégrée
Affichage ECG avec mode plein écran et système d'annotation ontologique
"""

import streamlit as st
import json
import os
from pathlib import Path
from PIL import Image
import pandas as pd
from datetime import datetime
import sys
import re

# Ajout des chemins pour l'annotation semi-automatique
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend"))

try:
    from correction_engine import OntologyCorrector
    from annotation_components import smart_annotation_input, display_annotation_summary
    ANNOTATION_AVAILABLE = True
except ImportError:
    ANNOTATION_AVAILABLE = False

def clean_case_id(case_id):
    """Nettoie case_id pour Streamlit session state (caractères alphanumériques + underscore seulement)"""
    # Remplace tous les caractères non-alphanumériques par des underscores
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', case_id)
    # Élimine les underscores multiples consécutifs
    cleaned = re.sub(r'_+', '_', cleaned)
    # Supprime les underscores au début et à la fin
    cleaned = cleaned.strip('_')
    return cleaned if cleaned else 'default_case'

def afficher_ecg_plein_ecran(image, case_id):
    """Mode plein écran ECG - Version simple et efficace"""
    
    # Nettoyage du case_id pour les clés Streamlit
    clean_id = clean_case_id(case_id)
    
    st.markdown("### 🖼️ Mode Plein Écran")
    
    # Contrôles simples
    col1, col2, col3 = st.columns([2, 2, 1])
    
    # Gérer le reset avec une variable temporaire
    reset_key = f"reset_zoom_{clean_id}"
    should_reset = st.session_state.get(reset_key, False)
    
    with col1:
        # Valeur par défaut du zoom, réinitialisée si reset demandé
        default_zoom = 100 if should_reset else 100
        zoom_level = st.slider("🔍 Zoom", 50, 300, default_zoom, 25, key=f"zoom_{clean_id}")
    
    with col2:
        if st.button("🔄 Reset Zoom", key=f"reset_{clean_id}"):
            # Marquer qu'un reset est demandé et recharger
            st.session_state[reset_key] = True
            st.rerun()
    
    with col3:
        if st.button("❌ Fermer", key=f"exit_fs_{clean_id}", type="primary"):
            fullscreen_key = f"fullscreen_{clean_id}"
            st.session_state[fullscreen_key] = False
            st.rerun()
    
    # Nettoyer le flag de reset après utilisation
    if should_reset:
        st.session_state[reset_key] = False
    
    # Calcul de la largeur pour le zoom
    width = int(800 * zoom_level / 100)
    
    # Affichage simple de l'image avec zoom
    st.image(
        image, 
        width=width,
        caption=f"ECG - {case_id} (Zoom: {zoom_level}%)",
        use_container_width=False
    )
    
    # Instructions simples
    st.info("💡 **Instructions :** Utilisez le slider pour zoomer, cliquez droit sur l'image pour l'ouvrir dans un nouvel onglet en vraie taille.")

def afficher_ecg_image(file_path):
    """Affichage d'une image ECG avec contrôles simples"""
    
    try:
        # Extraire le case_id du chemin de fichier
        case_id = Path(file_path).parent.name
        clean_id = clean_case_id(case_id)
        
        # Charger l'image
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(file_path)
            
            # Clé pour le mode plein écran
            fullscreen_key = f"fullscreen_{clean_id}"
            
            # Vérifier si on est en mode plein écran
            if st.session_state.get(fullscreen_key, False):
                afficher_ecg_plein_ecran(image, case_id)
                return
            
            # Affichage normal avec contrôles
            st.markdown("#### 🖼️ Visualisation ECG")
            
            # Contrôles principaux
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            with col1:
                st.markdown("**🖼️ Affichage**")
                if st.button("🖼️ Mode Plein Écran", key=f"btn_fullscreen_{clean_id}", type="primary", use_container_width=True):
                    st.session_state[fullscreen_key] = True
                    st.rerun()
            
            with col2:
                st.markdown("**🔍 Zoom**")
                zoom = st.slider(
                    "Niveau de zoom", 
                    100, 200, 100, 
                    step=10,
                    key=f"zoom_{clean_id}",
                    help="Ajustez le zoom de l'ECG (100% à 200%)"
                )
            
            with col3:
                st.markdown("**📏 Informations**")
                st.metric("Largeur", f"{image.size[0]}px")
                st.metric("Hauteur", f"{image.size[1]}px")
            
            with col4:
                st.markdown("**⚙️ Paramètres**")
                st.write(f"**Mode couleur :** {image.mode}")
                if zoom != 100:
                    calculated_width = int(800 * zoom / 100)
                    st.write(f"**Largeur zoom :** {calculated_width}px")
            
            # Affichage de l'image avec zoom
            width = int(800 * zoom / 100)
            st.image(image, width=width, caption=f"ECG - {case_id}", use_container_width=False)
            
        else:
            st.warning(f"⚠️ Format non supporté : {Path(file_path).suffix}")
            
    except Exception as e:
        st.error(f"❌ Erreur affichage ECG : {e}")

def interface_annotation_semi_automatique(case_id):
    """Interface d'annotation semi-automatique intégrée à la liseuse"""
    
    st.markdown("### 🧠 Annotation Semi-Automatique")
    
    if not ANNOTATION_AVAILABLE:
        st.error("❌ Système d'annotation non disponible")
        return
    
    # Chargement de l'ontologie si nécessaire
    if 'corrector' not in st.session_state:
        try:
            ontology_path = project_root / "data" / "ontologie.owx"
            st.session_state.corrector = OntologyCorrector(str(ontology_path))
            st.session_state.concepts = list(st.session_state.corrector.concepts.keys())
        except Exception as e:
            st.error(f"❌ Erreur chargement ontologie : {e}")
            return
    
    # Onglets pour organiser l'interface
    tab1, tab2 = st.tabs(["✏️ Nouvelle Annotation", "📋 Annotations Existantes"])
    
    with tab1:
        # Interface de saisie semi-automatique
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 🏷️ Annotations ECG")
            
            # Utiliser le système d'annotation semi-automatique
            selected_annotations = smart_annotation_input(
                key_prefix=f"annotations_{case_id}",
                max_tags=15
            )
            
            # Zone de contexte clinique
            context_clinique = st.text_area(
                "💭 Contexte clinique",
                height=100,
                key=f"context_{case_id}",
                placeholder="Patient, âge, antécédents, circonstances..."
            )
            
            # Zone d'interprétation experte
            interpretation_experte = st.text_area(
                "🩺 Interprétation experte",
                height=120,
                key=f"interpretation_{case_id}",
                placeholder="Votre diagnostic et commentaires détaillés..."
            )
        
        with col2:
            st.markdown("#### 📊 Résumé")
            
            # Affichage du résumé des annotations
            if selected_annotations:
                display_annotation_summary(selected_annotations, "📊 Résumé")
            else:
                st.info("Aucune annotation sélectionnée")
            
            # Bouton de sauvegarde
            if st.button("💾 Sauvegarder Annotation", type="primary", use_container_width=True):
                sauvegarder_annotation_experte(
                    case_id, 
                    selected_annotations, 
                    context_clinique, 
                    interpretation_experte
                )
    
    with tab2:
        # Affichage des annotations existantes
        afficher_annotations_existantes(case_id)

def afficher_annotations_existantes(case_id):
    """Affiche les annotations existantes pour un cas"""
    
    case_folder = Path("data/ecg_cases") / case_id
    annotations_file = case_folder / "annotations.json"
    
    if not annotations_file.exists():
        st.info("📭 Aucune annotation existante pour ce cas")
        return
    
    try:
        with open(annotations_file, 'r', encoding='utf-8') as f:
            annotations = json.load(f)
        
        if not annotations:
            st.info("📭 Aucune annotation trouvée")
            return
        
        st.markdown(f"#### 📋 {len(annotations)} annotation(s) existante(s)")
        
        for i, ann in enumerate(annotations):
            with st.expander(f"Annotation {i+1} - {ann.get('timestamp', 'Date inconnue')[:10]}", expanded=(i == 0)):
                
                # Informations générales
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type :** {ann.get('type', 'Non spécifié')}")
                    st.write(f"**Auteur :** {ann.get('auteur', 'Non spécifié')}")
                
                with col2:
                    st.write(f"**Date :** {ann.get('timestamp', 'Non spécifiée')[:19]}")
                    if 'nombre_concepts' in ann:
                        st.write(f"**Concepts :** {ann['nombre_concepts']}")
                
                # Annotations tags (semi-automatiques)
                if 'annotation_tags' in ann and ann['annotation_tags']:
                    st.markdown("**🏷️ Concepts ontologiques :**")
                    for tag in ann['annotation_tags']:
                        st.markdown(f"- 🧠 {tag}")
                
                # Contexte clinique
                if ann.get('contexte_clinique'):
                    st.markdown("**💭 Contexte clinique :**")
                    st.info(ann['contexte_clinique'])
                
                # Interprétation experte
                if ann.get('interpretation_experte'):
                    st.markdown("**🩺 Interprétation experte :**")
                    st.success(ann['interpretation_experte'])
                
                # Annotation textuelle (ancien format)
                if ann.get('interpretation') and not ann.get('interpretation_experte'):
                    st.markdown("**📝 Annotation :**")
                    st.write(ann['interpretation'])
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des annotations : {e}")

def sauvegarder_annotation_experte(case_id, annotations, context_clinique, interpretation_experte):
    """Sauvegarde l'annotation experte d'un cas ECG"""
    
    try:
        # Chemin du cas ECG
        case_folder = Path("data/ecg_cases") / case_id
        if not case_folder.exists():
            st.error(f"❌ Cas '{case_id}' non trouvé")
            return
        
        # Préparer les données d'annotation
        annotation_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "expert_semi_auto",
            "auteur": "expert",
            "annotation_tags": annotations,
            "contexte_clinique": context_clinique,
            "interpretation_experte": interpretation_experte,
            "nombre_concepts": len(annotations)
        }
        
        # Charger les annotations existantes
        annotations_file = case_folder / "annotations.json"
        if annotations_file.exists():
            with open(annotations_file, 'r', encoding='utf-8') as f:
                existing_annotations = json.load(f)
        else:
            existing_annotations = []
        
        # Ajouter la nouvelle annotation
        existing_annotations.append(annotation_data)
        
        # Sauvegarder
        with open(annotations_file, 'w', encoding='utf-8') as f:
            json.dump(existing_annotations, f, indent=2, ensure_ascii=False)
        
        # Mettre à jour aussi les métadonnées
        metadata_file = case_folder / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Ajouter les annotations dans les métadonnées pour compatibilité
            if 'annotations' not in metadata:
                metadata['annotations'] = []
            
            metadata['annotations'].append(annotation_data)
            metadata['last_annotation'] = datetime.now().isoformat()
            metadata['annotation_status'] = 'expert_annotated'
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Annotation sauvegardée pour le cas '{case_id}'!")
        st.info(f"📊 {len(annotations)} concepts ontologiques enregistrés")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")

def liseuse_ecg_simple():
    """Interface principale de la liseuse ECG avec annotation semi-automatique"""
    
    st.header("📺 Liseuse ECG - Visualisation & Annotation")
    st.markdown("*Visualisez et annotez les ECG avec l'aide de l'ontologie médicale*")
    
    # Répertoire des cas ECG
    cases_dir = Path("data/ecg_cases")
    
    if not cases_dir.exists():
        st.error("📁 Répertoire des cas ECG introuvable")
        return
    
    # Lister les cas disponibles
    cases = [d.name for d in cases_dir.iterdir() if d.is_dir()]
    
    if not cases:
        st.info("📭 Aucun cas ECG disponible")
        return
    
    st.markdown("### 📚 Sélection du cas ECG")
    
    # Sélecteur de cas
    selected_case = st.selectbox(
        "Choisissez un cas ECG",
        cases,
        help="Sélectionnez le cas ECG à visualiser"
    )
    
    if selected_case:
        case_folder = cases_dir / selected_case
        
        # Chercher les fichiers ECG
        ecg_files = []
        for ext in ['.png', '.jpg', '.jpeg']:
            ecg_files.extend(case_folder.glob(f"*{ext}"))
        
        if ecg_files:
            # Prendre le premier fichier ECG trouvé
            ecg_file = ecg_files[0]
            
            # Afficher l'ECG
            afficher_ecg_image(str(ecg_file))
            
            st.markdown("---")
            
            # Interface d'annotation semi-automatique intégrée
            interface_annotation_semi_automatique(selected_case)
            
        else:
            st.warning(f"⚠️ Aucun fichier ECG trouvé dans le cas '{selected_case}'")

if __name__ == "__main__":
    # Configuration de la page
    st.set_page_config(
        page_title="📚 Liseuse ECG Simple",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Liseuse ECG Simple")
    liseuse_ecg_simple()
