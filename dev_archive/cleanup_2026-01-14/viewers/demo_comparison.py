"""
Démonstration PDF.js vs solutions traditionnelles
Comparaison des approches pour l'affichage PDF
"""

import streamlit as st
import os

def demo_comparison():
    st.title("📊 Comparaison des solutions PDF")
    
    st.markdown("""
    ## 🆚 Ancien vs Moderne
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ❌ Approche traditionnelle
        **Problèmes :**
        - 🔧 **Poppler requis** (dépendance système)
        - 💾 **Installation lourde** (100+ MB)
        - 🖥️ **Spécifique OS** (Windows/Linux/macOS)
        - ⚠️ **Erreurs fréquentes** (PATH, permissions)
        - 🐌 **Conversion lente** (PDF → Image)
        - 📱 **Limité mobile** 
        
        **Code complexe :**
        ```python
        # Installation poppler requise
        from pdf2image import convert_from_path
        try:
            images = convert_from_path(pdf_path)
            # Conversion temps réel
        except Exception:
            # Gestion erreurs nombreuses
        ```
        """)
    
    with col2:
        st.markdown("""
        ### ✅ PDF.js moderne
        **Avantages :**
        - 🌐 **Zéro dépendance** (JavaScript natif)
        - ⚡ **Installation légère** (CDN)
        - 🖥️ **Multi-plateforme** (navigateur)
        - ✅ **Toujours fonctionnel**
        - 🚀 **Affichage direct** (pas de conversion)
        - 📱 **Mobile-friendly**
        
        **Code simple :**
        ```python
        # Aucune installation
        pdf_url = f"data:application/pdf;base64,{pdf_b64}"
        viewer_url = f"https://mozilla.github.io/pdf.js/web/viewer.html?file={pdf_url}"
        # Affichage direct
        ```
        """)
    
    st.markdown("""
    ---
    ## 📈 Statistiques d'usage
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sites utilisant PDF.js", "2M+", "Standard web")
    with col2:
        st.metric("Navigateurs supportés", "100%", "Moderne")
    with col3:
        st.metric("Taille installation", "0 MB", "vs 100+ MB")
    
    st.markdown("""
    ---
    ## 🎯 Conclusion
    
    **PDF.js est la solution moderne** pour l'affichage PDF sur le web :
    - Utilisé par **GitHub**, **Google Drive**, **Outlook Web**
    - Solution **officielle Mozilla** 
    - **Zéro configuration** utilisateur
    - **Performance optimale** sur tous supports
    
    > 💡 **C'est pourquoi nous avons adopté PDF.js** dans Edu-CG !
    """)

if __name__ == "__main__":
    demo_comparison()
