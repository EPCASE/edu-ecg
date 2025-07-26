#!/usr/bin/env python3
"""
Liseuse ECG Fonctionnelle - Affichage intelligent des ECG importés
Lit les ECG depuis data/ecg_cases/ et les affiche avec outils d'annotation intelligente
"""

import streamlit as st
import json
import os
from pathlib import Path
from PIL import Image
import pandas as pd
from datetime import datetime
import sys

# Ajout du chemin pour l'annotation intelligente
sys.path.append(str(Path(__file__).parent.parent / "admin"))

try:
    from annotation_intelligente import annotation_intelligente_admin, compare_annotations, load_ontology_concepts
    SMART_ANNOTATION_AVAILABLE = True
except ImportError:
    SMART_ANNOTATION_AVAILABLE = False

def clean_case_id(case_id):
    """Nettoie case_id pour Streamlit session state (caractères alphanumériques + underscore seulement)"""
    import re
    # Remplace tous les caractères non-alphanumériques par des underscores
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', case_id)
    # Élimine les underscores multiples consécutifs
    cleaned = re.sub(r'_+', '_', cleaned)
    # Supprime les underscores au début et à la fin
    cleaned = cleaned.strip('_')
    return cleaned if cleaned else 'default_case'

def image_to_base64(image):
    """Convertit une image PIL en base64"""
    import base64
    from io import BytesIO
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def liseuse_ecg_fonctionnelle():
    """Interface principale de la liseuse ECG"""
    
    # FORCER la navigation sur la liseuse à chaque chargement
    st.session_state.admin_page = "📺 Liseuse ECG"
    
    # Vérifier et corriger toute dérive de navigation
    if hasattr(st.session_state, 'admin_page') and st.session_state.admin_page != "📺 Liseuse ECG":
        st.session_state.admin_page = "📺 Liseuse ECG"
    
    st.title("📚 Liseuse ECG")
    
    # Indicateur de debug pour les contrôles
    with st.expander("🔧 État des Contrôles Interface", expanded=False):
        st.success("✅ Interface de contrôle ECG chargée")
        st.info("👀 Si vous ne voyez pas les contrôles, vérifiez l'affichage de l'ECG ci-dessous")
        st.write("📊 **Version des contrôles :** Mode plein écran + Zoom intégré")
    
    # Chargement des cas ECG
    cas_ecg = charger_cas_ecg()
    
    if not cas_ecg:
        afficher_aucun_cas()
        return
    
    # Sélection du cas avec callback pour préserver la navigation
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("#### 📊 Sélection")
        
        # Liste des cas disponibles
        options_cas = []
        for cas in cas_ecg:
            # Utiliser 'name' ou 'case_id' selon ce qui est disponible
            case_name = cas.get('name') or cas.get('case_id', 'Cas sans nom')
            label = f"📄 {case_name}"
            if 'age' in cas and cas['age']:
                label += f" (âge {cas['age']})"
            options_cas.append(label)
        
        # Utiliser une clé unique pour le selectbox avec callback
        cas_selectionne = st.selectbox(
            "Choisir un cas ECG :",
            options_cas,
            index=0,
            key="liseuse_cas_selection",
            on_change=lambda: setattr(st.session_state, 'admin_page', "📺 Liseuse ECG")
        )
        
        # Récupérer l'index sélectionné
        index_cas = options_cas.index(cas_selectionne)
        cas_actuel = cas_ecg[index_cas]
        
        # Informations du cas
        afficher_info_cas(cas_actuel)
    
    with col1:
        # Affichage de l'ECG
        afficher_ecg_principal(cas_actuel)
    
    # Interface d'annotation (optionnelle)
    st.markdown("---")
    interface_annotation_simple(cas_actuel)

def charger_cas_ecg():
    """Charge tous les cas ECG disponibles"""
    
    cas_ecg = []
    ecg_dir = Path("data/ecg_cases")
    
    if not ecg_dir.exists():
        return cas_ecg
    
    # Parcourir tous les dossiers de cas
    for case_folder in ecg_dir.iterdir():
        if case_folder.is_dir():
            cas_data = charger_cas_individuel(case_folder)
            if cas_data:
                cas_ecg.append(cas_data)
    
    # Trier par date de création (plus récent en premier)
    cas_ecg.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    
    return cas_ecg

