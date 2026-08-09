# 🛠️ Outillage Ontologie ECG

Ce dossier regroupe **tout l'outillage** (scripts Python + journal des
modifications) lié à l'ontologie ECG (`BrYOzRZIu7jQTwmfcGsi35.owl` /
`data/ontology_v2.json`), séparé du reste du dépôt pour ne garder à la
racine que les **fichiers ontologie eux-mêmes** (source de vérité) :

- `../BrYOzRZIu7jQTwmfcGsi35.owl` — source WebProtégé (à réimporter).
- `../BrYOzRZIu7jQTwmfcGsi35_patched_2026-08-09.owl` — dernier patch généré,
  **⚠️ pas encore réimporté et avec un écart connu** sur le voltage QRS
  (cf. `CHANGELOG_ONTOLOGIE.md` §8).
- `../data/ontology_v2.json` — **ontologie runtime canonique**, vérifiée
  conforme à l'état final du 2026-08-09 (revert fusion voltage + 20
  synonymes dédupliqués). Vérifiable via `scripts/verify_ontology_state.py`.

## Contenu

- `CHANGELOG_ONTOLOGIE.md` — journal complet de toutes les modifications
  apportées à l'ontologie (source de vérité historique, à tenir à jour).
- `scripts/` — tous les scripts de lecture/analyse/modification de
  l'ontologie :
  - **Conversion / régénération** : `convert_owl_to_v2.py`,
    `rebuild_ontology_from_owl.py`, `regenerate_ontology.py`.
  - **Audit / vérification** : `audit_ontology_full_2026_08_09.py`,
    `audit_ontology_redundancy.py`, `audit_golden.py`,
    `inspect_synonym_collisions_2026_08_09.py`,
    `verify_ontology_state.py` (nouveau — vérifie que le JSON reflète bien
    l'état documenté dans le changelog, ex. revert voltage + synonymes).
  - **Modifications ponctuelles (session 2026-08-09)** :
    `add_missing_concepts_relecture75.py`,
    `apply_relecture75_corrections.py`, `fix_remaining_unresolved.py`,
    `fix_ontology_redundancy_2026_08_09.py`,
    `fix_synonym_ambiguity_2026_08_09.py`,
    `fix_synonym_collisions_preexisting_2026_08_09.py`,
    `revert_voltage_merge_keep_owl_concept_2026_08_09.py`,
    `generate_owl_relecture75.py`,
    `apply_synonym_removals_to_owl_2026_08_09.py`.

> ⚠️ Ces scripts ont été **copiés** depuis `ecg-online/scripts/` (dépôt git
> séparé) — ils y restent aussi (ne pas les supprimer côté `ecg-online`,
> qui a son propre historique git). Ce dossier est une consolidation pour
> la maintenance de l'ontologie côté `edu-ecg` (racine), pas un
> remplacement.

## Vérifier l'état de l'ontologie

```powershell
python outil_ontologie/scripts/verify_ontology_state.py
```

Vérifie automatiquement (contre `data/ontology_v2.json`) :
1. Le revert de la fusion "voltage" (`VOLTAGE_DU_QRS_NORMAL` canonique,
   `VOLTAGE_NORMAL_DU_QRS` absent).
2. Les 20 suppressions/conservations de synonymes des catégories A/B/C
   (dédup des collisions pré-existantes, §8 du changelog).

## Point de vigilance en cours

Le `.owl` patché (`BrYOzRZIu7jQTwmfcGsi35_patched_2026-08-09.owl`) **ne
reflète pas encore** le revert de la fusion voltage ni les 20 retraits de
synonymes — seul le JSON (`data/ontology_v2.json`, 3 copies runtime) est à
jour. Ne pas réimporter ce `.owl` dans WebProtégé sans corriger cet écart
(cf. `CHANGELOG_ONTOLOGIE.md`, dernière section).

## Travaux à porter (non résolus, identifiés lors des sessions de fix golden)

### Comment gérer les qualificatifs du NER sans patcher à la volée (2026-08-09)

**Problème** : pour les troubles du rythme composés d'un diagnostic +
qualificatif (ex. "Flutter commun/typique", "ESV trigéminées/monomorphes"),
le NER (`ner_extractor.py`, règle LEGO §4) ne traite pas tous les cas de
façon homogène :
- **ESV/extrasystoles** : fonctionne bien — le prompt sépare explicitement
  diagnostic et qualificatif en 2 entités distinctes (`EXTRASYSTOLE_VENTRICULAIRE`
  + `MONOMORPHE`/`TRIGEMINISME_VENTRICULAIRE`/etc., qui existent comme
  concepts ontologiques séparés).
- **Flutter** : ne fonctionne PAS de façon fiable — GPT-4o tronque parfois
  `terme_brut` à `"flutter"` seul (perdant "commun"/"typique"/"droit"), qui
  se résout alors vers le concept générique `FLUTTER_ATRIAL` au lieu du
  spécifique `FLUTTER_DROIT_TYPIQUE` (dont "Flutter commun"/"Flutter typique"
  sont pourtant déjà des synonymes correctement étiquetés dans l'ontologie —
  ce n'est PAS un problème d'étiquetage, seulement de troncature côté NER).

**Filet de sécurité actuel (partiel)** : `_lexical_backstop_ids` dans
`candidate_report.py` rattrape après-coup un synonyme multi-mots distinctif
présent littéralement dans le texte mais raté par le NER — MAIS seulement
pour les concepts figurant dans `golden_ids` (donc actif en golden/test,
mais **pas en usage réel hors golden**, où la précision serait perdue).

**Solution générique proposée** (à implémenter, PAS en patch ad-hoc) : une
passe de « raffinement de spécificité » post-résolution NER, active pour
TOUS les concepts (pas seulement ceux du golden) : pour chaque concept
résolu par `resolve_term_to_ontology`, vérifier si le `contexte_phrase`
(texte source complet de l'entité, pas juste `terme_brut` tronqué) contient
littéralement un synonyme distinctif d'un **descendant** (enfant/petit-enfant
ontologique) du concept résolu ; si oui, **remplacer** (upgrade in-place,
pas dupliquer) l'ID résolu par ce descendant plus spécifique. Généralise le
mécanisme déjà existant du backstop lexical, sans dépendre du golden.

Points à trancher avant implémentation :
- Faut-il aussi adapter le prompt NER (règle LEGO) pour le cas "Flutter",
  en complément (traitement à la source) plutôt qu'en aval uniquement ?
- Le raffinement doit-il tourner sur `contexte_phrase` complet ou sur une
  fenêtre autour de l'entité (risque de faux rattachement si la phrase est
  longue et contient plusieurs diagnostics) ?
- Impact sur les temps de calcul (une recherche syn. par descendant, pour
  chaque concept résolu, à chaque appel) — envisager un index inverse
  synonyme→concept précalculé (réutiliser `_word_document_frequency` /
  `_is_synonym_specific_enough` déjà présents dans `candidate_report.py`).

