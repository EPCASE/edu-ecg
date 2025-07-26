import streamlit as st
import json
from pathlib import Path

# Fichier des autorisations (sessions assignées)
PERMISSIONS_PATH = Path(__file__).parent.parent.parent / "data" / "session_permissions.json"
# Fichier des utilisateurs (exemple CSV ou liste statique)
USERS_PATH = Path(__file__).parent.parent.parent / "users" / "profils.csv"
# Dossier des cas ECG
CASES_DIR = Path(__file__).parent.parent.parent / "data" / "ecg_cases"

def load_users():
    users = []
    try:
        with open(USERS_PATH, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if parts:
                    users.append(parts[0])
    except Exception:
        users = ["etudiant1", "etudiant2", "etudiant3"]
    return users

def load_cases():
    return [d.name for d in CASES_DIR.iterdir() if d.is_dir()]

def load_permissions():
    if PERMISSIONS_PATH.exists():
        with open(PERMISSIONS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_permissions(permissions):
    with open(PERMISSIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(permissions, f, indent=2, ensure_ascii=False)

def session_manager():
    st.title("🔑 Gestion des autorisations de sessions ECG")
    users = load_users()
    cases = load_cases()
    permissions = load_permissions()

    user = st.selectbox("👤 Sélectionner un utilisateur", users)
    assigned = set(permissions.get(user, []))
    selected = st.multiselect(
        "📋 Sessions ECG à autoriser pour cet utilisateur :",
        cases,
        default=list(assigned)
    )
    if st.button("💾 Enregistrer les autorisations"):
        permissions[user] = selected
        save_permissions(permissions)
        st.success("Autorisations mises à jour !")
    st.markdown("---")
    st.subheader("Aperçu des autorisations actuelles :")
    for u in users:
        st.write(f"**{u}** : {permissions.get(u, [])}")

if __name__ == "__main__":
    session_manager()
