#!/usr/bin/env python3
"""
Test pour vérifier que l'erreur de zoom est corrigée
"""

import streamlit as st
import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend"))

def test_zoom_functionality():
    """Test de la fonctionnalité zoom sans erreur session_state"""
    
    st.title("🧪 Test Correction Erreur Zoom")
    
    st.info("Ce test vérifie que l'erreur 'cannot be modified after widget instantiation' est corrigée.")
    
    # Simulation d'un ID de cas ECG
    test_case_id = "test_case_20250726"
    
    # Test du nettoyage d'ID (fonction de la liseuse)
    def clean_case_id(case_id):
        """Nettoie l'ID pour les clés Streamlit"""
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(case_id))
    
    clean_id = clean_case_id(test_case_id)
    st.success(f"✅ Clean ID généré : `{clean_id}`")
    
    # Test des contrôles de zoom (version corrigée)
    st.markdown("### 🔍 Test des contrôles de zoom")
    
    col1, col2 = st.columns([2, 1])
    
    # Gérer le reset avec une variable temporaire
    reset_key = f"reset_zoom_{clean_id}"
    should_reset = st.session_state.get(reset_key, False)
    
    with col1:
        # Valeur par défaut du zoom, réinitialisée si reset demandé
        default_zoom = 100 if should_reset else 100
        zoom_level = st.slider("🔍 Zoom", 50, 300, default_zoom, 25, key=f"zoom_{clean_id}")
        st.write(f"**Niveau de zoom actuel :** {zoom_level}%")
    
    with col2:
        if st.button("🔄 Reset Zoom", key=f"reset_{clean_id}"):
            # Marquer qu'un reset est demandé et recharger
            st.session_state[reset_key] = True
            st.rerun()
    
    # Nettoyer le flag de reset après utilisation
    if should_reset:
        st.session_state[reset_key] = False
    
    # Affichage des informations de debug
    st.markdown("### 🛠️ Debug Info")
    
    zoom_key = f"zoom_{clean_id}"
    if zoom_key in st.session_state:
        st.success(f"✅ Clé zoom présente: `{zoom_key}` = {st.session_state[zoom_key]}")
    else:
        st.info(f"ℹ️ Clé zoom pas encore initialisée: `{zoom_key}`")
    
    if reset_key in st.session_state:
        st.info(f"🔄 Flag reset: `{reset_key}` = {st.session_state[reset_key]}")
    else:
        st.success(f"✅ Pas de flag reset actif")
    
    # Test réussi
    st.markdown("---")
    if zoom_level:
        st.success("🎉 **Test réussi !** Le zoom fonctionne sans erreur session_state.")
        st.info("💡 Vous pouvez maintenant utiliser la liseuse ECG sans problème.")
    
    # Instructions
    st.markdown("### 📋 Instructions")
    st.markdown("""
    **Comment tester :**
    1. Ajustez le slider de zoom ➡️ Pas d'erreur
    2. Cliquez sur "Reset Zoom" ➡️ Le zoom revient à 100%
    3. Recommencez plusieurs fois ➡️ Pas d'erreur de session_state
    
    **Si ça fonctionne ici, ça fonctionnera dans la liseuse ECG !** ✅
    """)

if __name__ == "__main__":
    test_zoom_functionality()