def charger_cas_individuel(case_folder):
    """Charge les données d'un cas individuel"""
    
    try:
        # Lire les métadonnées
        metadata_path = case_folder / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            # Métadonnées par défaut si pas de fichier
            metadata = {
                'case_id': case_folder.name,
                'created_date': datetime.now().isoformat(),
                'statut': 'imported'
            }
        
        # Chercher le fichier principal (image ou XML)
        fichier_principal = None
        type_fichier = None
        
        # Priorité aux images
        for ext in ['.png', '.jpg', '.jpeg']:
            image_files = list(case_folder.glob(f"*{ext}"))
            if image_files:
                fichier_principal = image_files[0]
                type_fichier = 'image'
                break
        
        # Sinon chercher XML
        if not fichier_principal:
            xml_files = list(case_folder.glob("*.xml"))
            if xml_files:
                fichier_principal = xml_files[0]
                type_fichier = 'xml'
        
        # Sinon chercher PDF
        if not fichier_principal:
            pdf_files = list(case_folder.glob("*.pdf"))
            if pdf_files:
                fichier_principal = pdf_files[0]
                type_fichier = 'pdf'
        
        if fichier_principal:
            metadata['file_path'] = str(fichier_principal)
            metadata['file_type'] = type_fichier
            metadata['folder_path'] = str(case_folder)
            return metadata
        
        return None
        
    except Exception as e:
        st.error(f"Erreur chargement cas {case_folder.name}: {e}")
        return None

def afficher_aucun_cas():
    """Affichage quand aucun cas n'est disponible"""
    
    st.info("📭 Aucun cas ECG trouvé")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Pour commencer :")
        st.markdown("1. **Utilisez l'Import Intelligent** pour ajouter des ECG")
        st.markdown("2. **Ou importez manuellement** dans `data/ecg_cases/`")
        st.markdown("3. **Revenez ici** pour les visualiser")
    
    with col2:
        st.markdown("### 📁 Structure attendue :")
        st.code("""
data/ecg_cases/
├── cas_001/
│   ├── ecg_image.png
│   └── metadata.json
├── cas_002/
│   ├── ecg_data.xml
│   └── metadata.json
""", language="text")
    
    # Bouton pour aller à l'import
    if st.button("🎯 Aller à l'Import Intelligent", type="primary"):
        st.switch_page("🎯 Import Intelligent")

def afficher_info_cas(cas):
    """Affiche les informations d'un cas"""
    
    st.markdown("#### 📋 Informations")
    
    # ID du cas
    st.write(f"**ID :** {cas.get('case_id', 'Non défini')}")
    
    # Date
    date_str = cas.get('created_date', '')
    if date_str:
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            date_formatted = date_obj.strftime("%d/%m/%Y %H:%M")
            st.write(f"**Date :** {date_formatted}")
        except:
            st.write(f"**Date :** {date_str[:10]}")
    
    # Type de fichier
    type_fichier = cas.get('file_type', 'inconnu')
    st.write(f"**Type :** {type_fichier.upper()}")
    
    # Informations patient
    if 'age' in cas and cas['age']:
        st.write(f"**Âge :** {cas['age']} ans")
    
    if 'sexe' in cas and cas['sexe']:
        st.write(f"**Sexe :** {cas['sexe']}")
    
    # Contexte clinique
    if 'contexte' in cas and cas['contexte']:
        st.markdown("**Contexte :**")
        st.write(cas['contexte'])
    
    # Diagnostic
    if 'diagnostic' in cas and cas['diagnostic']:
        st.markdown("**Diagnostic :**")
        st.write(cas['diagnostic'])
    
    # Statut
    statut = cas.get('statut', 'imported')
    if statut == 'imported':
        st.success("✅ Importé")
    elif statut == 'annotated':
        st.info("📝 Annoté")
    else:
        st.write(f"**Statut :** {statut}")

def afficher_ecg_principal(cas):
    """Affiche l'ECG principal"""
    
    st.markdown("#### 🫀 ECG")
    
    file_path = cas.get('file_path')
    file_type = cas.get('file_type')
    
    if not file_path or not os.path.exists(file_path):
        st.error("❌ Fichier ECG introuvable")
        st.write(f"Chemin : {file_path}")
        return
    
    try:
        if file_type == 'image':
            case_id = cas.get('name') or cas.get('case_id', 'unknown')
            afficher_ecg_image(file_path, case_id)
        elif file_type == 'xml':
            afficher_ecg_xml(file_path)
        elif file_type == 'pdf':
            afficher_ecg_pdf(file_path)
        else:
            st.warning(f"⚠️ Type de fichier non supporté : {file_type}")
            
    except Exception as e:
        st.error(f"❌ Erreur affichage ECG : {e}")

def afficher_ecg_plein_ecran(image, case_id):
    """Mode plein écran ECG - Version simple et efficace"""
    
    # Nettoyage du case_id pour les clés Streamlit
    clean_id = clean_case_id(case_id)
    
