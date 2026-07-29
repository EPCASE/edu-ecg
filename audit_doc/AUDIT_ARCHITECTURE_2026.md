# 🏗️ AUDIT ARCHITECTURE, GÉNÉRICITÉ & HYGIÈNE DE REPO — 2026-07-29

> 🔒 **Figé le 2026-07-30** — constat + recommandations, aucune action
> destructive exécutée. À reprendre seulement si un chantier de nettoyage
> repo est explicitement décidé. Voir `roadmap_scientifique_2026.md` (actif)
> et `audit_doc/README.md` (index).

> **Périmètre** : les 4 workspaces (`ECG lecture`, `RAG ontologique`, `ECG evaluation`, `ECG collector`).
> **Distinct de** `AUDIT.md` (qui porte sur la robustesse scientifique du scoring/extraction — toujours
> valide, non remis en cause ici).
> **Objectif** (verbatim) : mettre à plat l'architecture, s'assurer que les briques sont génériques
> (éviter les "patchs"), anticiper le passage à l'anglais, identifier alternatives/améliorations,
> organiser le repo, supprimer les fichiers inutiles, mettre à jour la doc, supprimer les doublons.
> **Statut** : document de constat + recommandations. **Aucune action destructive n'a été exécutée.**
> Toute suppression/fusion listée ci-dessous doit être validée explicitement avant exécution.

---

## 0. Résumé exécutif

| Angle | État constaté | Sévérité |
|---|---|:---:|
| 1. Architecture générale | 4 workspaces non liés (pas de monorepo), 1 seul déployé (`ecg-online`) | 🟡 |
| 2. Généricité vs patchs | **Bonne nouvelle** : aucun ID/cas codé en dur trouvé, code auto-documenté générique | 🟢 |
| 3. Anglicisation | Ontologie déjà bilingue en données (`concept_name_en`), mais **jamais utilisée** à l'exécution ; prompts/UI 100 % FR en dur | 🟡 |
| 4. Alternatives / pistes IA | Déjà couvert en grande partie par `AUDIT.md` §7 ; renvoi + compléments | 🟢 |
| 5. Organisation du repo | Dette réelle mais localisée et facile à traiter | 🟡 |
| 6. Fichiers inutiles | 865 Mo d'exports HTML jetables, logs de debug, doublons `.owl`/`rag_index` | 🟡 |
| 7. Documentation | 3 copies de `ARCHITECTURE_PIPELINE.md`, 2 de `ARCHITECTURE.md`, chiffres obsolètes dans certaines | 🟡 |
| 8. Doublons de code | **Résolu (2026-07-29)** : `RAG ontologique` supprimé entièrement (confirmé inutilisé par `ecg-online` et par l'utilisateur) | ✅ |

**Verdict global** : pas de dette architecturale profonde (le cœur du pipeline est propre et générique),
mais une dette **d'hygiène de repo et de synchronisation** significative, concentrée sur un petit nombre
de causes précises et **peu risquées à corriger** une fois identifiées.

---

## 1. Mettre à plat l'architecture

### 1.1 Vue d'ensemble réelle

```
C:\Users\Administrateur\
├── bmad\
│   ├── ECG lecture\              ← contient le SEUL déployable réel
│   │   ├── ecg-online\           ← app Flask + rag_pipeline VENDORÉ (copie)
│   │   ├── rag_pipeline\         ← 2e copie locale (racine ECG lecture, hors ecg-online !)
│   │   ├── _standalone\          ← 3e copie quasi-complète (app + pipeline + docs)
│   │   ├── backend\              ← extracteur RDF/OWL, usage ponctuel
│   │   ├── dossier_ecole\        ← documents à destination de l'école (non technique)
│   │   └── 4x fichiers .owl à la racine (versions de l'ontologie source)
│   ├── ~~RAG ontologique\~~     ← 🗑️ SUPPRIMÉ (2026-07-29) : inutilisé par ecg-online, confirmé par l'utilisateur
│   └── ECG evaluation\           ← notebooks d'évaluation + scripts d'audit ponctuels
└── ECG collector\                ← Google Sheets backend (collecte des réponses étudiantes)
```

**Constat clé (mis à jour 2026-07-29)** : ce n'était pas "4 workspaces" au sens propre, c'était plutôt
**1 code source (`rag_pipeline`) recopié en 4 endroits**. Trois des quatre copies mortes ont été
supprimées au fil de cet audit (`ECG lecture/rag_pipeline`, `ECG lecture/_standalone`, et enfin
`RAG ontologique` lui-même) — il ne reste plus qu'**une seule copie du pipeline** :
`ecg-online/rag_pipeline` (déployée et confirmée comme unique source de vérité).

### 1.2 Flux de données réel

```
ECG collector (Google Sheets)          ← étudiants soumettent leurs interprétations
        ↓ (export CSV / API Sheets)
ECG evaluation (notebooks + goldenset) ← analyse offline, construction golden, métriques
        ↓ (fichiers golden .json copiés à la main)
ecg-online/data (cases_golden.json...) ← consommé par l'app en production
        ↓
ecg-online/app/*.py                    ← Flask, orchestration
        ↓
ecg-online/rag_pipeline/*.py           ← NER, recherche hybride, scoring, juge LLM
        ↓
ecg-online/rag_pipeline/data/ontology_v2.json  ← ontologie (source de vérité unique)
```

**Point de friction identifié → résolu (2026-07-29)** : `RAG ontologique` était censé être le lieu
historique de maintenance de l'ontologie, mais l'utilisateur a confirmé ne l'utiliser ni directement
ni via `ecg-online`. Les 2 scripts qui y faisaient encore référence (`rebuild_ontology_from_owl.py`,
`make_virtual_students.py`) ont été corrigés pour pointer vers `ecg-online/rag_pipeline` (source
unique). Un 3e script (`ECG collector/send_corrections.py --generate`) référençait un
`export_corrections_json.py` déjà absent de `RAG ontologique` (option déjà cassée avant suppression) —
commentaire mis à jour, option non fonctionnelle assumée.

### 1.3 Recommandation

Pas de refonte architecturale nécessaire — l'architecture neurosymbolique elle-même (NER → recherche
hybride → juge LLM → scoring symbolique) est saine et déjà documentée comme telle dans `AUDIT.md` §6.
Le vrai sujet est la **consolidation de la duplication** (§8) plutôt qu'un changement de conception.

