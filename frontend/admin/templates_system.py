"""
📋 Système de Templates et Modèles Prédéfinis pour ECG
Modèles d'annotations, cas types et templates pédagogiques
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import uuid

def display_templates_system():
    """Interface système de templates"""
    
    st.markdown("### 📋 Templates et Modèles Prédéfinis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Templates Annotation", "🎓 Cas Types", "📚 Sessions Modèles", "⚙️ Gestion"])
    
    with tab1:
        display_annotation_templates()
    
    with tab2:
        display_case_templates()
    
    with tab3:
        display_session_templates()
    
    with tab4:
        display_template_management()

def display_annotation_templates():
    """Gestion des templates d'annotation"""
    
    st.markdown("#### 📄 Templates d'Annotation ECG")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("##### 🎯 Templates Disponibles")
        
        templates = load_annotation_templates()
        
        if templates:
            for template_id, template_data in templates.items():
                with st.expander(f"📄 {template_data['name']}"):
                    st.markdown(f"**📝 Description :** {template_data['description']}")
                    st.markdown(f"**📂 Catégorie :** {template_data['category']}")
                    st.markdown(f"**🏷️ Annotations :** {len(template_data['annotations'])}")
                    
                    col_apply, col_edit = st.columns(2)
                    
                    with col_apply:
                        if st.button("📋 Appliquer", key=f"apply_{template_id}"):
                            st.session_state['apply_template'] = template_id
                    
                    with col_edit:
                        if st.button("✏️ Éditer", key=f"edit_{template_id}"):
                            st.session_state['edit_template'] = template_id
        else:
            st.info("📭 Aucun template disponible")
    
    with col2:
        # Application de template
        if 'apply_template' in st.session_state:
            apply_annotation_template(st.session_state['apply_template'])
        
        # Édition de template
        elif 'edit_template' in st.session_state:
            st.markdown("##### ✏️ Édition Template")
            st.info(f"Édition du template : {st.session_state['edit_template']}")
            if st.button("🔙 Retour", key="edit_template_back_btn"):
                del st.session_state['edit_template']
                st.rerun()
        
        # Création nouveau template
        else:
            create_annotation_template()

