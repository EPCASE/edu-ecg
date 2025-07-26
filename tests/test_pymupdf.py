#!/usr/bin/env python3
"""
Alternative à Poppler : PyMuPDF (fitz) pour conversion PDF
Installation simple : pip install PyMuPDF
"""

import streamlit as st
from PIL import Image
import io

def convert_pdf_with_pymupdf(pdf_data):
    """Convertir PDF en image avec PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        
        # Ouvrir le PDF depuis les données
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Convertir la première page en image
        page = pdf_document[0]  # Première page
        
        # Render en image (haute résolution)
        mat = fitz.Matrix(2.0, 2.0)  # Zoom 2x pour meilleure qualité
        pix = page.get_pixmap(matrix=mat)
        
        # Convertir en PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        pdf_document.close()
        return image, True, "Conversion réussie avec PyMuPDF"
        
    except ImportError:
        return None, False, "PyMuPDF non installé"
    except Exception as e:
        return None, False, f"Erreur PyMuPDF : {e}"

def test_pymupdf():
    """Test PyMuPDF"""
    st.header("🔧 Test PyMuPDF")
    
    uploaded_file = st.file_uploader("PDF à tester", type=['pdf'])
    
    if uploaded_file:
        pdf_data = uploaded_file.getvalue()
        
        with st.spinner("Conversion en cours..."):
            image, success, message = convert_pdf_with_pymupdf(pdf_data)
        
        if success:
            st.success(message)
            st.image(image, caption="PDF converti", use_container_width=True)
        else:
            st.error(message)
            
            if "non installé" in message:
                st.info("💡 Installation : `pip install PyMuPDF`")

if __name__ == "__main__":
    test_pymupdf()
