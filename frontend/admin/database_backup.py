"""
🔄 Système de Backup et Export/Import pour Base de Données ECG
Sauvegarde, restauration et migration des données
"""

import streamlit as st
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import os
import pandas as pd

def display_backup_system():
    """Interface système de backup et export/import"""
    
    st.markdown("### 💾 Système de Backup et Export/Import")
    
    tab1, tab2, tab3 = st.tabs(["📤 Export/Backup", "📥 Import/Restauration", "📊 Gestion Backups"])
    
    with tab1:
        display_export_interface()
    
    with tab2:
        display_import_interface()
    
    with tab3:
        display_backup_management()

def display_export_interface():
    """Interface d'export et backup"""
    
    st.markdown("#### 📤 Export de la Base de Données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🎯 Export Sélectif")
        
        # Sélection des cas à exporter
        available_cases = get_available_cases()
        
        if not available_cases:
            st.warning("📭 Aucun cas disponible pour export")
            return
        
        selected_cases = st.multiselect(
            "Sélectionner les cas à exporter :",
            options=[case['case_id'] for case in available_cases],
            format_func=lambda x: f"📋 {x}",
            help="Choisir les cas ECG à inclure dans l'export"
        )
        
        # Options d'export
        st.markdown("##### ⚙️ Options d'Export")
        
        include_images = st.checkbox("📷 Inclure images ECG", value=True, 
                                   help="Exporter les fichiers images avec métadonnées")
        include_annotations = st.checkbox("🏷️ Inclure annotations", value=True,
                                        help="Exporter toutes les annotations")
        include_sessions = st.checkbox("📚 Inclure sessions", value=False,
                                     help="Exporter les sessions d'exercices liées")
        
        # Format d'export
        export_format = st.selectbox(
            "📁 Format d'export :",
            ["ZIP Archive", "JSON Métadonnées seules", "CSV Tableau"],
            help="Choisir le format de sortie"
        )
        
        if st.button("🚀 **Créer Export**", type="primary", use_container_width=True):
            if selected_cases:
                create_export(selected_cases, include_images, include_annotations, 
                            include_sessions, export_format)
            else:
                st.warning("⚠️ Sélectionner au moins un cas")
    
    with col2:
        st.markdown("##### 💾 Backup Complet")
        
        st.info("""
        **Backup automatique inclut :**
        - 📋 Tous les cas ECG
        - 🏷️ Toutes les annotations 
        - 📚 Sessions utilisateur
        - ⚙️ Configuration système
        - 👥 Profils utilisateurs
        """)
        
        backup_name = st.text_input(
            "Nom du backup :",
            value=f"backup_ecg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Nom personnalisé pour le backup"
        )
        
        if st.button("💾 **Créer Backup Complet**", type="secondary", use_container_width=True):
            create_full_backup(backup_name)

def display_import_interface():
    """Interface d'import et restauration"""
    
    st.markdown("#### 📥 Import et Restauration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📤 Import de Cas ECG")
        
        uploaded_file = st.file_uploader(
            "Fichier d'import :",
            type=['zip', 'json'],
            help="Fichier ZIP ou JSON exporté depuis Edu-CG"
        )
        
        if uploaded_file:
            st.success(f"✅ Fichier chargé : {uploaded_file.name}")
            
            # Options d'import
            import_mode = st.selectbox(
                "Mode d'import :",
                ["Ajouter aux cas existants", "Remplacer cas existants", "Import sélectif"],
                help="Comportement en cas de conflit"
            )
            
            if st.button("📥 **Importer**", type="primary"):
                process_import(uploaded_file, import_mode)
    
    with col2:
        st.markdown("##### 🔄 Restauration Backup")
        
        # Liste des backups disponibles
        backups_dir = Path("backups")
        if backups_dir.exists():
            backup_files = list(backups_dir.glob("*.zip"))
            
            if backup_files:
                selected_backup = st.selectbox(
                    "Sélectionner backup :",
                    options=backup_files,
                    format_func=lambda x: f"💾 {x.name} ({get_file_size(x)})",
                    help="Choisir le backup à restaurer"
                )
                
                st.warning("⚠️ **ATTENTION** : La restauration remplacera toutes les données actuelles !")
                
                confirm_restore = st.checkbox("Je confirme vouloir restaurer ce backup")
                
                if st.button("🔄 **Restaurer**", disabled=not confirm_restore):
                    restore_backup(selected_backup)
            else:
                st.info("📭 Aucun backup disponible")
        else:
            st.info("📁 Dossier backup non trouvé")

