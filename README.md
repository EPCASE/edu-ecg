# 🫀 Edu-ECG - Plateforme d'apprentissage ECG

Plateforme interactive d'apprentissage de l'électrocardiogramme avec annotation semi-automatique et ontologie médicale.

## 🚀 Fonctionnalités

- 🧠 **Correction intelligente** basée sur une ontologie de 281 concepts ECG
- 📱 **Interface moderne** compatible desktop, tablette et mobile  
- 🎓 **Workflow pédagogique** : annotation expert → formation étudiant → évaluation
- 📊 **Analytics détaillés** avec scoring nuancé et suivi de progression
- 🔐 **Système d'authentification** avec gestion des rôles (admin, expert, étudiant)

## 📦 Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/EPCASE/edu-ecg.git
cd edu-ecg
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Utilisation

Lancer l'application :
```bash
streamlit run frontend/app.py
```

## 📁 Structure du projet

```
edu-ecg/
├── frontend/
│   ├── app.py                 # Application principale
│   ├── auth_system.py         # Système d'authentification
│   ├── annotation_components.py
│   └── admin/
│       └── smart_ecg_importer_simple.py
├── backend/
│   ├── correction_engine.py   # Moteur de correction ontologique
│   └── import_cases.py
├── data/
│   ├── ontologie.owx          # Ontologie ECG
│   ├── ecg_cases/            # Cas ECG (créé automatiquement)
│   └── ecg_sessions/         # Sessions d'exercices
└── requirements.txt
```

## 👥 Auteur

Grégoire Massoullié - gregoire.massoullie@orange.fr

## 📄 Licence

MIT License - Voir fichier LICENSE pour les détails
