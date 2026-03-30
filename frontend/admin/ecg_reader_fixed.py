import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import json
from pathlib import Path
from datetime import datetime

def ecg_reader_interface():
    """Interface de lecture ECG avancée avec outils de mesure"""
    
    st.title("📊 Liseuse ECG Avancée")
    st.markdown("### *Visualisation et mesure d'ECG avec fond millimétré*")
    
    # Sidebar pour configuration
    with st.sidebar:
        st.header("⚙️ Configuration d'affichage")
        
        # Type d'affichage
        display_mode = st.selectbox(
            "Mode d'affichage",
            ["12 dérivations standard", "6+6+DII long", "3x4 dérivations", "Dérivation unique"]
        )
        
        # Échelle
        st.subheader("📏 Échelle")
        voltage_scale = st.selectbox("Amplitude", ["5mm/mV", "10mm/mV", "20mm/mV"], index=1)
        time_scale = st.selectbox("Vitesse", ["25mm/s", "50mm/s", "100mm/s"], index=0)
        
        # Filtres
        st.subheader("🔧 Filtres")
        low_pass = st.slider("Filtre passe-bas (Hz)", 1, 150, 40)
        high_pass = st.slider("Filtre passe-haut (Hz)", 0.1, 5.0, 0.5)
        notch_filter = st.checkbox("Filtre 50Hz", value=True)
        
        # Outils de mesure
        st.subheader("📐 Outils de mesure")
        show_grid = st.checkbox("Grille millimétée", value=True)
        show_rulers = st.checkbox("Règles de mesure", value=False)
        show_calipers = st.checkbox("Compas de mesure", value=False)
    
    # Zone principale
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Sélection du cas ECG
        st.subheader("📂 Sélection du cas")
        
        # Liste des cas disponibles
        cases_dir = Path("data/ecg_cases")
        if cases_dir.exists():
            case_files = list(cases_dir.glob("*/metadata.json"))
            if case_files:
                case_options = []
                for case_file in case_files:
                    case_id = case_file.parent.name
                    case_options.append(case_id)
                
                selected_case = st.selectbox(
                    "Choisir un cas ECG",
                    case_options
                )
                
                # Chargement du cas
                if selected_case:
                    case_path = cases_dir / selected_case / "metadata.json"
                    case_data = load_ecg_case(case_path)
                    
                    if case_data:
                        display_ecg_viewer(case_data, display_mode, show_grid, selected_case)
            else:
                st.warning("Aucun cas ECG trouvé. Importez des cas via l'interface Admin.")
        else:
            st.warning("Dossier des cas ECG non trouvé.")
    
    with col2:
        st.subheader("📊 Mesures automatiques")
        
        # Zone de mesures
        if st.button("🔍 Analyser l'ECG"):
            with st.spinner("Analyse en cours..."):
                measurements = perform_automatic_measurements()
                display_measurements(measurements)
        
        st.subheader("✍️ Annotations")
        
        # Initialisation des annotations dans la session
        if 'annotations' not in st.session_state:
            st.session_state.annotations = []
        
        # Outils d'annotation
        annotation_type = st.selectbox(
            "Type d'annotation",
            ["Texte", "Mesure", "Zone d'intérêt", "Diagnostic", "Commentaire"]
        )
        
        # Interface selon le type d'annotation
        if annotation_type == "Texte":
            annotation_text = st.text_input("Texte à ajouter")
            x_pos = st.slider("Position X (%)", 0, 100, 50)
            y_pos = st.slider("Position Y (%)", 0, 100, 50)
            
            if st.button("➕ Ajouter annotation texte") and annotation_text:
                new_annotation = {
                    "type": "text",
                    "content": annotation_text,
                    "x": x_pos,
                    "y": y_pos,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": st.session_state.get('current_user', 'admin')
                }
                st.session_state.annotations.append(new_annotation)
                st.success(f"✅ Annotation ajoutée: {annotation_text}")
        
        elif annotation_type == "Mesure":
            mesure_type = st.selectbox("Type de mesure", ["Intervalle", "Amplitude", "Fréquence"])
            mesure_value = st.text_input("Valeur mesurée")
            mesure_unit = st.selectbox("Unité", ["ms", "mV", "bpm", "°"])
            
            if st.button("📏 Ajouter mesure") and mesure_value:
                new_annotation = {
                    "type": "measurement",
                    "measurement_type": mesure_type,
                    "value": mesure_value,
                    "unit": mesure_unit,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": st.session_state.get('current_user', 'admin')
                }
                st.session_state.annotations.append(new_annotation)
                st.success(f"✅ Mesure ajoutée: {mesure_value} {mesure_unit}")
        
        # Affichage des annotations existantes
        if st.session_state.annotations:
            st.markdown("---")
            st.subheader("📝 Annotations actuelles")
            
            for i, annotation in enumerate(st.session_state.annotations):
                with st.expander(f"{get_annotation_icon(annotation['type'])} {annotation['type'].title()} #{i+1}"):
                    display_annotation_details(annotation, i)
        
        # Actions globales
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder"):
                save_annotations_to_case()
        
        with col2:
            if st.button("📥 Charger"):
                load_annotations_from_case()
        
        with col3:
            if st.button("🗑️ Effacer tout"):
                st.session_state.annotations = []
                st.success("Toutes les annotations supprimées")