def display_backup_management():
    """Gestion des backups existants"""
    
    st.markdown("#### 📊 Gestion des Backups")
    
    backups_dir = Path("backups")
    
    if not backups_dir.exists():
        backups_dir.mkdir(exist_ok=True)
        st.info("📁 Dossier backup créé")
        return
    
    backup_files = list(backups_dir.glob("*.zip"))
    
    if not backup_files:
        st.info("📭 Aucun backup disponible")
        return
    
    # Tableau des backups
    st.markdown("##### 📋 Backups Disponibles")
    
    backup_data = []
    for backup_file in backup_files:
        stat = backup_file.stat()
        backup_data.append({
            'Nom': backup_file.name,
            'Taille': get_file_size(backup_file),
            'Date': datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            'Chemin': str(backup_file)
        })
    
    df_backups = pd.DataFrame(backup_data)
    
    # Affichage avec actions
    for idx, backup in df_backups.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"**📦 {backup['Nom']}**")
            st.caption(f"📅 {backup['Date']} • 💾 {backup['Taille']}")
        
        with col2:
            if st.button("📥", key=f"restore_{idx}", help="Restaurer"):
                st.session_state[f"confirm_restore_{idx}"] = True
        
        with col3:
            if st.button("📋", key=f"info_{idx}", help="Informations"):
                show_backup_info(backup['Chemin'])
        
        with col4:
            if st.button("🗑️", key=f"delete_{idx}", help="Supprimer"):
                st.session_state[f"confirm_delete_{idx}"] = True
        
        # Gestion confirmations
        if st.session_state.get(f"confirm_restore_{idx}"):
            handle_restore_confirmation(backup['Chemin'], idx)
        
        if st.session_state.get(f"confirm_delete_{idx}"):
            handle_delete_confirmation(backup['Chemin'], idx)
        
        st.markdown("---")

def get_available_cases():
    """Récupère liste des cas disponibles"""
    
    cases = []
    cases_dir = Path("data/ecg_cases")
    
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                cases.append({
                    'case_id': case_dir.name,
                    'path': case_dir
                })
    
    return cases

def create_export(selected_cases, include_images, include_annotations, include_sessions, export_format):
    """Crée export sélectif"""
    
    try:
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_format == "ZIP Archive":
            export_path = export_dir / f"export_ecg_{timestamp}.zip"
            create_zip_export(selected_cases, export_path, include_images, include_annotations)
            
        elif export_format == "JSON Métadonnées seules":
            export_path = export_dir / f"metadata_ecg_{timestamp}.json"
            create_json_export(selected_cases, export_path)
            
        elif export_format == "CSV Tableau":
            export_path = export_dir / f"tableau_ecg_{timestamp}.csv"
            create_csv_export(selected_cases, export_path)
        
        st.success(f"✅ Export créé : {export_path.name}")
        
        # Bouton de téléchargement
        with open(export_path, 'rb') as f:
            st.download_button(
                label="📥 Télécharger Export",
                data=f.read(),
                file_name=export_path.name,
                mime='application/octet-stream'
            )
            
    except Exception as e:
        st.error(f"❌ Erreur export : {e}")

def create_zip_export(selected_cases, export_path, include_images, include_annotations):
    """Crée export ZIP"""
    
    with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for case_id in selected_cases:
            case_dir = Path("data/ecg_cases") / case_id
            
            if case_dir.exists():
                # Métadonnées
                metadata_file = case_dir / "metadata.json"
                if metadata_file.exists():
                    zipf.write(metadata_file, f"{case_id}/metadata.json")
                
                # Images ECG
                if include_images:
                    for img_file in case_dir.glob("*.png"):
                        zipf.write(img_file, f"{case_id}/{img_file.name}")
                    for img_file in case_dir.glob("*.jpg"):
                        zipf.write(img_file, f"{case_id}/{img_file.name}")

