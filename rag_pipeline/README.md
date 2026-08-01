# 🧠 `edu-ecg-engine` — Moteur neurosymbolique ECG (6 briques)

> Package Python du moteur de correction ECG. **Source canonique unique** —
> `ecg-online` doit consommer ce package via une dépendance versionnée
> (`pip install`), pas via une copie manuelle du code. Cf.
> `audit_doc/roadmap_scientifique_2026.md` et la discussion d'architecture du
> 2026-08-01 (séparation moteur / application).

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

⚠️ **Étape intermédiaire.** Les modules s'importent aujourd'hui **à plat**
(`from ner_extractor import ...`), pas via des imports relatifs de package
(`from rag_pipeline.ner_extractor import ...`). C'est un héritage du mode
"vendoré" utilisé jusqu'ici dans `ecg-online/rag_pipeline/`.

Le `pyproject.toml` à la racine packagie ce dossier tel quel (imports à plat
préservés) pour permettre une installation `pip install` immédiate **sans**
réécrire tous les imports internes — trop risqué à faire d'un coup sur un
moteur en production. Une vraie migration vers des imports relatifs propres
(`from .ner_extractor import ...`) est un chantier ultérieur, optionnel.

## Installation depuis `ecg-online`

```bash
pip install "git+https://github.com/EPCASE/edu-ecg.git@<tag>#egg=edu-ecg-engine"
```

Où `<tag>` est un tag Git versionné de ce dépôt (ex. `engine-v1.1.0`), **jamais**
une branche mouvante — pour garantir la traçabilité (cf. P0.1, `pipeline_version`).

## Données vendorées

`data/ontology_v2.json` et `rag_index/*` (index BM25 + embeddings pré-calculés,
~10 Mo) sont packagés avec le module (`package-data`). Ce sont des **artefacts
versionnés au même titre que le code** : toute régénération de l'ontologie ou
réindexation doit donner lieu à un nouveau tag.

## Prochaine étape (non faite à cette date)

Remplacer `ecg-online/rag_pipeline/` (copie vendorée) par une dépendance
`pip install` de ce package, dans `ecg-online/requirements.txt`, en épinglant
un tag précis. Cf. `ecg-online/app/neuro_grader.py` (`_PIPELINE_DIR` +
`sys.path.insert`) qui devra être adapté pour importer le package installé
au lieu du dossier local.
