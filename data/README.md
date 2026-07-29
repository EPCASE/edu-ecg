# 📂 `data/` — rôle des fichiers d'ontologie

> Documenté le 2026-07-29 (audit d'hygiène de repo, `AUDIT_ARCHITECTURE_2026.md`).

## `ontology_v2.json` — ✅ Source de vérité amont (RUNTIME)

L'ontologie ECG actuelle (345 concepts, relations `requires`/`excludes`/`supports`/
`has_qualifiers`, synonymes). C'est la version consommée par le pipeline — sa
copie vendorée dans `ecg-online/rag_pipeline/data/ontology_v2.json` est celle
réellement exécutée en production (les deux sont synchronisées manuellement via
`rebuild_ontology_from_owl.py`).

## `ontology_from_owl.json` — 🟡 Conservé (V1, historique), rôle documenté

Export **V1** de l'ontologie (289 concepts), antérieur à `ontology_v2.json`.
**Conservé intentionnellement** malgré son obsolescence apparente car il est
encore lu par :
- `regenerate_ontology.py` (sortie par défaut du script) ;
- des notebooks archivés dans `ECG evaluation/archive/*_OLD.ipynb` (comparaisons
  historiques V1 vs V2) et `ECG evaluation/04_Comparison_Ontology.ipynb` (actif) ;
- `backend/rdf_owl_extractor.py` (génère ce format depuis l'OWL source).

**Ne pas supprimer** sans vérifier `04_Comparison_Ontology.ipynb` au préalable —
il sert de point de comparaison pour mesurer l'évolution V1→V2 de l'ontologie.

Le fichier `.json.backup` associé (copie identique) a été supprimé le
2026-07-29 (redondant, aucune référence trouvée).

## `id_to_iri.json` — Mapping technique régénérable

Mapping `concept_id → IRI OWL`, généré par le patch OWL (`ARCHITECTURE.md` §14.2).
Sortie intermédiaire du pipeline de patch, régénérable via `patch_ontology_owl.py`
— pas une source de vérité, mais conservé car peu volumineux et utile pour
diagnostiquer un mapping ID↔IRI sans relancer tout le patch.
