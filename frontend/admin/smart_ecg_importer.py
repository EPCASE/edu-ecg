"""
Outil d'import ECG intelligent avec recadrage et export unifié
Solution pour standardiser tous les formats vers un format commun
"""

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw
import base64
import json
import os
from pathlib import Path
import io
import uuid
from datetime import datetime

def smart_ecg_importer():
    """
    Interface d'import ECG intelligent avec recadrage et standardisation
    """
    
    st.header("📥 Import ECG Intelligent - Avec Recadrage")
    st.markdown("**Importez n'importe quel format → Recadrez l'ECG → Exportez vers format standard**")
    
    # Indicateur de progression
    progress_col1, progress_col2, progress_col3 = st.columns(3)
    
    with progress_col1:
        if 'uploaded_file_data' not in st.session_state:
            st.markdown("🔄 **1. Upload** ← Vous êtes ici")
        else:
            st.markdown("✅ **1. Upload** (Terminé)")
    
    with progress_col2:
        if 'uploaded_file_data' in st.session_state and 'cropped_ecg' not in st.session_state:
            st.markdown("🔄 **2. Recadrage** ← Étape suivante")
        elif 'cropped_ecg' in st.session_state:
            st.markdown("✅ **2. Recadrage** (Terminé)")
        else:
            st.markdown("⏳ **2. Recadrage**")
    
    with progress_col3:
        if 'cropped_ecg' in st.session_state:
            st.markdown("🔄 **3. Export** ← Étape finale")
        else:
            st.markdown("⏳ **3. Export**")
    
    st.markdown("---")
    
    # Interface à onglets
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "✂️ Recadrage", "💾 Export"])
    
    with tab1:
        _interface_upload()
    
    with tab2:
        if 'uploaded_file_data' in st.session_state:
            st.success("📁 Fichier chargé ! Interface de recadrage disponible ci-dessous :")
            _interface_recadrage()
        else:
            st.info("💡 Uploadez d'abord un fichier dans l'onglet 'Upload'")
    
    with tab3:
        if 'cropped_ecg' in st.session_state:
            st.success("✂️ ECG recadré ! Interface d'export disponible ci-dessous :")
            _interface_export()
        else:
            st.info("💡 Recadrez d'abord l'ECG dans l'onglet 'Recadrage'")

def _interface_upload():
    """Interface d'upload de fichiers"""
    
    st.subheader("📤 Upload de fichier ECG")
    
    # Upload de fichier
    uploaded_file = st.file_uploader(
        "Choisissez votre fichier ECG",
        type=['pdf', 'png', 'jpg', 'jpeg', 'xml'],
        help="Formats supportés : PDF, PNG, JPG, JPEG, XML"
    )
    
    if uploaded_file is not None:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        # Affichage des informations du fichier
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("#### 📊 Informations")
            st.write(f"**Nom :** {uploaded_file.name}")
            st.write(f"**Type :** {file_extension.upper()}")
            st.write(f"**Taille :** {len(uploaded_file.getvalue()) / 1024:.1f} KB")
        
        with col1:
            # Traitement selon le format
            if file_extension == '.pdf':
                success = _traiter_pdf(uploaded_file)
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                success = _traiter_image(uploaded_file)
            elif file_extension == '.xml':
                success = _traiter_xml(uploaded_file)
            else:
                st.error(f"❌ Format {file_extension} non supporté")
                success = False
            
            if success:
                st.success("✅ Fichier traité avec succès !")
                
                # Notification pour passer au recadrage
                st.markdown("---")
                st.info("🎯 **Étape suivante :** Cliquez sur l'onglet **'✂️ Recadrage'** ci-dessus pour recadrer votre ECG")
                
                # Bouton pour forcer le rechargement de l'interface
                if st.button("🔄 Actualiser l'interface", type="secondary"):
                    st.rerun()

