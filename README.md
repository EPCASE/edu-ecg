# 🫀 Edu-ECG - Plateforme d'apprentissage ECG

Plateforme interactive d'apprentissage de l'electrocardiogramme avec annotation semi-automatique et ontologie medicale.

## 🚀 Fonctionnalites

- 🧠 **Correction intelligente** basee sur une ontologie de 281 concepts ECG
- 📱 **Interface moderne** compatible desktop, tablette et mobile  
- 🎓 **Workflow pedagogique** : annotation expert → formation etudiant → evaluation
- 📊 **Analytics detailles** avec scoring nuance et suivi de progression
- 🔐 **Systeme d'authentification** avec gestion des roles (admin, expert, etudiant)

## 📦 Installation

1. Cloner le depot :
```bash
git clone https://github.com/EPCASE/edu-ecg.git
cd edu-ecg
```

2. Creer un environnement virtuel :
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Installer les dependances :
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Utilisation

Lancer l'application :
```bash
streamlit run frontend/app.py
```

## 👥 Auteur

Gregoire Massoullie - gregoire.massoullie@orange.fr

## 📄 Licence

MIT License
