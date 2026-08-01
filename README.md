# 🧠 Pipeline RAG Neurosymbolique — Évaluation ECG

> Module de correction automatique d'interprétations ECG par pipeline RAG neurosymbolique.  
> **Repo** : [EPCASE/edu-ecg](https://github.com/EPCASE/edu-ecg) — Branche `RAGontologique`

> 📋 Voir **[`AUDITS.md`](./AUDITS.md)** pour l'index des documents d'audit (robustesse scientifique, architecture/repo, choix technologiques) et runbooks.

---

## Vue d'ensemble

Le pipeline transforme le **texte libre d'un étudiant** en médecine en une **note structurée avec feedback pédagogique**, en 6 briques enchaînées :

```
Texte étudiant → NER → Recherche Hybride → Juge Neurosymbolique → Scoring → Rapport + Feedback
```

**Score moyen sur 15 cas × 7 étudiants : ~92%** (chiffre historique, non daté/non
recalculé récemment — score pédagogique moyen, distinct du F1 d'extraction ci-après)
| Latence : ~3-5s/cas

> 📊 **Métriques à jour** : voir [`audit_doc/METRICS_LEDGER.md`](audit_doc/METRICS_LEDGER.md)
> (source de vérité unique, P0.3) — notamment extraction P=90.4%/R=89.2%/F1=89.8%
> mesurée sur 100 réponses réelles annotées (`ecg-online/GOLDEN_EXTRACTION.md`).

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

## 📂 Structure (mise à jour 2026-07-29)

> ⚠️ Le pipeline ne vit **plus** dans un dossier `rag_pipeline/` à la racine de
> `ECG lecture/`. Après l'audit d'hygiène de repo (`AUDIT_ARCHITECTURE_2026.md`),
> **la seule copie du pipeline** est désormais vendorée dans l'app déployée
> `ecg-online/` — c'est la source de vérité unique.

```
ECG lecture/
├── ecg-online/                        # ★ App Flask déployée (source de vérité) ★
│   ├── app/                           # server.py, neuro_grader.py, golden_config.py...
│   ├── rag_pipeline/                  # ★ LE pipeline (6 briques + index + ontologie) ★
│   │   ├── ontology_index.py          # Brique 0/1 — Indexation ontologie
│   │   ├── ner_extractor.py           # Brique 2 — NER GPT-4o
│   │   ├── hybrid_search.py           # Brique 3 — Recherche Dense + BM25 + RRF
│   │   ├── neurosymbolic_judge.py     # Brique 4 — Coupe-circuit + Juge LLM
│   │   ├── scoring_v3.py              # Brique 5 — Scoring ontologique
│   │   ├── candidate_report.py        # Brique 6 — Orchestrateur + rapport
│   │   ├── pedagogical_feedback.py    # Brique 6 — Feedback GPT + cours SFC
│   │   ├── edn_knowledge_base.py      # Brique 6 — Knowledge base Item 231
│   │   ├── scoring_thresholds.py      # Seuils versionnés (magic numbers externalisés)
│   │   ├── ARCHITECTURE_PIPELINE.md   # Doc architecture détaillée (Mermaid)
│   │   ├── rag_index/                 # Index vectoriels pré-calculés (.npy + BM25)
│   │   └── tests/test_scoring_v3.py   # 18 tests de non-régression
│   ├── scripts/                       # extract_cases.py, build_ecg_gallery.py, export_corrections_json.py...
│   ├── frontend/                      # HTML/CSS/JS de l'app
│   └── data/                          # cases.json, ontology_v2.json (copie runtime)
│
├── backend/rdf_owl_extractor.py       # Parseur RDF/XML de l'OWL (source WebProtégé)
├── data/ontology_v2.json              # Ontologie runtime (345 concepts) — source amont
├── convert_owl_to_v2.py               # Convertisseur OWL → JSON V2
├── rebuild_ontology_from_owl.py       # Régénère ontology_v2.json en préservant l'enrichissement
├── _futur_fusion_ontologie/           # Éléments mis de côté (audit LLM, réf. externe Lille) — cf. son README
└── ARCHITECTURE.md                    # Documentation complète (Parties A→E)
```

Voir **[ARCHITECTURE.md](ARCHITECTURE.md)** pour le détail complet de chaque brique,
les métriques mesurées, l'audit de robustesse et la stratégie ontologie ↔ LLMs.

---

## 🚀 Usage rapide

### Corriger un texte étudiant (Python)

```python
import sys
sys.path.insert(0, "ecg-online/rag_pipeline")
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
cd ecg-online/scripts
python export_corrections_json.py                      # Avec feedback
python export_corrections_json.py --no-feedback        # Sans feedback GPT (plus rapide)
python export_corrections_json.py --students ECG-WY55  # Un seul étudiant
```

---

## 🔗 Dépendances externes

| Ressource | Localisation | Usage |
|-----------|-------------|-------|
| `.env` (clé OpenAI) | `ECG lecture/.env` ou `ecg-online/.env` | API GPT-4o, GPT-4o-mini, embeddings |
| `ontology_v2.json` | `ecg-online/rag_pipeline/data/` | Ontologie ECG runtime (345 concepts) — copie vendorée de `ECG lecture/data/ontology_v2.json` |
| `goldenset/` | `ECG evaluation/goldenset/` | 15 cas annotés par expert |
| CSV étudiants | `ECG evaluation/` | Réponses des étudiants |
| Images ECG | `ECG collector/images/` | PNG pour les rapports HTML |

---

## 🏗️ Stratégie d'interaction Ontologie ↔ LLMs

### Principe fondamental : séparation des responsabilités

```
┌──────────────────────────────────────────────────────────────┐
│              ONTOLOGIE (symbolique)                           │
│  • Source de vérité : 345 concepts, poids, catégories        │
│  • Index vectoriel : 658 documents (embeddings 1536-dim)     │
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
| Scoring V3 ontologique | Brique 5 | Poids/relations (requires/excludes/supports) plutôt qu'un simple match binaire |
| Forçage NONE | Brique 4 | Si ID invalide → NONE plutôt qu'un faux positif |

---

## 📖 Documentation détaillée

→ **[ARCHITECTURE.md](ARCHITECTURE.md)** — Documentation centralisée (Parties A→E) :
architecture, ontologie, app `ecg-online`, audit de robustesse, réannotation OWL.
→ **[ecg-online/rag_pipeline/ARCHITECTURE_PIPELINE.md](ecg-online/rag_pipeline/ARCHITECTURE_PIPELINE.md)** — Diagrammes Mermaid détaillés du pipeline.
→ **[AUDIT.md](AUDIT.md)** — Audit de robustesse scientifique (scoring/extraction).
→ **[AUDIT_ARCHITECTURE_2026.md](AUDIT_ARCHITECTURE_2026.md)** — Audit d'hygiène de repo (2026-07-29).

---

## Stack technique

- Python 3.14 | OpenAI GPT-4o + GPT-4o-mini | text-embedding-3-small
- NumPy · Pydantic · BM25Okapi · python-dotenv · pandas · tqdm
- Ontologie OWL ECG (345 concepts, 4 catégories pondérées)
- Cours SFC Item 231 — Référentiel CNEC 2e édition (30+ entrées EDN)
