"""
🧠 Interface Import ECG Intelligent
Permet au correcteur de saisir descriptions littéraires avec détection automatique concepts ontologie

Auteur: Dr. Grégoire + BMAD Team
Date: 2026-01-10
Story: 1.3.A - Prototype Détection MVP
"""

import streamlit as st
import sys
from pathlib import Path
import json
import re
from typing import List, Dict, Tuple

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Charger mapping ontologie
mapping_file = project_root / "data" / "epic1_ontology_mapping.json"
with open(mapping_file, 'r', encoding='utf-8') as f:
    ONTOLOGY_MAPPING = json.load(f)

# Configuration page
st.set_page_config(
    page_title="🧠 Import ECG Intelligent",
    page_icon="🏥",
    layout="wide"
)

st.title("🧠 Import ECG Intelligent - Epic 1")
st.markdown("**Saisissez votre description ECG** - Les concepts seront détectés automatiquement")

# Session state
if 'description_text' not in st.session_state:
    st.session_state.description_text = ""
if 'detected_concepts' not in st.session_state:
    st.session_state.detected_concepts = []
if 'validated_concepts' not in st.session_state:
    st.session_state.validated_concepts = set()

# Fonction détection concepts
def detect_concepts(text: str) -> List[Dict]:
    """
    Détecte concepts dans le texte en utilisant le mapping ontologie
    Returns: List[{ontology_id, concept_name, matched_text, confidence}]
    """
    detected = []
    text_lower = text.lower()
    
    concept_mappings = ONTOLOGY_MAPPING.get('concept_mappings', {})
    
    for concept_name, mapping in concept_mappings.items():
        # Vérifier concept principal
        if concept_name.lower() in text_lower:
            detected.append({
                'ontology_id': mapping.get('ontology_id', ''),
                'concept_name': concept_name,
                'matched_text': concept_name,
                'match_type': 'exact',
                'confidence': 1.0
            })
            continue
        
        # Vérifier synonymes
        for synonyme in mapping.get('synonymes', []):
            if synonyme.lower() in text_lower:
                detected.append({
                    'ontology_id': mapping.get('ontology_id', ''),
                    'concept_name': concept_name,
                    'matched_text': synonyme,
                    'match_type': 'synonyme',
                    'confidence': 0.95
                })
                break
    
    # Dédupliquer par ontology_id
    seen_ids = set()
    unique_detected = []
    for d in detected:
        if d['ontology_id'] not in seen_ids:
            seen_ids.add(d['ontology_id'])
            unique_detected.append(d)
    
    return unique_detected

# Fonction enrichissement implications
def get_implications(validated_concepts: set) -> List[Dict]:
    """
    Retourne les concepts auto-validés par implications
    """
    implications = []
    implication_rules = ONTOLOGY_MAPPING.get('implication_rules', {})
    concept_mappings = ONTOLOGY_MAPPING.get('concept_mappings', {})
    
    # Créer map concept_name -> ontology_id
    name_to_id = {name: mapping.get('ontology_id', '') 
                  for name, mapping in concept_mappings.items()}
    id_to_name = {v: k for k, v in name_to_id.items() if v}
    
    for concept_name in validated_concepts:
        ontology_id = name_to_id.get(concept_name)
        if not ontology_id:
            continue
        
        # Vérifier règles d'implication
        if ontology_id in implication_rules:
            rule = implication_rules[ontology_id]
            for implied_id in rule.get('auto_validate', []):
                implied_name = id_to_name.get(implied_id)
                if implied_name and implied_name not in validated_concepts:
                    implications.append({
                        'concept_name': implied_name,
                        'ontology_id': implied_id,
                        'implied_by': concept_name,
                        'rule_description': rule.get('description', '')
                    })
    
    return implications

# ZONE PRINCIPALE
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📝 Description ECG (écrivez naturellement)")
    
    description = st.text_area(
        "Description littéraire",
        value=st.session_state.description_text,
        height=250,
        placeholder="Exemple: Bloc AV 2nd degré type Mobitz 1 avec allongement progressif du PR jusqu'à onde P bloquée. QRS fins à 95 ms. Rythme sinusal à 70 bpm. Pas de trouble repolarisation.",
        help="Écrivez votre description comme vous le feriez naturellement. Les concepts seront détectés automatiquement.",
        key="description_input"
    )
    
    # Détection temps réel (avec debounce simulé)
    if description != st.session_state.description_text:
        st.session_state.description_text = description
        st.session_state.detected_concepts = detect_concepts(description)
    
    # Stats
    char_count = len(description)
    word_count = len(description.split())
    st.caption(f"📊 {char_count} caractères, {word_count} mots")