def display_case_templates():
    """Gestion des templates de cas ECG"""
    
    st.markdown("#### 🎓 Cas Types ECG")
    
    st.info("""
    **🎯 Cas types disponibles :**
    - 📊 Infarctus du myocarde (STEMI/NSTEMI)
    - 💓 Troubles du rythme (FA, Flutter, TV)
    - 🔒 Blocs de conduction (BAV, BBG, BBD)
    - 📈 Hypertrophies (VG, VD, OG, OD)
    - ✅ ECG normaux (différents âges)
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📋 Créer Cas Type")
        
        case_categories = {
            "Infarctus": ["STEMI Antérieur", "STEMI Inférieur", "NSTEMI", "Onde Q de nécrose"],
            "Arythmie": ["Fibrillation Auriculaire", "Flutter Auriculaire", "Tachycardie Ventriculaire", "ESV"],
            "Bloc": ["BAV 1er degré", "BAV 2ème degré", "BAV 3ème degré", "BBG", "BBD"],
            "Hypertrophie": ["HVG", "HVD", "HOG", "HOD"],
            "Normal": ["ECG Normal Adulte", "ECG Normal Enfant", "Variante Normale"]
        }
        
        selected_category = st.selectbox("Catégorie :", list(case_categories.keys()), key="case_category_select")
        selected_type = st.selectbox("Type spécifique :", case_categories[selected_category], key="case_type_select")
        
        if st.button("🎯 **Créer Cas Type**", type="primary", key="create_case_type_btn"):
            create_case_template(selected_category, selected_type)
    
    with col2:
        st.markdown("##### 📚 Bibliothèque de Cas")
        
        case_templates = load_case_templates()
        
        if case_templates:
            for template_id, template_data in case_templates.items():
                with st.expander(f"🎓 {template_data['name']}"):
                    st.markdown(f"**📂 Catégorie :** {template_data['category']}")
                    st.markdown(f"**🎯 Difficulté :** {template_data['difficulty']}")
                    st.markdown(f"**📝 Description :** {template_data['description'][:100]}...")
                    
                    if st.button("🚀 Utiliser Template", key=f"use_case_{template_id}"):
                        st.info(f"Template {template_data['name']} sélectionné pour utilisation")
                        st.session_state['selected_case_template'] = template_id
        else:
            st.info("📭 Aucun cas type disponible")

def display_session_templates():
    """Gestion des templates de sessions"""
    
    st.markdown("#### 📚 Sessions Modèles")
    
    predefined_sessions = {
        "Débutant": {
            "ECG de Base": {
                "description": "Reconnaissance des éléments de base",
                "cases": ["ECG Normal Adulte", "Bradycardie Sinusale", "Tachycardie Sinusale"],
                "duration": 30
            },
            "Troubles du Rythme": {
                "description": "Arythmies courantes",
                "cases": ["Fibrillation Auriculaire", "ESV Isolées", "Flutter Auriculaire"],
                "duration": 45
            }
        },
        "Intermédiaire": {
            "Infarctus": {
                "description": "Reconnaissance des infarctus",
                "cases": ["STEMI Antérieur", "STEMI Inférieur", "NSTEMI"],
                "duration": 60
            },
            "Blocs de Conduction": {
                "description": "Troubles de conduction",
                "cases": ["BAV 1er degré", "BBG", "BBD"],
                "duration": 45
            }
        },
        "Avancé": {
            "Cas Complexes": {
                "description": "Cas multi-pathologies",
                "cases": ["FA + HVG", "STEMI + BAV", "TV Polymorphe"],
                "duration": 90
            }
        }
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🎯 Sessions Prédéfinies")
        
        for level, sessions in predefined_sessions.items():
            st.markdown(f"**📊 Niveau {level}**")
            
            for session_name, session_data in sessions.items():
                with st.expander(f"📚 {session_name}"):
                    st.markdown(f"**📝 Description :** {session_data['description']}")
                    st.markdown(f"**⏱️ Durée :** {session_data['duration']} min")
                    st.markdown(f"**📋 Cas ({len(session_data['cases'])}) :** {', '.join(session_data['cases'][:3])}...")
                    
                    if st.button("🚀 Créer Session", key=f"create_session_{level}_{session_name}"):
                        create_session_from_template(level, session_name, session_data)
    
    with col2:
        st.markdown("##### ➕ Créer Session Personnalisée")
        
        session_name = st.text_input("Nom de la session :", key="session_name_input")
        session_description = st.text_area("Description :", key="session_description_area")
        session_level = st.selectbox("Niveau :", ["Débutant", "Intermédiaire", "Avancé", "Expert"], key="session_level_select")
        session_duration = st.number_input("Durée (minutes) :", min_value=15, max_value=180, value=60, key="session_duration_input")
        
        available_cases = get_available_cases()
        if available_cases:
            selected_cases = st.multiselect(
                "Sélectionner cas ECG :",
                options=[case['case_id'] for case in available_cases],
                format_func=lambda x: f"📋 {x}",
                key="session_cases_multiselect"
            )
            
            if st.button("📚 **Créer Session**", type="primary", key="create_custom_session_btn"):
                if session_name and selected_cases:
                    create_custom_session(session_name, session_description, session_level, session_duration, selected_cases)
                    st.success("✅ Session créée !")
                else:
                    st.warning("⚠️ Remplir nom et sélectionner des cas")
        else:
            st.warning("📭 Aucun cas ECG disponible")

def display_template_management():
    """Gestion des templates"""
    
    st.markdown("#### ⚙️ Gestion des Templates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📤 Export Templates")
        
        if st.button("💾 **Exporter Tous les Templates**", key="export_all_templates_btn"):
            export_all_templates()
        
        st.markdown("##### 📊 Statistiques")
        
        display_template_statistics()
    
    with col2:
        st.markdown("##### 📥 Import Templates")
        
        uploaded_template = st.file_uploader(
            "Importer templates :",
            type=['json'],
            help="Fichier JSON de templates",
            key="import_templates_uploader"
        )
        
        if uploaded_template:
            if st.button("📥 **Importer**", key="import_templates_btn"):
                import_templates(uploaded_template)
        
        st.markdown("##### 🗑️ Nettoyage")
        
        if st.button("🧹 **Nettoyer Templates Orphelins**", key="clean_orphaned_templates_btn"):
            clean_orphaned_templates()

def load_annotation_templates():
    """Charge les templates d'annotation"""
    
    template_file = Path("data/annotation_templates.json")
    
    if template_file.exists():
        with open(template_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Templates par défaut
        default_templates = create_default_annotation_templates()
        save_annotation_templates(default_templates)
        return default_templates

def create_default_annotation_templates():
    """Crée templates d'annotation par défaut"""
    
    templates = {
        "ecg_normal": {
            "name": "ECG Normal",
            "description": "Template pour ECG normal",
            "category": "Normal",
            "annotations": [
                {"concept": "Rythme sinusal", "type": "expert", "coefficient": 1.0},
                {"concept": "Fréquence normale", "type": "expert", "coefficient": 1.0},
                {"concept": "Axe normal", "type": "expert", "coefficient": 0.8},
                {"concept": "Pas d'anomalie de repolarisation", "type": "expert", "coefficient": 0.8}
            ],
            "created_date": datetime.now().isoformat()
        },
        "infarctus_stemi": {
            "name": "Infarctus STEMI",
            "description": "Template pour infarctus STEMI",
            "category": "Infarctus",
            "annotations": [
                {"concept": "Sus-décalage ST", "type": "expert", "coefficient": 1.0},
                {"concept": "Ondes Q de nécrose", "type": "expert", "coefficient": 0.9},
                {"concept": "Miroir", "type": "expert", "coefficient": 0.7},
                {"concept": "Territoire coronaire", "type": "expert", "coefficient": 0.8}
            ],
            "created_date": datetime.now().isoformat()
        }
    }
    
    return templates

def save_annotation_templates(templates):
    """Sauvegarde templates d'annotation"""
    
    template_file = Path("data/annotation_templates.json")
    template_file.parent.mkdir(exist_ok=True)
    
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)

def create_annotation_template():
    """Interface création template d'annotation"""
    
    st.markdown("##### ➕ Créer Template d'Annotation")
    
    template_name = st.text_input("Nom du template :", key="template_name_input")
    template_description = st.text_area("Description :", key="template_description_area")
    template_category = st.selectbox("Catégorie :", ["Normal", "Infarctus", "Arythmie", "Bloc", "Hypertrophie", "Autre"], key="template_category_select")
    
    st.markdown("**🏷️ Annotations du Template**")
    
    # Initialiser annotations dans session state
    if 'template_annotations' not in st.session_state:
        st.session_state.template_annotations = []
    
    # Interface d'ajout d'annotation
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        new_concept = st.text_input("Nouveau concept :", key="new_template_concept")
    
    with col2:
        new_coefficient = st.number_input("Coefficient :", min_value=0.1, max_value=1.0, value=1.0, step=0.1, key="template_coefficient_input")
    
    with col3:
        if st.button("➕ Ajouter", key="add_template_annotation_btn"):
            if new_concept:
                st.session_state.template_annotations.append({
                    "concept": new_concept,
                    "type": "expert",
                    "coefficient": new_coefficient
                })
                st.rerun()
    
    # Affichage annotations actuelles
    if st.session_state.template_annotations:
        st.markdown("**📋 Annotations Actuelles :**")
        
        for i, annotation in enumerate(st.session_state.template_annotations):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"🔹 {annotation['concept']}")
            
            with col2:
                st.markdown(f"⚖️ {annotation['coefficient']}")
            
            with col3:
                if st.button("🗑️", key=f"del_template_ann_{i}"):
                    st.session_state.template_annotations.pop(i)
                    st.rerun()
    
    # Boutons d'action
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 **Sauvegarder Template**", type="primary", key="save_template_btn"):
            if template_name and st.session_state.template_annotations:
                save_new_annotation_template(template_name, template_description, template_category, st.session_state.template_annotations)
                st.session_state.template_annotations = []
                st.success("✅ Template sauvegardé !")
                st.rerun()
            else:
                st.warning("⚠️ Nom et annotations requis")
    
    with col2:
        if st.button("🔄 Réinitialiser", key="reset_template_btn"):
            st.session_state.template_annotations = []
            st.rerun()

