import os
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
import streamlit as st

class PDFExtractor:
    """
    Extracteur PDF robuste utilisant PyMuPDF (fitz)
    Extrait images haute résolution (300 DPI) et texte
    """
    
    def __init__(self):
        self.temp_dir = Path("temp_images")
        self.temp_dir.mkdir(exist_ok=True)
        self.dpi = 300  # Haute résolution pour ECG
        
    def extract_images_and_text(self, pdf_file):
        """
        Extrait les images et le texte d'un PDF
        
        Args:
            pdf_file: BytesIO ou file-like object
            
        Returns:
            tuple: (images_list, text_content)
                images_list: List[dict] avec keys: page, index, image (PIL.Image), width, height
                text_content: str du texte extrait
        """
        images = []
        text_content = ""
        
        try:
            # Lire le PDF depuis le buffer
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Calculer la matrice de transformation pour 300 DPI
            zoom = self.dpi / 72  # 72 DPI par défaut
            mat = fitz.Matrix(zoom, zoom)
            
            # Extraire le texte et les images de chaque page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Extraire le texte
                text_content += page.get_text() + "\n"
                
                # Méthode 1: Extraire les images embarquées
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Convertir en PIL Image
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # Vérifier si c'est une image ECG (taille minimale)
                        if image.width > 400 and image.height > 200:
                            images.append({
                                "page": page_num + 1,
                                "index": img_index,
                                "image": image,
                                "width": image.width,
                                "height": image.height,
                                "source": "embedded"
                            })
                    except Exception as e:
                        print(f"Erreur extraction image embarquée: {e}")
                        continue
                
                # Méthode 2: Si aucune image trouvée, convertir la page entière
                if not image_list:
                    try:
                        # Rendre la page comme image (300 DPI)
                        pix = page.get_pixmap(matrix=mat)
                        img_bytes = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_bytes))
                        
                        images.append({
                            "page": page_num + 1,
                            "index": 0,
                            "image": image,
                            "width": image.width,
                            "height": image.height,
                            "source": "full_page"
                        })
                    except Exception as e:
                        print(f"Erreur conversion page: {e}")
            
            pdf_document.close()
            
        except Exception as e:
            error_msg = f"Erreur lors de l'extraction PDF: {str(e)}"
            print(error_msg)
            if 'st' in globals():
                st.error(error_msg)
            
        return images, text_content
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)