---

## 2. Généricité des briques vs "patchs correctifs"

### 2.1 Méthode

Recherche systématique dans `app/*.py` et `rag_pipeline/*.py` (copie de production `ecg-online`) de :
- IDs de concepts ou numéros de cas codés en dur (`concept_id == "..."`, `cas_id == N`) ;
- marqueurs de dette explicite (`TODO`, `FIXME`, `HACK`, `XXX`, "temporaire", "à corriger plus tard").

### 2.2 Résultat : constat rassurant

**Aucune occurrence** des deux catégories ci-dessus n'a été trouvée dans le code de production.
Au contraire, le code **s'auto-documente comme générique** à plusieurs endroits, ex. `scoring_v3.py` :

```python
"""Moteur GÉNÉRIQUE : aucun couple codé en dur, tout est lu dans l'ontologie."""
```

et `candidate_report.py` :
```python
# ... qu'aucune `excludes_families` n'est présente. Aucun ID codé en dur.
```

Les branchements conditionnels trouvés (`if cs.match_type == "exact"`, `"requires"`, `"qualifier"`...)
sont des **types de statut génériques**, pas des cas particuliers métier — c'est le design normal
d'une machine à états de scoring, pas un patch.

### 2.3 Nuance : où sont les "vrais" patchs, alors ?

Ils existent, mais **pas dans le code** — ils sont dans les **données** :
- `scripts/_fix_phase_e_conflicts.py` (session précédente) corrige des données (`cases_golden.json`)
  cas par cas, mais c'est documenté comme un script de correction ponctuelle assumé (convention `_*.py`),
  pas une logique cachée dans le pipeline.
- Les commentaires trouvés dans `scoring_v3.py`/`ner_extractor.py` autour du "coup du sort" sur
  `RYTHME_SINUSAL`/`req_score > 0` montrent que les correctifs récents sont bien de vrais **fixes de
  bug généraux** (règle de seuil), pas des `if concept == X`.

