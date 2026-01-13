"""
🎯 Demo Territory Selector - Test de l'interface de sélection de territoire

Lancer avec: streamlit run demo_territory_selector.py
"""

import streamlit as st
import json
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.components.territory_selector_ui import (
    render_territory_selectors,
    check_territory_completeness,
    get_territory_selection_summary,
    calculate_territory_bonus
)

# Charger l'ontologie
ontology_path = project_root / "data" / "ontology_from_owl.json"
if not ontology_path.exists():
    st.error("❌ Ontologie non trouvée")
    st.stop()

with open(ontology_path, 'r', encoding='utf-8') as f:
    ONTOLOGY = json.load(f)

# ============================================================================
# PAGE DEMO
# ============================================================================

st.set_page_config(page_title="Territory Selector Demo", page_icon="🗺️")

st.title("🗺️ Démonstration Territory Selector")
st.markdown("Test interactif du sélecteur de territoire contextuel")

st.markdown("---")

# Sélection du concept à tester
st.markdown("### 1️⃣ Sélectionnez un concept")

test_concepts = [
    "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST",
    "STEMI",
    "NSTEMI",
    "Hypertrophie VG",
    "BAV 1"
]

selected_concept = st.selectbox(
    "Concept à tester:",
    options=test_concepts,
    index=0
)

st.markdown("---")
st.markdown("### 2️⃣ Sélecteur de territoire")

# Afficher le sélecteur
territories, mirrors = render_territory_selectors(
    selected_concept,
    ONTOLOGY,
    key_prefix="demo"
)

# Afficher ce qui a été capturé
st.markdown("---")
st.markdown("### 3️⃣ Résultats")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Territoires sélectionnés:**")
    if territories:
        for terr in territories:
            st.write(f"📍 {terr}")
    else:
        st.info("Aucun territoire sélectionné")

with col2:
    st.markdown("**Miroirs sélectionnés:**")
    if mirrors:
        for mirr in mirrors:
            st.write(f"🪞 {mirr}")
    else:
        st.info("Aucun miroir sélectionné")

# Check complétude
st.markdown("---")
st.markdown("### 4️⃣ Validation")

is_complete, error_msg = check_territory_completeness(
    selected_concept,
    territories,
    ONTOLOGY
)

if is_complete:
    st.success("✅ Sélection complète")
else:
    st.error(f"❌ {error_msg}")

# Résumé
summary = get_territory_selection_summary(selected_concept, territories, mirrors)
if summary:
    st.info(f"📝 Résumé: {summary}")

# Test scoring (simulation)
st.markdown("---")
st.markdown("### 5️⃣ Simulation Scoring")

with st.expander("🧪 Simuler un matching avec réponse de référence"):
    st.markdown("**Définir les territoires attendus:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        from backend.territory_resolver import get_territory_config
        config = get_territory_config(selected_concept, ONTOLOGY)
        
        if config and config['territories']:
            expected_terr = st.multiselect(
                "Territoires attendus:",
                options=config['territories'],
                default=config['territories'][:1],
                key="expected_territories"
            )
        else:
            expected_terr = []
            st.info("Pas de territoires disponibles")
    
    with col2:
        if config and config['mirrors']:
            expected_mirr = st.multiselect(
                "Miroirs attendus:",
                options=config['mirrors'],
                key="expected_mirrors"
            )
        else:
            expected_mirr = []
            st.info("Pas de miroirs disponibles")
    
    if expected_terr or expected_mirr:
        bonus, explanation = calculate_territory_bonus(
            selected_concept,
            territories,
            mirrors,
            expected_terr,
            expected_mirr,
            ONTOLOGY
        )
        
        st.markdown("---")
        st.markdown("**Résultat du scoring:**")
        st.metric("Bonus territoire", f"+{bonus*100:.1f}%")
        st.markdown(f"**Explication:** {explanation}")

# Debug info
with st.expander("🔍 Debug - Configuration complète"):
    from backend.territory_resolver import get_territory_config
    config = get_territory_config(selected_concept, ONTOLOGY)
    if config:
        st.json(config)
    else:
        st.info("Pas de configuration territoire pour ce concept")