def create_json_export(selected_cases, export_path):
    """Crée export JSON métadonnées"""
    
    export_data = {
        'export_info': {
            'date': datetime.now().isoformat(),
            'version': '1.0',
            'cases_count': len(selected_cases)
        },
        'cases': []
    }
    
    for case_id in selected_cases:
        case_dir = Path("data/ecg_cases") / case_id
        metadata_file = case_dir / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                export_data['cases'].append(case_data)
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

def create_csv_export(selected_cases, export_path):
    """Crée export CSV tableau"""
    
    cases_data = []
    
    for case_id in selected_cases:
        case_dir = Path("data/ecg_cases") / case_id
        metadata_file = case_dir / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
                cases_data.append({
                    'Case ID': case_id,
                    'Nom': metadata.get('name', ''),
                    'Description': metadata.get('description', ''),
                    'Catégorie': metadata.get('category', ''),
                    'Difficulté': metadata.get('difficulty', ''),
                    'Date Création': metadata.get('created_date', ''),
                    'Annotations': len(metadata.get('annotations', []))
                })
    
    df = pd.DataFrame(cases_data)
    df.to_csv(export_path, index=False, encoding='utf-8')

def create_full_backup(backup_name):
    """Crée backup complet du système"""
    
    try:
        backups_dir = Path("backups")
        backups_dir.mkdir(exist_ok=True)
        
        backup_path = backups_dir / f"{backup_name}.zip"
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Cas ECG
            cases_dir = Path("data/ecg_cases")
            if cases_dir.exists():
                for file in cases_dir.rglob("*"):
                    if file.is_file():
                        zipf.write(file, f"ecg_cases/{file.relative_to(cases_dir)}")
            
            # Sessions
            sessions_dir = Path("data/ecg_sessions")
            if sessions_dir.exists():
                for file in sessions_dir.rglob("*"):
                    if file.is_file():
                        zipf.write(file, f"ecg_sessions/{file.relative_to(sessions_dir)}")
            
            # Profils utilisateurs
            users_dir = Path("users")
            if users_dir.exists():
                for file in users_dir.rglob("*"):
                    if file.is_file():
                        zipf.write(file, f"users/{file.relative_to(users_dir)}")
            
            # Ontologie
            ontology_file = Path("data/ontologie.owx")
            if ontology_file.exists():
                zipf.write(ontology_file, "data/ontologie.owx")
        
        file_size = get_file_size(backup_path)
        st.success(f"✅ Backup créé : {backup_path.name} ({file_size})")
        
    except Exception as e:
        st.error(f"❌ Erreur backup : {e}")

def process_import(uploaded_file, import_mode):
    """Traite import de fichier"""
    
    try:
        with st.spinner("📥 Import en cours..."):
            # Créer dossier temporaire
            temp_dir = Path("temp_import")
            temp_dir.mkdir(exist_ok=True)
            
            # Sauvegarder fichier uploadé
            temp_file = temp_dir / uploaded_file.name
            with open(temp_file, 'wb') as f:
                f.write(uploaded_file.read())
            
            # Traiter selon le type
            if uploaded_file.name.endswith('.zip'):
                process_zip_import(temp_file, import_mode)
            elif uploaded_file.name.endswith('.json'):
                process_json_import(temp_file, import_mode)
            
            # Nettoyage
            shutil.rmtree(temp_dir)
        
        st.success("✅ Import terminé avec succès !")
        
    except Exception as e:
        st.error(f"❌ Erreur import : {e}")

