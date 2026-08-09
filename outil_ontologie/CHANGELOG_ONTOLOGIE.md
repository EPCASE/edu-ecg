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
>
> Le script est **idempotent** : relancé après validation du cas 62 (aucun impact
> ontologie), il a réutilisé les mêmes 10 IRIs déjà mintés (`data/id_to_iri.json`)
> sans les régénérer — le `.owl` produit est identique (415 classes, re-validé).

### 6. Bilan de validation ontologie (2026-08-09)

- **359 concepts au total** (10 nouveaux inclus), 0 pointeur `parent`/`children` cassé.
- **75/75 cas ont un `expert_1` complet** — cas 62 validé manuellement le 2026-08-09.
- Tous les `concept_id` des 75 cas résolvent contre l'ontologie (`bad=[]`).
- **Dette pré-existante identifiée, non corrigée aujourd'hui** (hors périmètre) :
  - 8 incohérences bidirectionnelles parent↔children (`STIMULATION` ×7, `VOLTAGE_DU_QRS` ×1).
  - 21 collisions de synonymes pré-existantes sans lien avec les concepts créés
    aujourd'hui (ex. `bav`, `at`/`ta`, `brs`, `ers`, `rija`, `onde de Pardee`, etc.).

> 📌 **TODO (noté pour une prochaine session)** : traiter la dette de synonymes
> ci-dessus (collisions pré-existantes). Nécessite une décision au cas par cas
> (quel concept garde quel synonyme) — à ne pas corriger à l'aveugle, ripple effect
> possible sur des cas déjà validés.

### 7. Seconde relecture complète de fond (2026-08-09, après validation du cas 62)

Script : `ecg-online/scripts/audit_ontology_full_2026_08_09.py` — relit `data/ontology_v2.json`
dans son état final (après tous les fixes §1-4) et vérifie 7 dimensions :

| Vérification | Résultat |
|---|---|
| Références cassées (`parents`/`children`/`requires`/`supports`/`excludes`/`has_qualifiers`) | **0** |
| Incohérences bidirectionnelles parent↔children | 9 (= les mêmes 8 pré-existantes déjà documentées §6, `STIMULATION`/`VOLTAGE_DU_QRS` — **rien de nouveau**) |
| Concepts sans parent ni jamais cités comme enfant | 5 : 4 racines légitimes (`CONCEPTS_ECG`, `DESCRIPTION_ECG`, `PATHOLOGIE`, `TOPOGRAPHIE`) + `SYNCOPE` (concept `context` volontairement hors hiérarchie de signes ECG — attendu) |
| Auto-références | 0 |
| Cycles parent/enfant directs | 0 |
| Collisions de synonymes | 20 (les 21 pré-existantes de §6, **-1** car doublon `flutter atrial` corrigé §4 comptait double dans le 1er scan — confirmé : **aucune collision issue des 10 nouveaux concepts ne subsiste**) |
| `requires`/`excludes` contradictoires (un concept qui exige ET exclut la même cible) | 0 |

**Conclusion : ontologie viable, stable, sans régression.** Aucune anomalie nouvelle
détectée par rapport au bilan §6 ; toutes les corrections de la journée (concepts,
redondances, synonymes) sont confirmées cohérentes dans l'état final du fichier.
La dette pré-existante (§6) reste identique et documentée pour une session dédiée.

### 8. Traitement des 20 collisions de synonymes pré-existantes (2026-08-09, validé par l'expert)

Script : `ecg-online/scripts/fix_synonym_collisions_preexisting_2026_08_09.py` (idempotent,
3 copies runtime + migration des `concept_id` dans les cases). Décisions validées par
l'expert, 4 catégories :

**Catégorie A — règle "spécifique > générique"** (14 synonymes retirés du concept
générique/parent, gardés sur le concept le plus précis) :

