#!/usr/bin/env python3
"""
Test de la popup de confirmation de suppression améliorée
"""

import streamlit as st
import sys
from pathlib import Path

st.set_page_config(
    page_title="🧪 Test Popup Suppression",
    page_icon="🗑️",
    layout="wide"
)

def test_delete_confirmation_popup():
    """Test de la popup de confirmation de suppression"""
    
    st.title("🧪 Test de la Popup de Confirmation de Suppression")
    
    st.info("Ce test simule la nouvelle popup de confirmation de suppression des cas ECG.")
    
    # Simulation d'un cas ECG
    test_cases = [
        "ECG_Patient_001_Fibrillation",
        "ECG_Patient_002_Bradycardie", 
        "ECG_Patient_003_Tachycardie",
        "ECG_Test_Archive_001"
    ]
    
    st.markdown("### 📋 Cas ECG de test")
    
    # Affichage des cas avec boutons de suppression
    for i, case_name in enumerate(test_cases):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"📋 **{case_name}**")
            st.caption(f"Cas ECG de test numéro {i+1}")
        
        with col2:
            if st.button("✏️", key=f"edit_{case_name}", help="Éditer"):
                st.info(f"Édition de {case_name} (simulation)")
        
        with col3:
            if st.button("🗑️", key=f"delete_{case_name}", help="Supprimer"):
                st.session_state['delete_confirm'] = case_name
                st.rerun()
    
    # Gestion de la confirmation de suppression (copie de la nouvelle logique)
    if 'delete_confirm' in st.session_state:
        case_to_delete = st.session_state['delete_confirm']
        
        # Popup modale simulée avec Streamlit
        st.markdown("---")
        
        # Container stylisé pour simuler une popup
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ff4757, #ff3838);
            color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(255, 71, 87, 0.3);
            border: 2px solid #ff6b7a;
            margin: 20px 0;
            text-align: center;
        ">
            <h2 style="margin: 0; font-size: 24px;">🗑️ Confirmation de suppression</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Zone d'alerte principale
        st.markdown(f"""
        <div style="
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 3px solid #ff4757;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <div style="text-align: center;">
                <h3 style="color: #ff4757; margin: 0 0 15px 0;">⚠️ Attention !</h3>
                <p style="font-size: 18px; margin: 10px 0; color: #333;">
                    Êtes-vous sûr de vouloir supprimer le cas :
                </p>
                <p style="font-size: 20px; font-weight: bold; color: #ff4757; margin: 15px 0;">
                    📋 "{case_to_delete}"
                </p>
                <p style="color: #dc3545; font-weight: bold; font-size: 16px; margin: 15px 0;">
                    ⚠️ Cette action est définitive et irréversible !
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Espacement pour mettre en évidence les boutons
        st.markdown("### 🤔 Que souhaitez-vous faire ?")
        
        # Boutons de confirmation avec espacement amélioré
        col_space1, col_yes, col_space2, col_no, col_space3 = st.columns([1, 2, 0.5, 2, 1])
        
        with col_yes:
            if st.button("✅ OUI, SUPPRIMER", type="primary", key="confirm_delete", use_container_width=True):
                with st.spinner("🗑️ Suppression en cours..."):
                    # Simulation de la suppression
                    import time
                    time.sleep(2)  # Simulation du temps de suppression
                    
                    # Supprimer la confirmation
                    del st.session_state['delete_confirm']
                    st.balloons()  # Animation de succès
                    st.success(f"✅ Cas '{case_to_delete}' supprimé avec succès !")
                    time.sleep(2)
                    st.rerun()
        
        with col_no:
            if st.button("❌ NON, ANNULER", key="cancel_delete", use_container_width=True):
                del st.session_state['delete_confirm']
                st.info("ℹ️ Suppression annulée - Le cas est conservé")
                st.rerun()
        
        # Message d'aide
        st.info("💡 **Conseil :** Si vous souhaitez juste archiver temporairement le cas, utilisez la fonction d'édition pour le renommer avec un préfixe '[ARCHIVE]'.")
        
        st.markdown("---")
    
    # Instructions d'utilisation
    st.markdown("### 📋 Instructions de test")
    st.markdown("""
    **Comment tester la popup :**
    1. Cliquez sur un bouton 🗑️ à droite d'un cas ECG
    2. Une popup stylisée apparaît avec le nom du cas
    3. Choisissez **"OUI, SUPPRIMER"** pour confirmer (avec animation)
    4. Ou **"NON, ANNULER"** pour annuler
    
    **Fonctionnalités de la popup :**
    ✅ Design attractif avec dégradé rouge
    ✅ Nom du cas clairement affiché
    ✅ Avertissement sur l'irréversibilité
    ✅ Boutons bien espacés et visibles
    ✅ Animation lors de la suppression (ballons + spinner)
    ✅ Conseil d'archivage plutôt que suppression
    """)
    
    # État du test
    if 'delete_confirm' not in st.session_state:
        st.success("🎉 **Test prêt !** Cliquez sur un bouton 🗑️ pour tester la popup.")
    else:
        st.warning("⏳ **Popup active** - Confirmez ou annulez pour continuer le test.")

if __name__ == "__main__":
    test_delete_confirmation_popup()
