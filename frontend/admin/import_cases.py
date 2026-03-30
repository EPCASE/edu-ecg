import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import uuid
from PIL import Image
import pandas as pd

# Import conditionnel pour PDF
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

def admin_import_cases():
    """Interface d'import redirigée vers l'Import Intelligent amélioré"""
    
    st.header("📤 Import de Cas ECG")
    st.info("🔄 **Nouvelle Interface !** L'import de cas a été intégré dans l'Import Intelligent")
    
    st.markdown("""
    ### 🎯 Options d'Import Disponibles
    
    L'**Import Intelligent** propose maintenant deux modes :
    
    1. **📄 Import Simple** - Pour un ECG unique
       - Upload → Recadrage → Export
       - Interface linéaire et intuitive
    
    2. **📁 Import Multiple** - Pour créer des cas avec plusieurs ECG
       - Création de cas structuré
       - Ajout progressif d'ECG multiples
       - Recadrage individuel de chaque ECG
       - Métadonnées complètes
    
    ### 🚀 Comment Accéder
    
    Rendez-vous dans **🧠 Import Intelligent** pour :
    - ✅ Importer un ECG simple
    - ✅ Créer des cas multi-ECG
    - ✅ Recadrer individuellement chaque ECG
    - ✅ Organiser vos cas avec métadonnées
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🧠 Aller à l'Import Intelligent", type="primary", use_container_width=True):
            st.switch_page("pages/2_🧠_Import_Intelligent.py")
    
    with col2:
        st.markdown("#### 📊 Ancienne Interface")
        st.markdown("Cette interface a été **fusionnée** avec l'Import Intelligent pour une expérience unifiée.")
    
    # Statistiques des cas existants
    st.markdown("---")
    st.markdown("### 📈 Statistiques des Cas")
    
    # Compter les cas existants
    ecg_dir = Path("data/ecg_cases")
    if ecg_dir.exists():
        case_folders = [d for d in ecg_dir.iterdir() if d.is_dir()]
        total_cases = len(case_folders)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Total Cas", total_cases)
        
        # Compter les types
        multi_cases = 0
        simple_cases = 0
        
        for case_folder in case_folders:
            metadata_path = case_folder / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    if metadata.get('type') == 'multi_ecg':
                        multi_cases += 1
                    else:
                        simple_cases += 1
                except:
                    simple_cases += 1
            else:
                simple_cases += 1
        
        with col2:
            st.metric("📄 Cas Simples", simple_cases)
        with col3:
            st.metric("📁 Cas Multi-ECG", multi_cases)
    else:
        st.info("📂 Aucun cas ECG trouvé")

# =====================================================================
# FONCTIONS SUPPRIMÉES - MIGRÉES VERS IMPORT INTELLIGENT
# =====================================================================
# 
# Les fonctions suivantes ont été supprimées car intégrées 
# dans smart_ecg_importer_simple.py avec le mode "Import Multiple" :
#
# - create_new_case_interface()
# - add_ecg_to_case_interface() 
# - crop_current_ecg_interface()
# - preview_case_interface()
# - finalize_case_interface()
# - save_final_case()
# - et toutes les fonctions utilitaires associées
#
# Nouvelle localisation : 
# frontend/admin/smart_ecg_importer_simple.py -> import_multiple_workflow()
# =====================================================================

# Fin du fichier - Toutes les fonctions d'import multiple ont été supprimées
# et intégrées dans l'Import Intelligent pour une expérience unifiée
    """Interface pour créer un nouveau cas"""
    
    st.subheader("📋 Créer un Nouveau Cas ECG")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        case_name = st.text_input(
            "Nom du cas",
            placeholder="Ex: Infarctus Antérieur - Patient 45 ans",
            help="Nom descriptif pour identifier le cas"
        )
        
        case_description = st.text_area(
            "Description clinique",
            placeholder="Ex: Homme de 45 ans, douleur thoracique, facteurs de risque...",
            help="Contexte clinique détaillé"
        )
        
        # Métadonnées du cas
        case_category = st.selectbox(
            "Catégorie",
            ["Infarctus", "Arythmie", "Troubles de conduction", "Normal", "Autre"],
            help="Classification du cas pour l'organisation"
        )
        
        difficulty_level = st.select_slider(
            "Niveau de difficulté",
            options=["Débutant", "Intermédiaire", "Avancé", "Expert"],
            help="Niveau de difficulté pour les étudiants"
        )
    
    with col2:
        st.markdown("### 📊 Configuration")
        
        # Options du cas
        enable_annotations = st.checkbox("Permettre annotations", value=True)
        enable_sessions = st.checkbox("Utiliser dans sessions", value=True)
        auto_progression = st.checkbox("Progression automatique", value=False)
        
        # Preview des métadonnées
        if case_name:
            st.markdown("### 👁️ Aperçu")
            st.success(f"📋 **{case_name}**")
            st.info(f"📁 Catégorie: {case_category}")
            st.info(f"🎯 Niveau: {difficulty_level}")
    
    # Bouton de création
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Créer le Cas et Commencer l'Import", type="primary", disabled=not case_name):
            # Créer le cas dans la session
            st.session_state.current_case = {
                'name': case_name,
                'description': case_description,
                'category': case_category,
                'difficulty': difficulty_level,
                'enable_annotations': enable_annotations,
                'enable_sessions': enable_sessions,
                'auto_progression': auto_progression,
                'created_date': datetime.now().isoformat(),
                'case_id': str(uuid.uuid4())[:8]
            }
            st.session_state.case_ecgs = []
            st.success(f"✅ Cas '{case_name}' créé ! Passez à l'ajout d'ECG.")
            st.rerun()

def add_ecg_to_case_interface():
    """Interface pour ajouter un ECG au cas en cours"""
    
    current_case = st.session_state.current_case
    
    st.subheader(f"📥 Ajouter ECG au cas : {current_case['name']}")
    
    # Affichage du statut actuel
    ecg_count = len(st.session_state.case_ecgs)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Cas", current_case['name'])
    with col2:
        st.metric("📁 ECG Ajoutés", ecg_count)
    with col3:
        st.metric("📊 Catégorie", current_case['category'])
    
    st.markdown("---")
    
    # Upload d'un seul fichier à la fois
    uploaded_file = st.file_uploader(
        "📎 Sélectionnez UN fichier ECG",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        accept_multiple_files=False,
        help="Ajoutez un ECG à la fois pour un contrôle optimal",
        key=f"upload_ecg_{ecg_count}"
    )
    
    if uploaded_file:
        st.success(f"✅ Fichier sélectionné : {uploaded_file.name}")
        
        # Métadonnées pour cet ECG
        col1, col2 = st.columns(2)
        
        with col1:
            ecg_label = st.text_input(
                "Libellé de cet ECG",
                value=f"ECG_{ecg_count + 1:02d}",
                help="Nom spécifique pour cet ECG dans le cas"
            )
            
            ecg_timing = st.selectbox(
                "Moment de réalisation",
                ["Initial", "Post-traitement", "Contrôle", "Suivi", "Autre"],
                help="Contexte temporel de cet ECG"
            )
        
        with col2:
            ecg_notes = st.text_area(
                "Notes spécifiques",
                placeholder="Ex: Dérivations D1, D2, D3...",
                help="Notes particulières pour cet ECG"
            )
        
        # Prévisualisation
        try:
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Aperçu - {ecg_label}", use_container_width=True)
                
                # Bouton d'ajout avec option de recadrage
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("➕ Ajouter cet ECG (sans recadrage)", type="secondary"):
                        add_ecg_to_current_case(uploaded_file, ecg_label, ecg_timing, ecg_notes, image)
                
                with col2:
                    if st.button("✂️ Ajouter avec Recadrage", type="primary"):
                        add_ecg_to_current_case(uploaded_file, ecg_label, ecg_timing, ecg_notes, image, crop=True)
                        
            elif uploaded_file.type == 'application/pdf':
                st.info("📄 PDF détecté - Import direct possible")
                if st.button("➕ Ajouter ce PDF", type="primary"):
                    add_ecg_to_current_case(uploaded_file, ecg_label, ecg_timing, ecg_notes, None)
                    
        except Exception as e:
            st.error(f"❌ Erreur lors de la prévisualisation : {e}")
    
    # Actions sur le cas
    if ecg_count > 0:
        st.markdown("---")
        st.markdown("### 🎮 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ Voir Aperçu", help="Voir tous les ECG ajoutés"):
                st.session_state.active_tab = 2  # Tab aperçu
                st.rerun()
        
        with col2:
            if st.button("✂️ Recadrer Dernier", help="Recadrer le dernier ECG ajouté"):
                st.session_state.crop_step = True
                st.session_state.active_tab = 1  # Tab recadrage
                st.rerun()
        
        with col3:
            if st.button("✅ Finaliser Cas", type="primary", help="Terminer et sauvegarder le cas"):
                st.session_state.active_tab = 3  # Tab finaliser
                st.rerun()
        
        with col4:
            if st.button("🗑️ Annuler Cas", help="Annuler et recommencer"):
                st.session_state.current_case = None
                st.session_state.case_ecgs = []
                st.session_state.crop_step = False
                st.rerun()

def add_ecg_to_current_case(uploaded_file, label, timing, notes, image, crop=False):
    """Ajoute un ECG au cas en cours"""
    
    ecg_data = {
        'file': uploaded_file,
        'label': label,
        'timing': timing,
        'notes': notes,
        'image': image,
        'crop_needed': crop,
        'added_date': datetime.now().isoformat(),
        'ecg_index': len(st.session_state.case_ecgs)
    }
    
    st.session_state.case_ecgs.append(ecg_data)
    
    if crop:
        st.session_state.crop_step = True
        st.success(f"✅ ECG '{label}' ajouté ! Passez au recadrage.")
    else:
        st.success(f"✅ ECG '{label}' ajouté au cas !")
    
    st.rerun()

def crop_current_ecg_interface():
    """Interface de recadrage pour l'ECG actuel"""
    
    if not st.session_state.case_ecgs:
        st.info("📭 Aucun ECG à recadrer. Ajoutez d'abord un ECG.")
        return
    
    # Sélection de l'ECG à recadrer
    st.subheader("✂️ Recadrage d'ECG")
    
    ecg_options = [f"{ecg['label']} ({ecg['timing']})" for ecg in st.session_state.case_ecgs if ecg.get('image')]
    
    if not ecg_options:
        st.info("📭 Aucun ECG image disponible pour le recadrage.")
        return
    
    selected_ecg_idx = st.selectbox(
        "Sélectionnez l'ECG à recadrer",
        range(len(ecg_options)),
        format_func=lambda x: ecg_options[x]
    )
    
    selected_ecg = st.session_state.case_ecgs[selected_ecg_idx]
    image = selected_ecg['image']
    
    if image:
        st.image(image, caption=f"ECG à recadrer : {selected_ecg['label']}", use_container_width=True)
        
        # Interface de recadrage simplifiée
        st.markdown("### 📐 Paramètres de recadrage")
        
        col1, col2 = st.columns(2)
        
        with col1:
            left = st.slider("👈 Marge gauche", 0, image.width//2, 0)
            top = st.slider("👆 Marge haute", 0, image.height//2, 0)
        
        with col2:
            right = st.slider("👉 Marge droite", 0, image.width//2, 0)
            bottom = st.slider("👇 Marge basse", 0, image.height//2, 0)
        
        # Aperçu du recadrage
        if any([left, top, right, bottom]):
            cropped = image.crop((left, top, image.width - right, image.height - bottom))
            st.image(cropped, caption="Aperçu recadré", use_container_width=True)
            
            if st.button("✅ Appliquer le recadrage", type="primary"):
                # Mettre à jour l'ECG avec l'image recadrée
                st.session_state.case_ecgs[selected_ecg_idx]['image'] = cropped
                st.session_state.case_ecgs[selected_ecg_idx]['crop_applied'] = True
                st.session_state.crop_step = False
                st.success("✅ Recadrage appliqué ! Vous pouvez maintenant ajouter un autre ECG.")
                st.rerun()

def preview_case_interface():
    """Aperçu du cas avec tous les ECG"""
    
    current_case = st.session_state.current_case
    case_ecgs = st.session_state.case_ecgs
    
    st.subheader(f"👁️ Aperçu du cas : {current_case['name']}")
    
    # Informations du cas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 ECG Total", len(case_ecgs))
    with col2:
        st.metric("📊 Catégorie", current_case['category'])
    with col3:
        st.metric("🎯 Niveau", current_case['difficulty'])
    
    st.markdown("---")
    
    # Liste des ECG
    if case_ecgs:
        st.markdown("### 📋 ECG dans ce cas")
        
        for i, ecg in enumerate(case_ecgs):
            with st.expander(f"📄 {ecg['label']} - {ecg['timing']}", expanded=True):
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**📁 Libellé :** {ecg['label']}")
                    st.markdown(f"**⏰ Timing :** {ecg['timing']}")
                    st.markdown(f"**📝 Notes :** {ecg.get('notes', 'Aucune')}")
                    st.markdown(f"**✂️ Recadré :** {'✅ Oui' if ecg.get('crop_applied') else '❌ Non'}")
                
                with col2:
                    if ecg.get('image'):
                        st.image(ecg['image'], caption=f"ECG {i+1}", use_container_width=True)
                    else:
                        st.info("📄 Fichier PDF - Pas d'aperçu disponible")
                
                # Actions sur cet ECG
                ecg_col1, ecg_col2, ecg_col3 = st.columns(3)
                
                with ecg_col1:
                    if st.button(f"✂️ Recadrer", key=f"crop_{i}"):
                        st.session_state.active_tab = 1
                        st.rerun()
                
                with ecg_col2:
                    if st.button(f"📝 Modifier", key=f"edit_{i}"):
                        st.info("Fonction de modification à implémenter")
                
                with ecg_col3:
                    if st.button(f"🗑️ Supprimer", key=f"delete_{i}"):
                        st.session_state.case_ecgs.pop(i)
                        st.success(f"ECG {ecg['label']} supprimé")
                        st.rerun()
    else:
        st.info("📭 Aucun ECG ajouté pour le moment")

def finalize_case_interface():
    """Interface pour finaliser et sauvegarder le cas"""
    
    current_case = st.session_state.current_case
    case_ecgs = st.session_state.case_ecgs
    
    st.subheader("✅ Finaliser le Cas ECG")
    
    if not case_ecgs:
        st.warning("⚠️ Aucun ECG ajouté. Ajoutez au moins un ECG avant de finaliser.")
        return
    
    # Résumé final
    st.markdown("### 📊 Résumé Final")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Cas", current_case['name'])
    with col2:
        st.metric("📁 ECG Total", len(case_ecgs))
    with col3:
        st.metric("📊 Catégorie", current_case['category'])
    with col4:
        st.metric("🎯 Niveau", current_case['difficulty'])
    
    # Options de finalisation
    st.markdown("### ⚙️ Options de Finalisation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        generate_preview = st.checkbox("Générer aperçu automatique", value=True)
        create_annotations_template = st.checkbox("Créer template d'annotations", value=True)
        add_to_sessions = st.checkbox("Ajouter aux sessions disponibles", value=True)
    
    with col2:
        notify_users = st.checkbox("Notifier les utilisateurs", value=False)
        auto_publish = st.checkbox("Publier automatiquement", value=False)
        create_backup = st.checkbox("Créer sauvegarde", value=True)
    
    # Aperçu de la structure finale
    if st.checkbox("👁️ Voir la structure finale", value=False):
        final_structure = {
            'case_info': current_case,
            'ecgs': [
                {
                    'label': ecg['label'],
                    'timing': ecg['timing'],
                    'notes': ecg['notes'],
                    'has_image': ecg.get('image') is not None,
                    'is_cropped': ecg.get('crop_applied', False)
                }
                for ecg in case_ecgs
            ],
            'metadata': {
                'total_ecgs': len(case_ecgs),
                'creation_date': current_case['created_date'],
                'ready_for_use': True
            }
        }
        st.json(final_structure)
    
    # Boutons de finalisation
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("� Retour à l'Édition", help="Retourner à l'ajout d'ECG"):
            st.session_state.active_tab = 0
            st.rerun()
    
    with col2:
        if st.button("💾 Sauvegarder le Cas", type="primary", help="Sauvegarder définitivement le cas"):
            if save_final_case(current_case, case_ecgs):
                st.success("🎉 Cas sauvegardé avec succès !")
                st.balloons()
                
                # Reset de la session
                st.session_state.current_case = None
                st.session_state.case_ecgs = []
                st.session_state.crop_step = False
                
                # Bouton pour créer un nouveau cas
                if st.button("🚀 Créer un Nouveau Cas", type="secondary"):
                    st.rerun()
            else:
                st.error("❌ Erreur lors de la sauvegarde")
    
    with col3:
        if st.button("🗑️ Annuler Tout", help="Annuler et perdre les modifications"):
            if st.checkbox("⚠️ Confirmer l'annulation"):
                st.session_state.current_case = None
                st.session_state.case_ecgs = []
                st.session_state.crop_step = False
                st.rerun()

def save_final_case(case_info, ecgs_list):
    """Sauvegarde le cas final avec tous ses ECG"""
    
    try:
        # Créer le dossier du cas
        case_dir = Path("data/ecg_cases") / case_info['name']
        case_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder chaque ECG
        saved_ecgs = []
        
        for i, ecg in enumerate(ecgs_list):
            if ecg.get('image'):
                # Sauvegarder l'image
                filename = f"{ecg['label']}.png"
                file_path = case_dir / filename
                ecg['image'].save(file_path)
                saved_ecgs.append({
                    'filename': filename,
                    'label': ecg['label'],
                    'timing': ecg['timing'],
                    'notes': ecg['notes'],
                    'type': 'image',
                    'cropped': ecg.get('crop_applied', False)
                })
            elif ecg.get('file'):
                # Sauvegarder le fichier original (PDF, etc.)
                filename = f"{ecg['label']}.{ecg['file'].name.split('.')[-1]}"
                file_path = case_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(ecg['file'].getbuffer())
                saved_ecgs.append({
                    'filename': filename,
                    'label': ecg['label'],
                    'timing': ecg['timing'],
                    'notes': ecg['notes'],
                    'type': 'file'
                })
        
        # Créer les métadonnées du cas
        metadata = {
            'case_info': case_info,
            'ecgs': saved_ecgs,
            'creation_date': datetime.now().isoformat(),
            'version': '2.0',
            'multi_ecg': True,
            'total_files': len(saved_ecgs)
        }
        
        # Sauvegarder les métadonnées
        metadata_path = case_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        return False
    
    with tab2:
        st.subheader("🔢 Import format numérique")
        st.markdown("**Compatibilité HL7 XML et formats propriétaires**")
        
        # Zone de drag & drop spécialisée
        uploaded_xml = st.file_uploader(
            "Fichiers numériques ECG",
            type=['xml', 'hl7', 'scp', 'ecg'],
            help="Formats numériques : HL7 XML, SCP-ECG, formats propriétaires"
        )
        
        if uploaded_xml:
            st.success(f"📄 Fichier détecté : {uploaded_xml.name}")
            
            # Analyse du format
            file_content = uploaded_xml.read()
            
            if uploaded_xml.name.endswith('.xml'):
                st.info("🔍 Format XML détecté - Analyse HL7 en cours...")
                # TODO: Parser HL7
                
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Métadonnées détectées :**")
                st.write("- Format : XML/HL7")
                st.write("- Taille :", len(file_content), "bytes")
                
            with col2:
                if st.button("📊 Analyser le format"):
                    analyze_numerical_format(file_content)
    
    with tab3:
        st.subheader("🖼️ Traitement format image")
        st.markdown("**Recadrage, détection d'échelle et anonymisation**")
        
        uploaded_image = st.file_uploader(
            "Image ECG à traiter",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Images d'ECG scannés ou photographiés"
        )
        
        if uploaded_image:
            try:
                # Gérer les différents types de fichiers
                file_extension = uploaded_image.name.split('.')[-1].lower()
                
                if file_extension == 'pdf':
                    # Utiliser notre visualiseur intelligent pour les PDFs
                    st.info("� PDF détecté - Utilisation du visualiseur moderne")
                    
                    # Sauvegarder temporairement le PDF
                    temp_path = f"temp_{uploaded_image.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_image.getbuffer())
                    
                    # Utiliser le visualiseur intelligent
                    import sys
                    project_root = Path(__file__).parent.parent.parent
                    sys.path.append(str(project_root / "frontend" / "viewers"))
                    
                    try:
                        from ecg_viewer_smart import display_ecg_smart
                        success = display_ecg_smart(temp_path)
                        if success:
                            st.success("✅ PDF affiché avec PDF.js")
                            # Pour l'import, on garde le PDF tel quel
                            image = "PDF_FILE"  # Indicateur spécial
                        else:
                            st.warning("⚠️ Erreur d'affichage PDF")
                            image = None
                    except Exception as e:
                        st.error(f"❌ Erreur visualiseur : {e}")
                        st.info("💡 Convertissez le PDF en image (PNG/JPG) pour l'import")
                        os.remove(temp_path)
                        return
                else:
                    image = Image.open(uploaded_image)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if image == "PDF_FILE":
                        st.success("📄 PDF prêt pour l'import")
                    else:
                        st.image(image, caption="Image ECG originale", use_container_width=True)
                
                with col2:
                    st.markdown("### 🛠️ Outils de traitement")
                    
                    # Outils automatiques
                    if st.button("🔍 Détection automatique de grille"):
                        detect_ecg_grid(image)
                    
                    if st.button("✂️ Recadrage automatique"):
                        auto_crop_ecg(image)
                    
                    if st.button("🎭 Anonymisation"):
                        anonymize_ecg(image)
                    
                    # Outils semi-automatiques
                    st.markdown("### 🎯 Outils semi-automatiques")
                    st.info("Cliquez sur l'image pour définir les points de calibrage")
                    
                    # Paramètres d'échelle
                    st.markdown("**Échelle ECG standard :**")
                    st.write("- Amplitude : 10mm/mV")
                    st.write("- Temps : 25mm/sec")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors du traitement : {e}")
    
    with tab4:
        st.subheader("📊 Gestion de la base de données")
        
        # Statistiques de la base
        cases_dir = Path("data/ecg_cases")
        if cases_dir.exists():
            case_files = list(cases_dir.glob("*/metadata.json"))
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📋 Cas totaux", len(case_files))
            
            with col2:
                st.metric("🖼️ Images", count_files_by_type("image"))
            
            with col3:
                st.metric("🔢 Numériques", count_files_by_type("numerical"))
            
            with col4:
                st.metric("✅ Annotés", count_annotated_cases())
            
            # Liste des cas
            if case_files:
                st.markdown("### 📋 Cas disponibles")
                
                cases_data = []
                for case_file in case_files:
                    try:
                        with open(case_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        
                        cases_data.append({
                            "ID": case_data.get("case_id", "N/A"),
                            "Titre": case_data.get("metadata", {}).get("title", "Sans titre"),
                            "Format": case_data.get("ecg_data", {}).get("format", "N/A"),
                            "Difficulté": case_data.get("metadata", {}).get("difficulty", "N/A"),
                            "Statut": "✅ Annoté" if case_data.get("annotations") else "⏳ En attente"
                        })
                    except Exception as e:
                        st.error(f"Erreur lecture {case_file}: {e}")
                
                if cases_data:
                    df = pd.DataFrame(cases_data)
                    st.dataframe(df, use_container_width=True)
        else:
            st.info("📂 Aucun cas trouvé. Commencez par importer des ECG.")

def import_ecg_files(uploaded_files, clinical_context, metadata):
    """Traite l'import des fichiers ECG"""
    
    if not uploaded_files:
        st.error("❌ Aucun fichier sélectionné")
        return
    
    # Créer le dossier de destination s'il n'existe pas
    project_root = Path(__file__).parent.parent.parent
    ecg_cases_dir = project_root / "data" / "ecg_cases"
    ecg_cases_dir.mkdir(exist_ok=True)
    
    success_count = 0
    
    with st.spinner("📤 Import en cours..."):
        for uploaded_file in uploaded_files:
            try:
                # Générer un ID unique pour ce cas
                case_id = f"ecg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                
                # Créer un dossier pour ce cas
                case_dir = ecg_cases_dir / case_id
                case_dir.mkdir(exist_ok=True)
                
                # Sauvegarder le fichier
                file_extension = uploaded_file.name.split('.')[-1].lower()
                file_path = case_dir / f"ecg_image.{file_extension}"
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Créer les métadonnées du cas
                case_metadata = {
                    "case_id": case_id,
                    "filename": uploaded_file.name,
                    "file_type": file_extension,
                    "clinical_context": clinical_context,
                    "import_metadata": metadata,
                    "file_path": str(file_path),
                    "status": "imported",
                    "annotations": {},
                    "created_date": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat()
                }
                
                # Sauvegarder les métadonnées
                metadata_path = case_dir / "metadata.json"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(case_metadata, f, indent=2, ensure_ascii=False)
                
                success_count += 1
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'import de {uploaded_file.name}: {e}")
    
    if success_count > 0:
        st.success(f"✅ {success_count} fichier(s) importé(s) avec succès !")
        st.info(f"📁 Fichiers sauvegardés dans : {ecg_cases_dir}")
        st.balloons()
        
        # Rafraîchir la page pour montrer les nouveaux cas
        st.rerun()
    else:
        st.error("❌ Aucun fichier n'a pu être importé")

def analyze_numerical_format(file_content):
    """Analyse les formats numériques ECG"""
    st.markdown("### 🔍 Analyse du format numérique")
    
    # Détection basique du format
    content_str = str(file_content)
    
    if "HL7" in content_str or "ClinicalDocument" in content_str:
        st.success("📋 Format HL7 XML détecté")
        st.info("🔧 Parser HL7 à implémenter")
    elif "SCP" in content_str:
        st.success("📋 Format SCP-ECG détecté") 
        st.info("🔧 Parser SCP à implémenter")
    else:
        st.warning("❓ Format non reconnu - analyse manuelle requise")
    
    # Affichage d'un échantillon
    with st.expander("👁️ Aperçu du contenu (premiers 500 caractères)"):
        st.code(content_str[:500])

def detect_ecg_grid(image):
    """Détection automatique de la grille ECG"""
    st.info("🔍 Détection de grille en développement...")
    st.markdown("""
    **Algorithme prévu :**
    1. Détection des lignes de grille (10mm/mV, 25mm/sec)
    2. Identification des axes temporel et d'amplitude
    3. Calibrage automatique des mesures
    """)

def auto_crop_ecg(image):
    """Recadrage automatique de l'ECG"""
    st.info("✂️ Recadrage automatique en développement...")
    st.markdown("""
    **Fonctionnalités prévues :**
    1. Détection des bords du tracé ECG
    2. Suppression des marges inutiles
    3. Redressement automatique si rotation
    """)

def anonymize_ecg(image):
    """Anonymisation de l'ECG"""
    st.info("🎭 Anonymisation en développement...")
    st.markdown("""
    **Outils d'anonymisation :**
    1. Masquage automatique des zones de texte
    2. Suppression des informations patient
    3. Rognage manuel des zones sensibles
    """)

def count_files_by_type(file_type):
    """Compte les fichiers par type"""
    # TODO: Implémenter le comptage réel
    return 0

def count_annotated_cases():
    """Compte les cas annotés"""
    # TODO: Implémenter le comptage réel
    return 0

if __name__ == "__main__":
    admin_import_cases()