def save_new_annotation_template(name, description, category, annotations):
    """Sauvegarde nouveau template d'annotation"""
    
    templates = load_annotation_templates()
    
    template_id = str(uuid.uuid4())[:8]
    
    templates[template_id] = {
        "name": name,
        "description": description,
        "category": category,
        "annotations": annotations,
        "created_date": datetime.now().isoformat()
    }
    
    save_annotation_templates(templates)

def apply_annotation_template(template_id):
    """Interface application template à un cas"""
    
    st.markdown("##### 📋 Appliquer Template")
    
    templates = load_annotation_templates()
    template = templates.get(template_id)
    
    if not template:
        st.error("❌ Template non trouvé")
        return
    
    st.markdown(f"**Template :** {template['name']}")
    
    available_cases = get_available_cases()
    
    if not available_cases:
        st.warning("📭 Aucun cas disponible")
        return
    
    selected_case = st.selectbox(
        "Sélectionner cas :",
        options=[case['case_id'] for case in available_cases],
        format_func=lambda x: f"📋 {x}",
        key="apply_template_case_select"
    )
    
    apply_mode = st.selectbox(
        "Mode d'application :",
        ["Remplacer annotations", "Ajouter aux annotations", "Fusionner intelligent"],
        key="apply_template_mode_select"
    )
    
    if st.button("✅ **Appliquer Template**", type="primary", key="apply_template_action_btn"):
        apply_template_to_case(selected_case, template, apply_mode)
        st.success(f"✅ Template appliqué à {selected_case} !")
        
        if st.button("🔙 Retour", key="apply_template_back_btn"):
            del st.session_state['apply_template']
            st.rerun()

