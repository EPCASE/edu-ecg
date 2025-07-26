"""
Test du visualiseur ECG intelligent
Vérifie l'affichage adaptatif selon les formats
"""

import streamlit as st
import sys
from pathlib import Path

# Configuration
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "frontend" / "viewers"))

def test_ecg_viewer():
    st.title("🧪 Test Visualiseur ECG")
    
    st.markdown("""
    **Objectif :** Tester l'affichage adaptatif d'ECG  
    **Formats supportés :** PNG, JPG, PDF, XML, HL7
    """)
    
    # Test avec fichiers existants
    st.subheader("📁 Fichiers disponibles")
    
    # Chercher des ECGs dans le projet
    ecg_files = []
    
    # Dossier ECG principal
    ecg_dir = project_root / "ECG"
    if ecg_dir.exists():
        for file in ecg_dir.glob("*"):
            if file.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                ecg_files.append(str(file))
    
    # Cas ECG
    cases_dir = project_root / "data" / "ecg_cases"
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                for file in case_dir.glob("*"):
                    if file.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                        ecg_files.append(str(file))
    
    if ecg_files:
        selected_file = st.selectbox(
            "Choisir un fichier ECG à tester",
            ecg_files,
            format_func=lambda x: f"{Path(x).name} ({Path(x).suffix.upper()})"
        )
        
        if st.button("🔍 Tester l'affichage"):
            st.markdown("---")
            
            try:
                from ecg_viewer_smart import display_ecg_smart
                success = display_ecg_smart(selected_file)
                
                if success:
                    st.success("✅ Test réussi - ECG affiché correctement")
                else:
                    st.warning("⚠️ Affichage partiel - annotation possible")
                    
            except Exception as e:
                st.error(f"❌ Erreur de test : {e}")
                st.info("💡 Vérifiez que le visualiseur est correctement installé")
    
    else:
        st.info("📂 Aucun fichier ECG trouvé pour le test")
        st.markdown("""
        **Pour tester :**
        1. Placez un fichier ECG dans le dossier `ECG/`
        2. Ou importez des cas via l'interface admin
        """)
    
    # Upload test
    st.subheader("📤 Test avec upload")
    
    uploaded_file = st.file_uploader(
        "Tester avec votre fichier ECG",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Formats supportés : PNG, JPG, PDF"
    )
    
    if uploaded_file:
        # Sauvegarder temporairement
        temp_path = f"temp_test_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        
        st.markdown("---")
        st.markdown(f"### Test avec {uploaded_file.name}")
        
        try:
            from ecg_viewer_smart import display_ecg_smart
            success = display_ecg_smart(temp_path)
            
            if success:
                st.success("✅ Upload et affichage réussis")
            else:
                st.warning("⚠️ Affichage partiel")
                
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
        
        finally:
            # Nettoyer
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    test_ecg_viewer()
