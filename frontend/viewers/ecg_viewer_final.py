"""
Visualiseur ECG intelligent - Version finale robuste
Solution complète du problème "pas d'affichage pdf.js"
"""

import streamlit as st
import os
from pathlib import Path
from PIL import Image
import base64

# Import du visualiseur PDF robuste
try:
    from .pdf_viewer_robust import robust_pdfjs_viewer
except ImportError:
    try:
        from pdf_viewer_robust import robust_pdfjs_viewer
    except ImportError:
        def robust_pdfjs_viewer(pdf_path, height=600, max_size_mb=2):
            st.error("❌ Module PDF robuste non trouvé")
            return False

def display_ecg_smart(file_path, title="ECG"):
    """
    Affichage intelligent d'ECG selon le format détecté
    SOLUTION FINALE pour le problème d'affichage PDF.js
    """
    
    if not file_path or not Path(file_path).exists():
        st.error(f"❌ Fichier introuvable : {file_path}")
        return False
    
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    st.subheader(f"📊 {title}")
    
    # Indication du format avec icône
    format_info = {
        '.pdf': ('📄', 'PDF'),
        '.png': ('🖼️', 'Image PNG'), 
        '.jpg': ('🖼️', 'Image JPEG'),
        '.jpeg': ('🖼️', 'Image JPEG'),
        '.xml': ('📋', 'XML')
    }
    
    icon, format_name = format_info.get(file_extension, ('📁', 'Inconnu'))
    st.info(f"{icon} **Format :** {format_name}")
    
    # Affichage selon le format
    if file_extension == '.pdf':
        return _display_pdf_final(file_path)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        return _display_image_final(file_path)
    elif file_extension == '.xml':
        return _display_xml_final(file_path)
    else:
        return _display_unknown_final(file_path)

def _display_pdf_final(pdf_path):
    """
    Affichage PDF final avec toutes les solutions robustes
    """
    try:
        # Utiliser le visualiseur ultra-robuste
        return robust_pdfjs_viewer(str(pdf_path), height=600, max_size_mb=2)
    except Exception as e:
        st.error(f"❌ Erreur visualiseur robuste : {e}")
        return _pdf_emergency_mode(pdf_path)

def _pdf_emergency_mode(pdf_path):
    """
    Mode d'urgence PDF si tout échoue
    """
    st.warning("🚨 Mode d'urgence PDF activé")
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        file_size_mb = len(pdf_data) / (1024 * 1024)
        st.write(f"**Taille :** {file_size_mb:.1f} MB")
        
        # Solution 1 : Téléchargement
        st.download_button(
            label="📥 Télécharger PDF",
            data=pdf_data,
            file_name=pdf_path.name,
            mime="application/pdf",
            use_container_width=True
        )
        
        # Solution 2 : Lien PDF.js
        st.markdown("**[🌐 Ouvrir PDF.js externe](https://mozilla.github.io/pdf.js/web/viewer.html)**")
        
        # Solution 3 : Instructions
        with st.expander("📋 Instructions d'utilisation"):
            st.markdown("""
            1. Cliquez sur "Télécharger PDF" ci-dessus
            2. Cliquez sur "Ouvrir PDF.js externe"  
            3. Dans PDF.js, cliquez sur "Ouvrir un fichier"
            4. Sélectionnez le PDF téléchargé
            """)
        
        st.success("✅ Solutions alternatives disponibles")
        return True
        
    except Exception as e:
        st.error(f"❌ Mode d'urgence échoué : {e}")
        return False

def _display_image_final(image_path):
    """
    Affichage image final optimisé
    """
    try:
        image = Image.open(image_path)
        
        # Interface utilisateur
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.markdown("#### 📊 Infos")
            st.metric("Dimensions", f"{image.size[0]}×{image.size[1]}")
            
            file_size = os.path.getsize(image_path) / 1024
            st.metric("Taille", f"{file_size:.1f} KB")
            
            # Contrôles
            zoom = st.slider("🔍 Zoom", 25, 200, 100, 25)
        
        with col1:
            # Affichage avec zoom
            if zoom != 100:
                width = int(image.size[0] * zoom / 100)
                st.image(image, width=width, caption=f"ECG - {image_path.name}", use_container_width=False)
            else:
                st.image(image, use_container_width=True, caption=f"ECG - {image_path.name}")
        
        # Téléchargement
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        st.download_button(
            label="📥 Télécharger image",
            data=image_data,
            file_name=image_path.name,
            mime=f"image/{image_path.suffix[1:]}",
            use_container_width=True
        )
        
        st.success("✅ Image ECG affichée")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur affichage image : {e}")
        return False

def _display_xml_final(xml_path):
    """
    Affichage XML final avec analyse
    """
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Détection du type XML
        xml_type = "XML Générique"
        if 'HL7' in xml_content or 'ClinicalDocument' in xml_content:
            xml_type = "HL7 CDA"
        elif 'FDA-XML' in xml_content:
            xml_type = "FDA XML"
        elif 'ECG' in xml_content or 'waveform' in xml_content:
            xml_type = "XML ECG"
        
        st.success(f"✅ Type détecté : {xml_type}")
        
        # Informations de base
        lines = xml_content.count('\n')
        size_kb = len(xml_content.encode('utf-8')) / 1024
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Lignes", lines)
        with col2:
            st.metric("Taille", f"{size_kb:.1f} KB")
        
        # Contenu
        with st.expander("📄 Contenu XML", expanded=False):
            st.code(xml_content[:2000], language='xml')
            if len(xml_content) > 2000:
                st.caption("... (contenu tronqué à 2000 caractères)")
        
        # Téléchargement
        st.download_button(
            label="📥 Télécharger XML",
            data=xml_content.encode('utf-8'),
            file_name=xml_path.name,
            mime="application/xml",
            use_container_width=True
        )
        
        st.success("✅ Fichier XML traité")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur lecture XML : {e}")
        return False

def _display_unknown_final(file_path):
    """
    Gestion format inconnu
    """
    st.warning(f"⚠️ Format non reconnu : {file_path.suffix}")
    
    try:
        file_size = os.path.getsize(file_path) / 1024
        st.metric("Taille", f"{file_size:.1f} KB")
        
        # Tentative lecture texte
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                preview = f.read(500)
            
            with st.expander("👀 Aperçu"):
                st.text(preview)
                
        except:
            st.info("💡 Fichier binaire - aperçu non disponible")
        
        # Téléchargement
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        st.download_button(
            label="📥 Télécharger fichier",
            data=file_data,
            file_name=file_path.name,
            use_container_width=True
        )
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        return False

# Test du module
if __name__ == "__main__":
    st.set_page_config(page_title="Test ECG Smart Final", layout="wide")
    st.title("🧠 Visualiseur ECG Intelligent - Version Finale")
    
    uploaded_file = st.file_uploader(
        "Choisir un fichier ECG", 
        type=['pdf', 'png', 'jpg', 'jpeg', 'xml']
    )
    
    if uploaded_file:
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        
        display_ecg_smart(temp_path, "Test ECG")
        
        os.remove(temp_path)