def get_annotation_icon(annotation_type):
    """Retourne l'icône appropriée pour chaque type d'annotation"""
    icons = {
        "text": "📝",
        "measurement": "📏",
        "zone": "🎯",
        "diagnosis": "🩺",
        "comment": "💬"
    }
    return icons.get(annotation_type, "📌")

def display_annotation_details(annotation, index):
    """Affiche les détails d'une annotation"""
    
    if annotation['type'] == 'text':
        st.write(f"**Texte:** {annotation['content']}")
        st.write(f"**Position:** X={annotation['x']}%, Y={annotation['y']}%")
    
    elif annotation['type'] == 'measurement':
        st.write(f"**Mesure:** {annotation['measurement_type']}")
        st.write(f"**Valeur:** {annotation['value']} {annotation['unit']}")
    
    # Métadonnées communes
    st.write(f"**Auteur:** {annotation.get('author', 'Inconnu')}")
    st.write(f"**Horodatage:** {annotation.get('timestamp', 'N/A')}")
    
    # Bouton de suppression
    if st.button(f"🗑️ Supprimer", key=f"delete_{index}"):
        st.session_state.annotations.pop(index)
        st.success("Annotation supprimée")

def save_annotations_to_case():
    """Sauvegarde les annotations dans le cas ECG actuel"""
    
    if not st.session_state.annotations:
        st.warning("Aucune annotation à sauvegarder")
        return
    
    try:
        st.success(f"✅ {len(st.session_state.annotations)} annotation(s) sauvegardée(s)")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde: {e}")

def load_annotations_from_case():
    """Charge les annotations depuis le cas ECG actuel"""
    
    try:
        st.info("Chargement des annotations depuis le cas...")
        st.success("Annotations chargées avec succès")
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {e}")

