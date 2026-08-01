# 🧠 `edu-ecg-engine` — Moteur neurosymbolique ECG (6 briques)

> Package Python du moteur de correction ECG. **Source canonique de
> développement** (`edu-ecg` `main`) — `ecg-online` en garde une **copie
> vendorée figée**, mise à jour ponctuellement et manuellement à l'occasion
> d'un changement de version décidé (pas de dépendance `pip install` live).
> Cf. `audit_doc/roadmap_scientifique_2026.md` et la discussion d'architecture
> du 2026-08-01 (séparation moteur / application — convention retenue :
> vendoring versionné, pas de dépendance runtime).

## Les 6 briques

| # | Brique | Fichier |
|---|--------|---------|
| 0/1 | Socle ontologique (index vectoriel + BM25) | `ontology_index.py` |
| 2 | Extraction NER | `ner_extractor.py` |
| 3 | Recherche hybride (dense + BM25 + RRF) | `hybrid_search.py` |
| 4 | Juge neurosymbolique (coupe-circuit + LLM) | `neurosymbolic_judge.py` |
| 5 | Scoring ontologique V3 | `scoring_v3.py` |
| 6 | Rapport + feedback pédagogique | `candidate_report.py`, `pedagogical_feedback.py` |

Modules complémentaires : `semantic_layer.py`, `pattern_inference.py`,
`edn_knowledge_base.py`, `scoring_thresholds.py`.

## Statut du packaging (2026-08-01)

⚠️ Les modules s'importent aujourd'hui **à plat** (`from ner_extractor import
...`), pas via des imports relatifs de package (`from rag_pipeline.ner_extractor
import ...`). C'est un héritage du mode "vendoré" utilisé dans
`ecg-online/rag_pipeline/`, **conservé tel quel** — cf. convention ci-dessous.

Le `pyproject.toml` à la racine packagie ce dossier pour permettre de
l'installer/tester en isolation (venv de dev, CI), mais **ce n'est pas ainsi
que `ecg-online` le consomme en production** (cf. section suivante).

## Convention retenue : vendoring versionné, pas de dépendance runtime

`ecg-online/rag_pipeline/` est une **copie figée et autonome** du moteur, pas
un `pip install` de ce package. Décision du 2026-08-01 :

- **`edu-ecg` (ce dépôt)** = lieu de développement du moteur. Toute évolution
  (nouvelle règle de scoring, NER amélioré, etc.) se fait ici, sur une
  branche, mergée dans `main`, puis **taguée** (`engine-vX.Y.Z`) une fois
  stabilisée et testée.
- **`ecg-online/rag_pipeline/`** reste une copie manuelle, jamais modifiée
  directement pour du développement. Elle n'est mise à jour qu'à l'occasion
  d'une décision explicite de faire monter de version le moteur en
  production — jamais automatiquement, jamais via un `pip install` au
  déploiement (pas de dépendance réseau/build fragile sur Scalingo).
- Chaque mise à jour de la copie vendorée est un **événement traçable** :
  1. Copier le contenu du tag `edu-ecg` choisi vers `ecg-online/rag_pipeline/`.
  2. Relancer la suite de tests (`python -m unittest discover -s tests`) +
     `scripts/audit_golden.py` dans `ecg-online`.
  3. Committer avec un message explicite (`chore(engine): upgrade vendored
     rag_pipeline → engine-v1.2.0`).
  4. Mettre à jour `PIPELINE_VERSION` dans `app/neuro_grader.py` si le
     comportement du scoring/NER a changé (traçabilité `pipeline_version`
     déjà exposée dans `/api/grade`/`/api/health`, cf. P0.1).

**Pourquoi pas un `pip install` direct** : ça introduirait une dépendance
réseau/build au moment du déploiement Scalingo (clone Git, build du package)
sur une app en production utilisée par de vrais étudiants — un échec de build
casserait le déploiement. Le vendoring manuel garde `ecg-online` **totalement
autonome et stable**, au prix d'une synchronisation manuelle mais volontaire.

## Données vendorées

`data/ontology_v2.json` et `rag_index/*` (index BM25 + embeddings pré-calculés,
~10 Mo) sont packagés avec le module (`package-data`), pour permettre les tests
d'installation isolée. Ce sont des **artefacts versionnés au même titre que le
code** : toute régénération de l'ontologie ou réindexation doit donner lieu à
un nouveau tag.


## Historique des versions taguées

| Tag | Date | Contenu | Vendoré dans `ecg-online` ? |
|---|---|---|---|
| `engine-v1.1.0` | 2026-08-01 | Rapatriement initial (état identique à la copie vendorée du 2026-08-01) | ✅ Oui — c'est l'état déjà en place |
