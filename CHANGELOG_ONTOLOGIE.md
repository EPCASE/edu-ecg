# Changelog Ontologie — ECG lecture

> Fichier de suivi de toutes les modifications apportées à l'ontologie
> (`BrYOzRZIu7jQTwmfcGsi35.owl` + `data/ontology_v2.json` + ses copies runtime).
> Chaque entrée doit permettre de rejouer/tracer une modification et de
> savoir si elle a été réimportée dans WebProtégé Stanford.

---

## 2026-08-09 — Relecture complète des 75 cas pilotes (P1.3)

**Contexte** : relecture manuelle exhaustive des 75 cas du golden `scoring_pilot_v2.json`
par l'expert (fichier de notes `_tempreponserelecture75.md`), suivie d'un audit complet
de cohérence de l'ontologie (structure + synonymes).

### 1. Nouveaux concepts créés (10)

| concept_id | Label FR | Parent | Poids | Type | Cas d'origine |
|---|---|---|---|---|---|
| `TACHYCARDIE_VENTRICULAIRE_NON_SOUTENUE` | Tachycardie ventriculaire non soutenue | `TACHYCARDIE_VENTRICULAIRE` | 4 | pattern | — |
| `TACHYCARDIE_VENTRICULAIRE_SOUTENUE` | Tachycardie ventriculaire soutenue | `TACHYCARDIE_VENTRICULAIRE` | 5 | pattern | — |
| `ANGOR_DE_PRINZMETAL` | Angor de Prinzmetal | `ANOMALIES_DU_SEGMENT_ST` | 5 | pattern | cas 70 |
| `EXTENSION_VENTRICULE_DROIT` | Extension au ventricule droit | `VENTRICULE_DROIT` | 3 | finding | cas 60 |
| `MALADIE_RYTHMIQUE_OREILLETTE` | Maladie rythmique de l'oreillette | `DYSFONCTION_SINUSALE` | 4 | pattern | cas 31 |
| `S1Q3` | Aspect S1Q3 (McGinn-White) | `ANOMALIES_DU_SEGMENT_ST` | 3 | pattern | cas 53, 54 |
| `ONDE_P_RETROGRADE` | Onde P rétrograde | `ONDE_P` | 2 | finding | cas 44, 60 |
| `BLOC_DE_BRANCHE_ALTERNANT` | Bloc de branche alternant | `BLOC_DE_BRANCHE` | 4 | pattern | cas 14 |
| `FLUTTER_ATRIAL` | Flutter atrial (générique) | `TACHYCARDIE_ATRIALE` | 4 | pattern | cas 65 |
| `SYNCOPE` | Syncope (contexte clinique) | — (top-level) | — | context | cas 11 |

Script : `ecg-online/scripts/add_missing_concepts_relecture75.py` (idempotent, écrit
les 3 copies runtime de `ontology_v2.json`).

### 2. Corrections de données appliquées (cases + ontologie)

- **~16 corrections explicites** du fichier de relecture `_tempreponserelecture75.md` :
  suppressions de critères erronés (cas 8, 29, 42, 43, 51, 55, 56, 63, 68), corrections
  de `concept_id` (cas 59, 70), mise à jour du contexte clinique (cas 57).
  Script : `ecg-online/scripts/apply_relecture75_corrections.py`.
- **17 corrections supplémentaires** trouvées par audit croisé complet (concept_id
  invalides/typos, labels vides) sur les cas 11, 14, 44, 47, 49, 53, 54, 55, 60, 65, 73.
  Script : `ecg-online/scripts/fix_remaining_unresolved.py`.

### 3. Corrections de redondance structurelle (post-création des 10 concepts)

- `FLUTTER_ATRIAL` : suppression de `children`/`requires` (double hiérarchie avec ses
  sous-types déjà rattachés à `TACHYCARDIE_ATRIALE` / `FLUTTER_DROIT_TYPIQUE`).
- `BLOC_DE_BRANCHE_ALTERNANT` : suppression de `requires=[BLOC_DE_BRANCHE]`, redondant
  avec son propre `parent`.

Script : `ecg-online/scripts/fix_ontology_redundancy_2026_08_09.py`.

### 4. Corrections de synonymes ambigus (introduits par les nouveaux concepts)

- `TACHYCARDIE_VENTRICULAIRE` (parent) : retrait de `TVNS`, `tachycardie ventriculaire
  soutenue`, `TV soutenue` — désormais exclusifs de ses enfants `_NON_SOUTENUE`/`_SOUTENUE`.
- `EXTENSION_VENTRICULE_DROIT` : retrait de `infarctus inférieur avec extension au
  ventricule droit` (conservé uniquement sur `SYNDROME_CORONARIEN_A_LA_PHASE_AIGUE_
  AVEC_SUS_DECALAGE_DU_SEGMENT_ST`, qui décrit le tableau clinique complet).
- `FLUTTER_DROIT_TYPIQUE` / `TACHYCARDIE_ATRIALE` : retrait du synonyme littéral
  `flutter atrial` (désormais porté exclusivement par le nouveau concept générique
  `FLUTTER_ATRIAL`).

Script : `ecg-online/scripts/fix_synonym_ambiguity_2026_08_09.py`.

### 5. Reproduction dans le `.owl` (pour réimport WebProtégé Stanford)

- Les 10 concepts créés en JSON ont été **reproduits dans le `.owl`** (mint de nouveaux
  IRIs WebProtégé, hiérarchie `subClassOf`, restrictions `requires`/`supports`/
  `has_qualifiers`/`excludes`/`origin_structure`/`weight`, labels FR/EN, synonymes
  `skos:altLabel` — version finale post-dédup §4).
- Fichier produit : **`BrYOzRZIu7jQTwmfcGsi35_patched_2026-08-09.owl`**
  (415 classes, XML validé, 0 doublon d'IRI — cf. `_validate_patched_owl.py`).
- `data/id_to_iri.json` mis à jour avec les 10 nouveaux mappings `concept_id -> IRI`.
- Script : `ecg-online/scripts/generate_owl_relecture75.py`.

> ⚠️ **Action utilisateur requise** : importer
> `BrYOzRZIu7jQTwmfcGsi35_patched_2026-08-09.owl` dans le projet WebProtégé Stanford
> (`BrYOzRZIu7jQTwmfcGsi35`), en écrasant/fusionnant avec la version courante, pour que
> les 10 nouveaux concepts existent aussi côté WebProtégé et restent l'IRI de référence
> pour toute future réannotation (cf. `RUNBOOK_REBUILD_ONTOLOGIE.md`).

### 6. Bilan de validation ontologie (2026-08-09)

- 359 → **369 concepts** (+10), 0 pointeur `parent`/`children` cassé.
- 74/75 cas ont un `expert_1` complet ; cas **62 encore en attente** de relecture manuelle.
- Tous les `concept_id` des 75 cas résolvent contre l'ontologie (`bad=[]`).
- **Dette pré-existante identifiée, non corrigée aujourd'hui** (hors périmètre) :
  - 8 incohérences bidirectionnelles parent↔children (`STIMULATION` ×7, `VOLTAGE_DU_QRS` ×1).
  - 21 collisions de synonymes pré-existantes sans lien avec les concepts créés
    aujourd'hui (ex. `bav`, `at`/`ta`, `brs`, `ers`, `rija`, `onde de Pardee`, etc.).

---

## Format des entrées futures

```
## AAAA-MM-JJ — <titre court>

**Contexte** : ...

### Concepts créés / modifiés
| concept_id | changement | script |

### Réimport WebProtégé
- [ ] fait le ...
```