def afficher_ecg_plein_ecran(image, case_id):
    """Bouton pour ouvrir l'ECG en vrai plein écran dans un nouvel onglet"""
    
    # Nettoyage du case_id pour les clés Streamlit
    clean_id = clean_case_id(case_id)
    
    # Convertir l'image en base64 pour l'embedder
    import base64
    from io import BytesIO
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Créer une page HTML complète pour le plein écran
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ECG - {case_id}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: black;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-family: Arial, sans-serif;
            }}
            .ecg-container {{
                position: relative;
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .ecg-image {{
                max-width: 100%;
                max-height: 100%;
                cursor: grab;
                transition: transform 0.1s ease;
            }}
            .ecg-image:active {{
                cursor: grabbing;
            }}
            .controls {{
                position: fixed;
                top: 10px;
                left: 10px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                z-index: 1000;
            }}
            .zoom-btn {{
                background: #0066cc;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 2px;
                border-radius: 3px;
                cursor: pointer;
            }}
            .zoom-btn:hover {{
                background: #0052a3;
            }}
            .info {{
                position: fixed;
                bottom: 10px;
                left: 10px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="controls">
            <button class="zoom-btn" onclick="zoomIn()">🔍 +</button>
            <button class="zoom-btn" onclick="zoomOut()">🔍 -</button>
            <button class="zoom-btn" onclick="resetZoom()">🔄 Reset</button>
            <button class="zoom-btn" onclick="window.close()">❌ Fermer</button>
        </div>
        
        <div class="ecg-container">
            <img id="ecg-img" class="ecg-image" src="data:image/png;base64,{img_base64}" alt="ECG {case_id}">
        </div>
        
        <div class="info">
            📋 {case_id} | 🖱️ Cliquez et glissez pour déplacer | ⚙️ Utilisez la molette pour zoomer
        </div>
        
        <script>
            let scale = 1;
            let translateX = 0;
            let translateY = 0;
            let isDragging = false;
            let startX, startY;
            
            const img = document.getElementById('ecg-img');
            
            function updateTransform() {{
                img.style.transform = `scale(${{scale}}) translate(${{translateX}}px, ${{translateY}}px)`;
            }}
            
            function zoomIn() {{
                scale = Math.min(scale * 1.2, 5);
                updateTransform();
            }}
            
            function zoomOut() {{
                scale = Math.max(scale / 1.2, 0.1);
                updateTransform();
            }}
            
            function resetZoom() {{
                scale = 1;
                translateX = 0;
                translateY = 0;
                updateTransform();
            }}
            
            // Zoom avec la molette
            img.addEventListener('wheel', (e) => {{
                e.preventDefault();
                if (e.deltaY < 0) {{
                    zoomIn();
                }} else {{
                    zoomOut();
                }}
            }});
            
            // Déplacement par glisser-déposer
            img.addEventListener('mousedown', (e) => {{
                isDragging = true;
                startX = e.clientX - translateX;
                startY = e.clientY - translateY;
                e.preventDefault();
            }});
            
            document.addEventListener('mousemove', (e) => {{
                if (isDragging) {{
                    translateX = e.clientX - startX;
                    translateY = e.clientY - startY;
                    updateTransform();
                }}
            }});
            
            document.addEventListener('mouseup', () => {{
                isDragging = false;
            }});
            
            // Double-clic pour recentrer
            img.addEventListener('dblclick', () => {{
                translateX = 0;
                translateY = 0;
                updateTransform();
            }});
            
            // Raccourcis clavier
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'Escape') {{
                    window.close();
                }} else if (e.key === '+' || e.key === '=') {{
                    zoomIn();
                }} else if (e.key === '-') {{
                    zoomOut();
                }} else if (e.key === '0') {{
                    resetZoom();
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Encoder le HTML en base64 pour l'ouvrir dans un nouvel onglet
    html_base64 = base64.b64encode(html_content.encode()).decode()
    data_url = f"data:text/html;base64,{html_base64}"
    
    st.markdown("### 🖼️ Mode Plein Écran")
    
    # Bouton pour ouvrir en vrai plein écran
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <a href="{data_url}" target="_blank" style="
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            🖼️ OUVRIR EN VRAI PLEIN ÉCRAN
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Bouton pour fermer le mode
    if st.button("❌ Retour à l'affichage normal", key=f"exit_fs_{clean_id}", type="primary"):
        fullscreen_key = f"fullscreen_{clean_id}"
        st.session_state[fullscreen_key] = False
        st.rerun()
    
    # Instructions
    st.info("""
    💡 **Instructions :**
    - Cliquez sur le bouton ci-dessus pour ouvrir l'ECG en **vrai plein écran** dans un nouvel onglet
    - **Molette de souris** : Zoomer/dézoomer
    - **Cliquer + glisser** : Déplacer l'image  
    - **Double-clic** : Recentrer l'image
    - **Touches +/-** : Zoomer/dézoomer
    - **Touche 0** : Reset zoom
    - **Échap** : Fermer
    """)


def afficher_ecg_plein_ecran_old_backup():
        st.markdown("""
        **🎮 Contrôles disponibles :**
        - **🖱️ Glisser** : Déplacer l'image
        - **🖱️ Double-clic** : Recentrer l'image  
        - **⚙️ Sliders** : Zoom et luminosité
        - **🔄 Reset** : Paramètres par défaut
        
        **💡 Astuce :** Les réglages sont sauvegardés automatiquement
        """)
    
    # Message d'instructions
    st.info("🎮 **Mode Plein Écran Activé** - Utilisez les contrôles ci-dessous pour naviguer dans l'ECG")
    
    # Contrôles plein écran
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        zoom_level = st.slider("🔍 Zoom", 100, 200, 100, 10, key=f"zoom_{clean_id}")
    
    with col2:
        pan_mode = st.checkbox("✋ Mode Pan", key=f"pan_{clean_id}")
    
    with col3:
        if st.button("� Reset Vue", key=f"reset_{case_id}"):
            st.session_state[f"zoom_{clean_id}"] = 100
            st.session_state[f"pan_{clean_id}"] = False
            st.rerun()
    
    with col4:
        if st.button("❌ Fermer Plein Écran", key=f"exit_fs_{clean_id}", type="primary"):
            # Utiliser la même clé que dans afficher_ecg_image
            fullscreen_key = f"fullscreen_{clean_id}"
            st.session_state[fullscreen_key] = False
            st.rerun()
    
    # Affichage de l'image avec contrôles JavaScript fonctionnels
    st.markdown(f"""
    <style>
    .fullscreen-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.95);
        z-index: 999999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-sizing: border-box;
    }}
    
    .ecg-fullscreen-controls {{
        position: fixed;
        top: 30px;
        left: 50%;
        transform: translateX(-50%);
        background: white;
        padding: 15px 25px;
        border-radius: 15px;
        z-index: 1000000;
        display: flex;
        align-items: center;
        gap: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        border: 3px solid #4CAF50;
    }}
    
    .ecg-fullscreen-image {{
        max-width: 90vw;
        max-height: 75vh;
        object-fit: contain;
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 3px solid #4CAF50;
        cursor: grab;
        transition: transform 0.1s ease;
        box-shadow: 0 0 30px rgba(76, 175, 80, 0.3);
    }}
    
    .ecg-fullscreen-image:active {{
        cursor: grabbing;
    }}
    
    .zoom-slider {{
        width: 120px;
        height: 5px;
        background: #ddd;
        border-radius: 3px;
        outline: none;
        -webkit-appearance: none;
    }}
    
    .zoom-slider::-webkit-slider-thumb {{
        appearance: none;
        width: 16px;
        height: 16px;
        background: #4CAF50;
        border-radius: 50%;
        cursor: pointer;
    }}
    
    .fs-button {{
        background: #4CAF50;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s;
    }}
    
    .fs-button:hover {{
        background: #45a049;
        transform: scale(1.05);
    }}
    
    .fs-exit-button {{
        background: #f44336;
        color: white;
        border: none;
        padding: 10px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        font-size: 16px;
    }}
    
    .fs-exit-button:hover {{
        background: #da190b;
        transform: scale(1.05);
    }}
    
    .zoom-display {{
        font-weight: bold;
        color: #333;
        font-size: 16px;
        min-width: 50px;
        text-align: center;
    }}
    
    .fs-help {{
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.9);
        padding: 10px 20px;
        border-radius: 10px;
        color: #333;
        font-weight: bold;
        text-align: center;
        z-index: 1000000;
    }}
    </style>
    
    <div class="fullscreen-overlay" id="fullscreenOverlay">
        <div class="ecg-fullscreen-controls">
            <span>🔍</span>
            <input type="range" class="zoom-slider" id="zoomSlider" min="100" max="200" value="{zoom_level}" step="10">
            <span class="zoom-display" id="zoomDisplay">{zoom_level}%</span>
            <button class="fs-button" onclick="resetView()">🔄 Reset</button>
            <button class="fs-button" onclick="togglePan()" id="panBtn">✋ {"Pan ON" if pan_mode else "Pan"}</button>
            <button class="fs-exit-button" onclick="exitFullscreen()">❌ Fermer</button>
        </div>
        
        <img class="ecg-fullscreen-image" id="ecgImage" src="data:image/png;base64,{img_base64}" alt="ECG Plein Écran">
        
        <div class="fs-help">
            🎮 <strong>Contrôles:</strong> Molette=Zoom | Glisser=Pan | ESC=Fermer | +/-=Zoom clavier
        </div>
    </div>
    
    <script>
    (function() {{
        let zoom = {zoom_level};
        let panMode = {str(pan_mode).lower()};
        let isDragging = false;
        let startX, startY;
        let translateX = 0, translateY = 0;
        
        const slider = document.getElementById('zoomSlider');
        const display = document.getElementById('zoomDisplay');
        const image = document.getElementById('ecgImage');
        const panBtn = document.getElementById('panBtn');
        
        function updateImage() {{
            const scale = zoom / 100;
            image.style.transform = `scale(${{scale}}) translate(${{translateX}}px, ${{translateY}}px)`;
        }}
        
        // Synchronisation avec Streamlit
        slider.addEventListener('input', function() {{
            zoom = parseInt(this.value);
            display.textContent = zoom + '%';
            updateImage();
        }});
        
        window.resetView = function() {{
            zoom = 100;
            translateX = 0;
            translateY = 0;
            slider.value = 100;
            display.textContent = '100%';
            updateImage();
        }};
        
        window.togglePan = function() {{
            panMode = !panMode;
            panBtn.textContent = panMode ? '✋ Pan ON' : '✋ Pan';
            image.style.cursor = panMode ? 'grab' : 'default';
        }};
        
        window.exitFullscreen = function() {{
            document.getElementById('fullscreenOverlay').style.display = 'none';
            // Déclencher l'action Streamlit pour fermer le plein écran
            setTimeout(() => {{
                window.location.reload();
            }}, 100);
        }};
        
        // Gestion du pan
        image.addEventListener('mousedown', function(e) {{
            if (!panMode) return;
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
            image.style.cursor = 'grabbing';
            e.preventDefault();
        }});
        
        document.addEventListener('mousemove', function(e) {{
            if (!isDragging || !panMode) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            updateImage();
        }});
        
        document.addEventListener('mouseup', function() {{
            if (isDragging) {{
                isDragging = false;
                image.style.cursor = panMode ? 'grab' : 'default';
            }}
        }});
        
        // Zoom avec molette
        image.addEventListener('wheel', function(e) {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? -10 : 10;
            zoom = Math.max(100, Math.min(200, zoom + delta));
            slider.value = zoom;
            display.textContent = zoom + '%';
            updateImage();
        }});
        
        // Contrôles clavier
        document.addEventListener('keydown', function(e) {{
            switch(e.key) {{
                case 'Escape':
                    exitFullscreen();
                    break;
                case '+':
                case '=':
                    zoom = Math.min(200, zoom + 10);
                    slider.value = zoom;
                    display.textContent = zoom + '%';
                    updateImage();
                    break;
                case '-':
                    zoom = Math.max(100, zoom - 10);
                    slider.value = zoom;
                    display.textContent = zoom + '%';
                    updateImage();
                    break;
                case '0':
                    resetView();
                    break;
                case ' ':
                    e.preventDefault();
                    togglePan();
                    break;
            }}
        }});
        
        // Initialisation
        updateImage();
        
        // Mise à jour des contrôles
        if (panMode) {{
            image.style.cursor = 'grab';
            panBtn.textContent = '✋ Pan ON';
        }}
        
    }})();
    </script>
    """, unsafe_allow_html=True)

def afficher_ecg_image(file_path):
    st.markdown("### �️ Mode Plein Écran Activé")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.info("🚀 **Plein écran lancé !** Utilisez les contrôles dans la fenêtre plein écran.")
    
    with col2:
        st.markdown("""
        **🎮 Contrôles disponibles :**
        - 🔍 **Slider** : Zoom 100% à 200%
        - ✋ **Pan** : Glisser l'image
        - 🔄 **Reset** : Position initiale
        - **Molette** : Zoom rapide
        - **+/-** : Zoom clavier
        - **Espace** : Toggle pan
        - **Échap** : Sortir
        """)
    
    with col3:
        if st.button("❌ Sortir du Plein Écran", key="exit_fullscreen_generic", type="secondary"):
            # Cette fonction semble être un doublon - à supprimer
            st.rerun()
    
    # Script pour gérer les messages du plein écran
    st.markdown("""
    <script>
    window.addEventListener('message', function(event) {
        if (event.data.type === 'exit_fullscreen') {
            // Déclencher la sortie du mode plein écran côté Streamlit
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.textContent.includes('Sortir du Plein Écran')) {
                    btn.click();
                }
            });
        }
    });
    </script>
    """, unsafe_allow_html=True)

def afficher_ecg_image(file_path, case_id):
    """Affiche un ECG image"""
    
    try:
        image = Image.open(file_path)
        
        # Nettoyage du case_id pour les clés Streamlit
        clean_id = clean_case_id(case_id)
        
        # Vérifier si le mode plein écran est activé
        fullscreen_key = f"fullscreen_{clean_id}"
        
        if st.session_state.get(fullscreen_key, False):
            # Mode plein écran
            afficher_ecg_plein_ecran(image, case_id)
        else:
            # Mode normal avec contrôles améliorés et visibles
            st.markdown("### 🖼️ Affichage ECG")
            
            # Panneau de contrôle principal - toujours visible
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(90deg, #e3f2fd, #bbdefb); 
                           padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <h4 style="margin: 0; color: #1976d2;">🎛️ Panneau de Contrôle ECG</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Ligne de contrôles principaux
                ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 2, 2])
                
                # Nettoyage du case_id pour les clés Streamlit
                clean_id = clean_case_id(case_id)
                
                with ctrl_col1:
                    st.markdown("**🖼️ Affichage**")
                    if st.button("🖼️ Mode Plein Écran", key=f"btn_fullscreen_{clean_id}", type="primary", use_container_width=True):
                        st.session_state[fullscreen_key] = True
                        st.rerun()
                
                with ctrl_col2:
                    st.markdown("**🔍 Zoom**")
                    zoom = st.slider(
                        "Niveau de zoom", 
                        100, 200, 100, 
                        step=10,
                        key=f"zoom_{clean_id}",
                        help="Ajustez le zoom de l'ECG (100% à 200%)"
                    )
                
                with ctrl_col3:
                    st.markdown("**📏 Informations**")
                    st.metric("Largeur", f"{image.size[0]}px")
                    st.metric("Hauteur", f"{image.size[1]}px")
                
                with ctrl_col4:
                    st.markdown("**⚙️ Paramètres**")
                    st.write(f"**Mode couleur :** {image.mode}")
                    if zoom != 100:
                        calculated_width = int(800 * zoom / 100)
                        st.write(f"**Largeur zoom :** {calculated_width}px")
            
            st.markdown("---")
            
            # Affichage de l'image avec feedback visuel
            if zoom == 100:
                st.success("🖼️ **Affichage normal** - Taille originale")
                st.image(image, caption="ECG - Taille originale", use_container_width=True)
            else:
                st.info(f"🔍 **Mode Zoom {zoom}%** - Image redimensionnée")
                width = int(800 * zoom / 100)
                # Centrer l'image zoomée
                col_left, col_center, col_right = st.columns([1, 6, 1])
                with col_center:
                    st.image(image, width=width, caption=f"ECG - Zoom {zoom}%", use_container_width=False)
        
    except Exception as e:
        st.error(f"❌ Erreur chargement image : {e}")

def afficher_ecg_xml(file_path):
    """Affiche un ECG XML"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        st.markdown("#### 📋 Données XML ECG")
        
        # Aperçu du contenu
        with st.expander("📄 Contenu XML complet"):
            st.code(xml_content, language='xml')
        
        # Extraction d'informations si possible
        if 'HL7' in xml_content:
            st.info("🏥 Format HL7 CDA détecté")
        elif 'waveform' in xml_content.lower():
            st.info("📊 Données de forme d'onde détectées")
        
        # Recherche de valeurs importantes
        lines = xml_content.split('\n')[:20]  # Premières lignes
        st.markdown("#### 📊 Aperçu des données")
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['frequence', 'rhythm', 'bpm', 'rate']):
                st.write(f"• {line.strip()}")
        
    except Exception as e:
        st.error(f"❌ Erreur lecture XML : {e}")

def afficher_ecg_pdf(file_path):
    """Affiche un ECG PDF"""
    
    st.markdown("#### 📄 PDF ECG")
    
    try:
        # Lire le fichier PDF
        with open(file_path, 'rb') as f:
            pdf_data = f.read()
        
        # Affichage PDF.js
        import base64
        pdf_base64 = base64.b64encode(pdf_data).decode()
        
        iframe_html = f"""
        <div style="border: 2px solid #0066cc; border-radius: 10px; padding: 5px;">
            <iframe 
                src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}" 
                width="100%" 
                height="600" 
                style="border: none; border-radius: 5px;">
            </iframe>
        </div>
        """
        
        st.components.v1.html(iframe_html, height=620)
        
    except Exception as e:
        st.error(f"❌ Erreur affichage PDF : {e}")

def interface_annotation_simple(cas):
    """Interface d'annotation simplifiée avec formulaire"""
    
    st.markdown("### 📝 Annotation ECG")
    
    # Afficher les annotations existantes d'abord
    annotations_existantes = charger_annotations_existantes(cas)
    if annotations_existantes:
        with st.expander(f"📖 Annotations existantes ({len(annotations_existantes)})"):
            for i, ann in enumerate(annotations_existantes):
                st.markdown(f"**Annotation {i+1}** - {ann.get('date', 'N/A')[:16]}")
                
                # Affichage nouvelle annotation intelligente
                if ann.get('annotation_tags'):
                    st.markdown("**🏷️ Concepts annotés :**")
                    for tag in ann['annotation_tags']:
                        st.badge(tag)
                
                # Rétrocompatibilité anciennes annotations
                if ann.get('annotation_experte'):
                    st.write(f"**Annotation Experte :** {ann['annotation_experte']}")
                if ann.get('interpretation'):
                    st.write(f"**Interprétation :** {ann['interpretation']}")
                if ann.get('diagnostic'):
                    st.write(f"**Diagnostic :** {ann['diagnostic']}")
                st.markdown("---")
    
    # Interface d'annotation intelligente
    if SMART_ANNOTATION_AVAILABLE:
        st.markdown("---")
        
        # Récupérer les tags existants pour édition
        existing_tags = []
        if annotations_existantes:
            latest_annotation = annotations_existantes[-1]  # Plus récente
            existing_tags = latest_annotation.get('annotation_tags', [])
        
        # Interface d'annotation par mots-clés
        case_id = cas.get('name') or cas.get('case_id', 'unknown')
        
        # Nettoyage du case_id pour les clés Streamlit
        clean_id = clean_case_id(case_id)
        
        selected_tags = annotation_intelligente_admin(
            key_suffix=clean_id, 
            initial_tags=existing_tags
        )
        
        # Bouton de sauvegarde des tags
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("💾 Sauvegarder l'annotation", type="primary", key=f"save_tags_{clean_id}"):
                if selected_tags:
                    success = sauvegarder_annotation_tags(cas, selected_tags)
                    if success:
                        st.success("✅ Annotation par tags sauvegardée !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.warning("⚠️ Aucun tag sélectionné")
        
        with col2:
            if st.button("🔄 Actualiser", key=f"refresh_tags_{clean_id}"):
                # Simple rafraîchissement sans modifier la navigation
                st.rerun()
        
        with col3:
            # Mode fallback si problème avec l'ontologie
            if st.button("📝 Mode texte", key=f"fallback_{clean_id}"):
                st.session_state[f"use_fallback_{clean_id}"] = True
                # Rafraîchir pour activer le mode texte
                st.rerun()
    
    else:
        # Fallback : Interface texte classique
        case_form_id = cas.get('name') or cas.get('case_id', 'unknown')
        with st.form(key=f"annotation_form_{case_form_id}", clear_on_submit=True):
            st.markdown("#### ✍️ Annotation Expert (Mode texte)")
            st.warning("⚠️ Interface intelligente non disponible - Mode texte de secours")
            
            # Un seul champ unifié pour l'annotation complète
            annotation_complete = st.text_area(
                "Annotation experte complète :",
                placeholder="Ex: Rythme sinusal, FC 75 bpm, axe normal, ondes P présentes, QRS fins, pas d'anomalie ST-T. Diagnostic: ECG normal.",
                height=150,
                help="Saisissez votre expertise complète : description des observations + diagnostic."
            )
            
            # Bouton de soumission du formulaire
            submitted = st.form_submit_button("💾 Ajouter l'annotation experte", type="primary")
            
            if submitted:
                if annotation_complete.strip():
                    # Préserver l'état de navigation
                    if 'admin_page' in st.session_state:
                        st.session_state.admin_page = "📺 Liseuse ECG"
                    
                    success = sauvegarder_annotation_unifiee(cas, annotation_complete.strip())
                    if success:
                        st.success("✅ Annotation experte sauvegardée avec succès !")
                        # Le formulaire se vide automatiquement avec clear_on_submit=True
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.error("❌ Veuillez saisir l'annotation experte")
    
    # Bouton d'actualisation séparé du formulaire
    case_id = cas.get('name') or cas.get('case_id', 'unknown')
    clean_id = clean_case_id(case_id)
    if st.button("🔄 Actualiser la page", key=f"refresh_{clean_id}"):
        # Préserver complètement l'état de navigation actuel - ne pas le modifier
        # st.rerun() rafraîchit juste l'affichage sans changer de page
        st.rerun()

def charger_annotations_existantes(cas):
    """Charge les annotations existantes d'un cas"""
    
    try:
        metadata_path = Path(cas['folder_path']) / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return metadata.get('annotations', [])
    except Exception:
        pass
    return []

def sauvegarder_annotation_formulaire(cas, interpretation, diagnostic):
    """Sauvegarde une annotation depuis un formulaire"""
    
    try:
        # Charger les métadonnées existantes
        metadata_path = Path(cas['folder_path']) / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata_case_id = cas.get('name') or cas.get('case_id', 'unknown')
            metadata = {'case_id': metadata_case_id}
        
        # Ajouter l'annotation
        if 'annotations' not in metadata:
            metadata['annotations'] = []
        
        # Supprimer les annotations utilisateur existantes pour éviter l'accumulation
        metadata['annotations'] = [ann for ann in metadata['annotations'] if ann.get('auteur') != 'utilisateur']
        
        nouvelle_annotation = {
            'date': datetime.now().isoformat(),
            'interpretation': interpretation,
            'diagnostic': diagnostic,
            'auteur': 'utilisateur'
        }
        
        metadata['annotations'].append(nouvelle_annotation)
        metadata['statut'] = 'annotated'
        
        # Sauvegarder
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde : {e}")
        return False

def sauvegarder_annotation(cas, interpretation, diagnostic):
    """Sauvegarde une annotation"""
    
    try:
        # Charger les métadonnées existantes
        metadata_path = Path(cas['folder_path']) / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {'case_id': cas['case_id']}
        
        # Ajouter l'annotation
        if 'annotations' not in metadata:
            metadata['annotations'] = []
        
        # Supprimer les annotations utilisateur existantes pour éviter l'accumulation
        metadata['annotations'] = [ann for ann in metadata['annotations'] if ann.get('auteur') != 'utilisateur']
        
        nouvelle_annotation = {
            'date': datetime.now().isoformat(),
            'interpretation': interpretation,
            'diagnostic': diagnostic,
            'auteur': 'utilisateur'  # Peut être étendu
        }
        
        metadata['annotations'].append(nouvelle_annotation)
        metadata['statut'] = 'annotated'
        
        # Sauvegarder
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Préserver l'état de navigation avant d'afficher le succès
        if 'admin_page' in st.session_state:
            st.session_state.admin_page = "📺 Liseuse ECG (WP2)"
        
        st.success("✅ Annotation sauvegardée !")
        # Éviter st.balloons() qui peut causer des problèmes de navigation
        
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde : {e}")

def sauvegarder_annotation_unifiee(cas, annotation_complete):
    """Sauvegarde une annotation experte unifiée"""
    
    try:
        # Charger les métadonnées existantes
        metadata_path = Path(cas['folder_path']) / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {'case_id': cas['case_id']}
        
        # Ajouter l'annotation unifiée
        if 'annotations' not in metadata:
            metadata['annotations'] = []
        
        # Supprimer les annotations expertes existantes pour éviter l'accumulation
        metadata['annotations'] = [ann for ann in metadata['annotations'] if ann.get('type') != 'expert']
        
        nouvelle_annotation = {
            'date': datetime.now().isoformat(),
            'annotation_experte': annotation_complete,
            'type': 'expert',
            'auteur': 'expert'
        }
        
        metadata['annotations'].append(nouvelle_annotation)
        metadata['statut'] = 'expertised'
        
        # Sauvegarder
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde annotation experte : {e}")
        return False

def sauvegarder_annotation_tags(cas, tags_list):
    """Sauvegarde une annotation sous forme de tags intelligents (remplace l'annotation existante)"""
    
    try:
        # Charger les métadonnées existantes
        metadata_path = Path(cas['folder_path']) / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {'case_id': cas['case_id']}
        
        # Initialiser les annotations si nécessaire
        if 'annotations' not in metadata:
            metadata['annotations'] = []
        
        # SUPPRIMER toutes les annotations expert existantes pour éviter l'accumulation
        metadata['annotations'] = [
            ann for ann in metadata['annotations'] 
            if ann.get('type') != 'expert_tags' and ann.get('auteur') != 'expert'
        ]
        
        # Ajouter la NOUVELLE annotation (unique)
        nouvelle_annotation = {
            'date': datetime.now().isoformat(),
            'annotation_tags': tags_list,
            'type': 'expert_tags',
            'auteur': 'expert'
        }
        
        metadata['annotations'].append(nouvelle_annotation)
        metadata['statut'] = 'expertised_tags'
        
        # Sauvegarder
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde annotation tags : {e}")
        return False

def afficher_historique_annotations(cas):
    """Affiche l'historique des annotations"""
    
    try:
        metadata_path = Path(cas['folder_path']) / "metadata.json"
        
        if not metadata_path.exists():
            st.info("📭 Aucune annotation trouvée")
            return
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        annotations = metadata.get('annotations', [])
        
        if not annotations:
            st.info("📭 Aucune annotation pour ce cas")
            return
        
        st.markdown("#### 📚 Historique des annotations")
        
        for i, annotation in enumerate(reversed(annotations)):  # Plus récent en premier
            with st.expander(f"📝 Annotation #{len(annotations)-i} - {annotation.get('date', '')[:16]}"):
                # Nouvelle annotation unifiée (expert)
                if annotation.get('annotation_experte'):
                    st.markdown("**Annotation Experte :**")
                    st.write(annotation['annotation_experte'])
                
                # Anciennes annotations séparées (rétrocompatibilité)
                if annotation.get('interpretation'):
                    st.markdown("**Interprétation :**")
                    st.write(annotation['interpretation'])
                
                if annotation.get('diagnostic'):
                    st.markdown("**Diagnostic :**")
                    st.write(annotation['diagnostic'])
                
                st.caption(f"Auteur : {annotation.get('auteur', 'inconnu')} - Type : {annotation.get('type', 'standard')}")
        
    except Exception as e:
        st.error(f"❌ Erreur chargement historique : {e}")

# Interface principale
if __name__ == "__main__":
    st.set_page_config(
        page_title="Liseuse ECG",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Liseuse ECG Fonctionnelle")
    liseuse_ecg_fonctionnelle()
