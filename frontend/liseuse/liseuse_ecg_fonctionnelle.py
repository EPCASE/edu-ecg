#!/usr/bin/env python3
"""
Liseuse ECG - Affichage intelligent avec navigation entre ECG
Gère tous les cas ECG de manière uniforme
Version intégrée dans le système principal
"""

import streamlit as st
import json
import os
from pathlib import Path
from PIL import Image
import pandas as pd
from datetime import datetime
import sys

# Import du nouveau visualiseur avancé
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from advanced_ecg_viewer import enhanced_ecg_display, advanced_ecg_viewer_component
    from annotation_components import smart_annotation_input, display_annotation_summary
    ADVANCED_VIEWER_AVAILABLE = True
    ANNOTATION_AVAILABLE = True
except ImportError:
    ADVANCED_VIEWER_AVAILABLE = False
    ANNOTATION_AVAILABLE = False

def liseuse_ecg_fonctionnelle():
    """Interface principale de la liseuse ECG"""
    
    st.title("📚 Liseuse ECG")
    
    # Chargement des cas ECG
    cas_ecg = charger_cas_ecg_multi()
    
    if not cas_ecg:
        afficher_aucun_cas()
        return
    
    # Interface principale
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Sélection du cas
        cas_selectionne = interface_selection_cas(cas_ecg)
        
        # Navigation ECG si multi-ECG
        if cas_selectionne and cas_selectionne.get('type') == 'multi_ecg':
            ecg_selectionne = interface_navigation_ecg(cas_selectionne)
        else:
            ecg_selectionne = None
    
    with col1:
        # Affichage principal
        if cas_selectionne:
            afficher_ecg_avec_navigation(cas_selectionne, ecg_selectionne)
        else:
            st.info("📝 Sélectionnez un cas pour commencer")
    
    # Interface d'annotation
    if cas_selectionne:
        st.markdown("---")
        interface_annotation_multi(cas_selectionne, ecg_selectionne)

def charger_cas_ecg_multi():
    """Charge tous les cas ECG disponibles"""
    
    cas_ecg = []
    ecg_dir = Path("data/ecg_cases")
    
    if not ecg_dir.exists():
        return cas_ecg
    
    # Parcourir tous les dossiers de cas
    for case_folder in ecg_dir.iterdir():
        if case_folder.is_dir():
            cas_data = charger_cas_individuel_multi(case_folder)
            if cas_data:
                cas_ecg.append(cas_data)
    
    # Trier par date de création (plus récent en premier)
    cas_ecg.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    
    return cas_ecg

def charger_cas_individuel_multi(case_folder):
    """Charge les données d'un cas ECG"""
    
    try:
        # Lire les métadonnées
        metadata_path = case_folder / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Cas multi-ECG avec métadonnées structurées
            if metadata.get('type') == 'multi_ecg':
                # Vérifier que les fichiers ECG existent
                ecgs_valides = []
                for ecg_meta in metadata.get('ecgs', []):
                    ecg_path = case_folder / ecg_meta['filename']
                    if ecg_path.exists():
                        ecg_meta['file_path'] = str(ecg_path)
                        ecgs_valides.append(ecg_meta)
                
                if ecgs_valides:
                    metadata['ecgs'] = ecgs_valides
                    metadata['folder_path'] = str(case_folder)
                    return metadata
            
            # Cas simple avec métadonnées
            else:
                # Chercher le fichier principal
                fichier_principal = trouver_fichier_principal(case_folder)
                if fichier_principal:
                    metadata['file_path'] = str(fichier_principal['path'])
                    metadata['file_type'] = fichier_principal['type']
                    metadata['folder_path'] = str(case_folder)
                    metadata['type'] = 'simple'
                    return metadata
        
        else:
            # Pas de métadonnées - cas simple legacy
            fichier_principal = trouver_fichier_principal(case_folder)
            if fichier_principal:
                # Déterminer si c'est multi-ECG
                images = list(case_folder.glob("*.png")) + list(case_folder.glob("*.jpg"))
                
                if len(images) > 1:
                    # Multi-ECG sans métadonnées - créer structure
                    metadata = {
                        'case_id': case_folder.name,
                        'name': f"Cas {case_folder.name}",
                        'type': 'multi_ecg',
                        'description': 'Cas multi-ECG importé automatiquement',
                        'created_date': datetime.now().isoformat(),
                        'folder_path': str(case_folder),
                        'ecgs': []
                    }
                    
                    for i, img_path in enumerate(images):
                        ecg_meta = {
                            'filename': img_path.name,
                            'label': f"ECG_{i+1}",
                            'timing': "Non défini",
                            'file_path': str(img_path)
                        }
                        metadata['ecgs'].append(ecg_meta)
                    
                    return metadata
                
                else:
                    # Cas simple legacy
                    metadata = {
                        'case_id': case_folder.name,
                        'name': f"Cas {case_folder.name}",
                        'type': 'simple',
                        'created_date': datetime.now().isoformat(),
                        'file_path': str(fichier_principal['path']),
                        'file_type': fichier_principal['type'],
                        'folder_path': str(case_folder)
                    }
                    return metadata
        
        return None
        
    except Exception as e:
        st.error(f"Erreur chargement cas {case_folder.name}: {e}")
        return None

