"""
Visualiseur PDF.js amélioré - Version robuste
Correction du problème d'affichage
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from pathlib import Path

def improved_pdfjs_viewer(pdf_path):
    """
    Visualiseur PDF.js amélioré avec gestion d'erreurs
    """
    
    st.subheader("📄 Visualiseur PDF.js")
    
    if not os.path.exists(pdf_path):
        st.error("❌ Fichier PDF introuvable")
        return False
    
    # Vérifier la taille du fichier
    file_size = os.path.getsize(pdf_path)
    file_size_mb = file_size / (1024 * 1024)
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("#### 📊 Informations")
        st.metric("Taille", f"{file_size_mb:.1f} MB")
        
        if file_size_mb > 10:
            st.warning("⚠️ Fichier volumineux")
            st.info("PDF.js peut être lent")
        
        # Options d'affichage
        method = st.radio(
            "Méthode d'affichage",
            ["PDF.js Intégré", "PDF.js Simple", "Lien direct"],
            help="Essayer différentes méthodes si l'affichage ne fonctionne pas"
        )
        
        height = st.selectbox(
            "Hauteur",
            ["400px", "500px", "600px", "700px"],
            index=2
        )
    
    with col1:
        try:
            if method == "PDF.js Intégré":
                success = display_embedded_pdfjs(pdf_path, height)
            elif method == "PDF.js Simple":
                success = display_simple_pdfjs(pdf_path, height)
            else:
                success = display_direct_link_pdfjs(pdf_path)
            
            if success:
                st.success("✅ PDF affiché avec succès")
                return True
            else:
                st.error("❌ Échec d'affichage")
                return False
                
        except Exception as e:
            st.error(f"❌ Erreur visualiseur : {e}")
            st.info("💡 Essayez une autre méthode d'affichage")
            return False

def display_embedded_pdfjs(pdf_path, height="600px"):
    """Méthode 1 : PDF.js intégré avec base64"""
    
    try:
        with open(pdf_path, "rb") as file:
            pdf_data = file.read()
        
        # Encoder en base64
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Vérifier la taille de base64 (limite navigateur)
        if len(pdf_base64) > 2000000:  # ~2MB limite
            st.warning("⚠️ PDF trop volumineux pour l'affichage intégré")
            return False
        
        # HTML avec PDF.js
        html_viewer = f"""
        <div style="width: 100%; height: {height}; border: 1px solid #ddd;">
            <iframe 
                src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}"
                width="100%" 
                height="100%"
                frameborder="0"
                sandbox="allow-same-origin allow-scripts">
                <p>Votre navigateur ne supporte pas les iframes.</p>
            </iframe>
        </div>
        """
        
        components.html(html_viewer, height=int(height.replace('px', '')) + 20)
        return True
        
    except Exception as e:
        st.error(f"Erreur méthode intégrée : {e}")
        return False

def display_simple_pdfjs(pdf_path, height="600px"):
    """Méthode 2 : PDF.js simple sans base64"""
    
    try:
        # HTML avec PDF.js générique + instructions
        html_viewer = f"""
        <div style="width: 100%; height: {height}; border: 1px solid #ddd; padding: 20px; text-align: center;">
            <h3>📄 Visualiseur PDF.js</h3>
            <p><strong>Fichier :</strong> {os.path.basename(pdf_path)}</p>
            <p><strong>Taille :</strong> {os.path.getsize(pdf_path)} bytes</p>
            <hr>
            <iframe 
                src="https://mozilla.github.io/pdf.js/web/viewer.html"
                width="100%" 
                height="80%"
                frameborder="0">
            </iframe>
            <p style="margin-top: 10px;">
                <em>Interface PDF.js chargée. Pour ouvrir votre PDF, utilisez le bouton "Ouvrir" dans l'interface.</em>
            </p>
        </div>
        """
        
        components.html(html_viewer, height=int(height.replace('px', '')) + 50)
        return True
        
    except Exception as e:
        st.error(f"Erreur méthode simple : {e}")
        return False

def display_direct_link_pdfjs(pdf_path):
    """Méthode 3 : Lien direct vers PDF.js"""
    
    try:
        file_name = os.path.basename(pdf_path)
        file_size = os.path.getsize(pdf_path)
        
        st.markdown(f"""
        ### 🔗 Affichage par lien direct
        
        **Fichier :** {file_name}  
        **Taille :** {file_size} bytes
        
        **Instructions :**
        1. Téléchargez le fichier ci-dessous
        2. Ouvrez [PDF.js en ligne](https://mozilla.github.io/pdf.js/web/viewer.html)
        3. Cliquez sur "Ouvrir un fichier" et sélectionnez votre PDF
        """)
        
        # Bouton de téléchargement
        with open(pdf_path, "rb") as file:
            st.download_button(
                "📥 Télécharger le PDF",
                file.read(),
                file_name=file_name,
                mime="application/pdf",
                help="Télécharger pour ouvrir dans PDF.js"
            )
        
        # Lien direct vers PDF.js
        st.markdown("""
        **Liens utiles :**
        - [PDF.js Viewer](https://mozilla.github.io/pdf.js/web/viewer.html) - Interface complète
        - [PDF.js Demo](https://mozilla.github.io/pdf.js/examples/) - Exemples
        """)
        
        return True
        
    except Exception as e:
        st.error(f"Erreur lien direct : {e}")
        return False

# Test de la fonction
if __name__ == "__main__":
    st.title("🧪 Test Visualiseur PDF.js Amélioré")
    
    # Chercher des PDFs
    test_files = []
    
    for pattern in ["ECG/*.pdf", "data/ecg_cases/*/*.pdf"]:
        for file in Path(".").glob(pattern):
            test_files.append(str(file))
    
    if test_files:
        st.success(f"✅ {len(test_files)} PDF(s) trouvé(s)")
        
        selected_pdf = st.selectbox("Choisir un PDF", test_files)
        
        if st.button("🔍 Tester l'affichage"):
            improved_pdfjs_viewer(selected_pdf)
    
    else:
        st.info("📂 Placez un PDF dans ECG/ ou importez un cas pour tester")
