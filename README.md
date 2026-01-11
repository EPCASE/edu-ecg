# 🫀 Edu-ECG – Plateforme d'enseignement interactif de l'électrocardiogramme

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

**📋 Projet Original** : Créé en décembre 2024 | **👨‍💻 Auteur** : Grégoire Massoullié | **🏛️ Institution** : EPCASE

---

## 🌐 **Accès Direct - Application Web**

**🎯 Pour les utilisateurs (étudiants/enseignants) :**
- ✅ **AUCUNE installation** requise
- ✅ **Accès web direct** : http://localhost:8501
- ✅ **Compatible tous navigateurs** (Chrome, Firefox, Safari, Edge)
- ✅ **Interface responsive** : PC, tablette, mobile

---

## 🎯 **Vue d'ensemble**

**Edu-ECG** Inventions l'apprentissage de l'électrocardiogramme avec :

### 🧠 **Correction Intelligente**
- **281 concepts ECG** organisés par ontologie médicale
- **Autocomplétion intelligente** avec suggestions en temps réel
- **Scoring nuancé** : reconnaît les réponses partiellement correctes
- **Feedback pédagogique** : suggestions constructives et comparaisons expert/étudiant

### 🎨 **Visualiseur ECG Avancé**
- **Zoom fluide** : molette souris + slider (0.25x - 5x)
- **Navigation pan** : clic-glisser pour explorer l'ECG
- **Outil de mesure** : caliper intégré pour intervalles et amplitudes
- **Mode plein écran** : présentation immersive
- **Grille ECG** : superposition 5mm/25mm

### 📱 **Interface Moderne**
- **Design épuré** : navigation sidebar intuitive
- **Mode dev actif** : accès admin anonyme par défaut
- **Authentification optionnelle** : connexion dans la sidebar
- **Multi-rôles** : admin, expert, étudiant

### 🎓 **Workflow Pédagogique**
1. **Expert** : Import ECG → Annotation avec ontologie → Création sessions
2. **Étudiant** : Consultation cas → Annotation guidée → Feedback intelligent
3. **Suivi** : Analytics détaillés, progression, scores

### 🎓 **Session Builder** (NOUVEAU)
**Interface complète pour créer des sessions de formation en minutes**
- **📤 Import intelligent** : ECG simple ou multi-ECG (évolution temporelle)
- **🏷️ Annotation assistée par LLM** : 3000 concepts détectés automatiquement
- **🔍 Recherche rapide** : Recherche instantanée dans l'ontologie (0ms)
- **📚 Création de sessions** : Workflow guidé en 4 étapes

**Accès :** http://localhost:8502  
**Documentation :** [`docs/SESSION_BUILDER_QUICKSTART.md`](docs/SESSION_BUILDER_QUICKSTART.md)

**Performance :**
- ⏱️ **1-2 min** pour créer un cas complet
- 🚀 **Cache Redis** : 70% des requêtes instantanées
- 🎯 **5-15 concepts** détectés automatiquement
- 💰 **Gratuit** avec mode Recherche Rapide

---

## 🚀 **Démarrage Rapide**

### Installation (administrateur uniquement)

```bash
# 1. Cloner le projet
git clone https://github.com/EPCASE/edu-ecg.git
cd edu-ecg

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
streamlit run frontend/app.py
```

### Accès utilisateurs
- Ouvrir **http://localhost:8501** dans le navigateur
- Mode développement actif (admin par défaut)
- Connexion optionnelle via sidebar

### Identifiants démo
- **Admin** : admin/admin123
- **Expert** : expert/expert123  
- **Étudiant** : etudiant/etudiant123

---

## 📁 **Structure du Projet**
```
ECG lecture/
├── frontend/                      # Interface utilisateur
│   ├── app.py                    # Application principale
│   ├── pages_ecg_cases.py        # Page cas ECG
│   ├── auth_system.py            # Authentification
│   ├── correction_engine.py      # Moteur ontologique
│   ├── advanced_ecg_viewer.py    # Visualiseur avancé
│   ├── annotation_components.py  # Composants annotation
│   └── admin/                    # Modules administration
│       └── smart_ecg_importer_simple.py
├── data/                         # Données
│   ├── ecg_cases/               # Base de cas ECG
│   ├── ecg_sessions/            # Sessions d'exercices
│   ├── ontology.json            # Ontologie ECG
│   └── users.json               # Base utilisateurs
├── backend/                      # Logique métier
├── deploy_to_github.bat         # Script déploiement
└── requirements.txt             # Dépendances Python
```

<div align="center">
🫀 Edu-ECG - Transformer l'apprentissage de l'électrocardiographie

Développé avec ❤️ pour l'éducation médicale
</div>