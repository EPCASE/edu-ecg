"""
🏷️ Système de Tags et Métadonnées Avancés pour ECG
Classification intelligente et recherche sémantique
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re

def display_advanced_tagging_system():
    """Interface système de tags et métadonnées avancés"""
    
    st.markdown("### 🏷️ Système de Tags et Métadonnées Avancés")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏷️ Gestion Tags", "📋 Métadonnées", "🔍 Recherche Avancée", "📊 Classification"])
    
    with tab1:
        display_tag_management()
    
    with tab2:
        display_metadata_editor()
    
    with tab3:
        display_advanced_search()
    
    with tab4:
        display_auto_classification()

def display_tag_management():
    """Interface de gestion des tags"""
    
    st.markdown("#### 🏷️ Gestion des Tags ECG")
    
    # Charger système de tags
    tag_system = load_tag_system()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("##### ➕ Créer Tags")
        
        # Catégories de tags
        tag_categories = ["Pathologie", "Âge Patient", "Qualité ECG", "Dérivations", "Rythme", "Morphologie", "Contexte Clinique", "Difficulté", "Personnalisé"]
        
        selected_category = st.selectbox("Catégorie :", tag_categories)
        
        new_tag = st.text_input("Nouveau tag :", placeholder="Ex: Fibrillation Auriculaire")
        
        tag_color = st.color_picker("Couleur :", "#1f77b4")
        
        tag_description = st.text_area("Description :", placeholder="Description du tag...")
        
        if st.button("➕ **Ajouter Tag**", type="primary"):
            if new_tag:
                add_new_tag(tag_system, selected_category, new_tag, tag_color, tag_description)
                st.success(f"✅ Tag '{new_tag}' ajouté !")
                st.rerun()
            else:
                st.warning("⚠️ Entrer un nom de tag")
    
    with col2:
        st.markdown("##### 📊 Tags Existants")
        
        # Affichage par catégorie
        for category, tags in tag_system.items():
            if tags:  # Seulement si la catégorie a des tags
                with st.expander(f"📁 {category} ({len(tags)})"):
                    for tag_name, tag_info in tags.items():
                        col_tag, col_actions = st.columns([3, 1])
                        
                        with col_tag:
                            st.markdown(f"""
                            <div style="display: inline-block; background-color: {tag_info['color']}; 
                                        color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                                {tag_name}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if tag_info.get('description'):
                                st.caption(tag_info['description'])
                        
                        with col_actions:
                            if st.button("🗑️", key=f"del_tag_{category}_{tag_name}", help="Supprimer"):
                                delete_tag(tag_system, category, tag_name)
                                st.rerun()
    
    # Application des tags aux cas
    st.markdown("---")
    st.markdown("##### 🎯 Appliquer Tags aux Cas")
    
    available_cases = get_available_cases()
    
    if available_cases:
        selected_case = st.selectbox(
            "Sélectionner cas :",
            options=[case['case_id'] for case in available_cases],
            format_func=lambda x: f"📋 {x}"
        )
        
        if selected_case:
            apply_tags_to_case(selected_case, tag_system)

def display_metadata_editor():
    """Interface d'édition des métadonnées"""
    
    st.markdown("#### 📋 Éditeur de Métadonnées Avancées")
    
    available_cases = get_available_cases()
    
    if not available_cases:
        st.warning("📭 Aucun cas disponible")
        return
    
    selected_case = st.selectbox(
        "Sélectionner cas à éditer :",
        options=[case['case_id'] for case in available_cases],
        format_func=lambda x: f"📋 {x}"
    )
    
    if selected_case:
        edit_case_metadata(selected_case)

