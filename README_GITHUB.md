# 🫀 Edu-ECG - Plateforme d'enseignement de l'électrocardiogramme

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

## 🎯 Description

**Edu-ECG** est une plateforme web interactive pour l'apprentissage de l'interprétation des électrocardiogrammes. Elle propose :

- 🧠 **Saisie semi-automatique intelligente** avec ontologie de 281 concepts ECG
- 📱 **Interface web moderne** accessible depuis tout navigateur
- 🎓 **Modes expert et étudiant** avec feedback pédagogique adaptatif
- 📊 **Import multi-formats** (PDF, PNG, JPG, XML, HL7)

## 🚀 Démarrage rapide

### Installation
```bash
git clone https://github.com/[votre-username]/edu-ecg.git
cd edu-ecg
pip install -r requirements.txt
```

**👨‍💻 Développé par :** EPCASE  
**📧 Contact :** gregoire.massoullie@orange.fr

### Lancement
```bash
python launch.py
```

Puis ouvrir : http://localhost:8501

## 📁 Structure du projet

```
📁 ECG lecture/
├── 🖥️ frontend/           # Interface Streamlit
├── 🧠 backend/            # Moteur ontologique
├── 📊 data/               # Cas ECG et ontologie
├── 👥 users/              # Gestion utilisateurs
├── 🧪 tests/              # Tests et validation
└── 📚 docs/               # Documentation
```

## 🎓 Fonctionnalités

### Mode Administrateur
- Import et annotation de cas ECG
- Gestion de la base de données
- Analytics et statistiques

### Mode Étudiant
- Consultation des cas ECG
- Annotation avec feedback intelligent
- Suivi de progression

## 🌐 Déploiement

### Scalingo (Recommandé)
Le projet est prêt pour le déploiement sur Scalingo avec tous les fichiers de configuration inclus.

### Autres plateformes
Compatible Heroku, Docker, et serveurs dédiés.

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez la documentation complète dans `README.md` pour plus de détails.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

**👨‍💻 Développeur :** EPCASE  
**📧 Contact :** gregoire.massoullie@orange.fr  
**🐛 Issues :** Pour rapporter des bugs ou suggérer des améliorations

---

**🚀 Révolutionnez l'enseignement de l'ECG !** 🫀