def _traiter_pdf(uploaded_file):
    """Traite les fichiers PDF"""
    
    st.markdown("#### 📄 PDF détecté")
    
    # Sauvegarder temporairement
    temp_pdf_path = f"temp_{uploaded_file.name}"
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    try:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        if file_size_mb > 2:
            # PDF volumineux - proposer téléchargement pour traitement externe
            st.warning(f"⚠️ PDF volumineux ({file_size_mb:.1f} MB)")
            st.info("💡 **Solution recommandée :** Convertissez le PDF en image avant import")
            
            st.download_button(
                label="📥 Télécharger PDF",
                data=uploaded_file.getvalue(),
                file_name=uploaded_file.name,
                mime="application/pdf"
            )
            
            st.markdown("**Instructions :**")
            st.markdown("1. Ouvrez le PDF téléchargé")
            st.markdown("2. Faites une capture d'écran de l'ECG (Windows+Shift+S)")
            st.markdown("3. Sauvegardez en PNG/JPG")
            st.markdown("4. Réimportez l'image ici")
            
            # Interface PDF.js pour visualisation
            st.markdown("---")
            st.markdown("#### 📖 Visualisation PDF (pour capture)")
            
            # Créer un viewer PDF.js simple
            pdf_base64 = base64.b64encode(uploaded_file.getvalue()).decode()
            
            iframe_html = f"""
            <div style="border: 2px dashed #ccc; padding: 20px; text-align: center;">
                <p><strong>📱 Pour capturer l'ECG :</strong></p>
                <p>1. Cliquez sur le lien ci-dessous pour ouvrir le PDF</p>
                <p>2. Utilisez Windows+Shift+S pour capturer l'ECG</p>
                <p>3. Sauvegardez et réimportez l'image</p>
                <br>
                <a href="data:application/pdf;base64,{pdf_base64}" target="_blank" 
                   style="background: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                   🔗 Ouvrir PDF dans un nouvel onglet
                </a>
            </div>
            """
            
            st.components.v1.html(iframe_html, height=200)
            
            # Stockage pour l'étape suivante
            st.session_state.uploaded_file_data = {
                'type': 'pdf_large',
                'filename': uploaded_file.name,
                'size_mb': file_size_mb,
                'data': uploaded_file.getvalue()
            }
            
            return True
            
        else:
            # PDF de taille raisonnable - proposer visualisation et capture
            st.info("📄 PDF détecté - Visualisation et capture recommandée")
            
            # Interface de visualisation et capture
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### � Visualiseur PDF")
                
                # Créer un viewer PDF.js
                pdf_base64 = base64.b64encode(uploaded_file.getvalue()).decode()
                
                # Essayer d'abord un iframe PDF.js
                iframe_html = f"""
                <iframe 
                    src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}" 
                    width="100%" 
                    height="500" 
                    style="border: 1px solid #ccc;">
                </iframe>
                """
                
                st.components.v1.html(iframe_html, height=520)
            
            with col2:
                st.markdown("#### 🎯 Instructions de capture")
                st.markdown("**1.** Visualisez l'ECG dans le viewer à gauche")
                st.markdown("**2.** Utilisez **Windows+Shift+S** pour capturer")
                st.markdown("**3.** Sélectionnez uniquement la zone ECG")
                st.markdown("**4.** Sauvegardez l'image (PNG/JPG)")
                st.markdown("**5.** Réimportez l'image capturée")
                
                st.markdown("---")
                st.markdown("#### 📥 Alternative")
                st.download_button(
                    label="📄 Télécharger PDF",
                    data=uploaded_file.getvalue(),
                    file_name=uploaded_file.name,
                    mime="application/pdf"
                )
            
            # Essayer conversion automatique si pdf2image disponible
            conversion_attempted = False
            try:
                from pdf2image import convert_from_path
                
                st.markdown("---")
                st.info("🔄 Tentative de conversion automatique...")
                
                # Convertir la première page
                images = convert_from_path(temp_pdf_path, first_page=1, last_page=1, dpi=200)
                
                if images:
                    image = images[0]
                    
                    st.success("✅ Conversion automatique réussie !")
                    st.image(image, caption="PDF converti en image", use_container_width=True)
                    
                    # Stocker pour le recadrage
                    st.session_state.uploaded_file_data = {
                        'type': 'pdf_converted',
                        'filename': uploaded_file.name,
                        'image': image,
                        'original_data': uploaded_file.getvalue()
                    }
                    
                    conversion_attempted = True
                    
            except ImportError:
                # pdf2image non disponible - c'est normal
                pass
            except Exception as e:
                st.warning(f"⚠️ Conversion automatique échouée : {e}")
            
            # Si pas de conversion automatique, proposer workflow manuel
            if not conversion_attempted:
                st.session_state.uploaded_file_data = {
                    'type': 'pdf_manual',
                    'filename': uploaded_file.name,
                    'data': uploaded_file.getvalue(),
                    'size_mb': file_size_mb
                }
            
            return True
                
    except Exception as e:
        st.error(f"❌ Erreur traitement PDF : {e}")
        return False
    
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