def display_advanced_search():
    """Interface de recherche avancée"""
    
    st.markdown("#### 🔍 Recherche Avancée et Sémantique")
    
    # Critères de recherche
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🎯 Critères de Recherche")
        
        # Recherche textuelle
        search_text = st.text_input("🔍 Recherche libre :", placeholder="Mots-clés, descriptions...")
        
        # Recherche par tags
        tag_system = load_tag_system()
        all_tags = []
        for category, tags in tag_system.items():
            for tag_name in tags.keys():
                all_tags.append(f"{category}: {tag_name}")
        
        selected_tags = st.multiselect("🏷️ Tags :", all_tags)
        
        # Filtres métadonnées
        st.markdown("**📊 Filtres Métadonnées**")
        
        date_range = st.date_input("📅 Période :", value=[], help="Filtrer par date de création")
        
        categories = st.multiselect("📂 Catégories :", 
                                  ["Infarctus", "Arythmie", "Normal", "Bloc", "Hypertrophie", "Autre"])
        
        difficulties = st.multiselect("🎯 Difficultés :", 
                                    ["Débutant", "Intermédiaire", "Avancé", "Expert"])
        
        # Filtres techniques
        st.markdown("**⚙️ Filtres Techniques**")
        
        min_annotations = st.number_input("Min annotations :", min_value=0, value=0)
        
        ecg_type = st.selectbox("Type ECG :", ["Tous", "Simple", "Multi-ECG"])
        
        quality_min = st.slider("Score qualité min :", 0, 100, 0)
    
    with col2:
        st.markdown("##### 📊 Résultats de Recherche")
        
        if st.button("🔍 **Rechercher**", type="primary"):
            results = perform_advanced_search({
                'text': search_text,
                'tags': selected_tags,
                'date_range': date_range,
                'categories': categories,
                'difficulties': difficulties,
                'min_annotations': min_annotations,
                'ecg_type': ecg_type,
                'quality_min': quality_min
            })
            
            display_search_results(results)

