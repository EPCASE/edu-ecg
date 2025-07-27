import streamlit as st
from pathlib import Path
from datetime import datetime
import json
from config import ECG_CASES_DIR  # Import depuis config.py

# Import des composants nécessaires
try:
    from annotation_components import smart_annotation_input, display_annotation_summary
except ImportError:
    # Fonctions de fallback si le module n'est pas disponible
    def smart_annotation_input(key_prefix, max_tags=10):
        if f'{key_prefix}_tags' not in st.session_state:
            st.session_state[f'{key_prefix}_tags'] = []
        
        new_tag = st.text_input("Ajouter une annotation:", key=f"{key_prefix}_input")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Ajouter", key=f"{key_prefix}_add"):
                if new_tag and new_tag not in st.session_state[f'{key_prefix}_tags']:
                    if len(st.session_state[f'{key_prefix}_tags']) < max_tags:
                        st.session_state[f'{key_prefix}_tags'].append(new_tag)
                        st.rerun()
        
        if st.session_state[f'{key_prefix}_tags']:
            st.write("**Annotations actuelles:**")
            for i, tag in enumerate(st.session_state[f'{key_prefix}_tags']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {tag}")
                with col2:
                    if st.button("❌", key=f"{key_prefix}_remove_{i}"):
                        st.session_state[f'{key_prefix}_tags'].pop(i)
                        st.rerun()
        
        return st.session_state[f'{key_prefix}_tags']

    def display_annotation_summary(annotations, title="Résumé"):
        if annotations:
            st.markdown(f"**{title}**")
            for ann in annotations:
                st.write(f"• {ann}")

def page_ecg_cases():
    """Page de consultation des cas ECG pour étudiants"""
    
    # Si un cas est sélectionné, afficher le détail
    if 'selected_case' in st.session_state and st.session_state.selected_case:
        display_case_detail(st.session_state.selected_case)
        return
    
    # Sinon, afficher la liste des cas
    st.markdown("## 📚 Cas ECG disponibles")
    
    ECG_CASES_DIR.mkdir(parents=True, exist_ok=True)
    available_cases = []
    
    if ECG_CASES_DIR.exists():
        for case_dir in ECG_CASES_DIR.iterdir():
            if case_dir.is_dir():
                metadata_file = case_dir / "metadata.json"
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(case_dir.glob(ext))
                if metadata_file.exists() and image_files:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            case_data = json.load(f)
                        sorted_images = sorted(image_files, key=lambda x: x.name)
                        case_data['image_paths'] = [str(img) for img in sorted_images]
                        case_data['image_path'] = str(sorted_images[0])
                        case_data['total_images'] = len(sorted_images)
                        case_data['case_folder'] = str(case_dir)
                        case_id = case_data.get('case_id', case_dir.name)
                        case_data['case_id'] = case_id
                        available_cases.append(case_data)
                    except Exception as e:
                        st.warning(f"⚠️ Erreur lecture métadonnées {case_dir.name}: {e}")

    if available_cases:
        st.success(f"✅ {len(available_cases)} cas disponibles")
        
        # Affichage en grille avec 3 colonnes
        cols_per_row = 3
        for i in range(0, len(available_cases), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(available_cases):
                    case_data = available_cases[i + j]
                    with cols[j]:
                        display_case_thumbnail(case_data)
    else:
        st.warning("⚠️ Aucun cas ECG disponible")
        st.info("""
        **💡 Pour avoir des cas disponibles :**
        1. Passez en mode Administrateur/Expert
        2. Utilisez l'Import Intelligent pour ajouter des ECG
        3. Annotez les cas dans la Liseuse ECG
        4. Les cas annotés apparaîtront ici pour les étudiants
        """)

def display_case_thumbnail(case_data):
    """Affiche une vignette pour un cas ECG"""
    case_id = case_data.get('case_id', 'Cas ECG')
    
    # Container pour la vignette
    with st.container():
        # Afficher la première image comme vignette
        if 'image_paths' in case_data and case_data['image_paths']:
            image_path = Path(case_data['image_paths'][0])
            if image_path.exists():
                st.image(str(image_path), use_container_width=True)
            else:
                st.info("📄 Image non disponible")
        
        # Informations du cas
        st.markdown(f"**{case_id}**")
        
        # Nombre d'ECG dans le cas
        if case_data.get('total_images', 1) > 1:
            st.caption(f"📊 {case_data['total_images']} ECG")
        
        # Bouton pour ouvrir le cas
        if st.button("📋 CAS ECG", key=f"open_{case_id}", use_container_width=True, type="primary"):
            st.session_state.selected_case = case_data
            st.rerun()

def display_case_detail(case_data):
    """Affiche le détail d'un cas ECG avec interface d'annotation"""
    case_id = case_data.get('case_id', 'Cas ECG')
    
    # Bouton retour
    if st.button("◀ Retour à la liste", key="back_to_list"):
        st.session_state.selected_case = None
        st.rerun()
    
    st.markdown(f"## 📋 Cas ECG: {case_id}")
    
    # Layout principal
    col_ecg, col_annot = st.columns([3, 2])
    
    with col_ecg:
        # Affichage ECG(s)
        if 'image_paths' in case_data and case_data['image_paths']:
            total_images = len(case_data['image_paths'])
            
            # Navigation entre les ECG avec flèches
            col_nav1, col_select, col_nav2 = st.columns([1, 3, 1])
            
            # Initialiser l'index si nécessaire
            if f'ecg_index_{case_id}' not in st.session_state:
                st.session_state[f'ecg_index_{case_id}'] = 0
            
            current_index = st.session_state[f'ecg_index_{case_id}']
            
            with col_nav1:
                if st.button("◀", key=f"prev_ecg_{case_id}", disabled=(current_index == 0)):
                    st.session_state[f'ecg_index_{case_id}'] = current_index - 1
                    st.rerun()
            
            with col_select:
                if total_images > 1:
                    ecg_index = st.selectbox(
                        "Sélectionner l'ECG :",
                        range(total_images),
                        format_func=lambda i: f"ECG {i+1}/{total_images}",
                        key=f"detail_ecg_select_{case_id}",
                        index=current_index
                    )
                    if ecg_index != current_index:
                        st.session_state[f'ecg_index_{case_id}'] = ecg_index
                        st.rerun()
                else:
                    ecg_index = 0
                    st.info(f"📊 Ce cas contient **1 ECG**")
            
            with col_nav2:
                if st.button("▶", key=f"next_ecg_{case_id}", disabled=(current_index >= total_images - 1)):
                    st.session_state[f'ecg_index_{case_id}'] = current_index + 1
                    st.rerun()
            
            # Bouton pour basculer vers le visualiseur avancé
            col_tools1, col_tools2 = st.columns([3, 1])
            with col_tools2:
                if st.button("🔍 Outils", key=f"tools_{case_id}", type="secondary"):
                    # Basculer l'état du visualiseur avancé
                    viewer_key = f'advanced_viewer_{case_id}'
                    st.session_state[viewer_key] = not st.session_state.get(viewer_key, False)
                    st.rerun()
            
            # Affichage de l'image - normale ou avec visualiseur avancé
            image_path = Path(case_data['image_paths'][current_index])
            
            if image_path.exists():
                # Vérifier si le visualiseur avancé est activé
                if st.session_state.get(f'advanced_viewer_{case_id}', False):
                    try:
                        from advanced_ecg_viewer import create_advanced_ecg_viewer
                        st.info("🔍 Visualiseur avancé activé - Utilisez les outils de zoom et mesure")
                        viewer_html = create_advanced_ecg_viewer(
                            image_path=str(image_path),
                            title=f"ECG {current_index+1}/{total_images} - {case_id}"
                        )
                        st.components.v1.html(
                            viewer_html,
                            height=800,
                            scrolling=False
                        )
                    except ImportError:
                        st.warning("⚠️ Module advanced_ecg_viewer non disponible")
                        st.image(str(image_path), 
                               caption=f"ECG {current_index+1}/{total_images} - {case_id}",
                               use_container_width=True)
                else:
                    # Affichage normal
                    st.image(str(image_path), 
                           caption=f"ECG {current_index+1}/{total_images} - {case_id}",
                           use_container_width=True)
            else:
                st.warning(f"⚠️ ECG {current_index+1} non trouvé")
    
    with col_annot:
        st.markdown("### 📝 Vos annotations")
        
        # Interface d'annotation avec autocomplétion
        key_prefix = f"student_{case_id}_annotations"
        
        # Initialiser les annotations si nécessaire
        if 'student_annotations' not in st.session_state:
            st.session_state['student_annotations'] = {}
        
        # Charger depuis fichier si disponible
        student_file = Path(case_data['case_folder']) / "student_annotations.json"
        if key_prefix not in st.session_state['student_annotations']:
            if student_file.exists():
                try:
                    with open(student_file, 'r', encoding='utf-8') as f:
                        st.session_state['student_annotations'][key_prefix] = json.load(f)
                except Exception:
                    st.session_state['student_annotations'][key_prefix] = []
            else:
                st.session_state['student_annotations'][key_prefix] = []
        
        # Interface d'annotation
        annotations = smart_annotation_input(
            key_prefix=key_prefix,
            max_tags=15
        )
        
        # Bouton de sauvegarde
        if st.button("💾 Sauvegarder mes annotations", key=f"save_detail_{case_id}"):
            st.session_state['student_annotations'][key_prefix] = annotations
            try:
                student_folder = Path(case_data['case_folder'])
                student_file = student_folder / "student_annotations.json"
                with open(student_file, 'w', encoding='utf-8') as f:
                    json.dump(annotations, f, ensure_ascii=False, indent=2)
                st.success("✅ Sauvegardé !")
            except Exception as e:
                st.error(f"Erreur : {e}")
        
        # Résumé structuré
        if annotations:
            st.markdown("---")
            display_annotation_summary(annotations, title="📊 Résumé de vos observations")
        
        # Comparaison avec expert
        st.markdown("---")
        show_correction = st.checkbox("Voir la correction experte", key=f"show_corr_detail_{case_id}")
        
        if show_correction:
            # Charger les annotations expertes
            expert_annots = []
            expert_file = Path(case_data['case_folder']) / "annotations.json"
            if expert_file.exists():
                try:
                    with open(expert_file, 'r', encoding='utf-8') as f:
                        expert_annots = json.load(f)
                except Exception:
                    expert_annots = []
            else:
                expert_annots = case_data.get('annotations', [])
            
            expert_tags = []
            for ann in expert_annots:
                if ann.get('type') == 'expert' or ann.get('auteur') == 'expert':
                    if ann.get('annotation_tags'):
                        expert_tags.extend(ann['annotation_tags'])
                    elif ann.get('concept'):
                        expert_tags.append(ann['concept'])
            
            if expert_tags:
                st.markdown("**🧠 Concepts experts :**")
                display_annotation_summary(expert_tags, title="")
                
                # Comparaison
                if annotations:
                    st.markdown("---")
                    overlap = set(expert_tags).intersection(set(annotations))
                    score = len(overlap) / len(expert_tags) * 100 if expert_tags else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Score", f"{score:.0f}%")
                    with col2:
                        st.metric("Concepts trouvés", f"{len(overlap)}/{len(expert_tags)}")
                    
                    if overlap:
                        st.success("✅ Points communs : " + ", ".join(overlap))
                    
                    missed = set(expert_tags) - set(annotations)
                    if missed:
                        st.info("💡 Concepts manqués : " + ", ".join(missed))
            else:
                st.info("Aucune annotation experte disponible pour ce cas.")
