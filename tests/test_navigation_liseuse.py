#!/usr/bin/env python3
"""
Test de la navigation corrigée de la liseuse ECG
"""

import streamlit as st
import sys
from pathlib import Path

# Configuration
st.set_page_config(
    page_title="Test Navigation Liseuse",
    page_icon="🧪",
    layout="wide"
)

# Ajout du chemin
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend" / "liseuse"))

st.title("🧪 Test Navigation Liseuse ECG")

# Simuler l'état admin
st.session_state.admin_page = "📺 Liseuse ECG (WP2)"

# Debug
with st.expander("🔍 État de Navigation"):
    st.write("Session State :")
    for key, value in st.session_state.items():
        if 'page' in key:
            st.write(f"- **{key}**: {value}")

st.markdown("---")

# Test de la liseuse
try:
    from liseuse_ecg_fonctionnelle import liseuse_ecg_fonctionnelle
    
    st.success("✅ Module liseuse chargé")
    st.info("💡 Testez les fonctionnalités : zoom, grille, sélection cas, annotations")
    st.warning("🎯 Vérifiez que vous ne retournez PAS vers l'Import Intelligent")
    
    # Lancer la liseuse
    liseuse_ecg_fonctionnelle()
    
except ImportError as e:
    st.error(f"❌ Erreur import : {e}")
except Exception as e:
    st.error(f"❌ Erreur : {e}")
    import traceback
    with st.expander("🐛 Détails"):
        st.code(traceback.format_exc())

# Vérification post-exécution
st.markdown("---")
st.markdown("### 🧪 Résultat du Test")

if st.session_state.get('admin_page') == "📺 Liseuse ECG (WP2)":
    st.success("✅ Navigation préservée sur la Liseuse ECG")
else:
    st.error(f"❌ Navigation déviée vers : {st.session_state.get('admin_page', 'Inconnu')}")

st.info("💡 Si le test réussit, la liseuse dans l'application principale devrait fonctionner correctement")