def trouver_fichier_principal(case_folder):
    """Trouve le fichier principal d'un cas"""
    
    # Priorité aux images
    for ext in ['.png', '.jpg', '.jpeg']:
        image_files = list(case_folder.glob(f"*{ext}"))
        if image_files:
            return {'path': image_files[0], 'type': 'image'}
    
    # Sinon chercher XML
    xml_files = list(case_folder.glob("*.xml"))
    if xml_files:
        return {'path': xml_files[0], 'type': 'xml'}
    
    # Sinon chercher PDF
    pdf_files = list(case_folder.glob("*.pdf"))
    if pdf_files:
        return {'path': pdf_files[0], 'type': 'pdf'}
    
    return None

def interface_selection_cas(cas_ecg):
    """Interface de sélection des cas"""
    
    st.markdown("#### 📊 Sélection du Cas")
    
    if not cas_ecg:
        st.warning("⚠️ Aucun cas ECG disponible")
        return None
    
    # Sélection du cas - affichage unifié
    options_cas = []
    for cas in cas_ecg:
        name = cas.get('name', cas.get('case_id', 'Cas sans nom'))
        
        # Affichage unifié - pas de différence visuelle entre types
        if cas.get('type') == 'multi_ecg':
            nb_ecg = len(cas.get('ecgs', []))
            label = f"� {name} ({nb_ecg} ECG)"
        else:
            label = f"� {name}"
        
        options_cas.append(label)
    
    if 'cas_selection_index' not in st.session_state:
        st.session_state.cas_selection_index = 0
    
    selection = st.selectbox(
        "Choisir un cas",
        options_cas,
        index=st.session_state.cas_selection_index,
        key="cas_selectbox"
    )
    
    # Récupérer le cas sélectionné
    index_cas = options_cas.index(selection)
    cas_selectionne = cas_ecg[index_cas]
    
    # Afficher les infos du cas
    afficher_info_cas_multi(cas_selectionne)
    
    return cas_selectionne

def interface_navigation_ecg(cas):
    """Interface de navigation pour les cas avec plusieurs ECG"""
    
    if cas.get('type') != 'multi_ecg':
        return None
    
    ecgs = cas.get('ecgs', [])
    if not ecgs:
        return None
    
    st.markdown("#### 🔄 Navigation ECG")
    
    # Informations rapides
    st.info(f"📊 **{len(ecgs)} ECG** dans ce cas")
    
    # Navigation par index
    if 'ecg_index' not in st.session_state:
        st.session_state.ecg_index = 0
    
    # Vérifier que l'index est valide
    if st.session_state.ecg_index >= len(ecgs):
        st.session_state.ecg_index = 0
    
    # Boutons de navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Précédent", disabled=(st.session_state.ecg_index == 0)):
            st.session_state.ecg_index -= 1
            st.rerun()
    
    with col3:
        if st.button("➡️ Suivant", disabled=(st.session_state.ecg_index == len(ecgs) - 1)):
            st.session_state.ecg_index += 1
            st.rerun()
    
    with col2:
        # Sélection directe
        ecg_labels = [f"{i+1}. {ecg['label']}" for i, ecg in enumerate(ecgs)]
        selection = st.selectbox(
            "ECG actuel",
            ecg_labels,
            index=st.session_state.ecg_index,
            key="ecg_selection"
        )
        
        # Mettre à jour l'index si changement
        new_index = ecg_labels.index(selection)
        if new_index != st.session_state.ecg_index:
            st.session_state.ecg_index = new_index
            st.rerun()
    
    # ECG actuel
    ecg_actuel = ecgs[st.session_state.ecg_index]
    
    # Informations de l'ECG actuel
    st.markdown("##### 📄 ECG Actuel")
    st.write(f"**Label:** {ecg_actuel['label']}")
    st.write(f"**Timing:** {ecg_actuel.get('timing', 'Non défini')}")
    if ecg_actuel.get('notes'):
        st.write(f"**Notes:** {ecg_actuel['notes']}")
    
    # Barre de progression
    progress = (st.session_state.ecg_index + 1) / len(ecgs)
    st.progress(progress, text=f"ECG {st.session_state.ecg_index + 1} sur {len(ecgs)}")
    
    return ecg_actuel