def process_zip_import(zip_file, import_mode):
    """Traite import ZIP"""
    
    cases_dir = Path("data/ecg_cases")
    cases_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(zip_file, 'r') as zipf:
        zipf.extractall("temp_extract")
        
        extract_dir = Path("temp_extract")
        
        # Traiter chaque cas
        for case_folder in extract_dir.iterdir():
            if case_folder.is_dir():
                target_dir = cases_dir / case_folder.name
                
                if target_dir.exists() and import_mode == "Ajouter aux cas existants":
                    st.warning(f"⚠️ Cas {case_folder.name} existe déjà, ignoré")
                    continue
                
                # Copier le cas
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                
                shutil.copytree(case_folder, target_dir)
                st.info(f"📋 Cas importé : {case_folder.name}")
        
        # Nettoyage
        shutil.rmtree(extract_dir)

def process_json_import(json_file, import_mode):
    """Traite import JSON métadonnées"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cases_dir = Path("data/ecg_cases")
    cases_dir.mkdir(exist_ok=True)
    
    for case_data in data.get('cases', []):
        case_id = case_data.get('case_id', case_data.get('name', 'unknown'))
        case_folder = cases_dir / case_id
        
        if case_folder.exists() and import_mode == "Ajouter aux cas existants":
            continue
        
        case_folder.mkdir(exist_ok=True)
        
        # Sauvegarder métadonnées
        metadata_file = case_folder / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)
        
        st.info(f"📋 Métadonnées importées : {case_id}")

def restore_backup(backup_file):
    """Restaure backup complet"""
    
    try:
        with st.spinner("🔄 Restauration en cours..."):
            # Sauvegarde temporaire
            temp_backup_dir = Path("temp_backup_current")
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
            
            # Extraire backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall("temp_restore")
            
            restore_dir = Path("temp_restore")
            
            # Restaurer chaque composant
            components = {
                "data/ecg_cases": restore_dir / "ecg_cases",
                "data/ecg_sessions": restore_dir / "ecg_sessions", 
                "users": restore_dir / "users"
            }
            
            for target, source in components.items():
                if source.exists():
                    target_path = Path(target)
                    
                    # Backup actuel
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    
                    # Restaurer
                    target_path.parent.mkdir(exist_ok=True)
                    shutil.copytree(source, target_path)
            
            # Nettoyage
            shutil.rmtree(restore_dir)
        
        st.success("✅ Restauration terminée !")
        st.info("🔄 Redémarrez l'application pour voir les changements")
        
    except Exception as e:
        st.error(f"❌ Erreur restauration : {e}")

def get_file_size(file_path):
    """Retourne taille formatée du fichier"""
    
    size_bytes = file_path.stat().st_size
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"

def show_backup_info(backup_path):
    """Affiche informations détaillées du backup"""
    
    try:
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            files = zipf.namelist()
            
            st.info(f"""
            **📦 Informations Backup**
            - **Fichiers** : {len(files)}
            - **Taille** : {get_file_size(Path(backup_path))}
            - **Cas ECG** : {len([f for f in files if 'ecg_cases' in f])}
            - **Sessions** : {len([f for f in files if 'ecg_sessions' in f])}
            """)
            
    except Exception as e:
        st.error(f"❌ Erreur lecture backup : {e}")

def handle_restore_confirmation(backup_path, idx):
    """Gère confirmation restauration"""
    
    st.warning(f"⚠️ Restaurer {Path(backup_path).name} ?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirmer", key=f"conf_restore_{idx}"):
            restore_backup(backup_path)
            del st.session_state[f"confirm_restore_{idx}"]
            st.rerun()
    
    with col2:
        if st.button("❌ Annuler", key=f"canc_restore_{idx}"):
            del st.session_state[f"confirm_restore_{idx}"]
            st.rerun()

def handle_delete_confirmation(backup_path, idx):
    """Gère confirmation suppression"""
    
    st.warning(f"🗑️ Supprimer {Path(backup_path).name} ?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Supprimer", key=f"conf_delete_{idx}"):
            Path(backup_path).unlink()
            st.success("✅ Backup supprimé")
            del st.session_state[f"confirm_delete_{idx}"]
            st.rerun()
    
    with col2:
        if st.button("❌ Annuler", key=f"canc_delete_{idx}"):
            del st.session_state[f"confirm_delete_{idx}"]
            st.rerun()

if __name__ == "__main__":
    display_backup_system()
