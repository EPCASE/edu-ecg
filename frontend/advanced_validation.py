import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageStat
import numpy as np
import cv2
import io
import tempfile
import os

def advanced_ecg_validation(uploaded_file):
    """
    Validation avancée des fichiers ECG avec analyse d'image
    """
    validation_report = {
        'score': 0,
        'max_score': 100,
        'checks': [],
        'recommendations': [],
        'auto_fixes': [],
        'image_analysis': None
    }
    
    # 1. Validation de base du fichier
    file_validation = validate_file_basics(uploaded_file)
    validation_report['checks'].extend(file_validation['checks'])
    validation_report['score'] += file_validation['score']
    
    # 2. Analyse d'image pour les formats image
    if uploaded_file.type and uploaded_file.type.startswith('image'):
        image_analysis = analyze_ecg_image(uploaded_file)
        validation_report['image_analysis'] = image_analysis
        validation_report['checks'].extend(image_analysis['checks'])
        validation_report['score'] += image_analysis['score']
        validation_report['recommendations'].extend(image_analysis['recommendations'])
    
    # 3. Suggestions d'amélioration
    if validation_report['score'] < 80:
        validation_report['recommendations'].append(
            "🎯 Score de qualité modéré - considérer l'optimisation du fichier"
        )
    
    return validation_report

def validate_file_basics(uploaded_file):
    """Validation de base du fichier"""
    checks = []
    score = 0
    max_basic_score = 40
    
    # Taille du fichier
    size_mb = uploaded_file.size / (1024 * 1024)
    if 0.1 <= size_mb <= 10:
        checks.append({"✅ Taille": f"{size_mb:.1f} MB - Optimal"})
        score += 15
    elif size_mb < 0.1:
        checks.append({"⚠️ Taille": f"{size_mb:.1f} MB - Très petit"})
        score += 5
    else:
        checks.append({"⚠️ Taille": f"{size_mb:.1f} MB - Volumineux"})
        score += 10
    
    # Format de fichier
    file_ext = uploaded_file.name.lower().split('.')[-1]
    if file_ext in ['png', 'jpg', 'jpeg']:
        checks.append({"✅ Format": f"{file_ext.upper()} - Image supportée"})
        score += 15
    elif file_ext == 'pdf':
        checks.append({"✅ Format": "PDF - Document supporté"})
        score += 15
    elif file_ext in ['xml', 'hl7']:
        checks.append({"✅ Format": f"{file_ext.upper()} - Format médical"})
        score += 15
    else:
        checks.append({"❌ Format": f"{file_ext.upper()} - Non supporté"})
    
    # Nom de fichier
    if len(uploaded_file.name) <= 50:
        checks.append({"✅ Nom": "Longueur appropriée"})
        score += 10
    else:
        checks.append({"⚠️ Nom": "Nom très long"})
        score += 5
    
    return {
        'checks': checks,
        'score': min(score, max_basic_score)
    }

def analyze_ecg_image(uploaded_file):
    """Analyse avancée d'image ECG"""
    checks = []
    recommendations = []
    score = 0
    max_image_score = 60
    
    try:
        # Charger l'image
        image = Image.open(uploaded_file)
        img_array = np.array(image)
        
        # 1. Résolution
        width, height = image.size
        resolution_score = analyze_resolution(width, height, checks)
        score += resolution_score
        
        # 2. Ratio d'aspect
        aspect_score = analyze_aspect_ratio(width, height, checks, recommendations)
        score += aspect_score
        
        # 3. Qualité d'image
        quality_score = analyze_image_quality(image, img_array, checks, recommendations)
        score += quality_score
        
        # 4. Détection de grille ECG
        grid_score = detect_ecg_grid(img_array, checks, recommendations)
        score += grid_score
        
        # 5. Contraste et lisibilité
        contrast_score = analyze_contrast(img_array, checks, recommendations)
        score += contrast_score
        
    except Exception as e:
        checks.append({"❌ Analyse": f"Erreur: {str(e)}"})
        recommendations.append("🔧 Vérifier l'intégrité du fichier image")
    
    return {
        'checks': checks,
        'recommendations': recommendations,
        'score': min(score, max_image_score)
    }