def afficher_info_cas_multi(cas):
    """Affiche les informations d'un cas (simple ou multi)"""
    
    st.markdown("#### 📋 Informations")
    
    # Nom et ID
    name = cas.get('name', cas.get('case_id', 'Sans nom'))
    st.write(f"**Nom:** {name}")
    st.write(f"**ID:** {cas.get('case_id', 'Non défini')}")
    
    # Type - affichage unifié
    type_cas = cas.get('type', 'simple')
    if type_cas == 'multi_ecg':
        nb_ecg = len(cas.get('ecgs', []))
        st.write(f"**Contenu:** {nb_ecg} ECG")
    else:
        st.write(f"**Contenu:** 1 ECG")
    
    # Date
    date_str = cas.get('created_date', '')
    if date_str:
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            date_formatted = date_obj.strftime("%d/%m/%Y %H:%M")
            st.write(f"**Date:** {date_formatted}")
        except:
            st.write(f"**Date:** {date_str[:10]}")
    
    # Description
    if cas.get('description'):
        st.write(f"**Description:** {cas['description']}")
    
    # Catégorie et difficulté (pour les cas multi)
    if cas.get('category'):
        st.write(f"**Catégorie:** {cas['category']}")
    if cas.get('difficulty'):
        st.write(f"**Niveau:** {cas['difficulty']}")

def afficher_ecg_avec_navigation(cas, ecg_selectionne=None):
    """Affiche l'ECG avec support simple et multi-ECG"""
    
    st.markdown("#### 🫀 Visualisation ECG")
    
    try:
        if cas.get('type') == 'multi_ecg':
            # Cas multi-ECG
            if ecg_selectionne:
                file_path = ecg_selectionne.get('file_path')
                if file_path and os.path.exists(file_path):
                    afficher_ecg_image_avec_controles(file_path, ecg_selectionne['label'])
                else:
                    st.error(f"❌ Fichier ECG introuvable: {file_path}")
            else:
                st.info("📝 Sélectionnez un ECG dans la navigation")
        
        else:
            # Cas simple
            file_path = cas.get('file_path')
            file_type = cas.get('file_type', 'image')
            
            if file_path and os.path.exists(file_path):
                if file_type == 'image':
                    case_name = cas.get('name', cas.get('case_id', 'ECG'))
                    afficher_ecg_image_avec_controles(file_path, case_name)
                elif file_type == 'xml':
                    afficher_ecg_xml(file_path)
                elif file_type == 'pdf':
                    afficher_ecg_pdf(file_path)
                else:
                    st.warning(f"⚠️ Type non supporté: {file_type}")
            else:
                st.error(f"❌ Fichier introuvable: {file_path}")
    
    except Exception as e:
        st.error(f"❌ Erreur affichage: {e}")