def _traiter_image(uploaded_file):
    """Traite les fichiers image"""
    
    st.markdown("#### 🖼️ Image détectée")
    
    try:
        # Charger l'image
        image = Image.open(uploaded_file)
        
        # Affichage de l'image
        st.image(image, caption=f"Image ECG - {uploaded_file.name}", use_container_width=True)
        
        # Informations détaillées
        st.write(f"**Dimensions :** {image.size[0]} × {image.size[1]} pixels")
        st.write(f"**Mode :** {image.mode}")
        
        # Stockage pour le recadrage
        st.session_state.uploaded_file_data = {
            'type': 'image',
            'filename': uploaded_file.name,
            'image': image,
            'original_data': uploaded_file.getvalue()
        }
        
        st.success("✅ Image chargée avec succès !")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur lecture image : {e}")
        return False

def _traiter_xml(uploaded_file):
    """Traite les fichiers XML"""
    
    st.markdown("#### 📋 XML détecté")
    
    try:
        # Lire le contenu XML
        xml_content = uploaded_file.getvalue().decode('utf-8')
        
        # Affichage du contenu (aperçu)
        with st.expander("📄 Aperçu du contenu XML"):
            st.code(xml_content[:1000], language='xml')
            if len(xml_content) > 1000:
                st.caption("... (contenu tronqué)")
        
        # Analyse du type XML
        xml_type = "XML Générique"
        if 'HL7' in xml_content:
            xml_type = "HL7 CDA"
        elif 'FDA-XML' in xml_content:
            xml_type = "FDA XML"
        elif 'waveform' in xml_content.lower():
            xml_type = "XML ECG"
        
        st.info(f"💡 Type détecté : {xml_type}")
        
        # Stockage pour traitement
        st.session_state.uploaded_file_data = {
            'type': 'xml',
            'filename': uploaded_file.name,
            'content': xml_content,
            'xml_type': xml_type,
            'original_data': uploaded_file.getvalue()
        }
        
        st.success("✅ XML analysé avec succès !")
        st.info("💡 Les fichiers XML seront traités comme métadonnées")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur lecture XML : {e}")
        return False

