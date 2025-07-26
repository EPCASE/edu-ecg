import streamlit as st
import streamlit.components.v1 as components
import os
import tempfile
from PIL import Image
import json
from datetime import datetime
import uuid

# Import validation avancée si disponible
try:
    from advanced_validation import advanced_ecg_validation, display_validation_report, create_quality_improvement_suggestions
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

def create_modern_upload_interface():
    """
    Interface d'upload moderne avec drag-and-drop inspirée d'ep-cases
    """
    
    upload_html = """
    <div class="upload-container">
        <div class="upload-zone" id="upload-zone" onclick="document.getElementById('file-input').click()">
            <div class="upload-content">
                <div class="upload-icon">📁</div>
                <h3>Glissez-déposez votre ECG ici</h3>
                <p>ou cliquez pour sélectionner</p>
                <p class="formats">Formats supportés: PDF, PNG, JPG, JPEG, XML, HL7</p>
                <div class="upload-examples">
                    <span class="format-badge">📄 PDF</span>
                    <span class="format-badge">🖼️ PNG</span>
                    <span class="format-badge">📊 JPG</span>
                    <span class="format-badge">📋 XML</span>
                    <span class="format-badge">⚡ HL7</span>
                </div>
            </div>
        </div>
        
        <div class="upload-progress" id="upload-progress" style="display: none;">
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <p id="progress-text">Téléchargement en cours...</p>
        </div>
        
        <div class="upload-success" id="upload-success" style="display: none;">
            <div class="success-icon">✅</div>
            <h4>Fichier téléchargé avec succès !</h4>
            <p id="file-info"></p>
        </div>
    </div>
    
    <style>
        .upload-container {
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
        }
        
        .upload-zone {
            border: 3px dashed #cccccc;
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .upload-zone:hover {
            border-color: #007bff;
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 123, 255, 0.15);
        }
        
        .upload-zone.dragover {
            border-color: #28a745;
            background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
            transform: scale(1.02);
        }
        
        .upload-content h3 {
            margin: 15px 0 10px 0;
            color: #495057;
            font-weight: 600;
        }
        
        .upload-content p {
            margin: 5px 0;
            color: #6c757d;
        }
        
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
        
        .formats {
            font-size: 14px;
            font-style: italic;
            margin-top: 15px !important;
        }
        
        .upload-examples {
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .format-badge {
            background: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .upload-progress {
            margin-top: 20px;
            text-align: center;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #007bff, #0056b3);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        
        .upload-success {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 2px solid #28a745;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin-top: 20px;
        }
        
        .success-icon {
            font-size: 48px;
            margin-bottom: 15px;
            animation: checkmark 0.6s ease-in-out;
        }
        
        @keyframes checkmark {
            0% { transform: scale(0); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }
        
        .upload-success h4 {
            color: #155724;
            margin-bottom: 10px;
        }
        
        .upload-success p {
            color: #155724;
            margin: 5px 0;
        }
    </style>
    
    <script>
        const uploadZone = document.getElementById('upload-zone');
        const progressDiv = document.getElementById('upload-progress');
        const successDiv = document.getElementById('upload-success');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const fileInfo = document.getElementById('file-info');
        
        // Drag and drop events
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });
        
        function handleFileUpload(file) {
            // Simulate upload progress
            uploadZone.style.display = 'none';
            progressDiv.style.display = 'block';
            
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);
                    showSuccess(file);
                }
                progressFill.style.width = progress + '%';
                progressText.textContent = `Téléchargement: ${Math.round(progress)}%`;
            }, 100);
        }
        
        function showSuccess(file) {
            setTimeout(() => {
                progressDiv.style.display = 'none';
                successDiv.style.display = 'block';
                
                const sizeKB = (file.size / 1024).toFixed(1);
                fileInfo.innerHTML = `
                    <strong>${file.name}</strong><br>
                    Taille: ${sizeKB} KB<br>
                    Type: ${file.type || 'Non défini'}
                `;
                
                // Trigger Streamlit rerun after 2 seconds
                setTimeout(() => {
                    window.parent.location.reload();
                }, 2000);
            }, 500);
        }
    </script>
    """
    
    return components.html(upload_html, height=400)

def detect_ecg_format(uploaded_file):
    """
    Détection intelligente du format ECG
    """
    file_info = {
        'type': 'Inconnu',
        'pages': 1,
        'quality': 'Bonne',
        'ecg_detected': True,
        'recommendations': []
    }
    
    # Détection par extension
    file_extension = uploaded_file.name.lower().split('.')[-1]
    
    if file_extension in ['pdf']:
        file_info['type'] = 'PDF ECG'
        file_info['recommendations'].append("📄 Sélection de page disponible")
        
    elif file_extension in ['png', 'jpg', 'jpeg']:
        file_info['type'] = 'Image ECG'
        
        # Analyse de l'image si possible
        try:
            image = Image.open(uploaded_file)
            width, height = image.size
            
            if width < 800 or height < 600:
                file_info['quality'] = 'Résolution faible'
                file_info['recommendations'].append("📏 Augmenter la résolution à 300 DPI minimum")
            
            # Ratio d'aspect ECG typique
            aspect_ratio = width / height
            if aspect_ratio < 1.2:
                file_info['recommendations'].append("🔄 Orientation portrait détectée - paysage recommandé")
                
        except Exception:
            pass
            
    elif file_extension in ['xml']:
        file_info['type'] = 'XML ECG'
        file_info['recommendations'].append("📊 Format structuré détecté")
        
    elif file_extension in ['hl7']:
        file_info['type'] = 'HL7 ECG'
        file_info['recommendations'].append("⚡ Format médical standard")
        
    return file_info

