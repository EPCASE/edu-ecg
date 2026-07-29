# 🔮 Futur projet — Fusion / enrichissement de l'ontologie ECG

> Créé le 2026-07-29 lors du nettoyage de repo (cf. `AUDIT_ARCHITECTURE_2026.md`).
> Ce dossier **regroupe des éléments mis de côté du repo actif** car ils ne sont
> **utilisés par aucun code de production actuel**, mais sont conservés
> intentionnellement pour un **futur projet de fusion/enrichissement de
> l'ontologie ECG** avec d'autres référentiels externes.
>
> ⚠️ Rien ici n'est chargé par `ecg-online/` ni par le pipeline en production.

## Contenu

### `frontend/pages/correction_llm.py`
Fichier **vide** (0 octet) — ébauche jamais commencée d'une page Streamlit de
correction (mentionnée dans `ARCHITECTURE.md` mais jamais implémentée). Conservé
comme placeholder si ce projet de page dédiée est repris.

### `data/onto_audit/` (75 fichiers `01.json` → `75.json`)
Sorties d'un script d'audit LLM (`audit_ontology_llm.py`, référencé dans
`ARCHITECTURE.md` §16 mais absent du repo actuel) qui relisait chaque cas des
75 tracés ECG face au catalogue de concepts et proposait des enrichissements
ontologiques ancrés (par cas).

### `data/onto_audit_raw.json`
Sortie brute/consolidée correspondante (avant agrégation par
`aggregate_onto_audit.py`, lui aussi absent du repo actuel).

### `data/onto_review/` (233 fichiers, un par concept)
Fiches de relecture individuelle par concept ontologique (nom du fichier =
`concept_id.json`) — probablement générées pour une revue manuelle concept par
concept en vue d'un audit de couverture plus large.

### `data/ontologielille/`
Référentiel ontologique ECG externe ("Lille") :
- `grille(1).txt` — hiérarchie de tags ECG (FR/EN), format arborescent indenté
  avec codes numériques (ex: `0156 | Anomalie de la qualité du tracé | Trace
  quality anomaly`).
- `ecg_tag_translation(1).csv` — même référentiel en CSV structuré
  (`etag_id, etagt_id, etagt_language, etagt_text, etag_parent_id, etag_weight,
  etag_type`).

Ce référentiel est **totalement indépendant** de l'ontologie `ontology_v2.json`
actuelle (aucun recouvrement d'ID, nomenclature différente) — probablement
récupéré pour comparaison/enrichissement croisé futur (couverture de concepts,
granularité, structure hiérarchique alternative).

## Pourquoi regroupés ici plutôt que supprimés

Ces éléments documentent un travail exploratoire (audit LLM du catalogue,
référentiel externe Lille) lié à un **projet futur de fusion/enrichissement
de l'ontologie**, distinct du pipeline de production actuel. Ils ont été
déplacés hors de `data/` et `frontend/` (racine du repo actif) pour :
1. Ne plus polluer l'inventaire du repo de production (`ecg-online/`).
2. Rester facilement récupérables et regroupés en un seul endroit le jour où
   ce projet de fusion est repris.

## Statut

⬜ Projet non démarré / en attente. Aucune action requise tant que ce chantier
n'est pas explicitement lancé.
