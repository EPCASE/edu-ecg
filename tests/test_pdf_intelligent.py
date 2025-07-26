#!/usr/bin/env python3
"""
Solution PDF Intelligente - Multi-méthodes sans Poppler
Essaie plusieurs alternatives dans l'ordre de préférence
"""

import streamlit as st
from PIL import Image
import io
import base64

def convert_pdf_smart(pdf_data):
    """
    Conversion PDF intelligente avec multiples alternatives
    Essaie dans l'ordre : PyMuPDF > pdfplumber > Workflow manuel
    """
    
    methods_tried = []
    
    # 1. PyMuPDF (le plus performant)
    try:
        import fitz
        
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        page = pdf_document[0]
        mat = fitz.Matrix(2.0, 2.0)  # Haute résolution
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        pdf_document.close()
        
        return image, True, "✅ Conversion PyMuPDF réussie", "pymupdf"
        
    except ImportError:
        methods_tried.append("PyMuPDF non disponible")
    except Exception as e:
        methods_tried.append(f"PyMuPDF échoué : {e}")
    
    # 2. pdfplumber (alternative)
    try:
        import pdfplumber
        from io import BytesIO
        
        with pdfplumber.open(BytesIO(pdf_data)) as pdf:
            page = pdf.pages[0]
            image = page.to_image(resolution=200)
            pil_image = image.original
            
        return pil_image, True, "✅ Conversion pdfplumber réussie", "pdfplumber"
        
    except ImportError:
        methods_tried.append("pdfplumber non disponible")
    except Exception as e:
        methods_tried.append(f"pdfplumber échoué : {e}")
    
    # 3. Workflow manuel avec PDF.js
    return None, False, "⚠️ Conversion automatique impossible", "manual", methods_tried

def smart_pdf_interface(pdf_data, filename):
    """Interface intelligente pour PDFs"""
    
    st.markdown("#### 📄 PDF détecté - Traitement intelligent")
    
    # Tentative de conversion
    with st.spinner("🔄 Essai de conversion automatique..."):
        result = convert_pdf_smart(pdf_data)
        
        if len(result) == 4:
            image, success, message, method = result
        else:
            image, success, message, method, methods_tried = result
    
    if success:
        # Conversion réussie !
        st.success(f"{message} ({method})")
        st.image(image, caption=f"PDF converti - {filename}", use_container_width=True)
        
        return {
            'type': 'pdf_converted',
            'image': image,
            'filename': filename,
            'method': method
        }
    
    else:
        # Conversion échouée - Interface manuelle intelligente
        st.warning(message)
        
        with st.expander("🔍 Détails des tentatives"):
            for attempt in methods_tried:
                st.write(f"• {attempt}")
        
        # Interface PDF.js améliorée
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("#### 📖 Visualiseur PDF.js")
            
            pdf_base64 = base64.b64encode(pdf_data).decode()
            iframe_html = f"""
            <div style="border: 2px solid #0066cc; border-radius: 10px; padding: 10px;">
                <iframe 
                    src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}" 
                    width="100%" 
                    height="500" 
                    style="border: none; border-radius: 5px;">
                </iframe>
            </div>
            """
            st.components.v1.html(iframe_html, height=530)
        
        with col2:
            st.markdown("#### 🎯 Guide capture")
            st.markdown("**Étapes simples :**")
            st.markdown("1. 📱 **Windows+Shift+S**")
            st.markdown("2. 🎯 **Sélectionnez l'ECG**")
            st.markdown("3. 💾 **Ctrl+V** pour coller")
            st.markdown("4. 🔄 **Sauvegardez en PNG**")
            st.markdown("5. ⬆️ **Réimportez ici**")
            
            st.markdown("---")
            st.markdown("#### 📥 Solutions")
            
            # Bouton téléchargement
            st.download_button(
                label="📄 Télécharger PDF",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf"
            )
            
            # Installation optionnelle
            st.markdown("#### ⚡ Conversion auto")
            st.code("pip install PyMuPDF", language="bash")
            st.caption("Puis relancez l'application")
        
        return {
            'type': 'pdf_manual',
            'data': pdf_data,
            'filename': filename
        }

# Test de l'interface
def test_smart_pdf():
    """Test de l'interface PDF intelligente"""
    
    st.title("🧠 Test PDF Intelligent")
    st.markdown("Essaie plusieurs méthodes de conversion automatique")
    
    uploaded_file = st.file_uploader("PDF à tester", type=['pdf'])
    
    if uploaded_file:
        pdf_data = uploaded_file.getvalue()
        result = smart_pdf_interface(pdf_data, uploaded_file.name)
        
        st.markdown("---")
        st.json(result)

if __name__ == "__main__":
    st.set_page_config(page_title="PDF Intelligent", layout="wide")
    test_smart_pdf()