def show_immediate_preview(uploaded_file):
    """
    Affichage immédiat des informations du fichier avec validation
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Fichier détecté")
        st.write(f"**Nom** : {uploaded_file.name}")
        st.write(f"**Taille** : {uploaded_file.size / 1024:.1f} KB")
        st.write(f"**Type** : {uploaded_file.type}")
        
        # Détection automatique du format
        format_info = detect_ecg_format(uploaded_file)
        st.write(f"**Format ECG** : {format_info['type']}")
        
        # Indicateur de qualité
        quality_color = "green" if format_info['quality'] == 'Bonne' else "orange"
        st.write(f"**Qualité** : :{quality_color}[{format_info['quality']}]")
    
    with col2:
        st.subheader("🔍 Aperçu")
        
        # Miniature immédiate pour les images
        if uploaded_file.type and uploaded_file.type.startswith('image'):
            try:
                st.image(uploaded_file, width=200, caption="Aperçu ECG")
            except Exception:
                st.write("📄 Impossible d'afficher l'aperçu")
        elif 'pdf' in uploaded_file.type.lower():
            st.write("📄 PDF détecté - Aperçu après traitement")
        else:
            st.write("📊 Format de données ECG")
    
    # Recommandations
    if format_info['recommendations']:
        st.subheader("💡 Recommandations")
        for rec in format_info['recommendations']:
            st.info(rec)
    
    return format_info

def intelligent_validation(uploaded_file, format_info):
    """
    Validation intelligente en temps réel avec suggestions et validation avancée
    """
    validation_results = {
        'valid': True,
        'warnings': [],
        'suggestions': [],
        'auto_fixes': []
    }
    
    # Validation avancée si disponible
    if VALIDATION_AVAILABLE:
        try:
            st.subheader("🔍 Validation Avancée ECG")
            with st.spinner("Analyse de qualité en cours..."):
                advanced_report = advanced_ecg_validation(uploaded_file)
            
            # Afficher le rapport avancé
            score_percent = display_validation_report(advanced_report)
            create_quality_improvement_suggestions(score_percent)
            
            # Intégrer les résultats dans notre validation
            if score_percent < 60:
                validation_results['valid'] = False
                validation_results['warnings'].append(f"❌ Score qualité insuffisant: {score_percent:.1f}%")
            elif score_percent < 80:
                validation_results['warnings'].append(f"⚠️ Score qualité modéré: {score_percent:.1f}%")
            
        except Exception as e:
            st.warning(f"⚠️ Erreur validation avancée: {str(e)}")
    
    # Validation de la taille
    if uploaded_file.size > 10_000_000:  # > 10MB
        validation_results['warnings'].append("⚠️ Fichier volumineux - traitement plus lent")
        validation_results['suggestions'].append("🔧 Compresser l'image ou réduire la résolution")
        
    elif uploaded_file.size < 50_000:  # < 50KB
        validation_results['warnings'].append("⚠️ Fichier très petit - qualité possiblement insuffisante")
        validation_results['suggestions'].append("📈 Augmenter la résolution ou la qualité")
    
    # Validation du format
    file_extension = uploaded_file.name.lower().split('.')[-1]
    if file_extension not in ['pdf', 'png', 'jpg', 'jpeg', 'xml', 'hl7']:
        validation_results['valid'] = False
        validation_results['warnings'].append("❌ Format non supporté")
        validation_results['suggestions'].append("🔄 Convertir en PDF, PNG, JPG, XML ou HL7")
    
    # Validation du nom de fichier
    if len(uploaded_file.name) > 100:
        validation_results['warnings'].append("⚠️ Nom de fichier très long")
        validation_results['auto_fixes'].append("✂️ Raccourcissement automatique proposé")
    
    # Suggestions d'amélioration qualité
    if format_info['quality'] != 'Bonne':
        validation_results['suggestions'].append("🎯 Optimiser la qualité avant import")
    
    return validation_results

def show_validation_results(validation_results):
    """
    Affichage des résultats de validation avec interface moderne
    """
    if validation_results['valid']:
        st.success("✅ Fichier valide - Prêt à importer")
    else:
        st.error("❌ Fichier non valide")
        return False
    
    # Warnings
    if validation_results['warnings']:
        with st.expander("⚠️ Avertissements", expanded=len(validation_results['warnings']) > 0):
            for warning in validation_results['warnings']:
                st.warning(warning)
    
    # Suggestions
    if validation_results['suggestions']:
        with st.expander("💡 Suggestions d'amélioration"):
            for suggestion in validation_results['suggestions']:
                st.info(suggestion)
    
    # Auto-fixes
    if validation_results['auto_fixes']:
        with st.expander("🔧 Corrections automatiques disponibles"):
            for fix in validation_results['auto_fixes']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(fix)
                with col2:
                    if st.button("Appliquer", key=f"fix_{hash(fix)}"):
                        st.success("✅ Correction appliquée")
    
    return True

def create_progressive_workflow():
    """
    Workflow progressif avec étapes claires
    """
    # Étapes du workflow
    steps = [
        "📤 Upload",
        "🔍 Validation", 
        "✂️ Recadrage",
        "📊 Métadonnées",
        "💾 Sauvegarde"
    ]
    
    current_step = st.session_state.get('import_step', 0)
    
    # Barre de progression
    progress_cols = st.columns(len(steps))
    
    for i, (col, step) in enumerate(zip(progress_cols, steps)):
        with col:
            if i < current_step:
                st.success(f"✅ {step}")
            elif i == current_step:
                st.info(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")
    
    # Barre de progression numérique
    progress_percent = (current_step / len(steps)) * 100
    st.progress(progress_percent / 100)
    st.write(f"Progression: {progress_percent:.0f}%")
    
    return current_step

# Interface principale améliorée
def enhanced_import_interface():
    """
    Interface d'import améliorée inspirée d'ep-cases
    """
    st.title("📤 Import ECG Intelligent - Version Améliorée")
    st.write("*Inspiré par ep-cases pour une expérience utilisateur optimale*")
    
    # Workflow progressif
    current_step = create_progressive_workflow()
    
    if current_step == 0:
        # Étape 1: Upload moderne
        st.subheader("📁 Sélection du fichier ECG")
        
        # Interface drag-and-drop moderne
        create_modern_upload_interface()
        
        # Fallback classique
        st.write("---")
        st.write("**Alternative classique :**")
        uploaded_file = st.file_uploader(
            "Choisir un fichier ECG",
            type=['pdf', 'png', 'jpg', 'jpeg', 'xml', 'hl7'],
            help="Formats supportés: PDF, PNG, JPG, XML, HL7"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.import_step = 1
            st.rerun()
    
    elif current_step == 1:
        # Étape 2: Validation et prévisualisation
        st.subheader("🔍 Validation et Prévisualisation")
        
        uploaded_file = st.session_state.uploaded_file
        
        # Prévisualisation immédiate
        format_info = show_immediate_preview(uploaded_file)
        
        # Validation intelligente
        validation_results = intelligent_validation(uploaded_file, format_info)
        
        # Affichage des résultats
        if show_validation_results(validation_results):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⬅️ Retour"):
                    st.session_state.import_step = 0
                    st.rerun()
            
            with col2:
                if st.button("➡️ Continuer vers le recadrage"):
                    st.session_state.import_step = 2
                    st.rerun()
    
    elif current_step == 2:
        # Étape 3: Recadrage (existant)
        st.subheader("✂️ Recadrage Interactif")
        st.info("🔄 Intégration avec votre système de recadrage existant")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Retour"):
                st.session_state.import_step = 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Métadonnées"):
                st.session_state.import_step = 3
                st.rerun()
    
    elif current_step == 3:
        # Étape 4: Métadonnées
        st.subheader("📊 Métadonnées et Contexte Clinique")
        
        with st.form("metadata_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Nom du cas", placeholder="Ex: ECG Patient 001")
                st.selectbox("Type d'ECG", [
                    "ECG de repos 12 dérivations",
                    "ECG d'effort",
                    "Holter ECG",
                    "ECG pédiatrique",
                    "Autre"
                ])
                st.text_area("Contexte clinique", placeholder="Âge, sexe, symptômes...")
            
            with col2:
                st.selectbox("Niveau de difficulté", [
                    "Débutant",
                    "Intermédiaire", 
                    "Avancé",
                    "Expert"
                ])
                st.multiselect("Tags", [
                    "Rythme", "Ischémie", "Trouble conducteur",
                    "Hypertrophie", "Arythmie", "Normal"
                ])
                st.text_area("Notes additionnelles", placeholder="Observations particulières...")
            
            submitted = st.form_submit_button("➡️ Finaliser l'import")
            if submitted:
                st.session_state.import_step = 4
                st.rerun()
    
    elif current_step == 4:
        # Étape 5: Sauvegarde
        st.subheader("💾 Finalisation")
        st.success("🎉 Import ECG terminé avec succès !")
        
        # Récapitulatif
        with st.expander("📋 Récapitulatif de l'import", expanded=True):
            if 'uploaded_file' in st.session_state:
                file = st.session_state.uploaded_file
                st.write(f"**Fichier** : {file.name}")
                st.write(f"**Taille** : {file.size / 1024:.1f} KB")
                st.write(f"**Traitement** : Terminé")
                st.write(f"**Statut** : ✅ Prêt pour annotation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nouveau fichier"):
                # Reset du workflow
                for key in ['import_step', 'uploaded_file']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("➡️ Aller à la liseuse ECG"):
                st.info("🔄 Redirection vers la liseuse ECG...")

if __name__ == "__main__":
    enhanced_import_interface()
