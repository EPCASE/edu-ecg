"""
🔧 Solution Robuste pour Import PDF ECG
Résout les problèmes d'import PDF avec multiple fallbacks
"""

import streamlit as st
import io
from pathlib import Path
from PIL import Image
import base64

class PDFImporter:
    """Import PDF avec multiples stratégies de fallback"""
    
    def __init__(self):
        self.method_used = None
        self.supported_methods = []
        self._check_available_methods()
    
    def _check_available_methods(self):
        """Vérifie quelles bibliothèques PDF sont disponibles"""
        
        # Méthode 1: PyMuPDF (fitz) - Le plus rapide
        try:
            import fitz
            self.supported_methods.append('pymupdf')
        except ImportError:
            pass
        
        # Méthode 2: pdf2image - Populaire
        try:
            from pdf2image import convert_from_bytes
            self.supported_methods.append('pdf2image')
        except ImportError:
            pass
        
        # Méthode 3: PyPDF2 - Basique (déjà dans requirements)
        try:
            import PyPDF2
            self.supported_methods.append('pypdf2')
        except ImportError:
            pass
        
        # Méthode 4: PDF.js (JavaScript dans navigateur) - Toujours disponible
        self.supported_methods.append('pdfjs')
    
    def import_pdf(self, uploaded_file):
        """
        Import PDF avec fallback automatique
        
        Returns:
            dict: {
                'success': bool,
                'images': list[PIL.Image],
                'text': str,
                'method': str,
                'error': str (si échec)
            }
        """
        
        result = {
            'success': False,
            'images': [],
            'text': '',
            'method': None,
            'error': None
        }
        
        # Essayer les méthodes dans l'ordre de préférence
        for method in self.supported_methods:
            try:
                if method == 'pymupdf':
                    result = self._import_with_pymupdf(uploaded_file)
                elif method == 'pdf2image':
                    result = self._import_with_pdf2image(uploaded_file)
                elif method == 'pypdf2':
                    result = self._import_with_pypdf2(uploaded_file)
                elif method == 'pdfjs':
                    result = self._import_with_pdfjs(uploaded_file)
                
                if result['success']:
                    result['method'] = method
                    self.method_used = method
                    return result
                    
            except Exception as e:
                result['error'] = f"{method}: {str(e)}"
                continue
        
        # Si toutes les méthodes échouent
        result['error'] = f"Toutes les méthodes ont échoué. Disponibles: {', '.join(self.supported_methods)}"
        return result
    
    def _import_with_pymupdf(self, uploaded_file):
        """Méthode 1: PyMuPDF (fitz) - Rapide et robuste"""
        import fitz
        
        result = {'success': False, 'images': [], 'text': ''}
        
        # Lire le fichier en bytes
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        
        # Ouvrir avec fitz
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Extraire chaque page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Extraire le texte
            result['text'] += page.get_text() + "\n"
            
            # Convertir la page en image (haute résolution pour ECG)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            result['images'].append({
                'page': page_num + 1,
                'image': img,
                'width': img.width,
                'height': img.height
            })
        
        pdf_document.close()
        result['success'] = True
        return result
    
    def _import_with_pdf2image(self, uploaded_file):
        """Méthode 2: pdf2image - Nécessite poppler"""
        from pdf2image import convert_from_bytes
        
        result = {'success': False, 'images': [], 'text': ''}
        
        # Lire le fichier
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        
        # Convertir en images (300 DPI pour ECG)
        images = convert_from_bytes(pdf_bytes, dpi=300)
        
        for idx, img in enumerate(images):
            result['images'].append({
                'page': idx + 1,
                'image': img,
                'width': img.width,
                'height': img.height
            })
        
        result['success'] = True
        result['text'] = "(Extraction texte non disponible avec pdf2image)"
        return result
    
    def _import_with_pypdf2(self, uploaded_file):
        """Méthode 3: PyPDF2 - Texte uniquement, pas d'images"""
        import PyPDF2
        
        result = {'success': False, 'images': [], 'text': ''}
        
        # Lire le fichier
        uploaded_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        
        # Extraire le texte de toutes les pages
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            result['text'] += page.extract_text() + "\n"
        
        # PyPDF2 ne peut pas extraire d'images directement
        # On affiche un placeholder
        result['success'] = True
        st.warning("⚠️ PyPDF2 utilisé: texte extrait mais images non disponibles. Installez `PyMuPDF` ou `pdf2image` pour extraction d'images.")
        return result
    
    def _import_with_pdfjs(self, uploaded_file):
        """Méthode 4: PDF.js - Affichage dans le navigateur (toujours disponible)"""
        
        result = {'success': False, 'images': [], 'text': ''}
        
        # Lire le fichier et encoder en base64
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Créer un viewer PDF.js embarqué
        st.markdown("### 📄 Aperçu PDF (PDF.js)")
        st.info("💡 Le PDF est affiché ci-dessous. Faites un clic droit > Enregistrer l'image pour extraire les ECG.")
        
        # Embed PDF.js viewer
        pdf_display = f'''
        <iframe 
            src="data:application/pdf;base64,{pdf_base64}" 
            width="100%" 
            height="800px" 
            type="application/pdf"
            style="border: 2px solid #ddd; border-radius: 8px;">
        </iframe>
        '''
        
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        result['success'] = True
        result['text'] = "(Visualisation PDF uniquement - extraction texte non disponible)"
        
        # Ajouter bouton de téléchargement
        st.download_button(
            label="📥 Télécharger le PDF",
            data=pdf_bytes,
            file_name=uploaded_file.name,
            mime="application/pdf"
        )
        
        return result
    
    def get_diagnostic_info(self):
        """Retourne des informations de diagnostic"""
        return {
            'supported_methods': self.supported_methods,
            'method_used': self.method_used,
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self):
        """Recommandations d'installation selon les méthodes disponibles"""
        recommendations = []
        
        if 'pymupdf' not in self.supported_methods:
            recommendations.append({
                'package': 'PyMuPDF',
                'install': 'pip install PyMuPDF',
                'reason': 'Méthode la plus rapide et robuste pour extraction PDF',
                'priority': 'Haute'
            })
        
        if 'pdf2image' not in self.supported_methods:
            recommendations.append({
                'package': 'pdf2image',
                'install': 'pip install pdf2image (+ installer Poppler)',
                'reason': 'Alternative populaire pour conversion PDF → images',
                'priority': 'Moyenne'
            })
        
        return recommendations