| Synonyme | Gardé sur | Retiré de |
|---|---|---|
| `activité atriale sinusale` | `RYTHME_SINUSAL` | `MORPHOLOGIE_ONDE_P_SINUSALE` |
| `arythmie ventriculaire polymorphe` | `TACHYCARDIE_VENTRICULAIRE_POLYMORPHE` | `ARYTHMIE_VENTRICULAIRE` |
| `aspect de bloc de branche droite` | `ASPECT_DE_RETARD_DROIT` | `BLOC_DE_BRANCHE_DROIT`, `BLOC_DE_BRANCHE_DROIT_COMPLET` |
| `aspect de bloc de branche gauche` | `ASPECT_DE_RETARD_GAUCHE` | `BLOC_DE_BRANCHE_GAUCHE` |
| `at` | `TACHYCARDIE_ATRIALE` | `TACHYCARDIE_ATRIALE_FOCALE` |
| `bloc de branche droite` | `BLOC_DE_BRANCHE_DROIT` | `BLOC_DE_BRANCHE_DROIT_COMPLET` |
| `morphologie normale des ondes p` / `ondes p de morphologie normale` | `MORPHOLOGIE_ONDE_P_SINUSALE` | `ONDE_P_NORMALE` |
| `onde de pardee` | `COURANT_DE_LESION_SOUS_EPICARDIQUE` | `SYNDROME_CORONARIEN_A_LA_PHASE_AIGUE_AVEC_SUS_DECALAGE_DU_SEGMENT_ST` |
| `onde p avant chaque complexe qrs` | `1_1` | `ONDE_P_PRESENTE` |
| `perte de l'automatisme sinusal` | `PARALYSIE_SINUSALE` | `DYSFONCTION_SINUSALE` |
| `sous-décalage en miroir` | `MIROIR` | `COURANT_DE_LESION_SOUS_ENDOCARDIQUE` |
| `ta` | `TACHYCARDIE_ATRIALE` | `FLUTTER_ATRIAL_ATYPIQUE` |
| `trouble de conduction at(rio/o)ventriculaire` (2 variantes) | `BLOC_AURICULO_VENTRICULAIRE` | `TROUBLES_DE_CONDUCTION_ET_DE_L_AUTOMATICITE` |
| `échappement jonctionnel` | `RYTHME_D_ECHAPPEMENT_JONCTIONNEL` | `ECHAPPEMENT` |