with col2:
    st.subheader(f"🤖 {len(st.session_state.detected_concepts)} concepts détectés")
    
    if st.session_state.detected_concepts:
        # Bouton valider tout
        if st.button("✅ Tout valider", use_container_width=True):
            st.session_state.validated_concepts = {
                c['concept_name'] for c in st.session_state.detected_concepts
            }
            st.rerun()
        
        st.markdown("---")
        
        # Liste concepts détectés
        for concept in st.session_state.detected_concepts:
            concept_name = concept['concept_name']
            matched_text = concept['matched_text']
            match_type = concept['match_type']
            
            # Icône selon type
            icon = '✅' if match_type == 'exact' else '🔍'
            type_label = 'Match exact' if match_type == 'exact' else 'Synonyme'
            
            # Checkbox validation
            is_validated = concept_name in st.session_state.validated_concepts
            
            if st.checkbox(
                f"{icon} **{concept_name}**",
                value=is_validated,
                key=f"checkbox_{concept['ontology_id']}",
                help=f"{type_label} - Texte trouvé: \"{matched_text}\""
            ):
                st.session_state.validated_concepts.add(concept_name)
            else:
                st.session_state.validated_concepts.discard(concept_name)
            
            st.caption(f"↳ {type_label}: \"{matched_text}\"")
            st.markdown("---")
    else:
        st.info("💡 Commencez à écrire pour détecter des concepts automatiquement")

# Section implications
if st.session_state.validated_concepts:
    st.divider()
    
    implications = get_implications(st.session_state.validated_concepts)
    
    if implications:
        st.subheader(f"💡 {len(implications)} implications suggérées")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🤖 Tout appliquer", use_container_width=True):
                for impl in implications:
                    st.session_state.validated_concepts.add(impl['concept_name'])
                st.rerun()
        
        for impl in implications:
            st.markdown(f"""
            <div style="background: #e7f3ff; padding: 10px; border-radius: 5px; margin: 5px 0;">
                🤖 <strong>{impl['concept_name']}</strong><br>
                <small>Impliqué par: {impl['implied_by']}<br>
                {impl['rule_description']}</small>
            </div>
            """, unsafe_allow_html=True)

# Récapitulatif final
st.divider()
st.subheader("📊 Récapitulatif")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Concepts détectés", len(st.session_state.detected_concepts))

with col2:
    st.metric("Concepts validés", len(st.session_state.validated_concepts))

with col3:
    implications_count = len(get_implications(st.session_state.validated_concepts))
    st.metric("Implications disponibles", implications_count)

# Sauvegarde template
if st.session_state.validated_concepts:
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        case_id = st.text_input(
            "ID du cas",
            value=f"EPIC1_{len(st.session_state.validated_concepts):03d}",
            help="Identifiant unique du cas ECG"
        )
        
        diagnostic_principal = st.text_input(
            "Diagnostic principal",
            help="Diagnostic principal de l'ECG (ex: BAV 2 Mobitz 1)"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Enregistrer Template", type="primary", use_container_width=True):
            if not diagnostic_principal:
                st.error("⚠️ Veuillez saisir un diagnostic principal")
            else:
                # Créer template
                template = {
                    "case_id": case_id,
                    "description_litteraire": st.session_state.description_text,
                    "diagnostic_principal": diagnostic_principal,
                    "expected_concepts": list(st.session_state.validated_concepts),
                    "concepts_detectes_auto": st.session_state.detected_concepts,
                    "implications": get_implications(st.session_state.validated_concepts),
                    "metadata": {
                        "created_date": "2026-01-10",
                        "detection_method": "automatic_with_validation",
                        "total_concepts": len(st.session_state.validated_concepts)
                    }
                }
                
                st.success(f"✅ Template créé : {case_id}")
                
                # Afficher JSON
                with st.expander("👁️ Prévisualiser JSON"):
                    st.json(template)
                
                # TODO: Sauvegarder dans fichier
                st.info("💾 Sauvegarde automatique à implémenter (Story 1.3.D)")

# Footer
st.divider()
st.caption("""
🧠 **Interface Import Intelligent v1.0** - Story 1.3.A  
✅ Détection automatique concepts | 🔍 Synonymes reconnus | 🤖 Implications suggérées
""")
