import streamlit as st
import pandas as pd
from PIL import Image
import os
import re
import base64
from io import BytesIO
from datetime import datetime

def clean_case_id(case_id):
    """Nettoie le case_id pour une utilisation sécurisée dans les clés Streamlit"""
    if not case_id:
        return "default"
    # Remplacer tous les caractères non alphanumériques par des underscores
    clean_id = re.sub(r'[^a-zA-Z0-9]', '_', str(case_id))
    # Supprimer les underscores multiples
    clean_id = re.sub(r'_+', '_', clean_id)
    # Supprimer les underscores au début et à la fin
    clean_id = clean_id.strip('_')
    return clean_id if clean_id else "default"

def afficher_ecg_plein_ecran(image, case_id):
    """Bouton pour ouvrir l'ECG en vrai plein écran dans un nouvel onglet"""
    
    # Nettoyage du case_id pour les clés Streamlit
    clean_id = clean_case_id(case_id)
    
    # Convertir l'image en base64 pour l'embedder
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

def afficher_ecg_image(file_path, case_id):
    """Affiche un ECG image avec possibilité de plein écran"""
    
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
            # Mode normal
            st.markdown("### 🖼️ Affichage ECG")
            
            # Contrôles de base
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                zoom = st.slider("🔍 Zoom", 50, 200, 100, 10, key=f"zoom_{clean_id}")
            
            with col2:
                if st.button("🔄 Reset", key=f"reset_{clean_id}"):
                    st.session_state[f"zoom_{clean_id}"] = 100
                    st.rerun()
            
            with col3:
                if st.button("🖼️ Plein Écran", key=f"fs_{clean_id}", type="primary"):
                    st.session_state[fullscreen_key] = True
                    st.rerun()
            
            # Affichage de l'image
            width = int(800 * zoom / 100)
            st.image(
                image, 
                width=width,
                caption=f"ECG - {case_id}",
                use_container_width=False
            )
            
            # Informations sur l'image
            st.info(f"📊 **Dimensions:** {image.size[0]} x {image.size[1]} pixels | **Zoom:** {zoom}%")
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de l'image : {str(e)}")

if __name__ == "__main__":
    st.title("Test ECG Viewer")
    
    # Test de la fonction
    test_case_id = "ECG_test_çàéù"
    st.write(f"Case ID original : {test_case_id}")
    st.write(f"Case ID nettoyé : {clean_case_id(test_case_id)}")
