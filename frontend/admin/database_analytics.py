"""
📊 Analytics Avancés pour Base de Données ECG
Module d'analyse et statistiques complètes
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# Vérification des dépendances optionnelles
PLOTLY_AVAILABLE = False
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    px = None
    go = None

def install_analytics_dependencies():
    """Interface pour installer les dépendances analytics"""
    st.warning("📊 Module Analytics - Dépendances manquantes")
    st.info("Pour utiliser pleinement le module Analytics, vous devez installer plotly.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.code("pip install plotly", language="bash")
        st.caption("Installation manuelle")
    
    with col2:
        if st.button("🚀 Utiliser requirements_full.txt", key="install_full_deps"):
            st.info("Lancez cette commande dans votre terminal :")
            st.code("pip install -r requirements_full.txt", language="bash")
            st.success("Redémarrez l'application après l'installation !")
    
    st.divider()
    st.subheader("📈 Fonctionnalités disponibles sans plotly")
    
    # Afficher quand même les métriques de base
    show_basic_analytics()

def show_basic_analytics():
    """Affichage des analytics de base sans plotly"""
    try:
        data_dir = Path("data")
        
        # Métriques générales
        st.subheader("📊 Métriques générales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Compter les cas ECG
        ecg_cases_dir = data_dir / "ecg_cases"
        total_cases = len(list(ecg_cases_dir.glob("*.json"))) if ecg_cases_dir.exists() else 0
        
        # Compter les sessions
        sessions_dir = data_dir / "ecg_sessions"
        total_sessions = len(list(sessions_dir.glob("*.json"))) if sessions_dir.exists() else 0
        
        with col1:
            st.metric("Total Cas ECG", total_cases)
        
        with col2:
            st.metric("Total Sessions", total_sessions)
        
        with col3:
            ratio = f"{total_sessions/total_cases:.1f}" if total_cases > 0 else "0"
            st.metric("Sessions/Cas", ratio)
        
        with col4:
            st.metric("Taille DB", f"{get_database_size():.1f} MB")
        
        # Analyse des diagnostics
        if total_cases > 0:
            st.subheader("🏥 Analyse des diagnostics")
            diagnostics = get_diagnostics_summary()
            
            if diagnostics:
                # Affichage en tableau
                df_diag = pd.DataFrame(list(diagnostics.items()), 
                                     columns=["Diagnostic", "Nombre"])
                df_diag = df_diag.sort_values("Nombre", ascending=False)
                st.dataframe(df_diag, use_container_width=True)
        
        # Recommandations
        st.subheader("💡 Recommandations")
        show_recommendations(total_cases, total_sessions)
        
    except Exception as e:
        st.error(f"Erreur lors du calcul des métriques : {str(e)}")

def get_database_size():
    """Calcule la taille totale de la base de données en MB"""
    try:
        data_dir = Path("data")
        if not data_dir.exists():
            return 0
        
        total_size = 0
        for path in data_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        
        return total_size / (1024 * 1024)  # Convertir en MB
    except:
        return 0

def get_diagnostics_summary():
    """Résumé des diagnostics dans la base de données"""
    diagnostics = defaultdict(int)
    
    try:
        cases_dir = Path("data/ecg_cases")
        if not cases_dir.exists():
            return {}
        
        for case_file in cases_dir.glob("*.json"):
            try:
                with open(case_file, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                    
                # Extraire le diagnostic
                diagnostic = case_data.get('diagnostic', 'Non spécifié')
                if isinstance(diagnostic, list):
                    for d in diagnostic:
                        diagnostics[d] += 1
                else:
                    diagnostics[diagnostic] += 1
                    
            except Exception:
                continue
    except Exception:
        pass
    
    return dict(diagnostics)

def show_recommendations(total_cases, total_sessions):
    """Affiche des recommandations basées sur les métriques"""
    recommendations = []
    
    if total_cases == 0:
        recommendations.append("🎯 Commencez par importer vos premiers cas ECG")
    elif total_cases < 10:
        recommendations.append("📈 Ajoutez plus de cas pour enrichir votre base de données")
    
    if total_sessions == 0 and total_cases > 0:
        recommendations.append("🔄 Créez des sessions d'annotation pour vos cas existants")
    elif total_sessions < total_cases * 0.5:
        recommendations.append("✍️ Augmentez le taux d'annotation de vos cas")
    
    ratio = total_sessions / total_cases if total_cases > 0 else 0
    if ratio > 2:
        recommendations.append("⭐ Excellent taux d'annotation ! Continuez ainsi")
    
    if not recommendations:
        recommendations.append("✅ Votre base de données est bien équilibrée")
    
    for rec in recommendations:
        st.info(rec)

def display_database_analytics():
    """Interface d'analytics avancés pour la base de données ECG"""
    
    st.markdown("### 📊 Analytics de la Base de Données ECG")
    
    # Vérifier si plotly est disponible
    if not PLOTLY_AVAILABLE:
        install_analytics_dependencies()
        return
    
    # Le reste du code original avec plotly...
    
    # Charger les données
    cases_data = load_all_cases_data()
    
    if not cases_data:
        st.warning("📭 Aucune donnée disponible pour l'analyse")
        return
    
    # Métriques globales
    display_global_metrics(cases_data)
    
    # Graphiques et analyses
    col1, col2 = st.columns(2)
    
    with col1:
        display_cases_evolution(cases_data)
        display_annotation_distribution(cases_data)
    
    with col2:
        display_categories_chart(cases_data)
        display_quality_metrics(cases_data)
    
    # Analyses détaillées
    display_detailed_analytics(cases_data)

