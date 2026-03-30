"""
Visualiseur ECG intelligent - Affichage adaptatif selon le format
L'objectif : montrer l'ECG de façon optimale pour l'annotation
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from pathlib import Path
from PIL import Image
import json

def display_ecg_smart(file_path, case_data=None):
    """
    Affichage intelligent d'ECG selon le format disponible
    Priorité : Lisibilité pour annotation > Format technique
    """
    
    if not os.path.exists(file_path):
        st.error("❌ Fichier ECG introuvable")
        return False
    
    file_ext = os.path.splitext(file_path)[1].lower()
    file_size = os.path.getsize(file_path)
    
    st.markdown(f"### 🫀 ECG - {os.path.basename(file_path)}")
    
    # Informations du fichier
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Format", file_ext.upper())
    with col2:
        st.metric("Taille", f"{file_size//1024} KB")
    with col3:
        if case_data:
            st.metric("ID", case_data.get('case_id', 'N/A'))
    
    # Affichage selon le format
    try:
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return display_ecg_image(file_path)
        
        elif file_ext == '.pdf':
            return display_ecg_pdf(file_path)
        
        elif file_ext in ['.xml', '.hl7']:
            return display_ecg_data(file_path)
        
        else:
            st.warning(f"⚠️ Format {file_ext} non reconnu")
            return display_ecg_fallback(file_path)
            
    except Exception as e:
        st.error(f"❌ Erreur d'affichage : {e}")
        return display_ecg_fallback(file_path)

def display_ecg_image(file_path):
    """Affichage optimisé pour images ECG"""
    
    try:
        # Vérification et optimisation de l'image
        img = Image.open(file_path)
        
        # Affichage direct sans contrôles de zoom
        st.image(img, caption=f"ECG - {os.path.basename(file_path)}", use_container_width=True)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur lecture image : {e}")
        return False

def display_ecg_pdf(file_path):
    """Affichage PDF avec visualiseur amélioré"""
    
    st.markdown("#### 📄 ECG au format PDF")
    
    # Utiliser le visualiseur PDF amélioré
    try:
        from pdf_viewer_improved import improved_pdfjs_viewer
        return improved_pdfjs_viewer(file_path)
    except ImportError:
        # Fallback vers la méthode simple
        return display_basic_pdf(file_path)

def display_basic_pdf(file_path):
    """Affichage PDF basique en cas d'erreur"""
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("#### ⚙️ Options")
        st.info("🌐 Visualiseur PDF basique")
    
    with col1:
        try:
            with open(file_path, "rb") as file:
                pdf_data = file.read()
            
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # HTML simple et robuste
            html_viewer = f"""
            <div style="width: 100%; height: 500px; border: 1px solid #ccc;">
                <iframe 
                    src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}"
                    width="100%" 
                    height="100%"
                    style="border: none;">
                    <p>Impossible d'afficher le PDF. <a href="https://mozilla.github.io/pdf.js/web/viewer.html" target="_blank">Ouvrir PDF.js</a></p>
                </iframe>
            </div>
            """
            
            components.html(html_viewer, height=520)
            st.success("✅ PDF affiché (mode basique)")
            return True
            
        except Exception as e:
            st.error(f"❌ Erreur affichage PDF : {e}")
            
            # Proposer téléchargement
            try:
                with open(file_path, "rb") as file:
                    st.download_button(
                        "📥 Télécharger le PDF",
                        file.read(),
                        file_name=os.path.basename(file_path),
                        mime="application/pdf"
                    )
                st.info("💡 Ouvrez le fichier dans votre lecteur PDF préféré")
                return True
            except:
                return False

def display_ecg_data(file_path):
    """Affichage pour données ECG structurées (XML, HL7)"""
    
    st.markdown("#### 📊 Données ECG structurées")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("#### 📋 Métadonnées")
            
            # Extraction d'infos basiques
            if 'patient' in content.lower():
                st.success("👤 Données patient détectées")
            if 'waveform' in content.lower():
                st.success("📈 Tracé ECG détecté")
            if 'measurement' in content.lower():
                st.success("📏 Mesures disponibles")
        
        with col1:
            # Aperçu du contenu
            st.code(content[:1000] + "..." if len(content) > 1000 else content, language='xml')
        
        st.info("💡 Les données structurées peuvent être traitées pour extraire les tracés")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur lecture données : {e}")
        return False

def display_ecg_fallback(file_path):
    """Affichage de secours pour formats non reconnus"""
    
    st.warning("⚠️ Format non reconnu - Affichage de base")
    
    # Informations fichier
    file_stats = os.stat(file_path)
    st.info(f"""
    **Fichier :** {os.path.basename(file_path)}  
    **Taille :** {file_stats.st_size} bytes  
    **Modifié :** {file_stats.st_mtime}
    """)
    
    # Proposer téléchargement
    try:
        with open(file_path, "rb") as file:
            st.download_button(
                "📥 Télécharger le fichier",
                file.read(),
                file_name=os.path.basename(file_path)
            )
    except Exception as e:
        st.error(f"❌ Impossible de lire le fichier : {e}")
    
    return False

# Interface de test
if __name__ == "__main__":
    st.title("🫀 Visualiseur ECG Intelligent")
    
    st.markdown("""
    **Objectif :** Afficher l'ECG de façon optimale pour l'annotation,  
    quel que soit le format (PNG, PDF, XML, HL7...)
    """)
    
    # Test avec fichiers d'exemple
    test_file = st.file_uploader(
        "Tester avec votre ECG",
        type=['png', 'jpg', 'jpeg', 'pdf', 'xml', 'hl7']
    )
    
    if test_file:
        # Sauvegarder temporairement
        temp_path = f"temp_{test_file.name}"
        with open(temp_path, "wb") as f:
            f.write(test_file.read())
        
        # Afficher
        success = display_ecg_smart(temp_path)
        
        # Nettoyer
        os.remove(temp_path)
        
        if success:
            st.success("✅ ECG affiché avec succès")
        else:
            st.error("❌ Problème d'affichage")
