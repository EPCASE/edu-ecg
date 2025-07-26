#!/usr/bin/env python3
"""
Test direct de la liseuse ECG dans l'application
"""

import streamlit as st
import sys
from pathlib import Path

# Configuration
st.set_page_config(
    page_title="Test Liseuse ECG",
    page_icon="📚",
    layout="wide"
)

# Ajout des chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend" / "liseuse"))

st.title("📚 Test Liseuse ECG")

# Simuler l'état de navigation pour éviter les retours à l'accueil
if 'admin_page' not in st.session_state:
    st.session_state.admin_page = "📺 Liseuse ECG (WP2)"

if 'student_page' not in st.session_state:
    st.session_state.student_page = "📚 Cas ECG"

# Affichage de debug
with st.expander("🔍 Debug Navigation"):
    st.write(f"admin_page: {st.session_state.get('admin_page', 'Non défini')}")
    st.write(f"student_page: {st.session_state.get('student_page', 'Non défini')}")

st.markdown("---")

try:
    from liseuse_ecg_fonctionnelle import liseuse_ecg_fonctionnelle
    
    st.success("✅ Module liseuse chargé avec succès")
    
    # Lancer la liseuse
    liseuse_ecg_fonctionnelle()
    
except ImportError as e:
    st.error(f"❌ Erreur import liseuse : {e}")
    st.info("💡 Vérifiez que le fichier liseuse_ecg_fonctionnelle.py existe")
    
except Exception as e:
    st.error(f"❌ Erreur liseuse : {e}")
    import traceback
    with st.expander("🐛 Détails de l'erreur"):
        st.code(traceback.format_exc())
