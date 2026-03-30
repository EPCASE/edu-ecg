"""
Visualiseur PDF moderne avec PDF.js intégré
Solution web native sans dépendances système
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import os

def create_pdfjs_viewer(pdf_path, width="100%", height="600px"):
    """
    Crée un visualiseur PDF avec PDF.js intégré
    Aucune dépendance système requise !
    """
    
    # Lire le fichier PDF
    try:
        with open(pdf_path, "rb") as file:
            pdf_data = file.read()
        
        # Encoder en base64 pour l'embarquer
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # HTML avec PDF.js via CDN
        html_code = f"""
        <div style="width: {width}; height: {height};">
            <iframe 
                src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}"
                width="100%" 
                height="100%"
                style="border: none;">
            </iframe>
        </div>
        """
        
        return html_code
        
    except Exception as e:
        return f"""
        <div style="padding: 20px; border: 2px dashed #ccc; text-align: center;">
            <h3>📄 Fichier PDF non disponible</h3>
            <p>Erreur: {str(e)}</p>
            <p>Vous pouvez utiliser l'annotation avec des images PNG/JPG</p>
        </div>
        """

def create_lightweight_pdf_viewer(pdf_path):
    """
    Visualiseur PDF léger avec PDF.js
    Alternative moderne à poppler
    """
    
    st.subheader("📄 Visualiseur PDF (PDF.js)")
    
    if not os.path.exists(pdf_path):
        st.warning("Fichier PDF introuvable. Veuillez utiliser des images PNG/JPG pour l'annotation.")
        return False
    
    # Options d'affichage
    col1, col2 = st.columns([3, 1])
    
    with col2:
        height = st.selectbox(
            "Hauteur du visualiseur",
            ["400px", "600px", "800px", "1000px"],
            index=1
        )
        
        st.info("""
        💡 **PDF.js intégré**
        - Aucune installation requise
        - Fonctionne dans tous les navigateurs
        - Zoom, recherche, impression
        """)
    
    with col1:
        # Afficher le visualiseur PDF.js
        html_viewer = create_pdfjs_viewer(pdf_path, height=height)
        components.html(html_viewer, height=int(height.replace('px', '')) + 50)
    
    return True

def display_pdf_or_image(file_path):
    """
    Affiche un fichier PDF ou image de manière intelligente
    Priorité: PDF.js > Image directe > Message d'erreur
    """
    
    if not os.path.exists(file_path):
        st.error("Fichier introuvable")
        return False
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        # Utiliser PDF.js pour les PDFs
        return create_lightweight_pdf_viewer(file_path)
    
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        # Affichage direct pour les images
        st.image(file_path, use_container_width=True)
        return True
    
    else:
        st.warning(f"Format de fichier non supporté: {file_ext}")
        return False

# Test de la fonction
if __name__ == "__main__":
    st.title("🔧 Test du visualiseur PDF.js")
    
    st.markdown("""
    ### Avantages de PDF.js :
    - ✅ **Aucune dépendance système** (poppler non requis)
    - ✅ **JavaScript pur** - fonctionne partout
    - ✅ **Interface complète** (zoom, recherche, navigation)
    - ✅ **Utilisé par Firefox** et millions de sites web
    - ✅ **Léger et rapide**
    """)
    
    # Test avec un fichier d'exemple
    test_pdf = "ECG/ECG1.pdf"
    if os.path.exists(test_pdf):
        create_lightweight_pdf_viewer(test_pdf)
    else:
        st.info("Placez un fichier ECG1.pdf dans le dossier ECG/ pour tester")
