import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Tentative d'import Plotly avec fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def user_management_interface():
    """Interface de gestion des utilisateurs (WP4)"""
    
    st.title("👥 Gestion des Utilisateurs")
    st.markdown("### *Profils, authentification et analytics*")
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Profils Utilisateurs",
        "📊 Statistiques",
        "🔒 Mode Examen",
        "💬 Commentaires"
    ])
    
    with tab1:
        user_profiles_management()
    
    with tab2:
        user_analytics_dashboard()
    
    with tab3:
        exam_mode_management()
    
    with tab4:
        user_comments_management()

def user_profiles_management():
    """Gestion des profils utilisateurs"""
    
    st.subheader("👤 Gestion des Profils")
    
    # Actions principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Nouveau Utilisateur", use_container_width=True):
            create_new_user()
    
    with col2:
        if st.button("📤 Importer Utilisateurs", use_container_width=True):
            import_users_bulk()
    
    with col3:
        if st.button("📥 Exporter Liste", use_container_width=True):
            export_users_list()
    
    st.markdown("---")
    
    # Liste des utilisateurs existants
    users_df = load_users_data()
    
    if not users_df.empty:
        st.subheader("📋 Utilisateurs Enregistrés")
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            role_filter = st.selectbox(
                "Filtrer par rôle",
                ["Tous", "admin", "expert", "etudiant"]
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filtrer par statut",
                ["Tous", "actif", "inactif", "suspendu"]
            )
        
        with col3:
            search_term = st.text_input("🔍 Rechercher")
        
        # Application des filtres
        filtered_df = apply_user_filters(users_df, role_filter, status_filter, search_term)
        
        # Affichage du tableau
        if not filtered_df.empty:
            # Configuration des colonnes
            column_config = {
                "nom": st.column_config.TextColumn("Nom", width="medium"),
                "email": st.column_config.TextColumn("Email", width="large"),
                "role": st.column_config.SelectboxColumn(
                    "Rôle",
                    options=["admin", "expert", "etudiant"],
                    width="small"
                ),
                "statut": st.column_config.SelectboxColumn(
                    "Statut",
                    options=["actif", "inactif", "suspendu"],
                    width="small"
                ),
                "derniere_connexion": st.column_config.TextColumn(
                    "Dernière connexion",
                    width="medium"
                ),
                "progres": st.column_config.ProgressColumn(
                    "Progrès",
                    min_value=0,
                    max_value=100,
                    width="small"
                )
            }
            
            # Tableau éditable
            edited_df = st.data_editor(
                filtered_df,
                column_config=column_config,
                use_container_width=True,
                num_rows="dynamic"
            )
            
            # Sauvegarde des modifications
            if st.button("💾 Sauvegarder modifications"):
                save_users_data(edited_df)
                st.success("✅ Modifications sauvegardées")
        
        else:
            st.info("Aucun utilisateur ne correspond aux critères de filtrage")
    
    else:
        st.info("Aucun utilisateur enregistré. Créez le premier utilisateur.")

