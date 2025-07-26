import os
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

class PDFExtractor:
    def __init__(self):
        self.temp_dir = Path("temp_images")
        self.temp_dir.mkdir(exist_ok=True)
        
    def extract_images_and_text(self, pdf_file):
        """Extrait les images et le texte d'un PDF"""
        images = []
        text_content = ""
        
        try:
            # Lire le PDF depuis le buffer
            pdf_file.seek(0)
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
            
            # Extraire le texte et les images
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Extraire le texte
                text_content += page.get_text() + "\n"
                
                # Extraire les images
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
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
                            "image": image
                        })
            
            pdf_document.close()
            
        except Exception as e:
            st.error(f"Erreur lors de l'extraction: {str(e)}")
            
        return images, text_content
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)