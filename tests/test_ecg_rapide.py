#!/usr/bin/env python3
"""
Lancement rapide pour tests ECG
"""

import streamlit as st

st.set_page_config(
    page_title="Test ECG Rapide",
    page_icon="🧪", 
    layout="wide"
)

st.title("🧪 Test ECG Rapide")
st.markdown("**Outils de diagnostic et test des fonctionnalités ECG**")

# Menu de navigation simple
choix = st.selectbox(
    "Choisir un outil :",
    [
        "🏠 Accueil",
        "⚡ Import ECG Rapide", 
        "📚 Liseuse ECG Simple",
        "🔍 Test Diagnostic",
        "📊 Vérifier les Cas"
    ]
)

if choix == "⚡ Import ECG Rapide":
    st.markdown("---")
    try:
        from import_ecg_rapide import import_ecg_simple
        import_ecg_simple()
    except ImportError as e:
        st.error(f"❌ Erreur import : {e}")

elif choix == "📚 Liseuse ECG Simple":
    st.markdown("---")
    try:
        from liseuse_ecg_simple import liseuse_ecg_simple
        liseuse_ecg_simple()
    except ImportError as e:
        st.error(f"❌ Erreur import : {e}")

elif choix == "🔍 Test Diagnostic":
    st.markdown("---")
    st.markdown("### 🔍 Diagnostic du système")
    
    if st.button("🧪 Lancer tous les tests"):
        with st.spinner("Tests en cours..."):
            try:
                # Test des cas ECG
                from pathlib import Path
                import json
                
                ecg_dir = Path("data/ecg_cases")
                if ecg_dir.exists():
                    cases = [d for d in ecg_dir.iterdir() if d.is_dir()]
                    st.success(f"✅ {len(cases)} cas ECG trouvés")
                    
                    # Détail des cas
                    for case_folder in cases:
                        metadata_path = case_folder / "metadata.json"
                        if metadata_path.exists():
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            st.info(f"📁 {case_folder.name} - {metadata.get('type', 'N/A')} - Statut: {metadata.get('statut', 'N/A')}")
                else:
                    st.warning("⚠️ Répertoire data/ecg_cases non trouvé")
                    
            except Exception as e:
                st.error(f"❌ Erreur test : {e}")

elif choix == "📊 Vérifier les Cas":
    st.markdown("---")
    st.markdown("### 📊 État des cas ECG")
    
    try:
        from pathlib import Path
        import json
        
        ecg_dir = Path("data/ecg_cases")
        if ecg_dir.exists():
            cases = [d for d in ecg_dir.iterdir() if d.is_dir()]
            
            if cases:
                st.success(f"✅ {len(cases)} cas disponibles")
                
                # Tableau des cas
                cas_data = []
                for case_folder in cases:
                    metadata_path = case_folder / "metadata.json"
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            cas_data.append({
                                'ID': metadata.get('case_id', case_folder.name),
                                'Type': metadata.get('type', 'N/A'),
                                'Âge': metadata.get('age', 'N/A'),
                                'Sexe': metadata.get('sexe', 'N/A'),
                                'Statut': metadata.get('statut', 'N/A'),
                                'Annotations': len(metadata.get('annotations', []))
                            })
                        except Exception:
                            continue
                
                if cas_data:
                    import pandas as pd
                    df = pd.DataFrame(cas_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("⚠️ Aucun cas valide trouvé")
            else:
                st.warning("⚠️ Aucun cas trouvé")
        else:
            st.error("❌ Répertoire data/ecg_cases non trouvé")
            
    except Exception as e:
        st.error(f"❌ Erreur : {e}")

else:
    st.markdown("---")
    st.markdown("""
    ### 🏠 Bienvenue dans l'outil de test ECG
    
    **Fonctionnalités disponibles :**
    
    - **⚡ Import ECG Rapide** : Import simplifié d'images ECG avec métadonnées
    - **📚 Liseuse ECG Simple** : Visualisation et annotation des cas ECG
    - **🔍 Test Diagnostic** : Vérification du système et des fonctionnalités
    - **📊 Vérifier les Cas** : Tableau de bord des cas ECG disponibles
    
    **Workflow recommandé :**
    1. Utilisez l'Import ECG Rapide pour créer des cas
    2. Visualisez et annotez avec la Liseuse ECG Simple
    3. Vérifiez l'état avec les outils de diagnostic
    
    ---
    
    ### 🎯 Objectif
    Cet outil permet de tester rapidement les fonctionnalités d'import et d'annotation 
    ECG sans passer par l'interface complexe complète.
    """)
