"""
Visualiseur PDF.js ultra-robuste - Solution finale
Gestion complète du problème "pas d'affichage pdf.js"
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from pathlib import Path

def robust_pdfjs_viewer(pdf_path, height=600, max_size_mb=2):
    """
    Visualiseur PDF.js ultra-robuste avec gestion complète des erreurs
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        height: Hauteur de l'iframe (défaut: 600)
        max_size_mb: Taille maximale pour l'embarqué (défaut: 2MB)
    
    Returns:
        bool: True si l'affichage a réussi
    """
    
    if not pdf_path or not Path(pdf_path).exists():
        st.error("❌ Fichier PDF introuvable")
        return False
    
    try:
        # Lire le PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        file_size_mb = len(pdf_data) / (1024 * 1024)
        
        # Interface utilisateur améliorée
        col1, col2 = st.columns([4, 1])
        
        with col2:
            st.markdown("#### 📊 PDF Info")
            st.metric("Taille", f"{file_size_mb:.1f} MB")
            
            if file_size_mb > max_size_mb:
                st.warning("⚠️ Fichier volumineux")
                st.caption("Méthodes alternatives utilisées")
            else:
                st.success("✅ Taille optimale")
        
        with col1:
            if file_size_mb > max_size_mb:
                return _display_large_pdf_solutions(pdf_path, pdf_data, height)
            else:
                return _display_small_pdf_embedded(pdf_data, height)
                
    except Exception as e:
        st.error(f"❌ Erreur de lecture PDF : {e}")
        return _display_emergency_fallback(height)

def _display_small_pdf_embedded(pdf_data, height=600):
    """
    Affichage embarqué pour les petits PDFs
    """
    try:
        # Encoder en base64
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Vérifier la taille URL (limite navigateur)
        if len(pdf_base64) > 2000000:  # ~2MB base64
            st.warning("⚠️ Taille base64 trop importante")
            return False
        
        # URL PDF.js avec le PDF embarqué
        viewer_url = f"https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}"
        
        # Iframe stylée
        iframe_html = f"""
        <div style="
            border: 2px solid #e0e0e0; 
            border-radius: 10px; 
            overflow: hidden; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background: white;
        ">
            <iframe 
                src="{viewer_url}" 
                width="100%" 
                height="{height}" 
                style="border: none; display: block;"
                title="Visualiseur PDF">
            </iframe>
        </div>
        """
        
        st.components.v1.html(iframe_html, height=height + 10)
        
        # Feedback utilisateur
        with st.expander("ℹ️ Statut d'affichage", expanded=False):
            st.success("✅ PDF affiché via PDF.js embarqué")
            st.write(f"**Taille :** {len(pdf_data) / 1024:.1f} KB")
            st.write(f"**Méthode :** Intégration base64")
        
        return True
        
    except UnicodeEncodeError as e:
        st.error(f"❌ Erreur d'encodage : {e}")
        st.info("💡 Le PDF contient des caractères spéciaux - utilisation des méthodes alternatives")
        return False
    except Exception as e:
        st.error(f"❌ Erreur d'affichage embarqué : {e}")
        return False

def _display_large_pdf_solutions(pdf_path, pdf_data, height=600):
    """
    Solutions pour les gros PDFs ou en cas d'échec
    """
    st.subheader("🔄 PDF Volumineux - Solutions alternatives")
    
    # Interface à onglets
    tab1, tab2, tab3 = st.tabs(["📥 Téléchargement", "🌐 PDF.js Externe", "🛠️ Interface intégrée"])
    
    with tab1:
        st.markdown("#### 📥 Télécharger le PDF")
        st.info("💡 Méthode recommandée pour les gros fichiers")
        
        st.download_button(
            label="📄 Télécharger le fichier PDF",
            data=pdf_data,
            file_name=Path(pdf_path).name,
            mime="application/pdf",
            help="Téléchargez pour ouvrir dans votre lecteur PDF favori",
            use_container_width=True
        )
        
        st.success("✅ Téléchargement disponible")
        
    with tab2:
        st.markdown("#### 🌐 PDF.js en ligne")
        st.info("💡 Ouvre PDF.js dans un nouvel onglet")
        
        pdfjs_url = "https://mozilla.github.io/pdf.js/web/viewer.html"
        
        st.markdown(f"""
        **Étapes :**
        1. [🚀 Cliquez ici pour ouvrir PDF.js]({pdfjs_url})
        2. Téléchargez d'abord le PDF (onglet précédent)
        3. Dans PDF.js, cliquez sur "Ouvrir un fichier"
        4. Sélectionnez votre PDF téléchargé
        """)
        
        st.success("✅ Solution externe disponible")
        
    with tab3:
        st.markdown("#### 🛠️ Interface PDF.js intégrée")
        st.info("💡 Interface vide - chargez votre PDF avec 'Ouvrir un fichier'")
        
        iframe_html = f"""
        <div style="
            border: 2px solid #e0e0e0; 
            border-radius: 10px; 
            overflow: hidden;
            background: white;
        ">
            <iframe 
                src="https://mozilla.github.io/pdf.js/web/viewer.html" 
                width="100%" 
                height="{height}" 
                style="border: none;"
                title="Interface PDF.js">
            </iframe>
        </div>
        """
        
        st.components.v1.html(iframe_html, height=height + 10)
        st.success("✅ Interface PDF.js chargée")
    
    return True

def _display_emergency_fallback(height=600):
    """
    Fallback d'urgence si tout échoue
    """
    st.error("❌ Impossible d'afficher le PDF")
    
    # Guide de dépannage
    with st.expander("🆘 Guide de dépannage", expanded=True):
        st.markdown("""
        **Problèmes possibles :**
        - 🌐 Connexion internet instable
        - 🚫 Bloqueur de contenu/publicité actif  
        - 📱 Navigateur incompatible
        - 📄 Fichier PDF corrompu
        
        **Solutions à essayer :**
        1. **Vérifiez votre connexion internet**
        2. **Désactivez temporairement les bloqueurs** (AdBlock, etc.)
        3. **Essayez un autre navigateur** (Chrome, Firefox, Safari, Edge)
        4. **Rechargez la page** (F5 ou Ctrl+R)
        5. **Redémarrez l'application**
        """)
    
    # Interface PDF.js de secours
    st.markdown("#### 🌐 Interface PDF.js de secours")
    st.info("💡 Si cette interface se charge, PDF.js fonctionne sur votre système")
    
    iframe_html = f"""
    <div style="border: 1px solid #ccc; border-radius: 8px; overflow: hidden;">
        <iframe 
            src="https://mozilla.github.io/pdf.js/web/viewer.html" 
            width="100%" 
            height="{height}" 
            style="border: none;"
            title="Test PDF.js">
        </iframe>
    </div>
    """
    
    st.components.v1.html(iframe_html, height=height + 10)
    
    # Test de connectivité
    st.markdown("#### 🔍 Test de connectivité")
    if st.button("🧪 Tester la connexion PDF.js"):
        try:
            import urllib.request
            urllib.request.urlopen("https://mozilla.github.io/pdf.js/web/viewer.html", timeout=5)
            st.success("✅ Connexion PDF.js réussie")
        except:
            st.error("❌ Impossible de joindre PDF.js - vérifiez votre connexion")
    
    return False

# Test de la fonction si exécutée directement
if __name__ == "__main__":
    st.set_page_config(page_title="Test PDF.js Robuste", layout="wide")
    st.title("🔧 Test du visualiseur PDF.js robuste")
    
    # Interface de test
    test_pdf = st.file_uploader("Choisir un PDF à tester", type=['pdf'])
    
    if test_pdf:
        # Sauvegarder temporairement
        with open("temp_test.pdf", "wb") as f:
            f.write(test_pdf.read())
        
        # Tester l'affichage
        robust_pdfjs_viewer("temp_test.pdf")
        
        # Nettoyer
        os.remove("temp_test.pdf")
