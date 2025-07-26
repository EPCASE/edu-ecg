# 🫀 EDU-CG - Formation ECG Interactive

**Plateforme d'enseignement interactif de l'électrocardiogramme avec correction automatique basée sur ontologie médicale**

## 🎯 **Vue d'ensemble**

Edu-CG est une plateforme innovante qui révolutionne l'apprentissage de l'électrocardiogramme en combinant :
- 🧠 **Ontologie médicale** avec 281 concepts ECG
- 🤖 **Correction intelligente** hiérarchique et sémantique  
- 📱 **Interface tablette** compatible pour usage clinique
- 📚 **Base de cas experts** annotée par des cliniciens

## ⚡ **Démarrage rapide**

### 1. **Installation des dépendances**
```bash
pip install streamlit owlready2 pillow pandas
```

### 2. **Lancement de l'application**
```bash
python launch.py
```

### 3. **Accès à l'interface**
- 🌐 **URL**: http://localhost:8501
- 📱 **Compatible**: Tablette, mobile, desktop
- 👥 **Modes**: Admin (expert) / Étudiant

## 🏗️ **Architecture du projet**

```
📁 ECG lecture/
├── 🚀 launch.py              # ⭐ POINT D'ENTRÉE PRINCIPAL
├── 🚀 frontend/
│   ├── app.py                # Interface principale Streamlit
│   └── admin/
│       ├── import_cases.py   # WP1 - Import ECG multi-formats
│       └── annotation_tool.py # WP3 - Annotation ontologique
├── 🧠 backend/
│   └── correction_engine.py  # Moteur de correction sémantique
├── 📊 data/
│   ├── ontologie.owx         # Ontologie ECG (281 concepts)
│   └── ecg_cases/            # Base de cas annotés
└── 🧪 tests/
    ├── test_system.py        # Tests de validation
    ├── demo.py              # Démonstrations
    └── validate.py          # Validation complète
```

## 🎓 **Fonctionnalités principales**

### ✅ **Interface Admin/Expert**
- **📤 Import ECG**: Multi-formats (image, HL7 XML)
- **🏷️ Annotation ontologique**: Saisie assistée avec coefficients pondérés
- **⚙️ Configuration**: Paramètres de correction ajustables
- **📊 Gestion**: Vue d'ensemble de la base de cas

### ✅ **Interface Étudiant**
- **📚 Consultation**: Parcours des ECG avec annotations
- **🎯 Exercices**: Entraînement avec feedback immédiat
- **📈 Évaluation**: Scoring intelligent basé sur l'ontologie
- **📱 Responsive**: Optimisé pour tablettes et mobiles

### ✅ **Moteur de correction intelligent**
- **🎯 Correspondance exacte**: 100% pour concept identique
- **🔼 Concept parent**: 50% pour généralisation acceptée
- **🔽 Concept enfant**: 25% pour spécialisation acceptable
- **❌ Non reliés**: 0% pour concepts sans relation ontologique
- **💬 Feedback explicatif**: Justification pédagogique automatique

## 🔬 **Work Packages (WP) - État d'avancement**

### ✅ **WP3 : Outil d'interprétation ontologique** *(OPÉRATIONNEL)*
- Ontologie ECG chargée et fonctionnelle
- Moteur de correction hiérarchique implémenté
- Interface d'annotation avec coefficients ajustables
- Familles de concepts (Description/Interprétation/Diagnostic)

### 🔄 **WP1 : Base de données ECG** *(EN DÉVELOPPEMENT)*
- Interface d'import créée (images, HL7 XML)
- Métadonnées automatiques (utilisateur, date, contexte)
- Outils de traitement d'image (recadrage, anonymisation)

### 🔄 **WP2 : Liseuse ECG** *(PLANIFIÉ)*
- Affichage tracé numérique sur fond millimétré
- Outils de mesure (amplitude, durée)
- Configurations multi-dérivations

### 🔄 **WP4 : Gestion utilisateurs** *(PLANIFIÉ)*
- Authentification et profils
- Statistiques avancées
- Mode examen sécurisé

## 🧠 **Innovation pédagogique**

**Correction sémantique** au lieu du traditionnel vrai/faux :
```
Réponse attendue: "Tachycardie sinusale"
Réponse étudiant: "Tachycardie"
→ Score: 50% (concept parent acceptable)
→ Feedback: "Réponse correcte mais incomplète. Précisez le type de tachycardie."
```

## 📱 **Compatibilité**

- ✅ **Desktop**: Windows, Mac, Linux
- ✅ **Tablette**: iPad, Android (interface tactile optimisée)
- ✅ **Mobile**: Responsive design pour smartphones
- ✅ **Navigateurs**: Chrome, Firefox, Safari, Edge

## 🔧 **Développement**

### **Tests et validation**
```bash
python test_system.py      # Tests système complets
python demo.py            # Démonstration fonctionnalités
python validate.py        # Validation ontologie
```

### **Structure de développement**
- **Frontend**: Streamlit (Python)
- **Backend**: OWLready2 pour ontologie
- **Base de données**: JSON + système de fichiers
- **Tests**: Unittest + validation automatique

## 📊 **Métriques de performance**

- **🧠 Ontologie**: 281 concepts ECG intégrés
- **⚡ Scoring**: < 100ms par évaluation
- **📱 Interface**: Responsive sur tous écrans
- **🎯 Précision**: Scoring hiérarchique nuancé

## 🎓 **Impact pédagogique attendu**

1. **⏰ Réduction temps correction**: Automatisation pour enseignants
2. **📈 Apprentissage efficace**: Feedback immédiat et personnalisé
3. **📏 Standardisation**: Évaluations cohérentes inter-établissements
4. **🌐 Accessibilité**: Formation 24/7 auto-guidée

## 🚀 **Roadmap**

- **Phase 1** ✅: Ontologie + Correction sémantique + Interface de base
- **Phase 2** 🔄: Import multi-formats + Annotation complète
- **Phase 3** 🔜: Liseuse ECG + Outils de mesure
- **Phase 4** 🔜: Gestion utilisateurs + Mode examen

---

**🏆 Edu-CG représente une avancée majeure dans l'enseignement médical numérique, alliant rigueur scientifique et innovation pédagogique !**

> *Développé pour révolutionner l'apprentissage de l'ECG avec une approche basée sur l'intelligence artificielle et les ontologies médicales.*