def load_all_cases_data():
    """Charge toutes les données des cas ECG avec métadonnées complètes"""
    
    cases_data = []
    cases_dir = Path("data/ecg_cases")
    
    if not cases_dir.exists():
        return cases_data
    
    for case_dir in cases_dir.iterdir():
        if case_dir.is_dir():
            case_info = extract_case_metadata(case_dir)
            if case_info:
                cases_data.append(case_info)
    
    return cases_data

def extract_case_metadata(case_dir):
    """Extrait métadonnées complètes d'un cas"""
    
    try:
        metadata_file = case_dir / "metadata.json"
        
        # Métadonnées de base
        case_info = {
            'case_id': case_dir.name,
            'folder_path': str(case_dir),
            'folder_size_mb': get_folder_size(case_dir),
            'created_date': None,
            'category': 'Non classé',
            'difficulty': 'Non défini',
            'annotations_count': 0,
            'ecg_files_count': 0,
            'has_expert_annotation': False,
            'quality_score': 0
        }
        
        # Charger métadonnées JSON si disponibles
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            case_info.update({
                'name': metadata.get('name', case_dir.name),
                'description': metadata.get('description', ''),
                'category': metadata.get('category', 'Non classé'),
                'difficulty': metadata.get('difficulty', 'Non défini'),
                'created_date': metadata.get('created_date'),
                'type': metadata.get('type', 'simple'),
                'annotations': metadata.get('annotations', []),
                'annotations_count': len(metadata.get('annotations', [])),
            })
            
            # Analyse des ECG
            if metadata.get('type') == 'multi_ecg':
                case_info['ecg_files_count'] = len(metadata.get('ecgs', []))
            else:
                case_info['ecg_files_count'] = 1
        
        # Analyser annotations expertes
        case_info['has_expert_annotation'] = check_expert_annotations(case_info.get('annotations', []))
        
        # Calculer score qualité
        case_info['quality_score'] = calculate_quality_score(case_info)
        
        return case_info
        
    except Exception as e:
        st.error(f"Erreur extraction métadonnées {case_dir.name}: {e}")
        return None

def get_folder_size(folder_path):
    """Calcule taille d'un dossier en MB"""
    
    total_size = 0
    for file in folder_path.rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
    return round(total_size / (1024 * 1024), 2)

def check_expert_annotations(annotations):
    """Vérifie présence d'annotations expertes"""
    
    for ann in annotations:
        if ann.get('type') == 'expert' or ann.get('auteur') == 'expert':
            return True
    return False

def calculate_quality_score(case_info):
    """Calcule score qualité du cas (0-100)"""
    
    score = 0
    
    # Métadonnées complètes (40 points)
    if case_info.get('description'):
        score += 15
    if case_info.get('category') != 'Non classé':
        score += 10
    if case_info.get('difficulty') != 'Non défini':
        score += 10
    if case_info.get('created_date'):
        score += 5
    
    # Annotations (40 points)
    if case_info.get('annotations_count') > 0:
        score += 20
    if case_info.get('has_expert_annotation'):
        score += 20
    
    # Fichiers ECG (20 points)
    if case_info.get('ecg_files_count') > 0:
        score += 10
    if case_info.get('type') == 'multi_ecg':
        score += 10
    
    return min(score, 100)