def _interface_recadrage():
    """Interface de recadrage de l'ECG"""
    
    st.subheader("✂️ Recadrage de l'ECG")
    
    file_data = st.session_state.uploaded_file_data
    
    if file_data['type'] in ['image', 'pdf_converted']:
        _recadrage_interactif(file_data['image'])
    elif file_data['type'] == 'pdf_large':
        st.warning("⚠️ PDF volumineux - Capture d'écran requise")
        st.info("💡 Suivez les instructions dans l'onglet Upload pour capturer l'ECG")
        
        # Rappel des instructions
        st.markdown("""
        ### 📷 Comment capturer l'ECG :
        1. **Ouvrez le PDF** (lien dans l'onglet Upload)
        2. **Capturez l'écran** : Windows+Shift+S
        3. **Sélectionnez la zone ECG** uniquement
        4. **Sauvegardez** l'image (PNG/JPG recommandé)
        5. **Revenez à l'onglet Upload** et importez l'image capturée
        """)
        
    elif file_data['type'] == 'pdf_manual':
        st.info("� PDF en attente de capture")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📖 Rappel - Visualiseur PDF")
            
            # Recréer le viewer PDF.js
            pdf_base64 = base64.b64encode(file_data['data']).decode()
            
            iframe_html = f"""
            <iframe 
                src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}" 
                width="100%" 
                height="400" 
                style="border: 1px solid #ccc;">
            </iframe>
            """
            
            st.components.v1.html(iframe_html, height=420)
        
        with col2:
            st.markdown("#### 🎯 Guide de capture")
            st.markdown("**Étapes à suivre :**")
            st.markdown("1. 👀 Visualisez l'ECG à gauche")
            st.markdown("2. ⌨️ **Windows+Shift+S**")
            st.markdown("3. 🎯 Sélectionnez zone ECG")
            st.markdown("4. 💾 Sauvegardez l'image")
            st.markdown("5. 🔄 Réimportez dans Upload")
            
            st.markdown("---")
            st.markdown("#### ⚡ Raccourci")
            st.markdown("Au lieu de capturer, vous pouvez :")
            
            if st.button("📁 Importer image directement", type="secondary"):
                st.info("💡 Utilisez l'onglet Upload pour importer votre image capturée")
        
        st.markdown("---")
        st.warning("🔄 **Workflow recommandé :** Capturez l'ECG puis revenez à l'onglet Upload pour importer l'image")
    elif file_data['type'] == 'xml':
        st.info("📋 Fichier XML - Pas de recadrage nécessaire")
        st.markdown("Les données XML seront utilisées comme métadonnées")
        # Passer directement à l'export
        st.session_state.cropped_ecg = {
            'type': 'xml',
            'data': file_data
        }

def _recadrage_interactif(image):
    """Interface de recadrage interactif"""
    
    st.markdown("#### 🎯 Sélectionnez la zone ECG à conserver")
    
    # Redimensionner l'image pour l'affichage si trop grande
    display_image = image.copy()
    max_display_width = 800
    
    if display_image.width > max_display_width:
        ratio = max_display_width / display_image.width
        new_height = int(display_image.height * ratio)
        display_image = display_image.resize((max_display_width, new_height), Image.Resampling.LANCZOS)
    
    # Contrôles de recadrage
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("#### ⚙️ Contrôles")
        
        # Coordonnées de recadrage
        x1 = st.slider("X début", 0, display_image.width, 0)
        y1 = st.slider("Y début", 0, display_image.height, 0)
        x2 = st.slider("X fin", x1, display_image.width, display_image.width)
        y2 = st.slider("Y fin", y1, display_image.height, display_image.height)
        
        # Présets courants
        st.markdown("#### 📐 Présets")
        if st.button("🫀 ECG Standard"):
            # Recadrage typique ECG (centre de l'image)
            margin = 50
            st.session_state.crop_coords = (
                margin, margin, 
                display_image.width - margin, 
                display_image.height - margin
            )
            st.rerun()
        
        if st.button("📄 Page complète"):
            st.session_state.crop_coords = (0, 0, display_image.width, display_image.height)
            st.rerun()
    
    with col1:
        # Image avec zone de recadrage
        cropped_preview = display_image.crop((x1, y1, x2, y2))
        
        st.markdown("**🖼️ Image originale :**")
        st.image(display_image, use_container_width=True)
        
        st.markdown("**✂️ Aperçu recadré :**")
        st.image(cropped_preview, use_container_width=True)
        
        # Valider le recadrage
        if st.button("✅ Valider ce recadrage", type="primary"):
            # Calculer les coordonnées sur l'image originale
            scale_x = image.width / display_image.width
            scale_y = image.height / display_image.height
            
            real_x1 = int(x1 * scale_x)
            real_y1 = int(y1 * scale_y)
            real_x2 = int(x2 * scale_x)
            real_y2 = int(y2 * scale_y)
            
            # Recadrer l'image originale
            cropped_original = image.crop((real_x1, real_y1, real_x2, real_y2))
            
            # Stocker le résultat
            st.session_state.cropped_ecg = {
                'type': 'image',
                'image': cropped_original,
                'coordinates': (real_x1, real_y1, real_x2, real_y2),
                'original_filename': st.session_state.uploaded_file_data['filename']
            }
            
            st.success("✅ Recadrage validé ! Passez à l'export.")
            st.balloons()