**Conclusion** : la crainte initiale ("s'assurer que les briques soient suffisamment génériques et
éviter les patchs correctifs") **ne se vérifie pas** dans le pipeline actuel. C'est un point fort à
mettre en avant dans la documentation/soutenance, pas un chantier à mener.

---

## 3. Anticiper le passage à l'anglais

### 3.1 Ce qui est déjà prêt

- L'ontologie (`ontology_v2.json`, ~650 concepts) a un champ `concept_name_en` **rempli pour chaque
  concept** (ex. `"concept_name_en": "Type 1 Brugada pattern"`). Le travail terminologique de traduction
  a donc déjà été fait, au moins pour les noms de concepts.
- `convert_owl_to_v2.py` sait déjà peupler ce champ depuis l'OWL source (labels multilingues RDF).

### 3.2 Ce qui bloque un passage à l'anglais aujourd'hui

| Composant | Statut EN | Détail |
|---|---|---|
| `ontology_v2.json` (noms de concepts) | 🟢 Prêt | `concept_name_en` peuplé, mais **jamais lu** par `app/`/`rag_pipeline/` à l'exécution |
| Synonymes ontologiques (`synonymes`) | 🔴 Absent | Uniquement en français ; le matching lexical/NER perdrait tout rappel sur un texte anglais |
| `SYSTEM_PROMPT` (NER, juge, annotateur GPT, feedback pédagogique) | 🔴 Français en dur | 4 prompts système distincts, tous rédigés en français, aucune variante EN |
| Frontend (`frontend/*.html/.js`) | 🔴 Français en dur | Libellés UI non extraits dans un fichier de traduction |
| Aucune couche i18n/locale | 🔴 Absent | Pas de paramètre `lang=`, pas de `gettext`/fichiers `.po`/`.json` de traduction, nulle part dans le code |

### 3.3 Recommandation (chantier futur, pas urgent)

Si l'anglais devient un objectif réel (ex. publication internationale, cohorte non-francophone) :
1. Ajouter un paramètre `lang` traversant `app/server.py` → `rag_pipeline/*` → prompts.
2. Dupliquer chaque `SYSTEM_PROMPT` en version EN (travail de traduction médicale, pas de refonte).
3. Ajouter un champ `synonymes_en` à l'ontologie (reprendre la méthode déjà utilisée pour les
   synonymes FR, cf. `_apply_synonymes_C.py` en référence historique).
4. Extraire les chaînes du frontend dans un petit dictionnaire de traduction JS.
**Effort estimé** : moyen, bien cadré, aucun obstacle architectural — la séparation actuelle
(ontologie/prompts/UI comme couches distinctes) rend ce travail *additif*, pas une réécriture.

---

## 4. Solutions alternatives / pistes d'amélioration

Le tableau `AUDIT.md` §7 ("Lien avec les développements récents de l'IA") couvre déjà l'essentiel
(LLM-as-Judge encadré, embeddings médicaux locaux, juge local Mistral/Llama, raisonneur OWL, juge
multimodal). Compléments identifiés lors de cet audit :