def show_pdf_diagnostic():
    """Affiche un diagnostic du système PDF"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Diagnostic PDF")
    
    importer = PDFImporter()
    info = importer.get_diagnostic_info()
    
    st.sidebar.write(f"**Méthodes disponibles:** {len(info['supported_methods'])}")
    for method in info['supported_methods']:
        st.sidebar.success(f"✅ {method}")
    
    if info['recommendations']:
        with st.sidebar.expander("💡 Recommandations"):
            for rec in info['recommendations']:
                st.write(f"**{rec['package']}** (Priorité: {rec['priority']})")
                st.code(rec['install'])
                st.caption(rec['reason'])


def enhanced_pdf_import_interface():
    """Interface améliorée d'import PDF avec diagnostics"""
    
    st.title("📤 Import ECG PDF - Version Robuste")
    
    # Afficher diagnostic
    show_pdf_diagnostic()
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Choisir un fichier PDF ECG",
        type=['pdf'],
        help="Import PDF avec fallback automatique"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Fichier uploadé: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        # Créer l'importer
        importer = PDFImporter()
        
        # Afficher les méthodes disponibles
        with st.expander("🔍 Méthodes d'import disponibles"):
            for method in importer.supported_methods:
                st.info(f"✓ {method}")
        
        # Bouton d'import
        if st.button("🚀 Importer le PDF", type="primary"):
            with st.spinner("Import en cours..."):
                result = importer.import_pdf(uploaded_file)
            
            if result['success']:
                st.success(f"✅ Import réussi avec **{result['method']}** !")
                
                # Afficher les images extraites
                if result['images']:
                    st.subheader(f"📊 {len(result['images'])} image(s) extraite(s)")
                    
                    for idx, img_data in enumerate(result['images']):
                        st.write(f"**Page {img_data['page']}** - {img_data['width']}x{img_data['height']} px")
                        st.image(img_data['image'], use_container_width=True)
                
                # Afficher le texte extrait
                if result['text'].strip():
                    with st.expander("📝 Texte extrait"):
                        st.text(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
                
                # Sauvegarder dans session state
                st.session_state.imported_pdf = result
                st.session_state.uploaded_file = uploaded_file
                
            else:
                st.error(f"❌ Échec de l'import: {result['error']}")
                
                # Afficher les recommandations
                info = importer.get_diagnostic_info()
                if info['recommendations']:
                    st.warning("💡 Installez les packages suivants pour améliorer l'import:")
                    for rec in info['recommendations']:
                        st.code(rec['install'])


if __name__ == "__main__":
    enhanced_pdf_import_interface()