def afficher_ecg_image_avec_controles(file_path, titre):
    """Affiche une image ECG avec contrôles avancés et colonne d'interprétation"""
    
    try:
        image = Image.open(file_path)
        
        # Sélecteurs de visualisation
        if ADVANCED_VIEWER_AVAILABLE:
            view_mode = st.radio(
                "Mode d'affichage",
                ["📋 Affichage Standard", "🎨 Visualiseur Avancé"],
                horizontal=True,
                key=f"view_mode_{titre}",
                help="Choisir le mode d'affichage de l'ECG",
                label_visibility="collapsed"
            )
        else:
            view_mode = "📋 Affichage Standard"
            st.info("💡 Visualiseur avancé non disponible - mode standard")
        
        # Affichage selon le mode choisi
        if ADVANCED_VIEWER_AVAILABLE and view_mode == "🎨 Visualiseur Avancé":
            st.markdown(f"### 🔍 {titre}")
            
            # Visualiseur avancé avec dimensions augmentées de 15%
            # Le conteneur s'adapte strictement aux dimensions de l'ECG et occupe l'espace au maximum + 15%
            img_width, img_height = image.size
            aspect_ratio = img_height / img_width
            
            # Calculer la largeur de base puis ajouter 15%
            base_width = 1000  # Largeur de base du visualiseur
            enhanced_width = int(base_width * 1.15)  # +15%
            
            # Calculer la hauteur correspondante avec le même ratio
            enhanced_height = int(enhanced_width * aspect_ratio)
            
            print(f"📐 Dimensions augmentées +15%: {enhanced_width}x{enhanced_height}px (base: {base_width}px)")
            
            advanced_ecg_viewer_component(
                file_path, 
                titre, 
                height=enhanced_height + 60,  # +60 pour toolbar et marges
                container_width=enhanced_width
            )
            
            # Guide des contrôles
            with st.expander("🎮 Guide des contrôles avancés", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **🖱️ Navigation :**
                    - **Clic + Glisser** : Déplacer l'image
                    - **Molette souris** : Zoom in/out
                    - **Slider zoom** : Contrôle précis (0.25x - 5x)
                    - **🔄 Reset** : Retour vue initiale
                    """)
                
                with col2:
                    st.markdown("""
                    **🔧 Outils ECG :**
                    - **📏 Mesure** : Cliquer-glisser pour mesurer
                    - **⛶ Plein écran** : Mode immersif
                    - **Info panel** : Position et zoom temps réel
                    """)
        
        else:
            # Mode standard - Affichage simple sans contrôles de zoom
            st.image(image, use_container_width=True)
        
        # Module d'annotation rapide avec ontologie
        if ANNOTATION_AVAILABLE:
            st.markdown("---")
            st.markdown("### 🏷️ Annotation rapide")
            
            try:
                # Interface d'annotation compacte
                with st.expander("📝 Annoter cet ECG", expanded=False):
                    annotations = smart_annotation_input(
                        key_prefix=f"quick_annotation_{titre.replace(' ', '_')}",
                        max_tags=10
                    )
                    
                    if annotations:
                        st.markdown("**🎯 Résumé rapide :**")
                        display_annotation_summary(annotations)
                        
            except Exception as e:
                st.info("💡 Module d'annotation ontologique en cours de chargement...")
        
    except Exception as e:
        st.error(f"❌ Erreur affichage image: {e}")

def afficher_ecg_xml(file_path):
    """Affiche un fichier ECG XML"""
    
    st.info("📋 Fichier XML détecté")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with st.expander("📄 Contenu XML"):
            st.code(content[:1000] + "..." if len(content) > 1000 else content, language='xml')
        
        st.info("💡 L'affichage des tracés XML nécessite un module spécialisé")
        
    except Exception as e:
        st.error(f"❌ Erreur lecture XML: {e}")

def afficher_ecg_pdf(file_path):
    """Affiche un fichier ECG PDF"""
    
    st.info("📄 Fichier PDF détecté")
    
    try:
        with open(file_path, "rb") as file:
            pdf_data = file.read()
        
        import base64
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Viewer PDF simple
        html_viewer = f"""
        <iframe 
            src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}"
            width="100%" 
            height="600px"
            style="border: none;">
        </iframe>
        """
        
        st.components.v1.html(html_viewer, height=620)
        
    except Exception as e:
        st.error(f"❌ Erreur affichage PDF: {e}")

def interface_annotation_multi(cas, ecg_selectionne):
    """Interface d'annotation pour cas simple et multi-ECG avec ontologie"""
    
    st.markdown("### 📝 Annotation selon l'ontologie")
    
    # Déterminer l'ECG à annoter
    if cas.get('type') == 'multi_ecg':
        if not ecg_selectionne:
            st.info("📝 Sélectionnez un ECG pour l'annoter")
            return
        
        ecg_id = ecg_selectionne.get('label', 'ECG')
        st.write(f"**Annotation de:** {ecg_id}")
    else:
        ecg_id = "ECG_principal"
        st.write(f"**Annotation du cas:** {cas.get('name', 'ECG')}")
    
    # Interface d'annotation intelligente avec ontologie
    if ANNOTATION_AVAILABLE:
        try:
            # Module d'annotation semi-automatique
            annotations = smart_annotation_input(
                key_prefix=f"annotation_{cas['case_id']}_{ecg_id}",
                max_tags=15
            )
            
            # Affichage du résumé des annotations
            if annotations:
                st.markdown("---")
                display_annotation_summary(annotations)
                
                # Zone de notes complémentaires
                st.markdown("#### 📝 Notes complémentaires")
                notes_text = st.text_area(
                    "Observations détaillées",
                    placeholder="Ajoutez des détails ou observations spécifiques...",
                    key=f"notes_{cas['case_id']}_{ecg_id}",
                    height=100
                )
                
                # Sauvegarde des annotations
                if st.button("💾 Sauvegarder les annotations", key=f"save_{cas['case_id']}_{ecg_id}"):
                    annotation_data = {
                        'case_id': cas['case_id'],
                        'ecg_id': ecg_id,
                        'annotations': annotations,
                        'notes': notes_text,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Sauvegarder dans le state
                    if 'saved_annotations' not in st.session_state:
                        st.session_state['saved_annotations'] = {}
                    
                    annotation_key = f"{cas['case_id']}_{ecg_id}"
                    st.session_state['saved_annotations'][annotation_key] = annotation_data
                    
                    st.success("✅ Annotations sauvegardées avec succès!")
            
        except Exception as e:
            st.error(f"❌ Erreur module annotation: {e}")
            # Interface de fallback simple
            annotation_text = st.text_area(
                "💭 Votre interprétation (mode simple)",
                placeholder="Décrivez ce que vous observez sur cet ECG...",
                key=f"annotation_fallback_{cas['case_id']}_{ecg_id}"
            )
    else:
        # Interface d'annotation simple si module non disponible
        annotation_text = st.text_area(
            "💭 Votre interprétation",
            placeholder="Décrivez ce que vous observez sur cet ECG...",
            key=f"annotation_{cas['case_id']}_{ecg_id}"
        )
    
    if st.button("💾 Sauvegarder annotation", key=f"save_annotation_{ecg_id}"):
        sauvegarder_annotation(cas, ecg_id, annotation_text)

def sauvegarder_annotation(cas, ecg_id, annotation):
    """Sauvegarde une annotation"""
    
    if not annotation.strip():
        st.warning("⚠️ Annotation vide")
        return
    
    try:
        # Chemin du fichier d'annotations
        annotations_file = Path(cas['folder_path']) / "annotations_etudiant.json"
        
        # Charger annotations existantes
        if annotations_file.exists():
            with open(annotations_file, 'r', encoding='utf-8') as f:
                annotations = json.load(f)
        else:
            annotations = {
                'case_id': cas['case_id'],
                'annotations': [],
                'created_date': datetime.now().isoformat()
            }
        
        # Ajouter nouvelle annotation
        nouvelle_annotation = {
            'ecg_id': ecg_id,
            'annotation': annotation,
            'date': datetime.now().isoformat(),
            'type': 'etudiant'
        }
        
        annotations['annotations'].append(nouvelle_annotation)
        
        # Sauvegarder
        with open(annotations_file, 'w', encoding='utf-8') as f:
            json.dump(annotations, f, indent=2, ensure_ascii=False)
        
        st.success("✅ Annotation sauvegardée !")
        
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde: {e}")

def afficher_aucun_cas():
    """Affichage quand aucun cas n'est disponible"""
    
    st.info("📭 Aucun cas ECG trouvé")
    
    st.markdown("""
    ### 🎯 Pour commencer :
    
    1. **Utilisez l'Import Intelligent** pour ajouter des ECG
    2. **Ou ajoutez manuellement** des fichiers dans `data/ecg_cases/`
    3. **Revenez ici** pour les visualiser et les annoter
    
    ### 📁 Types de cas supportés :
    - **Cas simples** : Un ECG par cas
    - **Cas multi-ECG** : Plusieurs ECG liés (évolution, comparaison)
    - **Formats** : PNG, JPG, PDF, XML
    """)
    
    if st.button("🎯 Aller à l'Import Intelligent", type="primary"):
        st.switch_page("pages/2_🧠_Import_Intelligent.py")

# Fonction legacy pour compatibilité
def charger_cas_ecg():
    """Fonction legacy - redirige vers la nouvelle version"""
    return charger_cas_ecg_multi()

# Export des fonctions principales pour compatibilité
__all__ = ['liseuse_ecg_fonctionnelle', 'charger_cas_ecg']