def display_auto_classification():
    """Interface de classification automatique"""
    
    st.markdown("#### 📊 Classification Automatique")
    
    st.info("""
    **🤖 Classification Intelligente :**
    - Analyse automatique des descriptions
    - Détection de pathologies
    - Suggestion de tags
    - Classification par complexité
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🎯 Classification en Lot")
        
        if st.button("🤖 **Classifier Tous les Cas**", type="primary"):
            classify_all_cases()
        
        st.markdown("##### 📝 Classification Manuelle")
        
        available_cases = get_available_cases()
        
        if available_cases:
            selected_case = st.selectbox(
                "Cas à classifier :",
                options=[case['case_id'] for case in available_cases],
                format_func=lambda x: f"📋 {x}"
            )
            
            if st.button(f"🔍 **Analyser {selected_case}**"):
                analyze_single_case(selected_case)
    
    with col2:
        st.markdown("##### 📊 Statistiques Classification")
        
        display_classification_stats()

def load_tag_system():
    """Charge le système de tags"""
    
    tag_file = Path("data/tag_system.json")
    
    if tag_file.exists():
        with open(tag_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Système par défaut
        default_system = {
            "Pathologie": {},
            "Âge Patient": {},
            "Qualité ECG": {},
            "Dérivations": {},
            "Rythme": {},
            "Morphologie": {},
            "Contexte Clinique": {},
            "Difficulté": {},
            "Personnalisé": {}
        }
        save_tag_system(default_system)
        return default_system

def save_tag_system(tag_system):
    """Sauvegarde le système de tags"""
    
    tag_file = Path("data/tag_system.json")
    tag_file.parent.mkdir(exist_ok=True)
    
    with open(tag_file, 'w', encoding='utf-8') as f:
        json.dump(tag_system, f, indent=2, ensure_ascii=False)

def add_new_tag(tag_system, category, tag_name, color, description):
    """Ajoute nouveau tag au système"""
    
    if category not in tag_system:
        tag_system[category] = {}
    
    tag_system[category][tag_name] = {
        'color': color,
        'description': description,
        'created_date': datetime.now().isoformat(),
        'usage_count': 0
    }
    
    save_tag_system(tag_system)

def delete_tag(tag_system, category, tag_name):
    """Supprime tag du système"""
    
    if category in tag_system and tag_name in tag_system[category]:
        del tag_system[category][tag_name]
        save_tag_system(tag_system)

def apply_tags_to_case(case_id, tag_system):
    """Interface pour appliquer tags à un cas"""
    
    # Charger métadonnées du cas
    case_dir = Path("data/ecg_cases") / case_id
    metadata_file = case_dir / "metadata.json"
    
    if not metadata_file.exists():
        st.warning("⚠️ Métadonnées non trouvées")
        return
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    current_tags = metadata.get('tags', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏷️ Tags Actuels**")
        
        if current_tags:
            for tag in current_tags:
                col_tag, col_remove = st.columns([3, 1])
                with col_tag:
                    st.markdown(f"🔹 {tag}")
                with col_remove:
                    if st.button("❌", key=f"remove_{tag}"):
                        current_tags.remove(tag)
                        metadata['tags'] = current_tags
                        save_case_metadata(case_id, metadata)
                        st.rerun()
        else:
            st.info("Aucun tag appliqué")
    
    with col2:
        st.markdown("**➕ Ajouter Tags**")
        
        # Sélection par catégorie
        for category, tags in tag_system.items():
            if tags:
                available_tags = [tag for tag in tags.keys() if tag not in current_tags]
                
                if available_tags:
                    selected_tag = st.selectbox(
                        f"{category} :",
                        ["Sélectionner..."] + available_tags,
                        key=f"select_{category}"
                    )
                    
                    if selected_tag != "Sélectionner..." and st.button(f"➕ Ajouter", key=f"add_{category}"):
                        current_tags.append(selected_tag)
                        metadata['tags'] = current_tags
                        
                        # Incrémenter compteur d'usage
                        tag_system[category][selected_tag]['usage_count'] += 1
                        save_tag_system(tag_system)
                        
                        save_case_metadata(case_id, metadata)
                        st.rerun()

def edit_case_metadata(case_id):
    """Interface d'édition métadonnées complètes"""
    
    case_dir = Path("data/ecg_cases") / case_id
    metadata_file = case_dir / "metadata.json"
    
    if not metadata_file.exists():
        st.warning("⚠️ Métadonnées non trouvées")
        return
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    st.markdown(f"**📋 Édition : {case_id}**")
    
    # Métadonnées de base
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Nom :", value=metadata.get('name', ''))
        category = st.selectbox("Catégorie :", 
                               ["Non classé", "Infarctus", "Arythmie", "Normal", "Bloc", "Hypertrophie", "Autre"],
                               index=0 if metadata.get('category') == 'Non classé' else 
                               ["Non classé", "Infarctus", "Arythmie", "Normal", "Bloc", "Hypertrophie", "Autre"].index(metadata.get('category', 'Non classé')))
        
        difficulty = st.selectbox("Difficulté :",
                                ["Non défini", "Débutant", "Intermédiaire", "Avancé", "Expert"],
                                index=0 if metadata.get('difficulty') == 'Non défini' else
                                ["Non défini", "Débutant", "Intermédiaire", "Avancé", "Expert"].index(metadata.get('difficulty', 'Non défini')))
    
    with col2:
        # Métadonnées cliniques
        st.markdown("**👤 Données Patient**")
        
        patient_age = st.number_input("Âge patient :", min_value=0, max_value=120, 
                                    value=metadata.get('patient_age', 0))
        
        patient_gender = st.selectbox("Sexe :", ["Non spécifié", "Masculin", "Féminin"],
                                    index=0 if not metadata.get('patient_gender') else
                                    ["Non spécifié", "Masculin", "Féminin"].index(metadata.get('patient_gender', 'Non spécifié')))
        
        clinical_context = st.text_area("Contexte clinique :", 
                                      value=metadata.get('clinical_context', ''))
    
    # Description étendue
    description = st.text_area("Description :", value=metadata.get('description', ''))
    
    # Métadonnées techniques
    st.markdown("**⚙️ Métadonnées Techniques**")
    
    col3, col4 = st.columns(2)
    
    with col3:
        ecg_speed = st.selectbox("Vitesse ECG :", ["25 mm/s", "50 mm/s", "12.5 mm/s"],
                               index=0 if not metadata.get('ecg_speed') else
                               ["25 mm/s", "50 mm/s", "12.5 mm/s"].index(metadata.get('ecg_speed', '25 mm/s')))
        
        ecg_voltage = st.selectbox("Calibrage :", ["10 mm/mV", "5 mm/mV", "20 mm/mV"],
                                 index=0 if not metadata.get('ecg_voltage') else
                                 ["10 mm/mV", "5 mm/mV", "20 mm/mV"].index(metadata.get('ecg_voltage', '10 mm/mV')))
    
    with col4:
        derivations = st.multiselect("Dérivations :",
                                   ["DI", "DII", "DIII", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"],
                                   default=metadata.get('derivations', []))
        
        filters_applied = st.multiselect("Filtres appliqués :",
                                       ["Passe-bas", "Passe-haut", "50Hz", "Lissage"],
                                       default=metadata.get('filters_applied', []))
    
    # Boutons d'action
    col5, col6 = st.columns(2)
    
    with col5:
        if st.button("💾 **Sauvegarder**", type="primary", use_container_width=True):
            # Mettre à jour métadonnées
            metadata.update({
                'name': name,
                'description': description,
                'category': category,
                'difficulty': difficulty,
                'patient_age': patient_age,
                'patient_gender': patient_gender,
                'clinical_context': clinical_context,
                'ecg_speed': ecg_speed,
                'ecg_voltage': ecg_voltage,
                'derivations': derivations,
                'filters_applied': filters_applied,
                'last_modified': datetime.now().isoformat()
            })
            
            save_case_metadata(case_id, metadata)
            st.success("✅ Métadonnées sauvegardées !")
    
    with col6:
        if st.button("🔄 **Réinitialiser**", use_container_width=True):
            st.rerun()

def perform_advanced_search(criteria):
    """Effectue recherche avancée"""
    
    results = []
    cases_dir = Path("data/ecg_cases")
    
    if not cases_dir.exists():
        return results
    
    for case_dir in cases_dir.iterdir():
        if case_dir.is_dir():
            case_metadata = load_case_metadata(case_dir.name)
            
            if case_metadata and matches_criteria(case_metadata, criteria):
                results.append(case_metadata)
    
    return results

def matches_criteria(metadata, criteria):
    """Vérifie si un cas correspond aux critères"""
    
    # Recherche textuelle
    if criteria['text']:
        search_fields = [
            metadata.get('name', ''),
            metadata.get('description', ''),
            metadata.get('clinical_context', '')
        ]
        
        search_text = ' '.join(search_fields).lower()
        if criteria['text'].lower() not in search_text:
            return False
    
    # Tags
    if criteria['tags']:
        case_tags = metadata.get('tags', [])
        for tag_filter in criteria['tags']:
            tag_name = tag_filter.split(': ')[1]  # Format "Category: Tag"
            if tag_name not in case_tags:
                return False
    
    # Catégories
    if criteria['categories']:
        if metadata.get('category') not in criteria['categories']:
            return False
    
    # Difficultés
    if criteria['difficulties']:
        if metadata.get('difficulty') not in criteria['difficulties']:
            return False
    
    # Annotations minimum
    if criteria['min_annotations'] > 0:
        annotations_count = len(metadata.get('annotations', []))
        if annotations_count < criteria['min_annotations']:
            return False
    
    # Type ECG
    if criteria['ecg_type'] != "Tous":
        ecg_type = metadata.get('type', 'simple')
        if criteria['ecg_type'] == "Multi-ECG" and ecg_type != 'multi_ecg':
            return False
        if criteria['ecg_type'] == "Simple" and ecg_type != 'simple':
            return False
    
    return True

def display_search_results(results):
    """Affiche résultats de recherche"""
    
    if not results:
        st.info("🔍 Aucun résultat trouvé")
        return
    
    st.success(f"✅ {len(results)} cas trouvé(s)")
    
    for result in results:
        with st.expander(f"📋 {result.get('name', result.get('case_id', 'Cas sans nom'))}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📂 Catégorie :** {result.get('category', 'Non classé')}")
                st.markdown(f"**🎯 Difficulté :** {result.get('difficulty', 'Non défini')}")
                st.markdown(f"**🏷️ Annotations :** {len(result.get('annotations', []))}")
                
                if result.get('tags'):
                    tags_display = ' '.join([f"🔹 {tag}" for tag in result['tags'][:3]])
                    if len(result['tags']) > 3:
                        tags_display += f" (+{len(result['tags'])-3})"
                    st.markdown(f"**🏷️ Tags :** {tags_display}")
            
            with col2:
                if result.get('description'):
                    st.markdown(f"**📝 Description :** {result['description'][:100]}...")
                
                if result.get('clinical_context'):
                    st.markdown(f"**🏥 Contexte :** {result['clinical_context'][:100]}...")

def classify_all_cases():
    """Classification automatique de tous les cas"""
    
    with st.spinner("🤖 Classification en cours..."):
        cases_dir = Path("data/ecg_cases")
        processed = 0
        
        if cases_dir.exists():
            for case_dir in cases_dir.iterdir():
                if case_dir.is_dir():
                    classify_single_case(case_dir.name)
                    processed += 1
        
        st.success(f"✅ {processed} cas classifiés !")

def classify_single_case(case_id):
    """Classification automatique d'un cas"""
    
    metadata = load_case_metadata(case_id)
    if not metadata:
        return
    
    # Analyse du texte
    description = metadata.get('description', '').lower()
    clinical_context = metadata.get('clinical_context', '').lower()
    text_content = f"{description} {clinical_context}"
    
    # Détection de pathologies
    pathology_keywords = {
        'Infarctus': ['infarctus', 'stemi', 'nstemi', 'onde q', 'nécrose'],
        'Arythmie': ['fibrillation', 'flutter', 'tachycardie', 'bradycardie', 'arythmie'],
        'Bloc': ['bloc', 'block', 'bbb', 'bav', 'hemibloc'],
        'Hypertrophie': ['hypertrophie', 'hvg', 'hvd', 'hod', 'hog']
    }
    
    detected_category = 'Normal'
    for category, keywords in pathology_keywords.items():
        if any(keyword in text_content for keyword in keywords):
            detected_category = category
            break
    
    # Mise à jour si pas déjà classifié
    if metadata.get('category') == 'Non classé':
        metadata['category'] = detected_category
        save_case_metadata(case_id, metadata)

def analyze_single_case(case_id):
    """Analyse détaillée d'un cas"""
    
    metadata = load_case_metadata(case_id)
    if not metadata:
        st.error("❌ Cas non trouvé")
        return
    
    st.markdown(f"**🔍 Analyse : {case_id}**")
    
    # Analyse du contenu
    description = metadata.get('description', '')
    clinical_context = metadata.get('clinical_context', '')
    
    analysis_results = {
        'pathology_detected': [],
        'suggested_tags': [],
        'complexity_score': 0,
        'quality_indicators': []
    }
    
    # Détection pathologies
    pathology_patterns = {
        'Fibrillation Auriculaire': r'fibrillation.*auriculaire|fa|afib',
        'Infarctus': r'infarctus|stemi|nstemi|imi',
        'Bloc AV': r'bloc.*av|bav|block.*av',
        'Tachycardie': r'tachycardie|tachy|fc.*>.*100'
    }
    
    text_content = f"{description} {clinical_context}".lower()
    
    for pathology, pattern in pathology_patterns.items():
        if re.search(pattern, text_content):
            analysis_results['pathology_detected'].append(pathology)
    
    # Suggestions de tags
    tag_suggestions = {
        'Qualité ECG': ['Bonne qualité', 'Artefacts', 'Parasites'],
        'Rythme': ['Sinusal', 'Irrégulier', 'Rapide', 'Lent'],
        'Morphologie': ['Onde P normale', 'QRS large', 'Onde T inversée']
    }
    
    # Calcul complexité
    complexity_factors = [
        len(analysis_results['pathology_detected']) * 20,
        len(metadata.get('annotations', [])) * 10,
        50 if metadata.get('type') == 'multi_ecg' else 0
    ]
    
    analysis_results['complexity_score'] = min(sum(complexity_factors), 100)
    
    # Affichage résultats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔬 Pathologies Détectées**")
        if analysis_results['pathology_detected']:
            for pathology in analysis_results['pathology_detected']:
                st.success(f"✅ {pathology}")
        else:
            st.info("ℹ️ Aucune pathologie détectée")
        
        st.markdown(f"**📊 Score Complexité : {analysis_results['complexity_score']}/100**")
    
    with col2:
        st.markdown("**🏷️ Tags Suggérés**")
        
        for category, suggestions in tag_suggestions.items():
            st.markdown(f"**{category} :**")
            for suggestion in suggestions[:2]:
                if st.button(f"➕ {suggestion}", key=f"suggest_{suggestion}"):
                    # Ajouter tag au cas
                    current_tags = metadata.get('tags', [])
                    if suggestion not in current_tags:
                        current_tags.append(suggestion)
                        metadata['tags'] = current_tags
                        save_case_metadata(case_id, metadata)
                        st.success(f"✅ Tag '{suggestion}' ajouté !")

def display_classification_stats():
    """Affiche statistiques de classification"""
    
    cases_dir = Path("data/ecg_cases")
    
    if not cases_dir.exists():
        st.info("📭 Aucune donnée disponible")
        return
    
    stats = {
        'total_cases': 0,
        'classified_cases': 0,
        'categories': defaultdict(int),
        'tagged_cases': 0,
        'avg_tags_per_case': 0
    }
    
    total_tags = 0
    
    for case_dir in cases_dir.iterdir():
        if case_dir.is_dir():
            metadata = load_case_metadata(case_dir.name)
            if metadata:
                stats['total_cases'] += 1
                
                category = metadata.get('category', 'Non classé')
                if category != 'Non classé':
                    stats['classified_cases'] += 1
                
                stats['categories'][category] += 1
                
                tags = metadata.get('tags', [])
                if tags:
                    stats['tagged_cases'] += 1
                    total_tags += len(tags)
    
    if stats['total_cases'] > 0:
        stats['avg_tags_per_case'] = total_tags / stats['total_cases']
    
    # Affichage
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📋 Cas Totaux", stats['total_cases'])
        st.metric("✅ Cas Classifiés", stats['classified_cases'], 
                 f"{stats['classified_cases']/stats['total_cases']*100:.1f}%" if stats['total_cases'] > 0 else "0%")
    
    with col2:
        st.metric("🏷️ Cas avec Tags", stats['tagged_cases'])
        st.metric("📊 Tags/Cas Moyen", f"{stats['avg_tags_per_case']:.1f}")
    
    # Répartition par catégorie
    st.markdown("**📂 Répartition par Catégorie**")
    for category, count in stats['categories'].items():
        percentage = count / stats['total_cases'] * 100 if stats['total_cases'] > 0 else 0
        st.progress(percentage / 100, text=f"{category}: {count} cas ({percentage:.1f}%)")

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

def load_case_metadata(case_id):
    """Charge métadonnées d'un cas"""
    
    case_dir = Path("data/ecg_cases") / case_id
    metadata_file = case_dir / "metadata.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    return None

def save_case_metadata(case_id, metadata):
    """Sauvegarde métadonnées d'un cas"""
    
    case_dir = Path("data/ecg_cases") / case_id
    metadata_file = case_dir / "metadata.json"
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    display_advanced_tagging_system()