def apply_template_to_case(case_id, template, mode):
    """Applique template à un cas ECG"""
    
    case_dir = Path("data/ecg_cases") / case_id
    metadata_file = case_dir / "metadata.json"
    
    if not metadata_file.exists():
        return
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    current_annotations = metadata.get('annotations', [])
    template_annotations = template['annotations'].copy()
    
    if mode == "Remplacer annotations":
        metadata['annotations'] = template_annotations
    
    elif mode == "Ajouter aux annotations":
        metadata['annotations'] = current_annotations + template_annotations
    
    elif mode == "Fusionner intelligent":
        # Éviter doublons basés sur concept
        existing_concepts = {ann['concept'] for ann in current_annotations}
        new_annotations = [ann for ann in template_annotations if ann['concept'] not in existing_concepts]
        metadata['annotations'] = current_annotations + new_annotations
    
    # Ajouter métadonnées du template
    metadata['template_applied'] = {
        'template_name': template['name'],
        'template_category': template['category'],
        'applied_date': datetime.now().isoformat(),
        'apply_mode': mode
    }
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def load_case_templates():
    """Charge templates de cas"""
    
    template_file = Path("data/case_templates.json")
    
    if template_file.exists():
        with open(template_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {}

def create_case_template(category, case_type):
    """Crée template de cas ECG"""
    
    templates = load_case_templates()
    
    template_id = str(uuid.uuid4())[:8]
    
    # Données par défaut selon le type
    template_data = {
        "name": f"{case_type} - Template",
        "description": f"Template pour cas de type {case_type}",
        "category": category,
        "difficulty": get_default_difficulty(category),
        "clinical_context": get_default_clinical_context(case_type),
        "suggested_annotations": get_default_annotations(case_type),
        "created_date": datetime.now().isoformat()
    }
    
    templates[template_id] = template_data
    
    # Sauvegarder
    template_file = Path("data/case_templates.json")
    template_file.parent.mkdir(exist_ok=True)
    
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    
    st.success(f"✅ Template '{case_type}' créé !")

def get_default_difficulty(category):
    """Retourne difficulté par défaut selon catégorie"""
    
    difficulty_map = {
        "Normal": "Débutant",
        "Arythmie": "Intermédiaire", 
        "Bloc": "Intermédiaire",
        "Infarctus": "Avancé",
        "Hypertrophie": "Intermédiaire"
    }
    
    return difficulty_map.get(category, "Intermédiaire")

def get_default_clinical_context(case_type):
    """Retourne contexte clinique par défaut"""
    
    contexts = {
        "STEMI Antérieur": "Patient 55 ans, douleur thoracique intense, dyspnée",
        "Fibrillation Auriculaire": "Patient 70 ans, palpitations irrégulières",
        "BAV 3ème degré": "Patient syncope, bradycardie symptomatique",
        "HVG": "Patient hypertendu, dyspnée d'effort",
        "ECG Normal Adulte": "Patient 35 ans, bilan systématique"
    }
    
    return contexts.get(case_type, "Contexte clinique à définir")

def get_default_annotations(case_type):
    """Retourne annotations suggérées par défaut"""
    
    annotations = {
        "STEMI Antérieur": ["Sus-décalage ST", "Territoire LAD", "Onde Q", "Miroir inférieur"],
        "Fibrillation Auriculaire": ["Rythme irrégulier", "Absence onde P", "RR variables"],
        "BAV 3ème degré": ["Dissociation AV", "P > QRS", "Échappement ventriculaire"],
        "HVG": ["Onde R amplifiée", "Indice de Sokolow", "Strain pattern"],
        "ECG Normal Adulte": ["Rythme sinusal", "Fréquence normale", "Axe normal"]
    }
    
    return annotations.get(case_type, [])

def create_session_from_template(level, session_name, session_data):
    """Crée session à partir d'un template"""
    
    session_id = f"{level}_{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    session_metadata = {
        "name": f"{level} - {session_name}",
        "description": session_data['description'],
        "level": level,
        "estimated_duration": session_data['duration'],
        "cases": session_data['cases'],
        "created_date": datetime.now().isoformat(),
        "created_from_template": True,
        "template_info": {
            "level": level,
            "original_name": session_name
        }
    }
    
    # Sauvegarder session
    sessions_dir = Path("data/ecg_sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    session_file = sessions_dir / f"{session_id}.json"
    
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_metadata, f, indent=2, ensure_ascii=False)
    
    st.success(f"✅ Session '{session_name}' créée !")