def _interface_export():
    """Interface d'export vers format standard"""
    
    st.subheader("💾 Export vers Format Standard")
    
    cropped_data = st.session_state.cropped_ecg
    
    # Informations sur l'ECG recadré
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("#### 📊 Métadonnées")
        
        # Informations automatiques
        case_id = st.text_input("ID du cas", value=f"ecg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
        
        filename = st.text_input("Nom du fichier", value=f"{case_id}.png")
        
        # Métadonnées cliniques
        st.markdown("#### 🏥 Contexte clinique")
        age = st.number_input("Âge patient", min_value=0, max_value=120, value=65)
        sexe = st.selectbox("Sexe", ["M", "F", "Non spécifié"])
        contexte = st.text_area("Contexte clinique", placeholder="Ex: Douleur thoracique, dyspnée...")
        diagnostic = st.text_area("Diagnostic", placeholder="Ex: Rythme sinusal, BBD...")
    
    with col1:
        if cropped_data['type'] == 'image':
            # Affichage de l'image recadrée
            st.markdown("#### 📄 ECG final")
            st.image(cropped_data['image'], caption="ECG recadré prêt pour export", use_container_width=True)
            
            # Informations techniques
            st.write(f"**Dimensions :** {cropped_data['image'].size[0]} × {cropped_data['image'].size[1]} pixels")
        
        elif cropped_data['type'] == 'xml':
            st.markdown("#### 📋 Données XML")
            st.info("Fichier XML traité comme métadonnées")
    
    # Bouton d'export
    st.markdown("---")
    
    if st.button("🚀 Exporter vers la liseuse", type="primary"):
        success = _executer_export(case_id, filename, cropped_data, {
            'age': age,
            'sexe': sexe,
            'contexte': contexte,
            'diagnostic': diagnostic
        })
        
        if success:
            st.success("🎉 ECG exporté avec succès vers la liseuse !")
            st.balloons()
            
            # Proposer de continuer
            if st.button("➕ Importer un autre ECG"):
                # Nettoyer la session
                for key in ['uploaded_file_data', 'cropped_ecg']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

def _executer_export(case_id, filename, cropped_data, metadata):
    """Exécute l'export vers le format standard"""
    
    try:
        # Créer le répertoire de destination
        export_dir = Path("data/ecg_cases") / case_id
        export_dir.mkdir(parents=True, exist_ok=True)
        
        if cropped_data['type'] == 'image':
            # Sauvegarder l'image
            image_path = export_dir / filename
            cropped_data['image'].save(image_path, 'PNG', optimize=True)
            
            file_path = str(image_path)
            
        elif cropped_data['type'] == 'xml':
            # Sauvegarder le XML
            xml_path = export_dir / f"{case_id}.xml"
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(cropped_data['data']['content'])
            
            file_path = str(xml_path)
        
        # Créer les métadonnées JSON
        metadata_json = {
            'case_id': case_id,
            'filename': filename,
            'file_path': file_path,
            'created_date': datetime.now().isoformat(),
            'type': cropped_data['type'],
            'age': metadata['age'],
            'sexe': metadata['sexe'],
            'contexte': metadata['contexte'],
            'diagnostic': metadata['diagnostic'],
            'statut': 'imported',
            'metadata': {
                'source_file': st.session_state.uploaded_file_data['filename'],
                'import_method': 'smart_importer'
            }
        }
        
        # Si image, ajouter les dimensions
        if cropped_data['type'] == 'image':
            metadata_json['dimensions'] = {
                'width': cropped_data['image'].size[0],
                'height': cropped_data['image'].size[1]
            }
            if 'coordinates' in cropped_data:
                metadata_json['crop_coordinates'] = cropped_data['coordinates']
        
        # Sauvegarder les métadonnées
        metadata_path = export_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_json, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Fichiers sauvegardés dans : {export_dir}")
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur export : {e}")
        return False

# Interface principale
if __name__ == "__main__":
    st.set_page_config(
        page_title="Import ECG Intelligent", 
        page_icon="📥",
        layout="wide"
    )
    
    st.title("📥 Import ECG Intelligent - Avec Recadrage")
    smart_ecg_importer()