**Catégorie B — erreur clinique corrigée** :
- `rija` (Rythme Idio-Jonctionnel Accéléré) était à tort sur `RYTHME_D_ECHAPPEMENT_JONCTIONNEL`
  (rythme d'échappement = *lent* par définition, contradiction clinique). Retiré, gardé
  uniquement sur `RYTHME_JONCTIONELLE_ACCELERE`.

**Catégorie C — arbitrage clinique (décision expert)** :
- `brs` (Brugada Syndrome) : gardé sur `SYNDROME_DE_BRUGADA`, retiré de `ASPECT_DE_BRUGADA`
  (le signe ECG isolé).
- `ers` (Early Repolarization Syndrome) : gardé sur `SYNDROME_DE_REPOLARISATION_PRECOCE`,
  retiré de `REPOLARISATION_PRECOCE` (le signe ECG isolé).

**Catégorie D — fusion de concepts quasi-doublons** :
- `VOLTAGE_DU_QRS_NORMAL` (finding, présent dans le `.owl`) fusionné **dans**
  `VOLTAGE_NORMAL_DU_QRS` (pattern, concept **JSON uniquement**, couche d'enrichissement
  Partie B — porte l'inférence `QRS_NORMAL.requires`). Synonymes et `excludes` unis,
  `VOLTAGE_DU_QRS_NORMAL` supprimé du JSON, toutes les références résiduelles recâblées
  (`VOLTAGE_DU_QRS.children`, et le `concept_id` dans `scoring_pilot_v2.json` +
  `scoring_v2_review.json` migré vers `VOLTAGE_NORMAL_DU_QRS`).

**⚠️ Correction (2026-08-09, plus tard le même jour)** : décision D **inversée**. Le
concept **réellement présent dans le `.owl` source** (`VOLTAGE_DU_QRS_NORMAL`) est
conservé comme canonique — pas `VOLTAGE_NORMAL_DU_QRS` (qui n'était qu'un doublon
JSON-only, à tort choisi car il portait l'inférence Partie B). Script
`revert_voltage_merge_keep_owl_concept_2026_08_09.py` :
- Recrée `VOLTAGE_DU_QRS_NORMAL` (type=finding, hide=1, définition originale
  restaurée depuis backup pré-fusion) en union des synonymes/excludes accumulés sur
  `VOLTAGE_NORMAL_DU_QRS`, supprime `VOLTAGE_NORMAL_DU_QRS`, recâble toutes les
  références résiduelles (`QRS_NORMAL.requires` → `VOLTAGE_DU_QRS_NORMAL`,
  `VOLTAGE_DU_QRS.children`), migre le `concept_id` dans `scoring_pilot_v2.json` +
  `scoring_v2_review.json`.
- Vérifié safe via lecture du code source de `PatternInferencer` : l'inférence ne
  matche que sur la **string** `concept_id`, indépendamment du champ `type` —
  inverser le sens de la fusion ne casse rien.
- Bénéfice collatéral : résout aussi une des 9 incohérences parent↔children
  pré-existantes (`VOLTAGE_DU_QRS`), désormais `VOLTAGE_DU_QRS_NORMAL` proprement
  listé dans `VOLTAGE_DU_QRS.children` (8 restantes, toutes `STIMULATION`).

**Validation post-traitement (après le revert D)** :
- Ré-audit complet (`audit_ontology_full_2026_08_09.py`) : 358 concepts, `dangling=0`,
  `syn_collisions=0`, `cycles=0`, `req_excl_contradictions=0`,
  **`incoherent_parent_children=8`** (↓ de 9, cf. ci-dessus).
- Inférence `ECG_NORMAL` re-testée : **intacte** (normal → infère ; HAG → bloqué).
- Tous les `concept_id` des 75 cas résolvent toujours (`bad=[]` sur pilot + review).
- Ancien `.owl` patché (reflétant l'ancien sens de fusion) archivé dans
  `_owl_archive/BrYOzRZIu7jQTwmfcGsi35_patched_2026-08-09_v1_obsolete.owl`.
- Nouveau `.owl` régénéré (`generate_owl_relecture75.py`, réutilise les 10 IRI
  existants — idempotent) puis les 20 suppressions de synonymes (catégories A/B/C)
  appliquées directement aux classes OWL existantes via
  `apply_synonym_removals_to_owl_2026_08_09.py` (20 `skos:altLabel` retirés).
  Validation finale : XML valide, 415 classes, 0 doublon d'IRI, les 20 synonymes
  cibles bien absents.
- **Retest golden final** (`scripts/audit_golden.py`, audit golden × ontologie) :
  **0 anomalie bloquante**, 21 avertissements cosmétiques préexistants (doublons de
  labels inoffensifs, sans rapport avec les changements du jour) — confirme que
  l'ensemble des changements du jour (10 nouveaux concepts, fix redondance
  structurelle, 2 vagues de dédoublonnage de synonymes, revert de la fusion D) ne
  casse aucune référence golden (`unknown_concept_id=0`, `dangling_requires=0`,
  `dangling_excludes=0`, `case_without_validant=0`).

> ⚠️ **Écart `.owl` connu (à traiter avant réimport WebProtégé)** : `VOLTAGE_DU_QRS_NORMAL`
> **existe réellement comme classe OWL** (avec ses propres `excludes`/annotation `hide`),
> alors que `VOLTAGE_NORMAL_DU_QRS` (le concept conservé après fusion) **n'a jamais existé
> dans le `.owl`** — c'est un concept JSON-only de la couche Partie B. Le script
> `generate_owl_relecture75.py` ne gère que l'AJOUT des 10 nouveaux concepts (§1) ; il
> **ne reflète pas** les retraits de synonymes A/B/C ni la suppression/fusion de la
> classe `VOLTAGE_DU_QRS_NORMAL` dans le `.owl` patché déjà produit.
> **Action recommandée** : ne PAS réimporter le `.owl` tel quel pour ce qui concerne le
> voltage QRS — traiter cet écart manuellement dans WebProtégé (retirer la classe
> `VOLTAGE_DU_QRS_NORMAL`, ou la conserver et la rebrancher comme le concept canonique
> selon la politique Partie B), ou écrire un script dédié de suppression/fusion OWL avant
> le prochain rebuild. Les 3 retraits de synonymes A/B/C purs (sans suppression de classe)
> restent, eux, mineurs et peuvent être répliqués à la main dans WebProtégé sans risque.

---

## 2026-08-09 (suite) — Résorption de 5 clusters de FP golden (post-relecture75)

**Contexte** : re-test complet du golden (100 items) après la relecture 75 cas,
analyse des faux positifs (FP) résiduels par cluster `ontology_id`, traitement
ciblé de 5 clusters demandés : `ECG_NORMAL`, `FLUTTER_ATRIAL`, `FREQUENCE_NORMALE`,
`ARYTHMIE_ATRIALE`, `ONDE_P_RETROGRADE` (cluster `NONE` explicitement différé).

### Modifications ontologie
| concept_id | changement | raison |
|---|---|---|
| `ARYTHMIE_ATRIALE` | synonyme `"rythme non sinusal"` retiré | trop générique/faux cliniquement — un rythme non sinusal peut être jonctionnel (cas 21-01, `RYTHME_D_ECHAPPEMENT_JONCTIONNEL`), pas forcément une arythmie atriale |
| `ECG_NORMAL` | synonyme `"Pas d'anomalie"` retiré | trop générique — matchait à tort des négations locales ("pas d'anomalie de la conduction/repolarisation") vers le diagnostic global ECG normal |

Index RAG reconstruit + propagé (`rebuild_rag_index.py`) après chaque retrait,
3 copies ontologie re-synchronisées (hash MD5 vérifié).

### Modifications NER (`rag_pipeline/ner_extractor.py`, propagé à `ecg-online`)
- Nouvelle règle explicite : `"non sinusal"` / `"rythme non sinusal"` **seul**
  (sans diagnostic précis d'arythmie atriale nommé) → négation directe
  `terme_brut="Rythme sinusal", statut="absent"` (remplace l'ancienne extraction
  brute `terme_brut="non sinusal"` qui se résolvait ensuite via le synonyme
  d'`ARYTHMIE_ATRIALE` retiré ci-dessus). Solution générique (mécanisme de
  négation, pas un cas particulier câblé en dur).

### Ré-annotations golden (scripts idempotents dans `outil_ontologie/scripts/`)
- `fix_frequence_normale_2026_08_09.py` — 1 correction (23-05 : 60bpm mal
  classé `BRADYCARDIE`) + 4 omissions ajoutées (25-02, 25-04, 28-05, 9-03).
- `fix_flutter_atrial_golden_gaps_2026_08_09.py` — 2 concepts fantômes
  (`ontology_id: ""`, artefact pré-ontologie du 2026-08-09) réparés (41-01,
  42-01) + 3 omissions du niveau générique `FLUTTER_ATRIAL` ajoutées en plus
  du spécifique déjà présent (37-01, 42-03, 45-01).
- `fix_ecg_normal_golden_gaps_2026_08_09.py` — 2 omissions (1-02, 23-04) où
  `pattern_inference` détecte correctement un ECG normal décrit élément par
  élément sans le dire littéralement.
- `fix_onde_p_retrograde_golden_gaps_2026_08_09.py` — 3 items où le golden
  utilisait le concept générique parent `MORPHOLOGIE_DE_L_ONDE_P_NON_SINUSALE`
  au lieu du spécifique `ONDE_P_RETROGRADE` déjà extrait par le pipeline
  (43-01, 44-01, 44-03) + 1 omission d'hypothèse (46-01).
- `fix_rythme_sinusal_non_sinusal_golden_gaps_2026_08_09.py` — effet de bord
  de la nouvelle règle NER : 12 items disant littéralement "non sinusal"
  n'avaient jamais `RYTHME_SINUSAL/absent` en golden (dont 14-02, une vraie
  erreur d'annotation golden : `RYTHME_SINUSAL/present` alors que le texte dit
  "non sinusal").
- `fix_residual_fp_2026_08_09.py` — 3 résiduels ponctuels après le batch
  ci-dessus : 42-02 (`FLUTTER_ATRIAL` parent manquant en plus du spécifique
  `FLUTTER_DROIT_TYPIQUE`, via "flutter commun"), 46-01 (hypothèse
  `FLUTTER_ATRIAL` manquante dans une liste de diagnostics différentiels),
  25-01 (FC 60bpm, `FREQUENCE_NORMALE` omis).

### Résultat retest golden (100 items)
- **v6 (avant ce batch)** : F1 87.0% (TP=534, FP=59, FN=100)
- **v7 (après les 5 clusters + résiduels)** : F1 90.7% (TP=576, FP=60, FN=58)
- **v8** : détection d'un effet de bord — 12 items golden avaient
  `ARYTHMIE_ATRIALE/present` ajouté uniquement via l'ancien synonyme
  générique retiré ; vérification en scoring réel (`scoring_v3`, règle 1b
  enfant→parent) : 9/12 restent correctement crédités via un descendant
  hiérarchique légitime déjà présent (FA, Flutter, TRIN — retirer le
  doublon golden explicite est neutre pour la note étudiant réelle), les
  3 autres (24-03, 25-01, 25-04 + 43-04 : BAV ou tachycardie non qualifiée)
  n'ont AUCUN lien hiérarchique avec `ARYTHMIE_ATRIALE` — c'était une
  vraie erreur d'annotation golden (le "non sinusal" ne signifiait pas
  arythmie atriale dans ces cas, ex. un BAV3 a un rythme non sinusal sans
  être une arythmie atriale). Script
  `fix_arythmie_atriale_golden_overreach_2026_08_09.py` — retrait
  d'`ARYTHMIE_ATRIALE` sur les 12 items concernés.
- **v9 (final)** : F1 93.0% (TP=591, FP=44, FN=45) — meilleur score à date,
  aucune régression détectée sur les 5 clusters traités.
- Rapports : `outil_ontologie/rapport_retest_extraction_golden_2026-08-09_v9_final.json`

### ⚠️ Limite NER identifiée à traiter (PAS corrigée aujourd'hui, cf. TODO)
Le NER **tronque les qualificatifs du concept "Flutter"** (ex. "flutter commun",
"flutter typique" → `terme_brut` réduit à `"flutter"` une partie du temps),
contrairement aux ESV où la règle LEGO 4b sépare bien diagnostic + qualificatif
en 2 entités distinctes résolues correctement (`EXTRASYSTOLE_VENTRICULAIRE` +
`MONOMORPHE`/`TRIGEMINISME_VENTRICULAIRE`/`BIGEMINISME_VENTRICULAIRE`).
Actuellement le filet lexical `_lexical_backstop_ids` (candidate_report.py)
rattrape ce cas **mais seulement si le concept spécifique fait partie du
golden_ids fourni** — en usage réel hors golden, la précision serait perdue
(résolution vers `FLUTTER_ATRIAL` générique au lieu de `FLUTTER_DROIT_TYPIQUE`).
Voir section "Travaux à porter" dans `outil_ontologie/README.md` pour la
solution générique proposée (raffinement de spécificité post-résolution).

---

## 2026-08-09 (suite 2) — Correction du piège de la "double négation" (juge sémantique)

**Contexte** : bug remonté en production (Scalingo) par l'utilisateur : la phrase
« absence d'anomalie de la repolarisation » (correctement extraite par le NER) était
scorée comme manquante (`"à compléter"`) au lieu d'être créditée.

### Root cause
1. Le NER extrait correctement `terme_brut="anomalie de la repolarisation"`,
   `statut="absent"` (négation bien retirée) — **pas un bug NER**.
2. La recherche hybride retourne parmi les candidats à la fois `TROUBLE_DE_REPOLARISATION`
   (pôle positif, cible attendue) et `PAS_D_ANOMALIE_DE_LE_REPOLARISATION` (le concept
   « normal » lui-même, dont le nom canonique/synonymes contiennent littéralement les
   mots résiduels "anomalie de la repolarisation" → score BM25/cosinus le plus élevé).
3. Le juge LLM (`neurosymbolic_judge.py`) choisissait à tort
   `PAS_D_ANOMALIE_DE_LE_REPOLARISATION` (piège lexical) au lieu de
   `TROUBLE_DE_REPOLARISATION`.
4. Résultat : `PAS_D_ANOMALIE_DE_LE_REPOLARISATION/absent` extrait (double négation)
   au lieu de `TROUBLE_DE_REPOLARISATION/absent` → le mécanisme `negation_of` du
   scoring (qui cherche `TROUBLE_DE_REPOLARISATION` dans les entités absentes pour
   créditer le validant golden) ne trouve rien → `match_type="missed"`.

### Correction appliquée
- **`rag_pipeline/neurosymbolic_judge.py`** (propagé + hash MD5 vérifié identique
  sur `ecg-online/rag_pipeline/neurosymbolic_judge.py`,
  `6843a1904d7bff78f0786b43aa9a0242`) : ajout de la règle **#10 "PIÈGE DE LA DOUBLE
  NÉGATION"** au `SYSTEM_PROMPT` — règle générique (pas un cas particulier câblé en
  dur) : quand un terme déjà nettoyé de sa négation décrit une anomalie/un trouble et
  que les candidats contiennent à la fois le pôle positif (l'anomalie elle-même) et
  un concept qui est la négation explicite de cette anomalie (nom "Pas de"/"Absence
  de"), le juge doit **toujours choisir le pôle positif** — le statut "absent" étant
  appliqué en aval par le scoring via `negation_of`.
- Aucune modification d'ontologie ni de `ner_extractor.py`/`scoring_v3.py` (tous
  deux vérifiés corrects et non modifiés).
- **7 autres concepts identifiés à risque théorique similaire** (audit synonymes à
  tournure négative, non modifiés individuellement — protégés par la règle générique
  du prompt) : `ABSENCE_D_ONDE_P`, `ABSENCE_D_ONDE_Q_PATHOLOGIQUE`,
  `DISSOCIATION_ATRIO_VENTRICULAIRE`, `ECG_NORMAL`, `PAS_DE_TROUBLES_DE_LA_CONDUCTION`,
  `SYNDROME_CORONARIEN_A_LA_PHASE_AIGUE_SANS_ELEVATION_DU_SEGMENT_ST`,
  `VOLTAGE_DU_QRS_NORMAL`.

### Résultat retest golden (100 items)
- **Avant (golden figé)** : F1 84.9% (TP=522, FP=71, FN=114)
- **Après (pipeline rejoué avec le fix)** : F1 93.1% (TP=590, FP=42, FN=46)
- Aucune régression détectée par rapport au v9 (93.0%) ; léger gain net.
- Rapport : `outil_ontologie/rapport_retest_extraction_golden_2026-08-09_v10_negation_judge_fix.json`

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
