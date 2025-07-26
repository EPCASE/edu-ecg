#!/usr/bin/env python3
"""
Alternative 2 : pdfplumber pour extraction PDF
Installation : pip install pdfplumber
"""

import streamlit as st
from PIL import Image, ImageDraw
import io

def convert_pdf_with_pdfplumber(pdf_data):
    """Convertir PDF avec pdfplumber"""
    try:
        import pdfplumber
        from io import BytesIO
        
        # Ouvrir le PDF
        with pdfplumber.open(BytesIO(pdf_data)) as pdf:
            page = pdf.pages[0]  # Première page
            
            # Extraire comme image
            image = page.to_image(resolution=200)
            pil_image = image.original
            
            return pil_image, True, "Conversion réussie avec pdfplumber"
            
    except ImportError:
        return None, False, "pdfplumber non installé"
    except Exception as e:
        return None, False, f"Erreur pdfplumber : {e}"

def test_pdfplumber():
    """Test pdfplumber"""
    st.header("🔧 Test pdfplumber")
    
    uploaded_file = st.file_uploader("PDF à tester", type=['pdf'])
    
    if uploaded_file:
        pdf_data = uploaded_file.getvalue()
        
        with st.spinner("Conversion en cours..."):
            image, success, message = convert_pdf_with_pdfplumber(pdf_data)
        
        if success:
            st.success(message)
            st.image(image, caption="PDF converti", use_container_width=True)
        else:
            st.error(message)
            
            if "non installé" in message:
                st.info("💡 Installation : `pip install pdfplumber`")

if __name__ == "__main__":
    test_pdfplumber()