def create_new_user():
    """Interface de création d'un nouvel utilisateur"""
    
    with st.expander("➕ Créer un Nouvel Utilisateur", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("Nom complet*")
            email = st.text_input("Email*")
            institution = st.text_input("Institution")
        
        with col2:
            role = st.selectbox("Rôle*", ["etudiant", "expert", "admin"])
            password = st.text_input("Mot de passe*", type="password")
            confirm_password = st.text_input("Confirmer mot de passe*", type="password")
        
        # Permissions spéciales
        if role in ["expert", "admin"]:
            st.subheader("🔐 Permissions Spéciales")
            
            col1, col2 = st.columns(2)
            
            with col1:
                can_import = st.checkbox("Import ECG", value=True)
                can_annotate = st.checkbox("Annotation", value=True)
                can_validate = st.checkbox("Validation cas", value=role=="admin")
            
            with col2:
                can_manage_users = st.checkbox("Gestion utilisateurs", value=role=="admin")
                can_exam_mode = st.checkbox("Mode examen", value=True)
                can_export = st.checkbox("Export données", value=role=="admin")
        
        # Métadonnées
        st.subheader("📝 Informations Complémentaires")
        
        col1, col2 = st.columns(2)
        
        with col1:
            specialite = st.text_input("Spécialité médicale")
            niveau = st.selectbox("Niveau", ["Débutant", "Intermédiaire", "Avancé", "Expert"])
        
        with col2:
            notes = st.text_area("Notes", height=100)
        
        # Validation et création
        if st.button("✅ Créer Utilisateur"):
            if validate_user_data(nom, email, password, confirm_password):
                user_data = {
                    "nom": nom,
                    "email": email,
                    "role": role,
                    "institution": institution,
                    "password_hash": hash_password(password),
                    "created_date": datetime.now().isoformat(),
                    "statut": "actif",
                    "specialite": specialite,
                    "niveau": niveau,
                    "notes": notes,
                    "derniere_connexion": None,
                    "progres": 0
                }
                
                if role in ["expert", "admin"]:
                    user_data["permissions"] = {
                        "import": can_import,
                        "annotate": can_annotate,
                        "validate": can_validate,
                        "manage_users": can_manage_users,
                        "exam_mode": can_exam_mode,
                        "export": can_export
                    }
                
                if create_user(user_data):
                    st.success(f"✅ Utilisateur {nom} créé avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("❌ Erreur lors de la création de l'utilisateur")

def user_analytics_dashboard():
    """Tableau de bord des analytics utilisateurs"""
    
    st.subheader("📊 Analytics et Statistiques")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    users_data = load_users_data()
    
    with col1:
        total_users = len(users_data) if not users_data.empty else 0
        st.metric("👥 Utilisateurs Total", total_users)
    
    with col2:
        # Vérifier si la colonne 'statut' existe
        if not users_data.empty and 'statut' in users_data.columns:
            active_users = len(users_data[users_data['statut'] == 'actif'])
        else:
            active_users = total_users  # Considérer tous comme actifs si pas de colonne statut
        st.metric("✅ Utilisateurs Actifs", active_users)
    
    with col3:
        # Vérifier si la colonne 'role' existe
        if not users_data.empty and 'role' in users_data.columns:
            students = len(users_data[users_data['role'] == 'etudiant'])
        else:
            students = 0
        st.metric("🎓 Étudiants", students)
    
    with col4:
        # Vérifier si la colonne 'role' existe
        if not users_data.empty and 'role' in users_data.columns:
            experts = len(users_data[users_data['role'].isin(['expert', 'admin'])])
        else:
            experts = 0
        st.metric("👨‍⚕️ Experts", experts)
    
    if not users_data.empty:
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition par rôle
            st.subheader("📈 Répartition par Rôle")
            role_counts = users_data['role'].value_counts()
            
            if PLOTLY_AVAILABLE:
                fig_roles = px.pie(
                    values=role_counts.values,
                    names=role_counts.index,
                    title="Distribution des Rôles"
                )
                st.plotly_chart(fig_roles, use_container_width=True)
            else:
                # Fallback sans Plotly
                st.bar_chart(role_counts)
        
        with col2:
            # Progression moyenne
            st.subheader("📊 Progression des Étudiants")
            student_data = users_data[users_data['role'] == 'etudiant']
            
            if not student_data.empty and 'progres' in student_data.columns:
                if PLOTLY_AVAILABLE:
                    fig_progress = px.histogram(
                        student_data,
                        x='progres',
                        bins=10,
                        title="Distribution des Progrès"
                    )
                    st.plotly_chart(fig_progress, use_container_width=True)
                else:
                    # Fallback sans Plotly
                    st.bar_chart(student_data['progres'].value_counts().sort_index())
            else:
                st.info("Aucune donnée de progression disponible")
        
        # Activité récente
        st.subheader("🕒 Activité Récente")
        
        # Simulation d'activité
        recent_activity = generate_recent_activity(users_data)
        
        if recent_activity:
            activity_df = pd.DataFrame(recent_activity)
            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("Aucune activité récente")
    
    else:
        st.info("Aucune donnée utilisateur disponible pour les analytics")

def exam_mode_management():
    """Gestion du mode examen sécurisé"""
    
    st.subheader("🔒 Mode Examen Sécurisé")
    
    # Configuration d'un nouvel examen
    with st.expander("➕ Créer un Nouvel Examen", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            exam_title = st.text_input("Titre de l'examen*")
            exam_duration = st.number_input("Durée (minutes)", min_value=10, max_value=300, value=60)
            start_date = st.date_input("Date de début")
            start_time = st.time_input("Heure de début")
        
        with col2:
            end_date = st.date_input("Date de fin")
            end_time = st.time_input("Heure de fin")
            max_participants = st.number_input("Nombre max de participants", min_value=1, max_value=1000, value=50)
        
        # Sélection des cas ECG
        st.subheader("📚 Sélection des Cas ECG")
        
        # Liste des cas disponibles
        available_cases = get_available_ecg_cases()
        selected_cases = st.multiselect(
            "Cas ECG pour l'examen",
            available_cases,
            help="Sélectionnez les cas ECG à inclure dans l'examen"
        )
        
        # Paramètres de sécurité
        st.subheader("🔐 Paramètres de Sécurité")
        
        col1, col2 = st.columns(2)
        
        with col1:
            prevent_copy = st.checkbox("Empêcher copier/coller", value=True)
            fullscreen_mode = st.checkbox("Mode plein écran obligatoire", value=True)
            randomize_order = st.checkbox("Ordre aléatoire des questions", value=True)
        
        with col2:
            block_navigation = st.checkbox("Bloquer navigation browser", value=True)
            time_limit_per_case = st.checkbox("Limite de temps par cas", value=False)
            auto_submit = st.checkbox("Soumission automatique", value=True)
        
        # Création de l'examen
        if st.button("🎯 Créer Examen"):
            exam_data = {
                "title": exam_title,
                "duration": exam_duration,
                "start_datetime": f"{start_date} {start_time}",
                "end_datetime": f"{end_date} {end_time}",
                "max_participants": max_participants,
                "cases": selected_cases,
                "security_settings": {
                    "prevent_copy": prevent_copy,
                    "fullscreen_mode": fullscreen_mode,
                    "randomize_order": randomize_order,
                    "block_navigation": block_navigation,
                    "time_limit_per_case": time_limit_per_case,
                    "auto_submit": auto_submit
                },
                "created_by": "admin",  # À remplacer par l'utilisateur actuel
                "created_date": datetime.now().isoformat(),
                "status": "planifié"
            }
            
            if create_exam(exam_data):
                st.success("✅ Examen créé avec succès !")
            else:
                st.error("❌ Erreur lors de la création de l'examen")
    
    # Liste des examens existants
    st.subheader("📋 Examens Programmés")
    
    exams_data = load_exams_data()
    
    if not exams_data.empty:
        # Affichage des examens
        for idx, exam in exams_data.iterrows():
            with st.expander(f"🎯 {exam['title']} - {exam['status']}", expanded=False):
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Début:** {exam['start_datetime']}")
                    st.write(f"**Fin:** {exam['end_datetime']}")
                    st.write(f"**Durée:** {exam['duration']} min")
                
                with col2:
                    st.write(f"**Participants max:** {exam['max_participants']}")
                    st.write(f"**Cas ECG:** {len(exam.get('cases', []))}")
                    st.write(f"**Statut:** {exam['status']}")
                
                with col3:
                    if st.button(f"🚀 Lancer", key=f"launch_{idx}"):
                        st.success("🎯 Examen lancé !")
                    
                    if st.button(f"📊 Résultats", key=f"results_{idx}"):
                        display_exam_results(exam)
                    
                    if st.button(f"🗑️ Supprimer", key=f"delete_{idx}"):
                        delete_exam(idx)
                        st.experimental_rerun()
    
    else:
        st.info("Aucun examen programmé")

def user_comments_management():
    """Gestion des commentaires utilisateurs"""
    
    st.subheader("💬 Commentaires et Feedback")
    
    # Affichage des commentaires récents
    comments_data = load_user_comments()
    
    if not comments_data.empty:
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            type_filter = st.selectbox(
                "Type de commentaire",
                ["Tous", "Bug", "Suggestion", "Question", "Compliment"]
            )
        
        with col2:
            status_filter = st.selectbox(
                "Statut",
                ["Tous", "Nouveau", "En cours", "Résolu", "Fermé"]
            )
        
        with col3:
            priority_filter = st.selectbox(
                "Priorité",
                ["Toutes", "Haute", "Moyenne", "Basse"]
            )
        
        # Application des filtres
        filtered_comments = apply_comments_filters(comments_data, type_filter, status_filter, priority_filter)
        
        # Affichage des commentaires
        for idx, comment in filtered_comments.iterrows():
            with st.expander(f"💬 {comment['type']} - {comment['user']} ({comment['date']})", expanded=False):
                
                st.write(f"**Contenu:** {comment['content']}")
                st.write(f"**Cas ECG:** {comment.get('ecg_case', 'N/A')}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_status = st.selectbox(
                        "Statut",
                        ["Nouveau", "En cours", "Résolu", "Fermé"],
                        index=["Nouveau", "En cours", "Résolu", "Fermé"].index(comment['status']),
                        key=f"status_{idx}"
                    )
                
                with col2:
                    new_priority = st.selectbox(
                        "Priorité",
                        ["Haute", "Moyenne", "Basse"],
                        index=["Haute", "Moyenne", "Basse"].index(comment['priority']),
                        key=f"priority_{idx}"
                    )
                
                with col3:
                    if st.button(f"💾 Mettre à jour", key=f"update_{idx}"):
                        update_comment_status(idx, new_status, new_priority)
                        st.success("✅ Commentaire mis à jour")
                
                # Réponse admin
                admin_response = st.text_area(
                    "Réponse administrateur",
                    value=comment.get('admin_response', ''),
                    key=f"response_{idx}"
                )
                
                if st.button(f"📤 Envoyer réponse", key=f"send_{idx}"):
                    save_admin_response(idx, admin_response)
                    st.success("✅ Réponse envoyée")
    
    else:
        st.info("Aucun commentaire utilisateur")

# Fonctions utilitaires (simulées pour la démonstration)

def load_users_data():
    """Charge les données utilisateurs"""
    users_file = Path("users/profils.csv")
    
    if users_file.exists():
        try:
            df = pd.read_csv(users_file)
            
            # Assurer que les colonnes essentielles existent
            required_columns = ['nom', 'email', 'role', 'statut']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'statut':
                        df[col] = 'actif'  # Par défaut actif
                    elif col == 'role':
                        df[col] = 'etudiant'  # Par défaut étudiant
                    elif col == 'nom':
                        df[col] = 'Utilisateur'
                    elif col == 'email':
                        df[col] = 'user@example.com'
            
            return df
        except Exception as e:
            st.warning(f"Erreur lecture fichier utilisateurs: {e}")
    
    # Données par défaut pour la démonstration
    return pd.DataFrame({
        'nom': ['Dr. Martin Durand', 'Sophie Leclerc', 'Jean Dupont'],
        'email': ['m.durand@chu.fr', 's.leclerc@univ.fr', 'j.dupont@etudiant.fr'],
        'role': ['expert', 'etudiant', 'etudiant'],
        'statut': ['actif', 'actif', 'inactif'],
        'institution': ['CHU Bordeaux', 'Université Lyon', 'Université Paris'],
        'derniere_connexion': ['2025-01-20', '2025-01-22', '2025-01-15'],
        'progres': [85, 65, 30]
    })

def import_users_bulk():
    """Interface d'import en masse d'utilisateurs"""
    
    with st.expander("📤 Import en Masse d'Utilisateurs", expanded=True):
        st.write("Importez plusieurs utilisateurs via un fichier CSV")
        
        # Template CSV
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Format du fichier CSV")
            st.code("""nom,email,role,institution,specialite,niveau
Dr. Jean Martin,j.martin@chu.fr,expert,CHU Paris,Cardiologie,Expert
Marie Dubois,m.dubois@univ.fr,etudiant,Université Lyon,Médecine,Intermédiaire""")
        
        with col2:
            # Téléchargement du template
            template_csv = """nom,email,role,institution,specialite,niveau
Exemple Nom,exemple@email.fr,etudiant,Institution,Spécialité,Débutant"""
            
            st.download_button(
                label="📥 Télécharger Template CSV",
                data=template_csv,
                file_name="template_utilisateurs.csv",
                mime="text/csv"
            )
        
        # Upload de fichier
        uploaded_file = st.file_uploader(
            "Choisir fichier CSV",
            type=['csv'],
            help="Format: nom,email,role,institution,specialite,niveau"
        )
        
        if uploaded_file is not None:
            try:
                # Lecture du CSV
                import_df = pd.read_csv(uploaded_file)
                
                st.subheader("👀 Aperçu des données")
                st.dataframe(import_df)
                
                # Validation
                valid, errors = validate_import_data(import_df)
                
                if errors:
                    st.error("❌ Erreurs détectées :")
                    for error in errors:
                        st.write(f"• {error}")
                
                if valid:
                    st.success("✅ Données valides")
                    
                    if st.button("🚀 Importer les utilisateurs"):
                        success_count = process_bulk_import(import_df)
                        st.success(f"✅ {success_count} utilisateurs importés avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")


def export_users_list():
    """Interface d'export de la liste utilisateurs"""
    
    with st.expander("📥 Export Liste Utilisateurs", expanded=True):
        
        # Options d'export
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_format = st.selectbox(
                "Format d'export",
                ["CSV", "Excel", "JSON"]
            )
        
        with col2:
            include_passwords = st.checkbox(
                "Inclure mots de passe hashés",
                value=False,
                help="Pour la sauvegarde de sécurité uniquement"
            )
        
        with col3:
            role_filter = st.selectbox(
                "Filtrer par rôle",
                ["Tous", "admin", "expert", "etudiant"]
            )
        
        # Génération de l'export
        if st.button("📤 Générer Export"):
            users_data = load_users_data()
            
            if not users_data.empty:
                # Application du filtre
                if role_filter != "Tous":
                    users_data = users_data[users_data['role'] == role_filter]
                
                # Suppression des données sensibles si nécessaire
                if not include_passwords and 'password_hash' in users_data.columns:
                    users_data = users_data.drop('password_hash', axis=1)
                
                # Génération du fichier
                if export_format == "CSV":
                    csv_data = users_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv_data,
                        file_name=f"utilisateurs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "JSON":
                    json_data = users_data.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Télécharger JSON",
                        data=json_data,
                        file_name=f"utilisateurs_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
                
                st.success("✅ Export généré avec succès !")
            
            else:
                st.warning("⚠️ Aucune donnée utilisateur à exporter")


def validate_import_data(df):
    """Valide les données d'import"""
    errors = []
    valid = True
    
    # Vérification des colonnes requises
    required_columns = ['nom', 'email', 'role']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"Colonnes manquantes: {', '.join(missing_columns)}")
        valid = False
    
    # Vérification des valeurs
    if 'role' in df.columns:
        invalid_roles = df[~df['role'].isin(['admin', 'expert', 'etudiant'])]['role'].unique()
        if len(invalid_roles) > 0:
            errors.append(f"Rôles invalides: {', '.join(invalid_roles)}")
            valid = False
    
    # Vérification des emails
    if 'email' in df.columns:
        invalid_emails = df[~df['email'].str.contains('@', na=False)]['email'].tolist()
        if invalid_emails:
            errors.append(f"Emails invalides: {', '.join(invalid_emails[:3])}...")
            valid = False
    
    return valid, errors


def process_bulk_import(df):
    """Traite l'import en masse d'utilisateurs"""
    success_count = 0
    
    for idx, row in df.iterrows():
        try:
            user_data = {
                "nom": row['nom'],
                "email": row['email'],
                "role": row['role'],
                "institution": row.get('institution', ''),
                "specialite": row.get('specialite', ''),
                "niveau": row.get('niveau', 'Débutant'),
                "password_hash": hash_password("motdepasse123"),  # Mot de passe par défaut
                "created_date": datetime.now().isoformat(),
                "statut": "actif",
                "derniere_connexion": None,
                "progres": 0
            }
            
            if create_user(user_data):
                success_count += 1
        
        except Exception as e:
            st.warning(f"Erreur pour {row.get('nom', 'utilisateur')}: {e}")
    
def apply_user_filters(df, role_filter, status_filter, search_term):
    """Applique les filtres sur les données utilisateurs"""
    filtered_df = df.copy()
    
    if role_filter != "Tous":
        filtered_df = filtered_df[filtered_df['role'] == role_filter]
    
    if status_filter != "Tous":
        filtered_df = filtered_df[filtered_df['statut'] == status_filter]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['nom'].str.contains(search_term, case=False, na=False) |
            filtered_df['email'].str.contains(search_term, case=False, na=False)
        ]
    
    return filtered_df
    """Applique les filtres sur les données utilisateurs"""
    filtered_df = df.copy()
    
    if role_filter != "Tous":
        filtered_df = filtered_df[filtered_df['role'] == role_filter]
    
    if status_filter != "Tous":
        filtered_df = filtered_df[filtered_df['statut'] == status_filter]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['nom'].str.contains(search_term, case=False, na=False) |
            filtered_df['email'].str.contains(search_term, case=False, na=False)
        ]
    
    return filtered_df