| Piste | Motivation | Effort |
|---|---|:---:|
| **Synchronisation automatique de l'ontologie** (script qui pousse `RAG ontologique` → toutes les copies vendorées, ou single-source + symlink) | Élimine la classe de bugs découverte au §8 (code obsolète silencieux) | Faible |
| **Externaliser `scoring_thresholds` en config versionnée unique** (déjà commencé, cf. `scoring_v3.py` qui l'importe) | Un seul fichier de vérité pour les seuils, partagé par toutes les copies packagées | Faible |
| **Packager `rag_pipeline` comme dépendance pip installable** (même en local, `pip install -e .`) | Remplace la copie manuelle par une vraie gestion de dépendance ; réduit le risque de divergence à zéro | Moyen |
| **CI légère (GitHub Actions) lançant `pytest` à chaque push** | Les 18 tests existants (`test_scoring_v3.py`) ne sont actuellement lancés que manuellement | Faible |

---

## 5 & 6. Organisation du repo & fichiers inutiles (proposition — non exécutée)

> ⚠️ **Rien n'a été supprimé.** Liste de candidats à valider un par un avant toute suppression.

### 5.1 Candidats suppression à fort impact / faible risque

| Cible | Taille | Justification |
|---|---:|---|
| `RAG ontologique/_ARCHIVE_2026-07-06/exports/*.html` (8 fichiers) | **865.6 Mo** | Exports de rapports HTML d'avril 2026, aucune valeur code, jamais référencés ailleurs |
| `ecg-online/*.log` (`review_stderr.log`, `review_stdout.log`, `server_stderr.log`, `server_stdout.log`) | ~80 Ko | Logs de debug de sessions passées, doivent être dans `.gitignore`, pas versionnés |
| `ecg-online/references_review.html`, `ecg-online/ecg_gallery_75.html` | ~815 Ko | Pages HTML de travail ponctuel (galerie/revue), pas de valeur pérenne à la racine |
| `ecg-online/docs/datareuters.md` | — | ✅ Supprimé (2026-07-29) — confirmé sans rapport avec le projet |
| `RAG ontologique/rag_index.bak_20260705_084652` | 4 Mo | Sauvegarde ponctuelle de l'index vectoriel, redondante avec `rag_index/` actuel |

### 5.2 Candidats fusion (pas suppression pure)

| Cible | Constat | Proposition |
|---|---|---|
| 4 fichiers `.owl` à la racine `ECG lecture/` (`BrYOzRZIu7jQTwmfcGsi35.owl`, `V1`, `_patched_2026-07-05`, `_ref_2026-07-06`) | 4 versions de la même ontologie source, ~400-515 Ko chacune, noms peu explicites | Garder uniquement la plus récente sous un nom clair (ex. `ontology_source.owl`), archiver les autres avec un historique Git plutôt que des noms de fichiers différents |
| `RAG ontologique/rag_index/` vs `rag_index_local/` | ✅ Clarifié et résolu (2026-07-29) : `rag_index_local` supprimé (résidu A/B test inutilisé). Puis **`RAG ontologique` supprimé dans son intégralité** (confirmé inutilisé, ni en dev ni par `ecg-online`) — n'a donc plus lieu d'être dans ce tableau |
| `ECG lecture/_standalone/` | ✅ Fait (2026-07-29) : supprimé, aucune valeur unique trouvée |

### 5.3 Scripts jetables `_*.py` (à conserver mais organiser)

- ✅ **Fait (2026-07-29)** : `ECG evaluation/goldenset_extraction/` — 42 scripts des catégories
  DIAG/SIM/CHECK/SMOKE/TEST/DEBUG supprimés après vérification qu'aucune interdépendance ni
  référence externe n'existait (aucun `import` croisé, aucun notebook actif ne les exécutait).
  Leur substance a été préservée dans `CAHIER_HISTORIQUE_DEV_2026-07.md` (même dossier) avant
  suppression — synthèse par fil d'investigation (axe ECG_NORMAL, rattrapage lexical, inférence
  `requires`...) reliant ces scripts aux correctifs aujourd'hui présents dans le pipeline de
  production. Les 43 scripts restants (`_apply_*`, `_propagate_*`, `_propose_*`, `_inspect_*`,
  `_audit_*`, `_inventory_*`, `_list_*`, `_pilot_*`, `_read_*`, `_verify_*`, `_hier_*`, `_diff_*`,
  `_fn_lever_*`, `_c_*`, `_eval_*`, `_cmp_*`, `_show_*`, `_health_*`, `_preflight_*`,
  `_ner_adapters.py`, `_replay_inference.py`, `_pick_axis_sample.py`, `_build_ft_dataset.py`,
  `_constrained_judge.py`, `_sync_onto_B.py`) sont conservés en l'état — non traités par ce nettoyage.
- `ECG evaluation/archive/` = 33 scripts supplémentaires, non traités (hors périmètre des 3 actions
  demandées le 2026-07-29).

---

## 7. Documentation — inventaire et doublons

### 7.1 Duplication documentaire (corrélée à la duplication de code, §8)

| Doublon | Emplacements |
|---|---|
| `ARCHITECTURE_PIPELINE.md` (×3) | `ECG lecture/_standalone/`, `ECG lecture/rag_pipeline/`, `RAG ontologique/` |
| `ARCHITECTURE.md` (×2) | `ECG lecture/` (racine), `ECG lecture/_standalone/` |
| `README.md` racine pipeline (×2 avec contenu proche) | `ECG lecture/rag_pipeline/README.md`, `RAG ontologique/README.md` |

### 7.2 Documents à mettre à jour en priorité (chiffres obsolètes)

- `ECG lecture/ARCHITECTURE.md` : à vérifier — contient historiquement le chiffre "42 % coupe-circuit"
  cité comme obsolète dans `AUDIT.md` R2 (à recouper et corriger avec les vrais chiffres §4bis de
  `AUDIT.md` : coupe-circuit 96.5 % de précision, 483/650 résolutions).
- Tout README mentionnant encore le "63,7 % d'hallucination" (déjà repéré comme caduc dans `AUDIT.md` §0).

