"""
Outil d'annotation unifié qui gère tous les formats
Solution au problème de conversion - PDF.js robuste intégré
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import sys
import base64
import os
from pathlib import Path
from PIL import Image

# Ajout des chemins pour les imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend" / "viewers"))

from correction_engine import OntologyCorrector

def _afficher_ecg_robuste(file_path):
    """
    Affichage ECG robuste - Solution complète pour PDFs volumineux
    """
    if not file_path or not Path(file_path).exists():
        st.error("❌ Fichier ECG introuvable")
        return False
    
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    # Affichage selon le format
    if file_extension == '.pdf':
        return _afficher_pdf_robuste(file_path)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        return _afficher_image_simple(file_path)
    elif file_extension == '.xml':
        return _afficher_xml_simple(file_path)
    else:
        st.warning(f"⚠️ Format non reconnu : {file_extension}")
        return False

def _afficher_pdf_robuste(pdf_path):
    """
    Solution robuste pour PDFs - Résout le problème d'affichage
    """
    st.markdown("**📄 ECG au format PDF**")
    
    try:
        # Lire le PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        file_size_mb = len(pdf_data) / (1024 * 1024)
        
        # Interface informative
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.metric("Taille", f"{file_size_mb:.1f} MB")
            if file_size_mb > 2:
                st.warning("⚠️ Volumineux")
            else:
                st.success("✅ Optimal")
        
        with col1:
            if file_size_mb > 2:
                # Solution pour PDFs volumineux
                st.info("💡 **Solution pour PDF volumineux**")
                
                # Onglets de solutions
                tab1, tab2 = st.tabs(["📥 Téléchargement", "🌐 PDF.js Externe"])
                
                with tab1:
                    st.download_button(
                        label="📄 Télécharger le PDF",
                        data=pdf_data,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        use_container_width=True,
                        help="Téléchargez pour ouvrir dans votre lecteur PDF"
                    )
                    st.success("✅ Téléchargement prêt")
                
                with tab2:
                    pdfjs_url = "https://mozilla.github.io/pdf.js/web/viewer.html"
                    st.markdown(f"**[🚀 Ouvrir PDF.js]({pdfjs_url})**")
                    st.markdown("**Instructions :**")
                    st.markdown("1. Téléchargez le PDF (onglet précédent)")
                    st.markdown("2. Ouvrez PDF.js via le lien")
                    st.markdown("3. Cliquez 'Ouvrir un fichier'")
                    st.markdown("4. Sélectionnez votre PDF")
                
                return True
            
            else:
                # Affichage direct pour petits PDFs
                try:
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                    
                    if len(pdf_base64) > 2000000:  # Limite URL
                        st.warning("⚠️ PDF optimisé mais URL trop longue")
                        return _afficher_pdf_fallback(pdf_path, pdf_data)
                    
                    viewer_url = f"https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_base64}"
                    
                    iframe_html = f"""
                    <div style="border: 2px solid #4CAF50; border-radius: 8px; overflow: hidden;">
                        <div style="background: #4CAF50; color: white; padding: 8px; font-weight: bold;">
                            📄 PDF.js - Affichage réussi
                        </div>
                        <iframe 
                            src="{viewer_url}" 
                            width="100%" 
                            height="500" 
                            style="border: none;">
                        </iframe>
                    </div>
                    """
                    
                    components.html(iframe_html, height=550)
                    st.success("🎉 PDF affiché avec succès !")
                    return True
                    
                except Exception as e:
                    st.error(f"❌ Erreur affichage direct : {e}")
                    return _afficher_pdf_fallback(pdf_path, pdf_data)
            
    except Exception as e:
        st.error(f"❌ Erreur lecture PDF : {e}")
        return False

def _afficher_pdf_fallback(pdf_path, pdf_data):
    """Fallback pour PDFs problématiques"""
    st.warning("🔄 Mode de secours activé")
    
    st.download_button(
        label="📥 Télécharger PDF",
        data=pdf_data,
        file_name=pdf_path.name,
        mime="application/pdf"
    )
    
    st.markdown("[🌐 Ouvrir PDF.js](https://mozilla.github.io/pdf.js/web/viewer.html)")
    return True

def _afficher_image_simple(image_path):
    """Affichage simple des images"""
    try:
        image = Image.open(image_path)
        st.image(image, caption=f"ECG - {image_path.name}", use_container_width=True)
        st.success("✅ Image ECG affichée")
        return True
    except Exception as e:
        st.error(f"❌ Erreur image : {e}")
        return False

def _afficher_xml_simple(xml_path):
    """Affichage simple des XML"""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        with st.expander("📄 Contenu XML"):
            st.code(xml_content[:1000], language='xml')
        
        st.success("✅ XML ECG lu")
        return True
    except Exception as e:
        st.error(f"❌ Erreur XML : {e}")
        return False

def unified_annotation_tool():
    """Interface d'annotation unifiée - fonctionne avec tous les formats"""
    
    st.header("🏷️ Annotation ECG Universelle")
    st.markdown("**Compatible :** PNG, JPG, PDF, XML - **Sans conversion forcée**")
    
    # Chargement de l'ontologie
    if 'corrector' not in st.session_state:
        try:
            ontology_path = project_root / "data" / "ontologie.owx"
            st.session_state.corrector = OntologyCorrector(str(ontology_path))
            st.session_state.concepts = st.session_state.corrector.get_concept_names()
            st.success(f"✅ Ontologie chargée : {len(st.session_state.concepts)} concepts disponibles")
        except Exception as e:
            st.error(f"❌ Erreur chargement ontologie : {e}")
            return
    
    # Interface à 2 colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🫀 ECG à annoter")
        
        # Sélection du cas
        cases_dir = Path("data/ecg_cases")
        available_cases = []
        
        if cases_dir.exists():
            for case_dir in cases_dir.iterdir():
                if case_dir.is_dir():
                    metadata_file = case_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        available_cases.append(case_data)
        
        if available_cases:
            selected_case = st.selectbox(
                "Choisir un cas à annoter",
                options=range(len(available_cases)),
                format_func=lambda i: f"{available_cases[i]['case_id']} - {available_cases[i].get('filename', 'Sans titre')}"
            )
            
            case_data = available_cases[selected_case]
            file_path = case_data.get('file_path', '')
            
            # Affichage robuste intégré pour PDFs volumineux
            try:
                success = _afficher_ecg_robuste(file_path)
                
                if success:
                    st.success("✅ ECG affiché - Prêt pour annotation")
                else:
                    st.warning("⚠️ Affichage partiel - Annotation possible")
                    
            except Exception as e:
                st.error(f"❌ Erreur visualiseur : {e}")
                # Fallback simple
                st.info(f"📄 Fichier détecté : {Path(file_path).name}")
                st.markdown("**Annotation possible même sans aperçu visuel**")
        
        else:
            st.info("📂 Aucun cas disponible. Importez d'abord des ECG.")
            return
    
    with col2:
        st.markdown("### 🧠 Annotation ontologique")
        
        # Interface de saisie
        st.markdown("**Recherche de concepts :**")
        user_input = st.text_input(
            "Tapez un concept médical",
            placeholder="Ex: rythme sinusal, bloc, arythmie...",
            help="Recherche dans les 281 concepts ECG"
        )
        
        # Filtrage intelligent
        if user_input and len(user_input) >= 2:
            matching_concepts = [
                concept for concept in st.session_state.concepts 
                if user_input.lower() in concept.lower()
            ]
            
            if matching_concepts:
                st.markdown("**💡 Concepts trouvés :**")
                
                # Limiter à 8 suggestions pour éviter l'encombrement
                for concept in matching_concepts[:8]:
                    col_concept, col_add = st.columns([3, 1])
                    
                    with col_concept:
                        st.write(f"• {concept}")
                    
                    with col_add:
                        if st.button("➕", key=f"add_{concept}_{selected_case}"):
                            add_annotation_to_case(concept, case_data)
            else:
                st.info("🔍 Aucun concept trouvé - Essayez d'autres termes")
        
        # Affichage des annotations actuelles
        st.markdown("### 📝 Annotations de ce cas")
        
        case_annotations = case_data.get('annotations', {})
        
        if case_annotations:
            for concept, details in case_annotations.items():
                col_text, col_coeff, col_del = st.columns([2, 1, 1])
                
                with col_text:
                    st.write(f"• {concept}")
                
                with col_coeff:
                    coeff = st.number_input(
                        "Poids", 
                        min_value=0.0, 
                        max_value=5.0, 
                        value=details.get('weight', 1.0),
                        step=0.1,
                        key=f"coeff_{concept}_{selected_case}"
                    )
                    # Mettre à jour le coefficient
                    if coeff != details.get('weight', 1.0):
                        update_annotation_weight(case_data, concept, coeff)
                
                with col_del:
                    if st.button("🗑️", key=f"del_{concept}_{selected_case}"):
                        remove_annotation_from_case(concept, case_data)
                        st.rerun()
        else:
            st.info("💭 Aucune annotation pour ce cas")
        
        # Bouton de sauvegarde
        if st.button("💾 Sauvegarder annotations", type="primary"):
            save_case_annotations(case_data)
            st.success("✅ Annotations sauvegardées")

def add_annotation_to_case(concept, case_data):
    """Ajouter une annotation à un cas"""
    if 'annotations' not in case_data:
        case_data['annotations'] = {}
    
    case_data['annotations'][concept] = {
        'weight': 1.0,
        'added_date': str(Path(__file__).stat().st_mtime)
    }
    
    save_case_annotations(case_data)
    st.success(f"✅ Concept ajouté : {concept}")
    st.rerun()

def update_annotation_weight(case_data, concept, weight):
    """Mettre à jour le poids d'une annotation"""
    if concept in case_data.get('annotations', {}):
        case_data['annotations'][concept]['weight'] = weight
        save_case_annotations(case_data)

def remove_annotation_from_case(concept, case_data):
    """Supprimer une annotation d'un cas"""
    if concept in case_data.get('annotations', {}):
        del case_data['annotations'][concept]
        save_case_annotations(case_data)

def save_case_annotations(case_data):
    """Sauvegarder les annotations dans le fichier métadata"""
    try:
        case_id = case_data['case_id']
        metadata_path = Path("data/ecg_cases") / case_id / "metadata.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde : {e}")

if __name__ == "__main__":
    st.title("🧪 Test Annotation Unifiée")
    unified_annotation_tool()