def display_global_metrics(cases_data):
    """Affiche métriques globales"""
    
    st.markdown("#### 📈 Métriques Globales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_cases = len(cases_data)
    annotated_cases = sum(1 for case in cases_data if case['annotations_count'] > 0)
    expert_cases = sum(1 for case in cases_data if case['has_expert_annotation'])
    total_size = sum(case['folder_size_mb'] for case in cases_data)
    
    with col1:
        st.metric("📋 Total Cas", total_cases)
    
    with col2:
        st.metric("✅ Cas Annotés", annotated_cases, f"{annotated_cases/total_cases*100:.1f}%" if total_cases > 0 else "0%")
    
    with col3:
        st.metric("🧠 Validation Experte", expert_cases, f"{expert_cases/total_cases*100:.1f}%" if total_cases > 0 else "0%")
    
    with col4:
        st.metric("💾 Taille Totale", f"{total_size:.1f} MB")

def display_cases_evolution(cases_data):
    """Graphique évolution des cas dans le temps"""
    
    st.markdown("#### 📅 Évolution des Cas ECG")
    
    # Préparer données temporelles
    dates = []
    for case in cases_data:
        if case.get('created_date'):
            try:
                date = datetime.fromisoformat(case['created_date'].replace('Z', '+00:00'))
                dates.append(date.date())
            except:
                continue
    
    if not dates:
        st.info("🗓️ Pas de données temporelles disponibles")
        return
    
    # Créer DataFrame pour le graphique
    df = pd.DataFrame({'date': dates})
    # Convertir en datetime pandas pour utiliser l'accessor .dt
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    evolution = df.groupby('month').size().reset_index(name='count')
    evolution['month_str'] = evolution['month'].astype(str)
    
    # Graphique
    fig = px.line(evolution, x='month_str', y='count', 
                  title="Nouveaux cas par mois",
                  markers=True)
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_annotation_distribution(cases_data):
    """Distribution des annotations"""
    
    st.markdown("#### 🏷️ Distribution des Annotations")
    
    annotation_counts = [case['annotations_count'] for case in cases_data]
    
    if not annotation_counts:
        st.info("📊 Pas de données d'annotations")
        return
    
    # Créer histogramme
    fig = px.histogram(x=annotation_counts, 
                      title="Répartition du nombre d'annotations par cas",
                      nbins=10)
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_categories_chart(cases_data):
    """Graphique répartition par catégories"""
    
    st.markdown("#### 📂 Répartition par Catégories")
    
    categories = [case['category'] for case in cases_data]
    category_counts = pd.Series(categories).value_counts()
    
    if category_counts.empty:
        st.info("📈 Pas de données de catégories")
        return
    
    # Graphique en secteurs
    fig = px.pie(values=category_counts.values, 
                names=category_counts.index,
                title="Cas par catégorie")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_quality_metrics(cases_data):
    """Métriques de qualité des cas"""
    
    st.markdown("#### ⭐ Score Qualité Moyen")
    
    quality_scores = [case['quality_score'] for case in cases_data]
    
    if not quality_scores:
        st.info("📊 Pas de données de qualité")
        return
    
    avg_quality = np.mean(quality_scores)
    
    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = avg_quality,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Score Qualité (0-100)"},
        delta = {'reference': 80},
        gauge = {'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}],
                'threshold': {'line': {'color': "red", 'width': 4},
                            'thickness': 0.75, 'value': 90}}))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_detailed_analytics(cases_data):
    """Analyses détaillées"""
    
    st.markdown("#### 🔍 Analyses Détaillées")
    
    # Tableau des cas avec métriques
    df_cases = pd.DataFrame(cases_data)
    
    if df_cases.empty:
        return
    
    # Sélectionner colonnes importantes
    display_columns = ['case_id', 'category', 'difficulty', 'annotations_count', 
                      'ecg_files_count', 'quality_score', 'folder_size_mb']
    
    available_columns = [col for col in display_columns if col in df_cases.columns]
    
    st.dataframe(
        df_cases[available_columns].sort_values('quality_score', ascending=False),
        use_container_width=True
    )
    
    # Recommandations
    display_recommendations(cases_data)

def display_recommendations(cases_data):
    """Affiche recommandations d'amélioration"""
    
    st.markdown("#### 💡 Recommandations d'Amélioration")
    
    total_cases = len(cases_data)
    if total_cases == 0:
        return
    
    # Analyses et recommandations
    low_quality_cases = [case for case in cases_data if case['quality_score'] < 50]
    unannotated_cases = [case for case in cases_data if case['annotations_count'] == 0]
    uncategorized_cases = [case for case in cases_data if case['category'] == 'Non classé']
    
    recommendations = []
    
    if low_quality_cases:
        recommendations.append(f"🔧 **{len(low_quality_cases)} cas** ont un score qualité faible (<50). Améliorer métadonnées et annotations.")
    
    if unannotated_cases:
        recommendations.append(f"📝 **{len(unannotated_cases)} cas** sans annotations. Prioriser l'annotation experte.")
    
    if uncategorized_cases:
        recommendations.append(f"📂 **{len(uncategorized_cases)} cas** non classés. Ajouter catégories pour organisation.")
    
    if not recommendations:
        st.success("✅ **Excellente qualité !** La base de données est bien structurée.")
    else:
        for rec in recommendations:
            st.warning(rec)

if __name__ == "__main__":
    display_database_analytics()