def create_custom_session(name, description, level, duration, cases):
    """Crée session personnalisée"""
    
    session_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    session_metadata = {
        "name": name,
        "description": description,
        "level": level,
        "estimated_duration": duration,
        "cases": cases,
        "created_date": datetime.now().isoformat(),
        "created_from_template": False,
        "custom_session": True
    }
    
    # Sauvegarder session
    sessions_dir = Path("data/ecg_sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    session_file = sessions_dir / f"{session_id}.json"
    
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_metadata, f, indent=2, ensure_ascii=False)

def export_all_templates():
    """Exporte tous les templates"""
    
    export_data = {
        "export_info": {
            "date": datetime.now().isoformat(),
            "version": "1.0"
        },
        "annotation_templates": load_annotation_templates(),
        "case_templates": load_case_templates()
    }
    
    export_file = Path("exports") / f"templates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    export_file.parent.mkdir(exist_ok=True)
    
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    st.success(f"✅ Templates exportés : {export_file.name}")
    
    # Bouton téléchargement
    with open(export_file, 'rb') as f:
        st.download_button(
            label="📥 Télécharger Export",
            data=f.read(),
            file_name=export_file.name,
            mime='application/json'
        )

def import_templates(uploaded_file):
    """Importe templates depuis fichier"""
    
    try:
        data = json.loads(uploaded_file.read().decode('utf-8'))
        
        # Import templates annotation
        if 'annotation_templates' in data:
            current_ann_templates = load_annotation_templates()
            current_ann_templates.update(data['annotation_templates'])
            save_annotation_templates(current_ann_templates)
        
        # Import templates cas
        if 'case_templates' in data:
            current_case_templates = load_case_templates()
            current_case_templates.update(data['case_templates'])
            
            case_template_file = Path("data/case_templates.json")
            case_template_file.parent.mkdir(exist_ok=True)
            
            with open(case_template_file, 'w', encoding='utf-8') as f:
                json.dump(current_case_templates, f, indent=2, ensure_ascii=False)
        
        st.success("✅ Templates importés avec succès !")
        
    except Exception as e:
        st.error(f"❌ Erreur import : {e}")

def display_template_statistics():
    """Affiche statistiques des templates"""
    
    ann_templates = load_annotation_templates()
    case_templates = load_case_templates()
    
    st.metric("📄 Templates Annotation", len(ann_templates))
    st.metric("🎓 Templates Cas", len(case_templates))
    
    # Répartition par catégorie
    categories = {}
    for template in ann_templates.values():
        cat = template.get('category', 'Autre')
        categories[cat] = categories.get(cat, 0) + 1
    
    if categories:
        st.markdown("**📊 Répartition Annotations :**")
        for cat, count in categories.items():
            st.markdown(f"- {cat}: {count}")

def clean_orphaned_templates():
    """Nettoie templates orphelins"""
    
    with st.spinner("🧹 Nettoyage en cours..."):
        # Logique de nettoyage des templates non utilisés
        cleaned_count = 0
        
        # Ici on pourrait implémenter la logique de nettoyage
        # Par exemple, supprimer templates non utilisés depuis X jours
        
        st.success(f"✅ {cleaned_count} templates orphelins supprimés")

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

if __name__ == "__main__":
    display_templates_system()