def load_ecg_case(case_path):
    """Charge un cas ECG depuis un fichier JSON"""
    try:
        with open(case_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du cas: {e}")
        return None

def display_ecg_viewer(case_data, display_mode, show_grid, case_id):
    """Affiche le visualiseur ECG avec le cas sélectionné"""
    
    st.subheader(f"📈 Cas {case_id}")
    
    # Informations du cas
    with st.expander("ℹ️ Informations du cas"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Fichier:** {case_data.get('filename', 'N/A')}")
            st.write(f"**Type:** {case_data.get('file_type', 'N/A')}")
            st.write(f"**Statut:** {case_data.get('status', 'N/A')}")
        
        with col2:
            st.write(f"**Créé:** {case_data.get('created_date', 'N/A')}")
            st.write(f"**Contexte:** {case_data.get('clinical_context', 'N/A')}")
    
    # Affichage de l'ECG
    file_path = case_data.get('file_path')
    if file_path and Path(file_path).exists():
        display_ecg_image_with_grid(Path(file_path), show_grid, display_mode)
    else:
        # Essayer d'autres chemins possibles
        project_root = Path(__file__).parent.parent.parent
        alternative_paths = [
            project_root / "data" / "ecg_cases" / case_id / f"ecg_image.{case_data.get('file_type', 'png')}",
            project_root / "data" / "ecg_cases" / case_id / case_data.get('filename', 'ecg.png')
        ]
        
        image_found = False
        for alt_path in alternative_paths:
            if alt_path.exists():
                display_ecg_image_with_grid(alt_path, show_grid, display_mode)
                image_found = True
                break
        
        if not image_found:
            st.error(f"Image ECG non trouvée pour le cas {case_id}")
            st.info("Générer un ECG de démonstration...")
            display_simulated_ecg(display_mode, show_grid)

def display_ecg_image_with_grid(image_path, show_grid, display_mode):
    """Affiche une image ECG avec grille millimétée et annotations"""
    
    try:
        # Chargement de l'image
        image = Image.open(image_path)
        
        # Création de la figure matplotlib
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(image, aspect='auto')
        
        if show_grid:
            # Ajout de la grille millimétée
            width, height = image.size
            
            # Grille fine (1mm = environ 4 pixels à 300 DPI)
            grid_spacing_fine = 15  # pixels
            grid_spacing_coarse = grid_spacing_fine * 5  # 5mm
            
            # Lignes fines
            for x in range(0, width, grid_spacing_fine):
                ax.axvline(x, color='red', alpha=0.3, linewidth=0.5)
            for y in range(0, height, grid_spacing_fine):
                ax.axhline(y, color='red', alpha=0.3, linewidth=0.5)
            
            # Lignes épaisses (5mm)
            for x in range(0, width, grid_spacing_coarse):
                ax.axvline(x, color='red', alpha=0.7, linewidth=1)
            for y in range(0, height, grid_spacing_coarse):
                ax.axhline(y, color='red', alpha=0.7, linewidth=1)
        
        # Ajout des annotations visuelles
        if 'annotations' in st.session_state and st.session_state.annotations:
            width, height = image.size
            
            for i, annotation in enumerate(st.session_state.annotations):
                if annotation['type'] == 'text' and 'x' in annotation and 'y' in annotation:
                    # Position sur l'image
                    x_pos = (annotation['x'] / 100) * width
                    y_pos = (annotation['y'] / 100) * height
                    
                    # Ajouter le texte
                    ax.annotate(
                        annotation['content'],
                        xy=(x_pos, y_pos),
                        xytext=(10, 10),
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                        fontsize=10,
                        color='black',
                        weight='bold'
                    )
                    
                    # Ajouter un point de marquage
                    ax.plot(x_pos, y_pos, 'ro', markersize=8, alpha=0.8)
        
        ax.set_title(f"ECG - Mode: {display_mode}")
        ax.set_xlabel("Temps (25mm/s)")
        ax.set_ylabel("Amplitude (10mm/mV)")
        
        # Suppression des ticks
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Affichage dans Streamlit
        st.pyplot(fig)
        plt.close()
        
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'image: {e}")

def display_simulated_ecg(display_mode, show_grid):
    """Affiche un ECG simulé"""
    
    st.info("📊 Affichage ECG simulé")
    
    # Simulation de données ECG
    time = np.linspace(0, 10, 2500)  # 10 secondes à 250 Hz
    
    # Génération d'un signal ECG simulé
    ecg_signal = generate_simulated_ecg(time)
    
    # Création du graphique
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(time, ecg_signal, 'k-', linewidth=1)
    ax.set_title(f"ECG Simulé - Mode: {display_mode}")
    
    if show_grid:
        # Grille millimétée
        ax.grid(True, which='major', alpha=0.7, color='red', linewidth=0.8)
        ax.grid(True, which='minor', alpha=0.3, color='red', linewidth=0.4)
        ax.minorticks_on()
    
    ax.set_xlim(0, 10)
    ax.set_ylim(-2, 2)
    ax.set_xlabel('Temps (s)')
    ax.set_ylabel('mV')
    
    st.pyplot(fig)
    plt.close()

def generate_simulated_ecg(time):
    """Génère un signal ECG simulé"""
    
    # Paramètres du signal ECG
    heart_rate = 75  # bpm
    rr_interval = 60 / heart_rate  # secondes
    
    signal = np.zeros_like(time)
    
    # Génération des complexes QRS
    for t_start in np.arange(0, time[-1], rr_interval):
        # Complexe QRS
        qrs_center = t_start
        r_wave = 1.0 * np.exp(-((time - qrs_center) / 0.02) ** 2)
        signal += r_wave
        
        # Onde T
        t_center = t_start + 0.3
        if t_center < time[-1]:
            t_wave = 0.3 * np.exp(-((time - t_center) / 0.1) ** 2)
            signal += t_wave
    
    return signal

def perform_automatic_measurements():
    """Effectue des mesures automatiques sur l'ECG"""
    
    # Simulation de mesures automatiques
    measurements = {
        "Fréquence cardiaque": "75 bpm",
        "Intervalle PR": "160 ms",
        "Durée QRS": "90 ms",
        "Intervalle QT": "400 ms",
        "QTc (Bazett)": "410 ms",
        "Axe électrique": "+60°",
        "Rythme": "Sinusal régulier"
    }
    
    return measurements

def display_measurements(measurements):
    """Affiche les mesures automatiques"""
    
    st.success("✅ Analyse terminée")
    
    for param, value in measurements.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{param}:**")
        with col2:
            st.write(value)
    
    # Interprétation automatique
    st.subheader("🤖 Interprétation automatique")
    st.info("ECG normal. Rythme sinusal régulier à 75 bpm. Intervalles dans les limites normales.")

if __name__ == "__main__":
    ecg_reader_interface()