def analyze_resolution(width, height, checks):
    """Analyse de la résolution"""
    total_pixels = width * height
    
    if total_pixels >= 1920 * 1080:  # Full HD ou plus
        checks.append({"✅ Résolution": f"{width}x{height} - Excellente"})
        return 15
    elif total_pixels >= 1280 * 720:  # HD
        checks.append({"✅ Résolution": f"{width}x{height} - Bonne"})
        return 12
    elif total_pixels >= 800 * 600:   # Minimale acceptable
        checks.append({"⚠️ Résolution": f"{width}x{height} - Acceptable"})
        return 8
    else:
        checks.append({"❌ Résolution": f"{width}x{height} - Insuffisante"})
        return 3

def analyze_aspect_ratio(width, height, checks, recommendations):
    """Analyse du ratio d'aspect"""
    ratio = width / height
    
    if 1.3 <= ratio <= 2.0:  # Ratio paysage typique pour ECG
        checks.append({"✅ Ratio": f"{ratio:.2f} - Optimal pour ECG"})
        return 10
    elif ratio > 2.0:
        checks.append({"⚠️ Ratio": f"{ratio:.2f} - Très large"})
        recommendations.append("📏 Ratio très large - vérifier le recadrage")
        return 6
    else:
        checks.append({"⚠️ Ratio": f"{ratio:.2f} - Format portrait"})
        recommendations.append("🔄 Format portrait détecté - paysage recommandé pour ECG")
        return 4

def analyze_image_quality(image, img_array, checks, recommendations):
    """Analyse de la qualité d'image"""
    score = 0
    
    # Vérifier si l'image est en couleur ou noir et blanc
    if len(img_array.shape) == 3:
        # Image couleur
        checks.append({"✅ Type": "Image couleur"})
        score += 5
        
        # Calculer la variance des couleurs pour détecter si c'est vraiment coloré
        color_variance = np.var(img_array, axis=(0, 1))
        if np.mean(color_variance) < 100:  # Seuil arbitraire
            recommendations.append("🎨 Image quasi-monochrome - conversion N&B possible")
    else:
        # Image en niveaux de gris
        checks.append({"✅ Type": "Image monochrome - Optimal pour ECG"})
        score += 8
    
    # Netteté (variance du Laplacien)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    try:
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var > 500:
            checks.append({"✅ Netteté": "Image nette"})
            score += 10
        elif laplacian_var > 100:
            checks.append({"⚠️ Netteté": "Netteté modérée"})
            score += 6
        else:
            checks.append({"❌ Netteté": "Image floue"})
            recommendations.append("🔍 Image floue - améliorer la netteté ou rescanner")
            score += 2
    except:
        pass
    
    return score

def detect_ecg_grid(img_array, checks, recommendations):
    """Détection de grille ECG"""
    try:
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Détection de lignes horizontales et verticales
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Détection de lignes avec Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None and len(lines) > 20:
            checks.append({"✅ Grille": f"Grille ECG détectée ({len(lines)} lignes)"})
            return 15
        elif lines is not None and len(lines) > 5:
            checks.append({"⚠️ Grille": f"Grille partielle ({len(lines)} lignes)"})
            recommendations.append("📐 Grille ECG partiellement visible - vérifier la qualité")
            return 8
        else:
            checks.append({"❌ Grille": "Aucune grille détectée"})
            recommendations.append("📊 Aucune grille ECG visible - vérifier que c'est bien un ECG")
            return 3
            
    except Exception:
        checks.append({"⚠️ Grille": "Analyse impossible"})
        return 5