def validate_user_data(nom, email, password, confirm_password):
    """Valide les données utilisateur"""
    if not all([nom, email, password]):
        st.error("❌ Veuillez remplir tous les champs obligatoires")
        return False
    
    if password != confirm_password:
        st.error("❌ Les mots de passe ne correspondent pas")
        return False
    
    if len(password) < 6:
        st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
        return False
    
    return True

def hash_password(password):
    """Hash le mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(user_data):
    """Crée un nouvel utilisateur"""
    # Simulation de création utilisateur
    return True

def save_users_data(df):
    """Sauvegarde les données utilisateurs"""
    # Simulation de sauvegarde
    pass

def generate_recent_activity(users_data):
    """Génère des données d'activité récente"""
    return [
        {"Utilisateur": "Sophie Leclerc", "Action": "Exercice ECG", "Date": "2025-01-22 14:30", "Score": "85%"},
        {"Utilisateur": "Jean Dupont", "Action": "Consultation cas", "Date": "2025-01-22 10:15", "Score": "-"},
        {"Utilisateur": "Dr. Martin Durand", "Action": "Annotation cas", "Date": "2025-01-21 16:45", "Score": "-"}
    ]

def get_available_ecg_cases():
    """Récupère la liste des cas ECG disponibles"""
    return ["ECG_001 - Infarctus antérieur", "ECG_002 - Tachycardie", "ECG_003 - Bradycardie"]

