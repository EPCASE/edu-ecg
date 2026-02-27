# 🫀 Edu-ECG — Pipeline RAG Neurosymbolique pour l'évaluation ECG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Benchmark](https://img.shields.io/badge/Benchmark-62.4%25-orange.svg)](#)

**📋 Branche** : `RAGontologique` | **👨‍💻 Auteur** : Grégoire Massoullié | **🏛️ Institution** : EPCASE

---

## � Vue d'ensemble

Ce dépôt contient le **pipeline RAG neurosymbolique 5 briques** pour l'évaluation
automatique de réponses étudiantes en lecture d'ECG, adossé à une ontologie OWL
de 289 concepts ECG.

### Architecture en 5 briques

| Brique | Module | Description |
|--------|--------|-------------|
| � 1 | `ontology_index.py` | Index vectoriel dense + BM25 depuis l'ontologie OWL |
| 🧱 2 | `ner_extractor.py` | NER clinique via GPT-4o (entités + statuts + diagnostics) |
| 🧱 3 | `hybrid_search.py` | Recherche hybride Dense + BM25 + Reciprocal Rank Fusion |
| 🧱 4 | `neurosymbolic_judge.py` | Juge neurosymbolique — coupe-circuit + GPT-4o-mini QCM |
| 🧱 5 | `scoring.py` | Scoring pondéré avec implications et bonus diagnostique |

### 🎨 **Visualiseur ECG Avancé**
- **Zoom fluide** : molette souris + slider (0.25x - 5x)
- **Navigation pan** : clic-glisser pour explorer l'ECG
### Benchmark v2 — 62.4% (médiane 86.2%)

| Métrique | Valeur |
|----------|--------|
| Score moyen | **62.4%** |
| Score médian | **86.2%** |
| Cas > 80% | 30/73 |
| Cas à 0% | 18/73 (frontière score brut 0 → pas de bonus) |

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner et passer sur la branche RAG
git clone https://github.com/EPCASE/edu-ecg.git
cd edu-ecg
git checkout RAGontologique

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la clé OpenAI
export OPENAI_API_KEY="sk-..."

# 4. Tester le scoring
cd rag_pipeline
python scoring.py
```

---

## 📁 Structure du projet

```
├── rag_pipeline/                  # Pipeline RAG 5 briques
│   ├── ontology_index.py         # 🧱 1 — Index vectoriel + BM25
│   ├── ner_extractor.py          # 🧱 2 — NER clinique GPT-4o
│   ├── hybrid_search.py          # 🧱 3 — Recherche hybride RRF
│   ├── neurosymbolic_judge.py    # 🧱 4 — Juge neurosymbolique
│   ├── scoring.py                # 🧱 5 — Scoring pondéré
│   ├── test_brique1.py           # Tests unitaires
│   ├── test_brique2.py
│   ├── test_brique3.py
│   ├── test_brique4.py
│   ├── rag_index/                # Index pré-calculé
│   │   ├── metadata_ontologie.json
│   │   └── bm25_corpus.json
│   └── README.md                 # Architecture détaillée
├── data/
│   └── ontology_from_owl.json    # Ontologie OWL → JSON (289 concepts)
├── backend/
│   ├── __init__.py
│   └── rdf_owl_extractor.py      # Extracteur OWL → JSON
├── regenerate_ontology.py         # Script de regénération ontologie
├── requirements.txt               # Dépendances Python
├── LICENSE
└── README.md                      # Ce fichier
```

---

## 📖 Documentation détaillée

Voir [`rag_pipeline/README.md`](rag_pipeline/README.md) pour l'architecture complète,
la stratégie de scoring et les pistes d'amélioration.

<div align="center">
🫀 Edu-ECG RAG Pipeline — Évaluation neurosymbolique des compétences ECG

Développé avec ❤️ pour l'éducation médicale
</div>