def analyze_contrast(img_array, checks, recommendations):
    """Analyse du contraste"""
    try:
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Calculer l'histogramme
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Calculer le contraste (écart-type de l'histogramme)
        contrast = np.std(gray)
        
        if contrast > 60:
            checks.append({"✅ Contraste": f"Excellent ({contrast:.1f})"})
            return 10
        elif contrast > 40:
            checks.append({"✅ Contraste": f"Bon ({contrast:.1f})"})
            return 7
        elif contrast > 20:
            checks.append({"⚠️ Contraste": f"Faible ({contrast:.1f})"})
            recommendations.append("🔆 Contraste faible - améliorer l'éclairage ou les paramètres")
            return 4
        else:
            checks.append({"❌ Contraste": f"Très faible ({contrast:.1f})"})
            recommendations.append("🔆 Contraste très faible - image difficilement lisible")
            return 1
            
    except Exception:
        checks.append({"⚠️ Contraste": "Analyse impossible"})
        return 3

def display_validation_report(validation_report):
    """Affichage du rapport de validation avec interface moderne"""
    
    # Score global avec barre de progression
    score_percent = (validation_report['score'] / validation_report['max_score']) * 100
    
    # Couleur selon le score
    if score_percent >= 80:
        score_color = "green"
        score_emoji = "🟢"
    elif score_percent >= 60:
        score_color = "orange" 
        score_emoji = "🟡"
    else:
        score_color = "red"
        score_emoji = "🔴"
    
    # Affichage du score
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric(
            "📊 Score de Qualité ECG", 
            f"{validation_report['score']}/{validation_report['max_score']}", 
            f"{score_percent:.1f}%"
        )
    
    with col2:
        st.progress(score_percent / 100)
    
    with col3:
        st.markdown(f"## {score_emoji}")
    
    # Détails de validation
    with st.expander("🔍 Détails de la validation", expanded=score_percent < 80):
        
        # Checks
        st.subheader("✅ Vérifications")
        for check_dict in validation_report['checks']:
            for key, value in check_dict.items():
                st.write(f"{key}: {value}")
        
        # Analyse d'image spécifique
        if validation_report['image_analysis']:
            st.subheader("🖼️ Analyse d'image")
            st.info("Analyse spécialisée pour les fichiers image ECG")
    
    # Recommandations
    if validation_report['recommendations']:
        with st.expander("💡 Recommandations d'amélioration"):
            for rec in validation_report['recommendations']:
                st.info(rec)
    
    # Actions correctives
    if validation_report['auto_fixes']:
        with st.expander("🔧 Corrections automatiques"):
            for fix in validation_report['auto_fixes']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(fix)
                with col2:
                    if st.button("Appliquer", key=f"fix_{hash(fix)}"):
                        st.success("✅ Correction appliquée")
    
    return score_percent

def create_quality_improvement_suggestions(score_percent):
    """Suggestions d'amélioration basées sur le score"""
    
    if score_percent >= 80:
        st.success("🎉 Excellente qualité ! Votre ECG est prêt pour l'import.")
    elif score_percent >= 60:
        st.warning("⚠️ Qualité correcte avec des améliorations possibles.")
        
        with st.expander("🎯 Suggestions d'optimisation"):
            st.write("""
            **Pour améliorer encore la qualité :**
            - 📸 Utiliser une résolution plus élevée (1920x1080 minimum)
            - 🔆 Améliorer l'éclairage lors de la numérisation
            - 📏 Vérifier l'orientation (paysage recommandé)
            - 🎯 Recadrer pour ne garder que l'ECG
            """)
    else:
        st.error("❌ Qualité insuffisante - Améliorations nécessaires")
        
        with st.expander("🚨 Actions correctives requises", expanded=True):
            st.write("""
            **Améliorations prioritaires :**
            - 📸 Augmenter significativement la résolution
            - 🔆 Améliorer le contraste et l'éclairage
            - 📐 Vérifier que la grille ECG est visible
            - 🎯 Recadrer précisément sur l'ECG
            - 🔄 Utiliser le format paysage
            """)
            
            if st.button("🔄 Nouvelle tentative recommandée"):
                st.info("Veuillez uploader un nouveau fichier avec les améliorations suggérées.")

# Interface de test pour la validation
def test_validation_interface():
    """Interface de test pour la validation avancée"""
    st.title("🧪 Test - Validation Avancée ECG")
    st.write("*Test du nouveau système de validation inspiré d'ep-cases*")
    
    uploaded_file = st.file_uploader(
        "Télécharger un ECG pour test",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Testez la validation avancée avec votre fichier ECG"
    )
    
    if uploaded_file:
        st.subheader("📊 Rapport de Validation")
        
        # Lancer la validation
        with st.spinner("🔍 Analyse en cours..."):
            validation_report = advanced_ecg_validation(uploaded_file)
        
        # Afficher les résultats
        score_percent = display_validation_report(validation_report)
        
        # Suggestions d'amélioration
        create_quality_improvement_suggestions(score_percent)
        
        # Aperçu du fichier
        if uploaded_file.type.startswith('image'):
            st.subheader("👁️ Aperçu")
            col1, col2 = st.columns(2)
            with col1:
                st.image(uploaded_file, caption="Image originale", width=300)
            with col2:
                st.write("**Informations :**")
                image = Image.open(uploaded_file)
                st.write(f"- Dimensions : {image.size[0]}x{image.size[1]}")
                st.write(f"- Mode : {image.mode}")
                st.write(f"- Taille : {uploaded_file.size / 1024:.1f} KB")

if __name__ == "__main__":
    test_validation_interface()
