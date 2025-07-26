import streamlit as st
import json
import sys
from pathlib import Path
from datetime import datetime

# Ajout des chemins pour les imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend"))

def admin_annotation_tool():
    """Interface d'annotation simple pour les experts"""
    
    st.header("🏷️ Annotation Expert ECG")
    st.markdown("*Interface simple d'annotation pour les experts*")
    
    # Sélection du cas à annoter
    cases_dir = Path(project_root / "data" / "ecg_cases")
    available_cases = load_available_cases(cases_dir)
    
    if not available_cases:
        st.info("📂 Aucun cas ECG disponible. Utilisez l'Import pour ajouter des cas.")
        return
    
    # Sélection simple du cas
    st.subheader("📋 Sélectionner un cas")
    selected_case_idx = st.selectbox(
        "Choisir un cas à annoter",
        options=range(len(available_cases)),
        format_func=lambda i: f"📋 {available_cases[i]['case_id']} - {available_cases[i].get('name', 'Sans titre')}"
    )
    
    case_data = available_cases[selected_case_idx]
    
    # Affichage de l'ECG
    st.subheader("🖼️ ECG à annoter")
    display_ecg_for_annotation(case_data)
    
    # Interface d'annotation TRÈS SIMPLE
    st.subheader("📝 Annotation de l'expert")
    
    # Zone de texte libre unique pour les annotations
    expert_annotations = st.text_area(
        "Vos annotations d'expert",
        placeholder="Décrivez ce que vous observez sur cet ECG : rythme, axe, anomalies, diagnostic...",
        height=200,
        key=f"expert_annotations_{case_data['case_id']}",
        help="Saisissez librement vos observations et diagnostic expert"
    )
    
    # Zone contexte clinique
    clinical_context = st.text_area(
        "Contexte clinique (optionnel)",
        placeholder="Âge, sexe, symptômes, contexte...",
        height=100,
        key=f"clinical_context_{case_data['case_id']}"
    )
    
    # Bouton de sauvegarde simple
    if st.button("💾 Sauvegarder l'annotation", type="primary"):
        if expert_annotations.strip():
            save_simple_expert_annotations(
                case_data['case_id'], 
                expert_annotations, 
                clinical_context
            )
            st.success("✅ Annotation sauvegardée avec succès !")
        else:
            st.warning("⚠️ Veuillez saisir au moins une annotation.")
    
    # Liste des cas déjà annotés
    st.subheader("📋 Cas déjà annotés")
    display_annotated_cases_list()

def save_simple_expert_annotations(case_id, annotations, clinical_context):
    """Sauvegarde simple des annotations d'expert"""
    
    # Créer le répertoire des sessions si nécessaire
    sessions_dir = project_root / "data" / "ecg_sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    # Structure simple des annotations expert
    expert_data = {
        "case_id": case_id,
        "expert_annotations": annotations,
        "clinical_context": clinical_context,
        "timestamp": datetime.now().isoformat(),
        "annotated_by": "expert",
        "status": "expert_annotated"
    }
    
    # Sauvegarder dans un fichier JSON simple
    expert_file = sessions_dir / f"expert_{case_id}.json"
    
    try:
        with open(expert_file, 'w', encoding='utf-8') as f:
            json.dump(expert_data, f, indent=2, ensure_ascii=False)
        
        st.session_state[f'expert_annotation_saved_{case_id}'] = True
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")

def display_annotated_cases_list():
    """Affiche la liste des cas déjà annotés par l'expert"""
    
    sessions_dir = project_root / "data" / "ecg_sessions"
    
    if not sessions_dir.exists():
        st.info("Aucun cas annoté pour le moment.")
        return
    
    # Rechercher tous les fichiers d'annotations expert
    expert_files = list(sessions_dir.glob("expert_*.json"))
    
    if not expert_files:
        st.info("Aucun cas annoté pour le moment.")
        return
    
    st.markdown(f"**{len(expert_files)} cas annotés**")
    
    for expert_file in expert_files:
        try:
            with open(expert_file, 'r', encoding='utf-8') as f:
                expert_data = json.load(f)
            
            case_id = expert_data.get('case_id', 'Inconnu')
            timestamp = expert_data.get('timestamp', '')
            annotations_preview = expert_data.get('expert_annotations', '')[:100] + "..."
            
            with st.expander(f"📋 {case_id} - {timestamp[:10]}"):
                st.text(annotations_preview)
                if st.button(f"✏️ Modifier {case_id}", key=f"edit_{case_id}"):
                    st.session_state[f'edit_case_id'] = case_id
                    st.rerun()
                
        except Exception as e:
            st.warning(f"Erreur lecture fichier {expert_file.name}: {e}")

def display_ecg_for_annotation(case_data):
    """Affichage simple de l'ECG pour annotation"""
    
    try:
        # Construire le chemin vers l'image ECG
        case_id = case_data['case_id']
        cases_dir = project_root / "data" / "ecg_cases"
        
        # Chercher le fichier d'image
        possible_extensions = ['.png', '.jpg', '.jpeg']
        ecg_file = None
        
        for ext in possible_extensions:
            potential_file = cases_dir / f"{case_id}{ext}"
            if potential_file.exists():
                ecg_file = potential_file
                break
        
        if ecg_file and ecg_file.exists():
            st.image(str(ecg_file), caption=f"ECG - {case_id}", use_column_width=True)
        else:
            st.warning(f"❌ Image ECG introuvable pour le cas {case_id}")
            st.info(f"Recherché dans : {cases_dir}")
            
    except Exception as e:
        st.error(f"❌ Erreur affichage ECG : {e}")

def load_available_cases(cases_dir):
    """Chargement simple des cas disponibles"""
    
    available_cases = []
    
    if not cases_dir.exists():
        return available_cases
    
    # Lister tous les fichiers image ECG
    for file_path in cases_dir.iterdir():
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            case_id = file_path.stem
            
            # Chercher le fichier metadata correspondant
            metadata_file = cases_dir / f"{case_id}_metadata.json"
            
            case_info = {
                'case_id': case_id,
                'file_path': str(file_path),
                'name': case_id
            }
            
            # Charger les métadonnées si disponibles
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        case_info.update(metadata)
                except:
                    pass  # Ignorer les erreurs de lecture metadata
            
            available_cases.append(case_info)
    
    return available_cases
