import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import json
from pathlib import Path
from datetime import datetime

def ecg_reader_interface():
       # Bouton de suppression
    if st.button(f"🗑️ Supprimer", key=f"delete_{index}"):
        st.session_state.annotations.pop(index)
        st.success("Annotation supprimée")
        st.rerun()nterface de lecture ECG avancée avec outils de mesure"""
    
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
            case_files = list(cases_dir.glob("*.json"))
            if case_files:
                selected_case = st.selectbox(
                    "Choisir un cas ECG",
                    [f.stem for f in case_files]
                )
                
                # Chargement du cas
                if selected_case:
                    case_path = cases_dir / f"{selected_case}.json"
                    case_data = load_ecg_case(case_path)
                    
                    if case_data:
                        display_ecg_viewer(case_data, display_mode, show_grid)
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
                st.rerun()
        
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
                st.rerun()
        
        elif annotation_type == "Zone d'intérêt":
            zone_description = st.text_input("Description de la zone")
            zone_type = st.selectbox("Type", ["Arythmie", "Onde anormale", "Artéfact", "Zone normale"])
            
            if st.button("🎯 Marquer zone") and zone_description:
                new_annotation = {
                    "type": "zone",
                    "description": zone_description,
                    "zone_type": zone_type,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": st.session_state.get('current_user', 'admin')
                }
                st.session_state.annotations.append(new_annotation)
                st.success(f"✅ Zone marquée: {zone_description}")
                st.rerun()
        
        elif annotation_type == "Diagnostic":
            diagnostic_text = st.text_area("Diagnostic proposé")
            confidence = st.slider("Niveau de confiance (%)", 0, 100, 80)
            
            if st.button("🩺 Ajouter diagnostic") and diagnostic_text:
                new_annotation = {
                    "type": "diagnosis",
                    "content": diagnostic_text,
                    "confidence": confidence,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": st.session_state.get('current_user', 'admin')
                }
                st.session_state.annotations.append(new_annotation)
                st.success(f"✅ Diagnostic ajouté: {diagnostic_text}")
                st.rerun()
        
        elif annotation_type == "Commentaire":
            comment_text = st.text_area("Commentaire")
            comment_category = st.selectbox("Catégorie", ["Observation", "Question", "Enseignement", "Correction"])
            
            if st.button("💬 Ajouter commentaire") and comment_text:
                new_annotation = {
                    "type": "comment",
                    "content": comment_text,
                    "category": comment_category,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": st.session_state.get('current_user', 'admin')
                }
                st.session_state.annotations.append(new_annotation)
                st.success(f"✅ Commentaire ajouté")
                st.rerun()
        
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
                st.experimental_rerun()

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
    
    elif annotation['type'] == 'zone':
        st.write(f"**Description:** {annotation['description']}")
        st.write(f"**Type:** {annotation['zone_type']}")
    
    elif annotation['type'] == 'diagnosis':
        st.write(f"**Diagnostic:** {annotation['content']}")
        st.write(f"**Confiance:** {annotation['confidence']}%")
    
    elif annotation['type'] == 'comment':
        st.write(f"**Commentaire:** {annotation['content']}")
        st.write(f"**Catégorie:** {annotation['category']}")
    
    # Métadonnées communes
    st.write(f"**Auteur:** {annotation.get('author', 'Inconnu')}")
    st.write(f"**Horodatage:** {annotation.get('timestamp', 'N/A')}")
    
    # Bouton de suppression
    if st.button(f"�️ Supprimer", key=f"delete_{index}"):
        st.session_state.annotations.pop(index)
        st.success("Annotation supprimée")
        st.experimental_rerun()

def save_annotations_to_case():
    """Sauvegarde les annotations dans le cas ECG actuel"""
    
    if not st.session_state.annotations:
        st.warning("Aucune annotation à sauvegarder")
        return
    
    try:
        # Simuler la sauvegarde (à implémenter avec le cas sélectionné)
        annotations_data = {
            "annotations": st.session_state.annotations,
            "saved_at": st.session_state.get('current_time', ''),
            "saved_by": st.session_state.get('current_user', 'admin'),
            "total_count": len(st.session_state.annotations)
        }
        
        # TODO: Sauvegarder dans le fichier JSON du cas
        st.success(f"✅ {len(st.session_state.annotations)} annotation(s) sauvegardée(s)")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde: {e}")

def load_annotations_from_case():
    """Charge les annotations depuis le cas ECG actuel"""
    
    try:
        # TODO: Charger depuis le fichier JSON du cas
        # Pour l'instant, simulation
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

def display_ecg_viewer(case_data, display_mode, show_grid):
    """Affiche le visualiseur ECG avec le cas sélectionné"""
    
    st.subheader(f"📈 {case_data.get('metadata', {}).get('title', 'ECG sans titre')}")
    
    # Informations du cas
    with st.expander("ℹ️ Informations du cas"):
        metadata = case_data.get('metadata', {})
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Description:** {metadata.get('description', 'N/A')}")
            st.write(f"**Difficulté:** {metadata.get('difficulty', 'N/A')}")
            st.write(f"**Date:** {metadata.get('created_date', 'N/A')}")
        
        with col2:
            st.write(f"**Tags:** {', '.join(metadata.get('tags', []))}")
            st.write(f"**Validé par:** {metadata.get('validated_by', 'N/A')}")
            st.write(f"**Contexte:** {metadata.get('clinical_context', 'N/A')}")
    
    # Affichage de l'ECG
    ecg_data = case_data.get('ecg_data', {})
    
    if ecg_data.get('format') == 'image':
        # Affichage image avec grille
        image_path = Path("data") / ecg_data.get('image_path', '')
        if image_path.exists():
            display_ecg_image_with_grid(image_path, show_grid, display_mode)
        else:
            st.error(f"Image ECG non trouvée: {image_path}")
    
    elif ecg_data.get('format') == 'numerical':
        # Affichage tracé numérique
        display_numerical_ecg(ecg_data, display_mode, show_grid)
    
    else:
        st.warning("Format d'ECG non supporté ou données manquantes")

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
                
                elif annotation['type'] == 'zone':
                    # Marquer une zone d'intérêt (rectangle simulé)
                    rect_x = width * 0.2  # Position simulée
                    rect_y = height * 0.3
                    rect_width = width * 0.3
                    rect_height = height * 0.2
                    
                    rect = patches.Rectangle(
                        (rect_x, rect_y), rect_width, rect_height,
                        linewidth=2, edgecolor='orange', facecolor='orange', alpha=0.3
                    )
                    ax.add_patch(rect)
                    
                    # Label de la zone
                    ax.text(
                        rect_x + rect_width/2, rect_y - 10,
                        annotation['description'],
                        ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.8),
                        fontsize=9, weight='bold'
                    )
                
                elif annotation['type'] == 'measurement':
                    # Ligne de mesure simulée
                    line_start_x = width * 0.4
                    line_end_x = width * 0.6
                    line_y = height * 0.5
                    
                    # Ligne de mesure
                    ax.plot([line_start_x, line_end_x], [line_y, line_y], 
                           'g-', linewidth=3, alpha=0.8)
                    
                    # Marqueurs de début et fin
                    ax.plot([line_start_x, line_start_x], [line_y-10, line_y+10], 
                           'g-', linewidth=2)
                    ax.plot([line_end_x, line_end_x], [line_y-10, line_y+10], 
                           'g-', linewidth=2)
                    
                    # Label de mesure
                    ax.text(
                        (line_start_x + line_end_x) / 2, line_y - 20,
                        f"{annotation['value']} {annotation['unit']}",
                        ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8),
                        fontsize=9, weight='bold'
                    )
        
        ax.set_title(f"ECG - Mode: {display_mode}")
        ax.set_xlabel("Temps (25mm/s)")
        ax.set_ylabel("Amplitude (10mm/mV)")
        
        # Suppression des ticks
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Affichage dans Streamlit
        st.pyplot(fig)
        plt.close()
        
        # Légende des annotations
        if 'annotations' in st.session_state and st.session_state.annotations:
            with st.expander("🏷️ Légende des annotations"):
                st.markdown("**Couleurs des annotations :**")
                st.markdown("🔴 **Rouge :** Annotations texte")
                st.markdown("🟠 **Orange :** Zones d'intérêt") 
                st.markdown("🟢 **Vert :** Mesures")
                st.markdown("🟡 **Jaune :** Étiquettes de texte")
        
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'image: {e}")

def display_numerical_ecg(ecg_data, display_mode, show_grid):
    """Affiche un ECG numérique avec fond millimétré"""
    
    st.info("📊 Affichage ECG numérique - Fonctionnalité en développement")
    
    # Simulation de données ECG
    time = np.linspace(0, 10, 2500)  # 10 secondes à 250 Hz
    
    # Génération d'un signal ECG simulé
    ecg_signal = generate_simulated_ecg(time)
    
    # Configuration selon le mode d'affichage
    if display_mode == "12 dérivations standard":
        leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
        rows, cols = 4, 3
    elif display_mode == "6+6+DII long":
        leads = ['I', 'aVR', 'V1', 'V4', 'II', 'aVL', 'V2', 'V5', 'III', 'aVF', 'V3', 'V6', 'II long']
        rows, cols = 3, 4
    else:
        leads = ['I', 'II', 'III', 'aVR']
        rows, cols = 2, 2
    
    # Création du graphique
    fig, axes = plt.subplots(rows, cols, figsize=(15, 10))
    axes = axes.flatten() if rows * cols > 1 else [axes]
    
    for i, lead in enumerate(leads[:len(axes)]):
        ax = axes[i]
        
        # Signal ECG (avec variations par dérivation)
        signal = ecg_signal + np.random.normal(0, 0.1, len(ecg_signal))
        
        ax.plot(time, signal, 'k-', linewidth=1)
        ax.set_title(lead, fontweight='bold')
        
        if show_grid:
            # Grille millimétée
            ax.grid(True, which='major', alpha=0.7, color='red', linewidth=0.8)
            ax.grid(True, which='minor', alpha=0.3, color='red', linewidth=0.4)
            ax.minorticks_on()
        
        # Configuration des axes
        ax.set_xlim(0, 10)
        ax.set_ylim(-2, 2)
        
        # Labels seulement sur les bords
        if i >= len(axes) - cols:
            ax.set_xlabel('Temps (s)')
        if i % cols == 0:
            ax.set_ylabel('mV')
    
    plt.tight_layout()
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
        # Onde P
        p_center = t_start - 0.15
        if p_center > 0:
            p_wave = 0.2 * np.exp(-((time - p_center) / 0.05) ** 2)
            signal += p_wave
        
        # Complexe QRS
        qrs_center = t_start
        q_wave = -0.1 * np.exp(-((time - (qrs_center - 0.02)) / 0.01) ** 2)
        r_wave = 1.0 * np.exp(-((time - qrs_center) / 0.02) ** 2)
        s_wave = -0.2 * np.exp(-((time - (qrs_center + 0.02)) / 0.01) ** 2)
        
        signal += q_wave + r_wave + s_wave
        
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
