# 🧠 Pipeline RAG Neurosymbolique — Évaluation ECG

> Module de correction automatique d'interprétations ECG par pipeline RAG neurosymbolique.  
> **Repo** : [EPCASE/edu-ecg](https://github.com/EPCASE/edu-ecg) — Branche `RAGontologique`

---

## Vue d'ensemble

Le pipeline transforme le **texte libre d'un étudiant** en médecine en une **note structurée avec feedback pédagogique**, en 6 briques enchaînées :

```
Texte étudiant → NER → Recherche Hybride → Juge Neurosymbolique → Scoring → Rapport + Feedback
```

**Score moyen sur 15 cas × 7 étudiants : ~92%** | Latence : ~3-5s/cas

---

## 🧱 Les 6 briques

| # | Brique | Fichier | Méthode |
|---|--------|---------|---------|
| 1 | **Socle ontologique** | `ontology_index.py` | OWL → embeddings + BM25 (411 docs, 180 concepts) |
| 2 | **Extraction NER** | `ner_extractor.py` | GPT-4o + Structured Outputs (Pydantic) |
| 3 | **Recherche hybride** | `hybrid_search.py` | Dense (cosinus) + BM25 + RRF fusion |
| 4 | **Juge neurosymbolique** | `neurosymbolic_judge.py` | Coupe-circuit (~60%) + GPT-4o-mini (~30%) |
| 5 | **Scoring ensembliste** | `scoring.py` | Dégressif par génération ontologique (90/80/70/60%) |
| 6 | **Rapport + Feedback** | `candidate_report.py` | Orchestration + feedback GPT basé cours SFC |

### Fichiers complémentaires (Brique 6)

| Fichier | Rôle |
|---------|------|
| `pedagogical_feedback.py` | Génération du commentaire pédagogique GPT-4o-mini |
| `edn_knowledge_base.py` | 30+ entrées du cours SFC Item 231 (rangs A/B/C) |

### Scripts d'export

| Fichier | Rôle |
|---------|------|
| `generate_html_report.py` | Rapport HTML standalone avec images base64 |
| `export_corrections_json.py` | Export JSON pour la page Streamlit Corrections |

---

## 📂 Structure

```
rag_pipeline/
├── ontology_index.py          # Brique 1 — Indexation ontologie
├── ner_extractor.py           # Brique 2 — NER GPT-4o
├── hybrid_search.py           # Brique 3 — Recherche Dense + BM25 + RRF
├── neurosymbolic_judge.py     # Brique 4 — Coupe-circuit + Juge LLM
├── scoring.py                 # Brique 5 — Scoring dégressif
├── candidate_report.py        # Brique 6 — Orchestrateur + rapport
├── pedagogical_feedback.py    # Brique 6 — Feedback GPT + cours SFC
├── edn_knowledge_base.py      # Brique 6 — Knowledge base Item 231
├── generate_html_report.py    # Export HTML (rapport complet)
├── export_corrections_json.py # Export JSON (pour Streamlit)
├── ARCHITECTURE_PIPELINE.md   # Doc architecture détaillée (Mermaid)
├── rag_index/                 # Index vectoriels pré-calculés
│   ├── vecteurs_ontologie.npy
│   ├── metadata_ontologie.json
│   └── bm25_corpus.json
└── tests/
    ├── test_scoring_quick.py
    ├── benchmark_evaluation.ipynb
    └── visualisation_espace_latent.ipynb
```

---

## 🚀 Usage rapide

### Corriger un texte étudiant (Python)

```python
from candidate_report import generate_candidate_report

report = generate_candidate_report(
    student_text="fibrillation atriale qrs fins tachycardie",
    golden_names=["Fibrillation atriale"],
    golden_ids=["FIBRILLATION_ATRIALE"],
    golden_roles=["validant"],
    with_feedback=True,
)

print(f"Score : {report.score_final_pct:.0f}%")
print(report.feedback_pedagogique.texte)
```

### Exporter les corrections pour Streamlit

```bash
python export_corrections_json.py                      # 7 étudiants, avec feedback
python export_corrections_json.py --no-feedback        # Sans feedback GPT (plus rapide)
python export_corrections_json.py --students ECG-WY55  # Un seul étudiant
```

---

## 🔗 Dépendances externes

| Ressource | Localisation | Usage |
|-----------|-------------|-------|
| `.env` (clé OpenAI) | `ECG lecture/.env` | API GPT-4o, GPT-4o-mini, embeddings |
| `ontology_from_owl.json` | `ECG lecture/data/` | Ontologie ECG (180 concepts) |
| `goldenset/` | `ECG evaluation/goldenset/` | 15 cas annotés par expert |
| CSV étudiants | `ECG evaluation/` | Réponses des 7 étudiants |
| Images ECG | `ECG collector/images/` | 15 PNG pour le rapport HTML |

---

## 🏗️ Stratégie d'interaction Ontologie ↔ LLMs

### Principe fondamental : séparation des responsabilités

```
┌──────────────────────────────────────────────────────────────┐
│              ONTOLOGIE (symbolique)                           │
│  • Source de vérité : 180 concepts, poids, catégories        │
│  • Index vectoriel : 411 documents (embeddings 1536-dim)     │
│  • Normalisation de texte : matching exact sans ambiguïté    │
└───────────────────────┬──────────────────────────────────────┘
                        │ Candidats Top-K + métadonnées
┌───────────────────────▼──────────────────────────────────────┐
│                 LLMs (neuronal)                               │
│  • Brique 2 (GPT-4o) : extraction NER brute                 │
│  • Brique 4 (GPT-4o-mini) : QCM contraint sur Top-K         │
│  • Brique 6 (GPT-4o-mini) : feedback pédagogique            │
│  Le LLM ne voit JAMAIS l'ontologie complète.                 │
│  Il ne peut PAS inventer un ID — validation post-LLM.        │
└──────────────────────────────────────────────────────────────┘
```

### Garde-fous

| Garde-fou | Couche | Mécanisme |
|---|---|---|
| Structured Outputs | Brique 2 & 4 | Schéma Pydantic garanti par l'API OpenAI |
| Validation post-LLM | Brique 4 | L'ID renvoyé doit être dans les candidats soumis |
| Coupe-circuit spécificité | Brique 4 | Annule le bypass si concept plus spécifique existe |
| Scoring dégressif | Brique 5 | Pénalisation progressive par génération ontologique |
| Forçage NONE | Brique 4 | Si ID invalide → NONE plutôt qu'un faux positif |

---

## 📖 Documentation détaillée

→ **[ARCHITECTURE_PIPELINE.md](ARCHITECTURE_PIPELINE.md)** — Architecture complète avec 15 diagrammes Mermaid (flowcharts, sequence diagrams, pie charts).

---

## Stack technique

- Python 3.14 | OpenAI GPT-4o + GPT-4o-mini | text-embedding-3-small
- NumPy · Pydantic · BM25Okapi · python-dotenv · pandas · tqdm
- Ontologie OWL ECG (~180 concepts, 4 catégories pondérées)
- Cours SFC Item 231 — Référentiel CNEC 2e édition (30+ entrées EDN)