### 7.3 Documents probablement sains (à vérifier rapidement, pas de signal d'alerte trouvé)

`ecg-online/AGENTS.md`, `ecg-online/ROADMAP.md`, `ecg-online/GOLDEN_EXTRACTION.md`,
`ECG lecture/ONTOLOGIE_DOCTRINE.md`, `ECG lecture/PART_B_RUNBOOK.md` — tous récents/déjà mis à jour
lors de sessions précédentes.

### 7.4 Recommandation

Une fois la duplication de code tranchée (§8), supprimer mécaniquement les copies de documentation
correspondant au code supprimé (pas la peine de maintenir 3 `ARCHITECTURE_PIPELINE.md` si 3 des 4
copies de `rag_pipeline` disparaissent).

---

## 8. 🔴 ✅ Doublons de code — RÉSOLU (2026-07-29)

### 8.1 Constat quantifié (historique)

`ecg-online/rag_pipeline/` (copie vendorée, **celle réellement en production**) et
`RAG ontologique/` (copie standalone, historiquement la source) contenaient chacune 12 fichiers
`.py` du pipeline cœur. Comparaison par hash MD5 (avant réalignement) :

| Fichier | Identique ? | Détail si différent |
|---|:---:|---|
| `edn_knowledge_base.py`, `ontology_index.py`, `pattern_inference.py`, `pedagogical_feedback.py`, `semantic_layer.py` | ✅ | — |
| `ner_extractor.py` | ❌ (6 lignes) | `ecg-online` a `temperature=0, seed=42` (fix déterminisme) — **absent** de `RAG ontologique` |
| `hybrid_search.py` | ❌ (6 lignes) | `ecg-online` a un fallback vers un index vendoré local — **absent** de `RAG ontologique` |
| `neurosymbolic_judge.py` | ❌ (4 lignes) | `ecg-online` a `temperature=0, seed=42` — **absent** de `RAG ontologique` |
| `scoring_v3.py` | ❌ (35 lignes) | `ecg-online` a le correctif du bug "requires manquant affiché comme trouvé" (score RYTHME_SINUSAL) — **absent** de `RAG ontologique`, qui contient donc un **bug déjà corrigé ailleurs** |
| `candidate_report.py` | ❌ (182 lignes) | `ecg-online` contient une fonctionnalité entière absente de `RAG ontologique` : `_lexical_backstop_ids` (rattrapage lexical déterministe post-NER, cf. `GOLDEN_EXTRACTION.md`) |
| `scoring_thresholds.py`, `__init__.py` | — | Présents uniquement dans `ecg-online` (n'existent pas dans `RAG ontologique`) |

### 8.2 Conclusion sans ambiguïté

**`ecg-online/rag_pipeline` est strictement en avance sur `RAG ontologique` sur les 5 fichiers
divergents.** Ce n'est pas une divergence "les deux ont des choses différentes à offrir" — c'est un
**instantané figé et daté** de `RAG ontologique`, qui n'a pas reçu les correctifs de fiabilité/
déterminisme faits ensuite dans la copie de production.

**Risque concret** : toute personne (y compris un futur agent IA) qui travaillerait sur
`RAG ontologique` en le croyant "la source de vérité" (ce que son nom suggère) :
- réintroduirait le bug du score RYTHME_SINUSAL déjà corrigé,
- n'aurait pas accès au rattrapage lexical qui améliore la fiabilité du NER,
- travaillerait avec une extraction non-déterministe (sans `seed=42`).

C'est la découverte la plus importante de cet audit — elle transforme "duplication = dette
cosmétique" (vision de `AUDIT.md` R6/P2.10) en "duplication = risque actif de régression".

### 8.3 Résolution finale (2026-07-29)

1. ✅ Source de vérité unique validée : `ecg-online/rag_pipeline`.
2. ✅ `RAG ontologique/*.py` réaligné (Option A), puis le dossier entier a été **supprimé** après
   confirmation par l'utilisateur qu'il n'était utilisé ni comme sandbox de dev, ni par `ecg-online`.
3. ✅ Les 2 autres copies mortes (`ECG lecture/rag_pipeline/`, `ECG lecture/_standalone/`) supprimées.
4. ✅ 3 scripts référençant encore `RAG ontologique` corrigés pour pointer vers `ecg-online/rag_pipeline`
   (source unique) : `rebuild_ontology_from_owl.py`, `make_virtual_students.py`,
   `ECG collector/send_corrections.py` (commentaire mis à jour, option `--generate` déjà non
   fonctionnelle avant suppression).

**Il ne reste plus qu'une seule copie du pipeline dans tout le repo** : `ecg-online/rag_pipeline`.
Le risque de régression silencieuse identifié en §8.2 est désormais éliminé structurellement
(il n'y a plus de copie obsolète à confondre avec la source de vérité).

---

## 9. Plan d'action proposé (ordre suggéré, chaque étape à valider séparément)

| # | Action | Type | Statut |
|---|---|---|:---:|
| 1 | Valider avec l'utilisateur : `ecg-online/rag_pipeline` = source de vérité unique du pipeline | Décision | ✅ Option A validée |
| 2 | Aligner `RAG ontologique/*.py` sur `ecg-online/rag_pipeline/*.py` (copie manuelle) | Correctif | ✅ Fait (hash identiques vérifiés, backup dans `RAG ontologique/_pre_align_backup_20260729/`) |
| 3 | Supprimer `RAG ontologique/_ARCHIVE_2026-07-06/exports/*.html` (865 Mo) | Suppression | ✅ Fait |
| 4 | Nettoyer les logs/HTML de debug à la racine `ecg-online` | Suppression | ✅ Fait (2 logs supprimés, 2 vidés — verrouillés par un serveur dev actif PID 11956/40232, non arrêté) |
| 5 | Clarifier/fusionner les 4 `.owl` et les 3 `rag_index*` | Fusion | ✅ `.owl` : 3 versions archivées dans `_archive_owl_versions/`, 1 active conservée. `rag_index.bak_20260705_084652` (4 Mo) supprimé. `rag_index`/`rag_index_local` : statut inchangé, à clarifier ultérieurement si besoin |
| 6 | Décider du sort de `ECG lecture/_standalone/` et des copies mortes de `rag_pipeline` | Suppression | ✅ Fait — `ECG lecture/rag_pipeline/` (1.55 Mo) et `ECG lecture/_standalone/` (47.46 Mo) supprimés, copie de production `ecg-online/rag_pipeline` vérifiée intacte |
| 7 | Mettre à jour `ARCHITECTURE.md` (chiffres obsolètes) une fois §2 et §8 tranchés | Documentation | ✅ Fait — 5 occurrences "42%" corrigées en "~74%" (chiffre mesuré, cf. `AUDIT.md` §4bis), note ajoutée invalidant le "63,7% hallucination" en §13.0 |
| 8 | Supprimer les documentations dupliquées correspondant au code supprimé | Documentation | ✅ Fait automatiquement — `rag_pipeline/README.md`, `rag_pipeline/ARCHITECTURE_PIPELINE.md`, `_standalone/ARCHITECTURE.md`, `_standalone/ARCHITECTURE_PIPELINE.md` ont disparu avec la suppression de leurs dossiers parents (étape 6). Seul `RAG ontologique/ARCHITECTURE_PIPELINE.md` + `RAG ontologique/README.md` subsistent (workspace toujours actif) |
| 9 | (Optionnel, hors urgence) Chantier anglicisation (§3.3) | Feature | ⬜ Non démarré |
| 10 | Supprimer `RAG ontologique` en intégralité (confirmé inutilisé par l'utilisateur, ni en dev ni par `ecg-online`) | Suppression | ✅ Fait — dossier supprimé (~13 Mo), 3 scripts référençant l'ancien chemin corrigés (`rebuild_ontology_from_owl.py`, `make_virtual_students.py`, `ECG collector/send_corrections.py`) |

**Gain total mesuré à date** : ~930 Mo libérés (865.6 Mo exports + 47.46 Mo `_standalone` + 4 Mo
`rag_index.bak` + 1.55 Mo `rag_pipeline` racine + 2.2 Mo `rag_index_local` + ~13 Mo `RAG ontologique`
restant), et surtout **élimination complète** de la duplication du pipeline (§8) : il ne reste plus
qu'une seule copie de `rag_pipeline` dans tout le repo (`ecg-online/rag_pipeline`).

---

*Audit réalisé le 2026-07-29. Complète `AUDIT.md` (robustesse scientifique) sans le remplacer.
Trame de travail de reconnaissance : `_AUDIT_TRAME_TRAVAIL.md` (jetable, à supprimer une fois ce
document validé et les actions engagées).*