def create_exam(exam_data):
    """Crée un nouvel examen"""
    return True

def load_exams_data():
    """Charge les données des examens"""
    return pd.DataFrame({
        'title': ['Examen Final Cardiologie', 'Test Intermédiaire ECG'],
        'start_datetime': ['2025-02-01 09:00', '2025-01-28 14:00'],
        'end_datetime': ['2025-02-01 11:00', '2025-01-28 15:30'],
        'duration': [120, 90],
        'max_participants': [50, 25],
        'status': ['planifié', 'en cours'],
        'cases': [['ECG_001', 'ECG_002'], ['ECG_003']]
    })

def display_exam_results(exam):
    """Affiche les résultats d'un examen"""
    st.info("📊 Interface de résultats d'examen - En développement")

def delete_exam(exam_id):
    """Supprime un examen"""
    pass

def load_user_comments():
    """Charge les commentaires utilisateurs"""
    return pd.DataFrame({
        'user': ['Sophie Leclerc', 'Jean Dupont'],
        'type': ['Suggestion', 'Bug'],
        'content': ['Ajouter plus de cas cliniques', 'Problème de chargement sur mobile'],
        'date': ['2025-01-22', '2025-01-21'],
        'status': ['Nouveau', 'En cours'],
        'priority': ['Moyenne', 'Haute'],
        'ecg_case': ['ECG_001', 'N/A'],
        'admin_response': ['', 'Problème pris en compte']
    })

def apply_comments_filters(df, type_filter, status_filter, priority_filter):
    """Applique les filtres sur les commentaires"""
    filtered_df = df.copy()
    
    if type_filter != "Tous":
        filtered_df = filtered_df[filtered_df['type'] == type_filter]
    
    if status_filter != "Tous":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if priority_filter != "Toutes":
        filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
    
    return filtered_df

def update_comment_status(comment_id, status, priority):
    """Met à jour le statut d'un commentaire"""
    pass

def save_admin_response(comment_id, response):
    """Sauvegarde la réponse administrateur"""
    pass

if __name__ == "__main__":
    user_management_interface()
