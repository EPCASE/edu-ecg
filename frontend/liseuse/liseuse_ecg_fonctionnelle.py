#!/usr/bin/env python3
"""
Liseuse ECG Multi-ECG - Affichage intelligent avec navigation entre ECG
Gère les cas simples et multi-ECG avec défilement
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

def liseuse_ecg_fonctionnelle():
    """Interface principale de la liseuse ECG avec support multi-ECG"""
    
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
    """Charge tous les cas ECG (simples et multi-ECG)"""
    
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
    """Charge les données d'un cas (simple ou multi-ECG)"""
    
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
    
    # Grouper par type
    cas_simples = [cas for cas in cas_ecg if cas.get('type') != 'multi_ecg']
    cas_multi = [cas for cas in cas_ecg if cas.get('type') == 'multi_ecg']
    
    # Statistiques
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📄 Cas simples", len(cas_simples))
    with col2:
        st.metric("📁 Cas multi", len(cas_multi))
    
    # Options de filtrage
    type_filtre = st.selectbox(
        "Filtrer par type",
        ["Tous", "Cas simples", "Cas multi-ECG"],
        key="filtre_type_cas"
    )
    
    # Filtrer les cas
    if type_filtre == "Cas simples":
        cas_filtres = cas_simples
    elif type_filtre == "Cas multi-ECG":
        cas_filtres = cas_multi
    else:
        cas_filtres = cas_ecg
    
    if not cas_filtres:
        st.warning("⚠️ Aucun cas correspond au filtre")
        return None
    
    # Sélection du cas
    options_cas = []
    for cas in cas_filtres:
        name = cas.get('name', cas.get('case_id', 'Cas sans nom'))
        
        if cas.get('type') == 'multi_ecg':
            nb_ecg = len(cas.get('ecgs', []))
            label = f"📁 {name} ({nb_ecg} ECG)"
        else:
            label = f"📄 {name}"
        
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
    cas_selectionne = cas_filtres[index_cas]
    
    # Afficher les infos du cas
    afficher_info_cas_multi(cas_selectionne)
    
    return cas_selectionne

def interface_navigation_ecg(cas):
    """Interface de navigation pour les cas multi-ECG"""
    
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
    
    # Type
    type_cas = cas.get('type', 'simple')
    if type_cas == 'multi_ecg':
        nb_ecg = len(cas.get('ecgs', []))
        st.write(f"**Type:** Multi-ECG ({nb_ecg} ECG)")
    else:
        st.write(f"**Type:** Cas simple")
    
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
    """Affiche une image ECG avec contrôles de zoom et grille"""
    
    try:
        image = Image.open(file_path)
        
        # Contrôles d'affichage
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            zoom_level = st.selectbox(
                "🔍 Zoom",
                ["Ajusté", "50%", "75%", "100%", "125%", "150%", "200%"],
                index=0,
                key=f"zoom_{titre}"
            )
        
        with col3:
            show_grid = st.checkbox(
                "📐 Grille",
                value=False,
                key=f"grid_{titre}",
                help="Afficher la grille millimétrique"
            )
        
        # Affichage de l'image
        with col1:
            st.markdown(f"**{titre}**")
        
        # Mode plein écran
        if st.button("🖼️ Mode Plein Écran", key=f"fullscreen_{titre}"):
            afficher_mode_plein_ecran(image, titre)
        
        # Affichage principal
        if zoom_level == "Ajusté":
            st.image(image, caption=titre, use_container_width=True)
        else:
            zoom_factor = int(zoom_level.replace('%', '')) / 100
            width = int(image.width * zoom_factor)
            st.image(image, caption=titre, width=width)
        
        # Grille ECG
        if show_grid:
            st.markdown("""
            <div style="opacity: 0.7; margin-top: -10px; font-size: 0.8em;">
            📐 Grille millimétrique: 25mm/s horizontalement, 10mm/mV verticalement
            </div>
            """, unsafe_allow_html=True)
        
        # Informations image
        with st.expander("📊 Détails image"):
            st.write(f"**Dimensions:** {image.width} × {image.height} pixels")
            st.write(f"**Mode:** {image.mode}")
            file_size = os.path.getsize(file_path) // 1024
            st.write(f"**Taille:** {file_size} KB")
        
    except Exception as e:
        st.error(f"❌ Erreur affichage image: {e}")

def afficher_mode_plein_ecran(image, titre):
    """Affiche l'ECG en mode plein écran"""
    
    st.markdown("### 🖼️ Mode Plein Écran")
    
    # Convertir en base64 pour affichage HTML
    import base64
    from io import BytesIO
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # HTML plein écran
    html_fullscreen = f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: black;
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
    " onclick="this.style.display='none'">
        <img src="data:image/png;base64,{img_base64}" 
             style="max-width: 95%; max-height: 95%; object-fit: contain;" 
             alt="{titre}">
        <div style="
            position: absolute;
            top: 20px;
            right: 20px;
            color: white;
            font-size: 24px;
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
        ">
            ✕ Cliquez pour fermer
        </div>
    </div>
    """
    
    st.components.v1.html(html_fullscreen, height=600)

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
    """Interface d'annotation pour cas simple et multi-ECG"""
    
    st.markdown("### 📝 Annotation")
    
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
    
    # Interface d'annotation simple
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