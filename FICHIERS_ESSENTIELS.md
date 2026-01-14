# 📦 Fichiers Essentiels pour Faire Fonctionner l'Application

**Date:** 11 janvier 2026

## ✅ Fichiers NÉCESSAIRES (à commiter sur GitHub)

### 🎯 Backend (Services Python)
```
backend/
├── __init__.py
├── rdf_owl_extractor.py        # Extraction ontologie OWL → JSON
├── ontology_service.py          # Service gestion ontologie
├── scoring_service_llm.py       # Scoring avec LLM
├── feedback_service.py          # Service feedback
├── pdf_extractor.py             # Extraction PDF
├── requirements.txt             # Dépendances backend
├── Dockerfile                   # Container backend
└── services/
    ├── llm_service.py           # Service OpenAI
    ├── ontology_service.py      # Service ontologie complet
    ├── llm_semantic_matcher.py  # Matching sémantique LLM
    └── concept_decomposer.py    # Décomposition concepts
```

### 🎨 Frontend (Interface Streamlit)
```
frontend/
├── app.py                       # Application principale ⭐
├── pages_ecg_cases.py           # Pages ECG cases
├── correction_llm_poc.py        # Module correction LLM
├── ecg_session_builder.py       # Constructeur sessions
├── requirements.txt             # Dépendances frontend
├── Dockerfile                   # Container frontend
├── .streamlit/
│   └── config.toml              # Config Streamlit
├── pages/
│   ├── ecg_import.py            # Page import ECG
│   └── correction_llm.py        # Page correction LLM
└── admin/
    └── smart_ecg_importer_simple.py  # Import intelligent
```

### 📊 Data (Ontologie)
```
data/
├── ontology_from_owl.json       # Ontologie JSON (280 concepts) ⭐
└── ontologie.owx                # Ontologie OWL source
```

### 🐳 Infrastructure
```
docker-compose.yml               # Orchestration containers
nginx/
└── nginx.conf                   # Config reverse proxy
requirements.txt                 # Dépendances racine
regenerate_ontology.py           # Script régénération ontologie
```

### 📚 Documentation Technique
```
docs/
├── architecture.md              # Architecture système
├── GUIDE_ONTOLOGIE_OWL.md       # Guide ontologie
├── SCORING_HIERARCHIQUE.md      # Scoring hiérarchique
├── ECG_SESSION_BUILDER_GUIDE.md # Guide session builder
└── ROADMAP_COMPLETE.md          # Roadmap projet
```

### 🧪 Tests
```
tests/
├── test_ontology_backward_compatibility.py
├── test_correction_owl_migration.py
└── test_cache_integration.py
```

### ⚙️ Configuration
```
.gitignore                       # Exclusions Git
.env.example                     # Template variables env
.streamlit/config.toml           # Config Streamlit
```

---

## ❌ Fichiers NON NÉCESSAIRES (exclus par .gitignore)

### 🗂️ BMAD & Session Notes (local seulement)
```
_bmad/                           # Notes session BMAD
_bmad-output/                    # Analyses & brainstorming
SESSION_RECAP_*.md               # Récaps sessions
PARTY_MODE_*.md                  # Party mode docs
AMELIORATIONS_*.md               # Notes améliorations
CORRECTIFS_*.md                  # Notes correctifs
INTEGRATION_*.md                 # Notes intégration
```

### 💾 Backups
```
backups/                         # Sauvegardes automatiques
*.backup                         # Fichiers backup
```

### 📁 Data Temporaire
```
data/ecg_cases/                  # ECG de test (créés dynamiquement)
data/ecg_sessions/               # Sessions de test
data/epi1c_dataset/              # Dataset EPIC1 (volumineux)
data/case_templates_epic1*.json  # Templates temporaires
data/test_cases*.json            # Cas de test
```

### 🔧 Scripts Temporaires
```
analyze_*.py                     # Scripts analyse
test_*.py                        # Scripts test
extract_*.py                     # Scripts extraction
cleanup_*.ps1                    # Scripts nettoyage
```

### 📦 Dev Archive
```
dev_archive/prototypes/          # Prototypes anciens
dev_archive/scripts/             # Scripts dev
dev_archive/docs_old/            # Docs obsolètes
```

---

## 🚀 Pour Déployer l'Application

### Depuis GitHub (clone):

```bash
# 1. Cloner le repo
git clone https://github.com/EPCASE/edu-ecg.git
cd edu-ecg

# 2. Créer .env depuis .env.example
cp .env.example .env
# Éditer .env avec vos clés API

# 3. Créer les dossiers data manquants
mkdir -p data/ecg_cases data/ecg_sessions

# 4. Lancer avec Docker
docker-compose up -d

# OU lancer localement
pip install -r requirements.txt
streamlit run frontend/app.py
```

### Fichiers créés automatiquement:
- `data/ecg_cases/` - Créé au premier import ECG
- `data/ecg_sessions/` - Créé à la première session
- `users.db` - Créé au premier utilisateur

---

## 📋 Checklist Commit Propre

### ✅ À inclure:
- [ ] Code backend (services Python)
- [ ] Code frontend (Streamlit)
- [ ] Ontologie JSON (`ontology_from_owl.json`)
- [ ] Documentation technique (`docs/`)
- [ ] Configuration Docker
- [ ] Requirements.txt
- [ ] .gitignore mis à jour
- [ ] README.md à jour

### ❌ À exclure:
- [ ] Dossier `_bmad/` et `_bmad-output/`
- [ ] Dossier `backups/`
- [ ] Dossier `data/ecg_cases/` (sauf structure vide)
- [ ] Dossier `data/ecg_sessions/` (sauf structure vide)
- [ ] Fichiers `*.backup`
- [ ] Scripts temporaires `test_*.py`, `analyze_*.py`
- [ ] Notes session `SESSION_RECAP_*.md`
- [ ] Dataset `data/epi1c_dataset/` (trop volumineux)
- [ ] Fichiers `.env` (secrets)

---

## 🎯 Commande Git Propre

```bash
# 1. Reset staging
git reset HEAD

# 2. Ajouter seulement fichiers essentiels
git add .gitignore
git add backend/
git add frontend/
git add data/ontology_from_owl.json
git add data/ontologie.owx
git add docs/
git add docker-compose.yml
git add nginx/
git add requirements.txt
git add regenerate_ontology.py
git add .streamlit/
git add .env.example
git add README.md
git add tests/

# 3. Commit
git commit -m "feat: Backend & Frontend complets avec ontologie OWL

✨ Nouveautés:
- Backend services (LLM, scoring, ontologie, feedback)
- Frontend Streamlit (pages ECG, correction, session builder)
- Ontologie JSON 280 concepts depuis OWL
- Infrastructure Docker complète

📚 Documentation:
- Guides techniques (ontologie, scoring, architecture)
- Roadmap complète

🔧 Configuration:
- Docker compose pour déploiement
- Nginx reverse proxy
- .gitignore optimisé (exclusion backups, data temp, BMAD notes)
"

# 4. Push
git push origin main
```

---

**Résumé:** Seulement ~50 fichiers essentiels au lieu de 400+ ! 🎉
