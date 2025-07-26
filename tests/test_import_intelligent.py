#!/usr/bin/env python3
"""
Test direct de l'Import Intelligent ECG
Démonstration du workflow unifié : import → recadrage → export
"""

import streamlit as st
import sys
from pathlib import Path

# Configuration Streamlit
st.set_page_config(
    page_title="🎯 Test Import Intelligent ECG",
    page_icon="🎯",
    layout="wide"
)

# Ajout des chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "frontend" / "admin"))

def main():
    """Interface de test de l'import intelligent"""
    
    st.title("🎯 Test Import Intelligent ECG")
    st.markdown("---")
    
    st.markdown("""
    ### 🚀 Workflow Unifié
    
    **📤 Étape 1** : Import multi-formats (PDF, PNG, JPG, XML)  
    **✂️ Étape 2** : Recadrage interactif avec curseurs  
    **📦 Étape 3** : Export standardisé vers liseuse  
    
    ---
    """)
    
    try:
        # Import du module
        from smart_ecg_importer import smart_ecg_importer
        
        st.success("✅ Module Import Intelligent chargé avec succès !")
        st.markdown("---")
        
        # Interface principale
        smart_ecg_importer()
        
    except ImportError as e:
        st.error(f"❌ Erreur d'import : {e}")
        st.markdown("""
        ### 🔧 Installation requise
        
        Assurez-vous que le fichier `smart_ecg_importer.py` est présent dans :
        ```
        frontend/admin/smart_ecg_importer.py
        ```
        """)
        
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
